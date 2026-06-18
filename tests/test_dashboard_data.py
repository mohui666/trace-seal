from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dashboard.export import (
    DashboardDataError,
    export_policy_rules,
    handle_dashboard_cli,
    list_runs,
    resolve_dashboard_run_dir,
)


class DashboardDataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "runs").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_run(
        self,
        run_id: str,
        *,
        started_at: str,
        status: str = "completed",
        command: str = "python agent.py",
        risk_rule: str | None = None,
    ) -> Path:
        run_dir = self.repo / "runs" / run_id
        run_dir.mkdir(parents=True)
        manifest = {
            "schema_version": 1,
            "run_id": run_id,
            "command_display": command,
            "started_at": started_at,
            "completed_at": started_at.replace("00+00:00", "01+00:00"),
            "status": status,
            "exit_code": 0,
        }
        (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        event = {
            "id": "evt_0001",
            "seq": 1,
            "type": "shell",
            "input": {"command": "git push origin main" if risk_rule else "python -m pytest"},
            "risk": {"level": "high" if risk_rule else "low", "policy_rule": risk_rule, "reasons": []},
            "file_changes": [],
        }
        (run_dir / "events.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
        return run_dir

    def test_latest_run(self) -> None:
        self._write_run("run_20260617_100000_000000", started_at="2026-06-17T10:00:00+00:00", risk_rule="git_push")
        (self.repo / "runs" / "latest").write_text("run_20260617_100000_000000\n", encoding="utf-8")
        payload = handle_dashboard_cli(["latest"], self.repo)
        self.assertEqual(payload["run_id"], "run_20260617_100000_000000")
        self.assertEqual(payload["event_count"], 1)
        self.assertEqual(payload["first_harmful_event"]["id"], "evt_0001")

    def test_specific_run(self) -> None:
        self._write_run("run_20260617_110000_000000", started_at="2026-06-17T11:00:00+00:00")
        payload = handle_dashboard_cli(["run", "run_20260617_110000_000000"], self.repo)
        self.assertEqual(payload["run_id"], "run_20260617_110000_000000")
        self.assertEqual(payload["command"], "python agent.py")

    def test_runs_sorted_descending(self) -> None:
        self._write_run("run_20260617_090000_000000", started_at="2026-06-17T09:00:00+00:00")
        self._write_run("run_20260617_120000_000000", started_at="2026-06-17T12:00:00+00:00")
        payload = handle_dashboard_cli(["list"], self.repo)
        self.assertEqual([r["run_id"] for r in payload["runs"]], ["run_20260617_120000_000000", "run_20260617_090000_000000"])

    def test_empty_runs(self) -> None:
        self.assertEqual(list_runs(self.repo), [])
        self.assertEqual(handle_dashboard_cli(["list"], self.repo)["runs"], [])

    def test_corrupt_run_does_not_break_list(self) -> None:
        self._write_run("run_20260617_130000_000000", started_at="2026-06-17T13:00:00+00:00")
        corrupt = self.repo / "runs" / "run_20260617_140000_000000"
        corrupt.mkdir()
        (corrupt / "manifest.json").write_text("{bad json", encoding="utf-8")
        (corrupt / "events.jsonl").write_text("", encoding="utf-8")
        runs = handle_dashboard_cli(["list"], self.repo)["runs"]
        self.assertEqual(len(runs), 2)
        corrupt_summary = next(r for r in runs if r["run_id"] == "run_20260617_140000_000000")
        self.assertEqual(corrupt_summary["status"], "failed")
        self.assertEqual(corrupt_summary["error"]["code"], "INVALID_JSON")

    def test_nonexistent_run(self) -> None:
        with self.assertRaises(DashboardDataError) as ctx:
            resolve_dashboard_run_dir("run_20990101_000000_000000", self.repo)
        self.assertEqual(ctx.exception.code, "RUN_NOT_FOUND")

    def test_path_traversal_rejected(self) -> None:
        for bad in ["../run_1", "run_../../x", "runs/latest/../../evil", str((self.repo / "runs").resolve())]:
            with self.subTest(bad=bad):
                with self.assertRaises(DashboardDataError) as ctx:
                    handle_dashboard_cli(["run", bad], self.repo)
                self.assertEqual(ctx.exception.code, "INVALID_RUN_ID")

    def test_policy_export(self) -> None:
        rules = export_policy_rules()
        ids = {r["rule_id"] for r in rules}
        self.assertIn("dangerous_delete", ids)
        self.assertIn("env_write", ids)
        self.assertIn("sensitive_file_read", ids)
        self.assertIn("git_push", ids)
        self.assertIn("suspicious_http_post", ids)
        self.assertIn("sensitive_http_request", ids)
        self.assertIn("insecure_http_request", ids)
        self.assertTrue(all("suggested_policy" in rule for rule in rules))


if __name__ == "__main__":
    unittest.main()
