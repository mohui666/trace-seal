from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any

from dashboard.export import export_dashboard_data
from minimizer.explain import explain_run
from policy.rules import evaluate_file_read
from replay.renderer import replay_run


class FileReadTrackingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env.pop("TRACESEAL_POLICY_MODE", None)
        completed = subprocess.run(
            [sys.executable, "-m", "traceseal", "run", "--", sys.executable, "examples/bad_agent_file_read.py"],
            cwd=cls.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            env=env,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(f"file read demo failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}")
        run_id = (cls.repo / "runs" / "latest").read_text(encoding="utf-8").strip()
        cls.run_dir = cls.repo / "runs" / run_id
        cls.events: list[dict[str, Any]] = [
            json.loads(line)
            for line in (cls.run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        ]
        cls.read_events = [event for event in cls.events if event.get("type") == "file.read"]

    def _event(self, source: str, path_suffix: str, *, status: str = "ok") -> dict[str, Any]:
        return next(
            event
            for event in self.read_events
            if event["input"]["source"] == source
            and event["input"]["path"].replace("\\", "/").endswith(path_suffix)
            and event["output"]["status"] == status
        )

    def test_common_read_apis_and_metadata(self) -> None:
        text_event = self._event("builtins.open", "trace_file_read_demo/notes.txt")
        binary_event = self._event("builtins.open", "trace_file_read_demo/Unicode 路径 with spaces/payload.bin")
        path_open_event = self._event("Path.open", "trace_file_read_demo/notes.txt")
        read_text_event = self._event("Path.read_text", "trace_file_read_demo/secrets/demo.env")
        read_bytes_event = self._event("Path.read_bytes", "trace_file_read_demo/Unicode 路径 with spaces/payload.bin")

        self.assertEqual(text_event["operation"], "file.read")
        self.assertEqual(text_event["input"]["mode"], "r")
        self.assertEqual(binary_event["input"]["mode"], "rb")
        self.assertEqual(path_open_event["input"]["mode"], "r")
        self.assertEqual(text_event["risk"]["level"], "low")
        self.assertGreater(text_event["output"]["bytes_read"], 0)
        self.assertEqual(binary_event["output"]["bytes_read"], binary_event["output"]["file_size"])
        self.assertGreater(read_text_event["output"]["bytes_read"], 0)
        self.assertEqual(read_bytes_event["output"]["bytes_read"], read_bytes_event["output"]["file_size"])
        self.assertTrue(all(event["output"]["success"] for event in [text_event, binary_event, path_open_event, read_text_event, read_bytes_event]))

    def test_failed_read_is_recorded(self) -> None:
        event = self._event("builtins.open", "trace_file_read_demo/missing.txt", status="exception")
        self.assertFalse(event["output"]["success"])
        self.assertEqual(event["output"]["bytes_read"], 0)
        self.assertIn("FileNotFoundError", event["output"]["exception"])

    def test_sensitive_read_risk_and_no_content_capture(self) -> None:
        event = self._event("Path.read_text", "trace_file_read_demo/secrets/demo.env")
        self.assertEqual(event["risk"]["level"], "high")
        self.assertEqual(event["risk"]["policy_rule"], "sensitive_file_read")
        self.assertEqual(event["risk"]["action"], "warn")
        serialized = json.dumps(self.read_events, ensure_ascii=False)
        self.assertNotIn("DEMO_TOKEN=not-a-real-secret", serialized)
        self.assertNotIn("ordinary demo notes", serialized)

        for path in [".env", ".env.local", "id_rsa", "id_ed25519", "keys/client.pem", "keys/client.key", "credentials", "secrets/value", "token", "password", ".ssh/config"]:
            with self.subTest(path=path):
                self.assertEqual(evaluate_file_read(path)["level"], "high")
        self.assertEqual(evaluate_file_read("docs/readme.txt")["level"], "low")

    def test_dashboard_replay_and_explain_support_file_reads(self) -> None:
        dashboard = export_dashboard_data(self.run_dir)
        self.assertTrue(any(event.get("type") == "file.read" for event in dashboard["events"]))
        self.assertEqual(dashboard["first_harmful_event"]["risk"]["policy_rule"], "sensitive_file_read")

        replay = replay_run(self.run_dir)
        explain = explain_run(self.run_dir)
        self.assertIn("文件读取", replay)
        self.assertIn("Path.read_text", replay)
        self.assertIn("读取敏感文件", explain)
        self.assertIn("sensitive_file_read", explain)

    def test_trace_internal_and_policy_reads_are_excluded(self) -> None:
        paths = [event.get("input", {}).get("path", "").replace("\\", "/") for event in self.read_events]
        self.assertFalse(any(path.endswith("events.jsonl") for path in paths))
        self.assertFalse(any(path.endswith("manifest.json") for path in paths))
        self.assertFalse(any(path.endswith("policy/default_policy.json") for path in paths))


if __name__ == "__main__":
    unittest.main()
