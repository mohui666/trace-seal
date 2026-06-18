from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from dashboard.export import export_dashboard_data
from minimizer.explain import explain_run
from policy.rules import evaluate_httpx_request
from replay.renderer import replay_run
from sdk.httpx_hooks import SENSITIVE_HEADERS, SENSITIVE_QUERY


class HttpxInterceptionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env.pop("TRACESEAL_POLICY_MODE", None)
        completed = subprocess.run(
            [sys.executable, "-m", "traceseal", "run", "--", sys.executable, "examples/bad_agent_httpx.py"],
            cwd=cls.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            env=env,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(f"httpx demo failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}")
        run_id = (cls.repo / "runs" / "latest").read_text(encoding="utf-8").strip()
        cls.run_dir = cls.repo / "runs" / run_id
        cls.events: list[dict[str, Any]] = [
            json.loads(line)
            for line in (cls.run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        ]
        cls.httpx_events = [event for event in cls.events if event.get("type") == "network.http"]

    def _event(self, source: str, path: str, *, status: str = "ok") -> dict[str, Any]:
        return next(
            event
            for event in self.httpx_events
            if event["input"]["source"] == source
            and event["input"]["path"] == path
            and event["output"]["status"] == status
        )

    def test_function_client_and_async_sources(self) -> None:
        expected_sources = {
            *(f"httpx.{name}" for name in ["get", "post", "put", "patch", "delete", "request"]),
            *(f"httpx.Client.{name}" for name in ["get", "post", "put", "patch", "delete", "request"]),
            *(f"httpx.AsyncClient.{name}" for name in ["get", "post", "put", "patch", "delete", "request"]),
        }
        sources = {event["input"]["source"] for event in self.httpx_events}
        self.assertTrue(expected_sources.issubset(sources))

        successful = [event for event in self.httpx_events if event["output"]["status"] == "ok"]
        self.assertEqual(len(successful), 18)
        self.assertTrue(all(event["operation"] == "httpx.request" for event in successful))
        self.assertTrue(all(event["output"]["status_code"] == 200 for event in successful))
        self.assertTrue(all(event["output"]["success"] for event in successful))
        self.assertTrue(all(isinstance(event["output"]["duration_ms"], int) for event in successful))

    def test_request_metadata_and_redaction(self) -> None:
        normal = self._event("httpx.get", "/function/get")
        sensitive = self._event("httpx.post", "/function/post")

        self.assertEqual(normal["input"]["method"], "GET")
        self.assertEqual(normal["input"]["host"], "127.0.0.1")
        self.assertEqual(normal["input"]["scheme"], "http")
        self.assertEqual(normal["risk"]["level"], "medium")
        self.assertEqual(normal["risk"]["policy_rule"], "insecure_http_request")

        self.assertEqual(sensitive["risk"]["level"], "high")
        self.assertEqual(sensitive["risk"]["policy_rule"], "sensitive_http_request")
        query = dict(parse_qsl(urlsplit(sensitive["input"]["url"]).query, keep_blank_values=True))
        for name in SENSITIVE_QUERY:
            self.assertEqual(query[name], "<redacted>")
        self.assertEqual(query["safe"], "visible-demo-value")
        for name in SENSITIVE_HEADERS:
            self.assertEqual(sensitive["input"]["headers"][name], "<redacted>")
        self.assertEqual(sensitive["input"]["headers"]["x-demo"], "visible-demo-value")

        self.assertEqual(
            evaluate_httpx_request("GET", "https://localhost/demo", scheme="https", host="localhost")["level"],
            "low",
        )
        self.assertEqual(
            evaluate_httpx_request("GET", "https://example.test/demo", scheme="https", host="example.test")["level"],
            "medium",
        )

    def test_bodies_and_secrets_are_not_recorded(self) -> None:
        serialized = json.dumps(self.httpx_events, ensure_ascii=False)
        for secret in [
            "SECRET_TOKEN_SHOULD_NOT_APPEAR",
            "API_KEY_SHOULD_NOT_APPEAR",
            "BODY_SHOULD_NOT_APPEAR",
            "RESPONSE_SHOULD_NOT_APPEAR",
            "RESPONSE_COOKIE_SHOULD_NOT_APPEAR",
        ]:
            self.assertNotIn(secret, serialized)
        for event in self.httpx_events:
            self.assertNotIn("content", event["input"])
            self.assertNotIn("json", event["input"])
            self.assertNotIn("body", event["input"])
            self.assertNotIn("body", event["output"])

    def test_timeout_connection_and_invalid_url_failures(self) -> None:
        failures = [event for event in self.httpx_events if event["output"]["status"] == "exception"]
        exception_types = {event["output"]["exception_type"] for event in failures}
        self.assertIn("ReadTimeout", exception_types)
        self.assertIn("ConnectError", exception_types)
        self.assertTrue(exception_types & {"UnsupportedProtocol", "InvalidURL"})
        self.assertTrue(all(not event["output"]["success"] for event in failures))
        self.assertTrue(all(event["output"]["status_code"] is None for event in failures))

    def test_dashboard_replay_and_explain(self) -> None:
        dashboard = export_dashboard_data(self.run_dir)
        self.assertTrue(any(event.get("type") == "network.http" for event in dashboard["events"]))
        self.assertEqual(dashboard["first_harmful_event"]["risk"]["policy_rule"], "sensitive_http_request")

        replay = replay_run(self.run_dir)
        explain = explain_run(self.run_dir)
        self.assertIn("HTTP 请求", replay)
        self.assertIn("httpx.post", json.dumps(dashboard, ensure_ascii=False))
        self.assertIn("敏感查询参数已脱敏", explain)
        self.assertIn("sensitive_http_request", explain)


if __name__ == "__main__":
    unittest.main()
