from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from dashboard.export import build_guard_dashboard_data, export_dashboard_data
from traceseal.guard_import import GUARD_ARTIFACT_NAME, import_guard_events
from traceseal.guard_schema import load_guard_events


class DashboardGuardDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = Path(__file__).parent / "fixtures"
        cls.health = load_guard_events(cls.fixtures / "guard_health.jsonl")[0]
        cls.spawn = load_guard_events(cls.fixtures / "guard_process_spawn.jsonl")[0]

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run_dir = self.root / "run_dashboard_guard"
        self.run_dir.mkdir()
        manifest = {
            "schema_version": 1,
            "run_id": self.run_dir.name,
            "command_display": "python agent.py",
            "started_at": "2026-06-22T00:00:00+00:00",
            "completed_at": "2026-06-22T00:00:01+00:00",
            "status": "completed",
            "exit_code": 0,
        }
        (self.run_dir / "manifest.json").write_text(
            json.dumps(manifest) + "\n", encoding="utf-8"
        )
        self.python_event = {
            "id": "evt_0001",
            "seq": 1,
            "type": "shell",
            "input": {"command": "python agent.py"},
            "risk": {"level": "low", "policy_rule": None, "reasons": []},
            "file_changes": [],
        }
        (self.run_dir / "events.jsonl").write_text(
            json.dumps(self.python_event) + "\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _source(self, name: str, events: list[dict]) -> Path:
        path = self.root / name
        path.write_text(
            "".join(
                json.dumps(event, ensure_ascii=False, separators=(",", ":"))
                + "\n"
                for event in events
            ),
            encoding="utf-8",
        )
        return path

    def test_old_run_has_unavailable_guard_without_changing_old_fields(self) -> None:
        payload = export_dashboard_data(self.run_dir)
        self.assertEqual(payload["run_id"], self.run_dir.name)
        self.assertEqual(payload["event_count"], 1)
        self.assertEqual(payload["events"][0]["id"], "evt_0001")
        self.assertEqual(
            payload["guard"],
            {
                "available": False,
                "schema_version": None,
                "artifact_path": None,
                "imported_at": None,
                "event_count": 0,
                "event_types": [],
                "risk_levels": {},
                "decisions": {},
                "redaction_statuses": {},
                "health_status": None,
                "policy": {
                    "available": False,
                    "artifact_path": None,
                    "artifact_type": "guard.policy.decisions.v1",
                    "generated_at": None,
                    "policy_source": None,
                    "dry_run": True,
                    "event_count": 0,
                    "evaluated_event_count": 0,
                    "decision_counts": {},
                    "enforcement_applied": False,
                    "error": None,
                },
                "events": [],
                "error": None,
            },
        )

    def test_guard_health_is_exposed_as_compact_summary(self) -> None:
        import_guard_events(self.run_dir, self.fixtures / "guard_health.jsonl")
        guard = export_dashboard_data(self.run_dir)["guard"]
        self.assertIs(guard["available"], True)
        self.assertEqual(guard["schema_version"], "guard.event.v1")
        self.assertEqual(guard["event_count"], 1)
        self.assertEqual(guard["event_types"], ["guard.health"])
        self.assertEqual(guard["health_status"], "ok")
        self.assertEqual(guard["events"][0]["event_type"], "guard.health")
        self.assertEqual(guard["events"][0]["message"], "guard health check ok")

    def test_process_spawn_is_metadata_only_and_target_is_not_executed(self) -> None:
        marker = self.root / "TARGET_MUST_NOT_EXIST.txt"
        event = copy.deepcopy(self.spawn)
        event["process"]["command_line"] = [
            "python",
            "-c",
            f"from pathlib import Path; Path({str(marker)!r}).write_text('executed')",
            "token=dashboard-secret",
        ]
        event["redaction"] = {"status": "not_applicable", "fields": []}
        import_guard_events(self.run_dir, self._source("spawn.jsonl", [event]))

        guard = export_dashboard_data(self.run_dir)["guard"]
        process = guard["events"][0]["process"]
        self.assertEqual(guard["event_types"], ["process.spawn"])
        self.assertEqual(process["program"], "python")
        self.assertIs(process["dry_run"], True)
        self.assertIs(process["executed"], False)
        self.assertIn("token=<redacted>", process["args"])
        self.assertNotIn("dashboard-secret", json.dumps(guard))
        self.assertFalse(marker.exists())

    def test_mixed_events_have_deterministic_aggregates(self) -> None:
        import_guard_events(self.run_dir, self.fixtures / "guard_mixed_events.jsonl")
        guard = build_guard_dashboard_data(self.run_dir)
        self.assertEqual(guard["event_count"], 2)
        self.assertEqual(guard["event_types"], ["guard.health", "process.spawn"])
        self.assertEqual(guard["risk_levels"], {"info": 2})
        self.assertEqual(guard["decisions"], {"observe": 2})
        self.assertEqual(
            guard["redaction_statuses"], {"not_applicable": 1, "redacted": 1}
        )
        self.assertEqual(
            [event["event_type"] for event in guard["events"]],
            ["guard.health", "process.spawn"],
        )

    def test_malformed_guard_artifact_is_isolated_in_guard_error(self) -> None:
        artifact = self.run_dir / GUARD_ARTIFACT_NAME
        artifact.write_text("\n{malformed guard json}\n", encoding="utf-8")
        guard = export_dashboard_data(self.run_dir)["guard"]
        self.assertIs(guard["available"], False)
        self.assertEqual(guard["event_count"], 0)
        self.assertEqual(guard["events"], [])
        self.assertEqual(guard["error"]["code"], "INVALID_GUARD_EVENTS")
        self.assertIn("line 2", guard["error"]["message"])

    def test_degraded_generic_guard_event_remains_visible(self) -> None:
        event = copy.deepcopy(self.health)
        event["event_id"] = "guard_evt_degraded_000001"
        event["event_type"] = "guard.error"
        event["risk_level"] = "low"
        event["guard"]["status"] = "degraded"
        event["metadata"]["message"] = "guard capability degraded"
        import_guard_events(self.run_dir, self._source("degraded.jsonl", [event]))

        guard = export_dashboard_data(self.run_dir)["guard"]
        self.assertIs(guard["available"], True)
        self.assertEqual(guard["event_types"], ["guard.error"])
        self.assertEqual(guard["risk_levels"], {"low": 1})
        self.assertEqual(guard["events"][0]["guard_status"], "degraded")
        self.assertEqual(guard["events"][0]["message"], "guard capability degraded")

    def test_dashboard_payload_with_guard_is_json_serializable(self) -> None:
        import_guard_events(self.run_dir, self.fixtures / "guard_mixed_events.jsonl")
        serialized = json.dumps(export_dashboard_data(self.run_dir), ensure_ascii=False)
        self.assertIn('"guard"', serialized)
        self.assertIn('"available": true', serialized)


if __name__ == "__main__":
    unittest.main()
