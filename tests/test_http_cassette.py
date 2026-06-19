from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock
from urllib.parse import parse_qsl, urlsplit

from dashboard.export import export_dashboard_data
from recorder.http_cassette import BODY_REDACTION, REDACTED, generate_http_cassette
from traceseal.cli import run_command


class HttpCassetteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "-m", "traceseal", "run", "--", sys.executable, "examples/bad_agent_http_cassette.py"],
            cwd=cls.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(f"cassette demo failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}")
        run_id = (cls.repo / "runs" / "latest").read_text(encoding="utf-8").strip()
        cls.run_dir = cls.repo / "runs" / run_id
        cls.events: list[dict[str, Any]] = [
            json.loads(line)
            for line in (cls.run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        ]
        cls.entries: list[dict[str, Any]] = [
            json.loads(line)
            for line in (cls.run_dir / "http_cassette.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        ]

    def _entry(self, method: str) -> dict[str, Any]:
        return next(entry for entry in self.entries if entry["method"] == method)

    def test_no_http_events_produce_empty_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events = root / "events.jsonl"
            events.write_text(json.dumps({"id": "evt_0001", "type": "file.read"}) + "\n", encoding="utf-8")
            summary = generate_http_cassette(events, root / "http_cassette.jsonl")
            self.assertTrue(summary["present"])
            self.assertEqual(summary["entry_count"], 0)
            self.assertEqual(summary["high_risk_count"], 0)
            self.assertEqual(summary["external_host_count"], 0)

    def test_httpx_get_generates_linked_entry(self) -> None:
        entry = self._entry("GET")
        self.assertEqual(entry["source_api"], "httpx.get")
        self.assertEqual(entry["response_status_code"], 200)
        event_ids = {event["id"] for event in self.events if event.get("type") == "network.http"}
        self.assertIn(entry["event_id"], event_ids)

    def test_sensitive_query_and_headers_are_redacted(self) -> None:
        entry = self._entry("POST")
        query = dict(parse_qsl(urlsplit(entry["url_redacted"]).query, keep_blank_values=True))
        for name in ("token", "api_key", "password"):
            self.assertEqual(query[name], REDACTED)
        self.assertEqual(query["safe"], "visible-demo-value")
        headers = {name.lower(): value for name, value in entry["request_headers_redacted"].items()}
        self.assertEqual(headers["authorization"], REDACTED)
        self.assertEqual(headers["x-api-key"], REDACTED)
        self.assertEqual(headers["x-credential-session"], REDACTED)
        self.assertEqual(headers["x-demo"], "visible-demo-value")
        self.assertEqual(entry["response_headers_redacted"]["set-cookie"], REDACTED)
        self.assertEqual(entry["response_headers_redacted"]["x-response-secret"], REDACTED)
        serialized_events = json.dumps(self.events)
        self.assertNotIn("FAKE_TOKEN_FOR_CASSETTE_DEMO", serialized_events)
        self.assertNotIn("FAKE_API_KEY_FOR_CASSETTE_DEMO", serialized_events)
        self.assertNotIn("FAKE_PASSWORD_FOR_CASSETTE_DEMO", serialized_events)

    def test_request_body_is_summary_only(self) -> None:
        summary = self._entry("POST")["request_body_summary"]
        self.assertTrue(summary["present"])
        self.assertEqual(summary["content_type"], "application/json")
        self.assertGreater(summary["size_bytes"], 0)
        self.assertEqual(len(summary["sha256"]), 64)
        self.assertEqual(summary["redaction"], BODY_REDACTION)
        self.assertNotIn("FAKE_REQUEST_BODY_NOT_STORED", json.dumps(self.entries))

    def test_response_body_is_summary_only(self) -> None:
        summary = self._entry("POST")["response_body_summary"]
        self.assertTrue(summary["present"])
        self.assertEqual(summary["content_type"], "application/json")
        self.assertGreater(summary["size_bytes"], 0)
        self.assertEqual(len(summary["sha256"]), 64)
        self.assertEqual(summary["redaction"], BODY_REDACTION)
        serialized = json.dumps(self.entries)
        self.assertNotIn("FAKE_RESPONSE_BODY_NOT_STORED", serialized)
        self.assertNotIn("FAKE_RESPONSE_COOKIE_NOT_STORED", serialized)
        self.assertNotIn("FAKE_RESPONSE_HEADER_NOT_STORED", serialized)

    def test_dashboard_contains_cassette_summary_and_entries(self) -> None:
        payload = export_dashboard_data(self.run_dir)
        cassette = payload["http_cassette"]
        self.assertTrue(cassette["summary"]["present"])
        self.assertEqual(cassette["summary"]["entry_count"], 2)
        self.assertEqual(len(cassette["entries"]), 2)
        self.assertTrue(cassette["summary"]["redacted"])

    def test_dashboard_caps_entries_at_fifty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            events = [
                {
                    "id": f"evt_{index:04d}",
                    "ts": "2026-06-19T00:00:00+00:00",
                    "type": "http",
                    "operation": "synthetic.http",
                    "input": {"method": "GET", "url": f"https://example.test/{index}"},
                    "output": {"status": "ok", "status_code": 200},
                    "risk": {"level": "low", "reasons": []},
                    "file_changes": [],
                }
                for index in range(55)
            ]
            (run_dir / "events.jsonl").write_text(
                "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
            )
            summary = generate_http_cassette(run_dir / "events.jsonl", run_dir / "http_cassette.jsonl")
            (run_dir / "manifest.json").write_text(
                json.dumps({"run_id": "run_synthetic", "http_cassette": summary}), encoding="utf-8"
            )
            cassette = export_dashboard_data(run_dir)["http_cassette"]
            self.assertEqual(cassette["summary"]["entry_count"], 55)
            self.assertEqual(len(cassette["entries"]), 50)

    def test_generation_failure_does_not_abort_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_cwd = Path.cwd()
            try:
                os.chdir(tmp)
                with mock.patch("traceseal.cli.generate_http_cassette", side_effect=RuntimeError("synthetic failure")):
                    exit_code = run_command(
                        argparse.Namespace(command=["--", sys.executable, "-c", "print('agent completed')"])
                    )
                self.assertEqual(exit_code, 0)
                run_id = (Path(tmp) / "runs" / "latest").read_text(encoding="utf-8").strip()
                manifest = json.loads((Path(tmp) / "runs" / run_id / "manifest.json").read_text(encoding="utf-8"))
                self.assertFalse(manifest["http_cassette"]["present"])
                self.assertIn("synthetic failure", manifest["http_cassette"]["error"])
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
