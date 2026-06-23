from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from dashboard.export import export_dashboard_data
from minimizer.explain import explain_run
from replay.renderer import replay_run
from traceseal.guard_import import GUARD_ARTIFACT_NAME, import_guard_events
from traceseal.guard_policy import (
    GUARD_POLICY_ARTIFACT_NAME,
    GuardPolicyError,
    apply_guard_policy_dry_run,
    evaluate_guard_event_policy,
    get_guard_policy_summary,
    load_guard_policy_decisions,
)
from traceseal.guard_schema import load_guard_events


class GuardPolicyDryRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = Path(__file__).parent / "fixtures"
        cls.health = load_guard_events(cls.fixtures / "guard_health.jsonl")[0]
        cls.spawn = load_guard_events(cls.fixtures / "guard_process_spawn.jsonl")[0]

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run_dir = self.root / "run_guard_policy"
        self.run_dir.mkdir()
        manifest = {
            "schema_version": 1,
            "run_id": self.run_dir.name,
            "command": ["python", "agent.py"],
            "command_display": "python agent.py",
            "status": "completed",
            "exit_code": 0,
        }
        (self.run_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (self.run_dir / "events.jsonl").write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _source(self, name: str, events: list[dict]) -> Path:
        path = self.root / name
        path.write_text(
            "".join(json.dumps(event, separators=(",", ":")) + "\n" for event in events),
            encoding="utf-8",
        )
        return path

    def _import(self, events: list[dict]) -> None:
        import_guard_events(self.run_dir, self._source("guard-source.jsonl", events))

    def test_guard_health_default_observe_dry_run_decision(self) -> None:
        self._import([self.health])
        summary = apply_guard_policy_dry_run(
            self.run_dir, self.fixtures / "policy_guard_observe.yaml"
        )
        decisions = load_guard_policy_decisions(self.run_dir)["decisions"]

        self.assertEqual(summary["evaluated_event_count"], 1)
        self.assertEqual(summary["decision_counts"], {"observe": 1})
        self.assertIs(summary["dry_run"], True)
        self.assertIs(summary["enforcement_applied"], False)
        self.assertEqual(decisions[0]["event_type"], "guard.health")
        self.assertEqual(decisions[0]["decision"], "observe")
        self.assertIs(decisions[0]["enforcement_applied"], False)

    def test_process_spawn_allow_matches_policy_without_execution(self) -> None:
        marker = self.root / "TARGET_MUST_NOT_EXIST.txt"
        event = copy.deepcopy(self.spawn)
        event["process"]["command_line"] = [
            "python",
            "safe_script.py",
            "-c",
            f"from pathlib import Path; Path({str(marker)!r}).write_text('executed')",
        ]
        self._import([event])

        apply_guard_policy_dry_run(
            self.run_dir, self.fixtures / "policy_guard_allow.yaml"
        )
        decision = load_guard_policy_decisions(self.run_dir)["decisions"][0]

        self.assertEqual(decision["decision"], "allow")
        self.assertEqual(decision["matched_rule"], "guard-spawn-safe-allow")
        self.assertIs(decision["dry_run"], True)
        self.assertIs(decision["enforcement_applied"], False)
        self.assertFalse(marker.exists())

    def test_process_spawn_warn_counts_are_reported(self) -> None:
        self._import([self.spawn])
        summary = apply_guard_policy_dry_run(
            self.run_dir, self.fixtures / "policy_guard_warn_process_spawn.yaml"
        )
        decision = load_guard_policy_decisions(self.run_dir)["decisions"][0]

        self.assertEqual(summary["decision_counts"], {"warn": 1})
        self.assertEqual(decision["decision"], "warn")
        self.assertEqual(decision["matched_rule"], "guard-spawn-warn-delete-demo")
        self.assertIs(decision["enforcement_applied"], False)

    def test_process_spawn_deny_is_metadata_only_and_does_not_block(self) -> None:
        marker = self.root / "TARGET_MUST_NOT_EXIST.txt"
        event = copy.deepcopy(self.spawn)
        event["process"]["process_name"] = "rm"
        event["process"]["command_line"] = [
            "rm",
            "-rf",
            "data",
            f"--would-create={marker}",
        ]
        event["redaction"] = {"status": "not_applicable", "fields": []}
        self._import([event])

        summary = apply_guard_policy_dry_run(
            self.run_dir, self.fixtures / "policy_guard_deny_process_spawn.yaml"
        )
        decision = load_guard_policy_decisions(self.run_dir)["decisions"][0]

        self.assertEqual(summary["decision_counts"], {"deny": 1})
        self.assertEqual(decision["decision"], "deny")
        self.assertEqual(decision["matched_rule"], "guard-spawn-deny-rm-rf")
        self.assertIs(decision["dry_run"], True)
        self.assertIs(decision["enforcement_applied"], False)
        self.assertFalse(marker.exists())

    def test_old_run_without_guard_events_does_not_crash(self) -> None:
        summary = apply_guard_policy_dry_run(
            self.run_dir, self.fixtures / "policy_guard_observe.yaml"
        )
        self.assertIs(summary["available"], False)
        self.assertEqual(summary["event_count"], 0)
        self.assertEqual(summary["evaluated_event_count"], 0)
        self.assertFalse((self.run_dir / GUARD_POLICY_ARTIFACT_NAME).exists())

    def test_malformed_policy_has_clear_error(self) -> None:
        self._import([self.health])
        policy = self.root / "policy.yaml"
        policy.write_text("version: [broken\n", encoding="utf-8")
        with self.assertRaisesRegex(GuardPolicyError, "cannot load policy file"):
            apply_guard_policy_dry_run(self.run_dir, policy)

    def test_malformed_guard_event_has_clear_error(self) -> None:
        (self.run_dir / GUARD_ARTIFACT_NAME).write_text(
            "{malformed guard json}\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(GuardPolicyError, "cannot load imported Guard events"):
            apply_guard_policy_dry_run(
                self.run_dir, self.fixtures / "policy_guard_observe.yaml"
            )

    def test_dashboard_data_exposes_policy_summary_and_per_event_decisions(self) -> None:
        self._import([self.health, self.spawn])
        apply_guard_policy_dry_run(
            self.run_dir, self.fixtures / "policy_guard_warn_process_spawn.yaml"
        )

        payload = export_dashboard_data(self.run_dir)
        guard = payload["guard"]
        self.assertIs(guard["policy"]["available"], True)
        self.assertIs(guard["policy"]["dry_run"], True)
        self.assertIs(guard["policy"]["enforcement_applied"], False)
        self.assertEqual(guard["policy"]["evaluated_event_count"], 2)
        self.assertEqual(guard["policy"]["decision_counts"], {"observe": 1, "warn": 1})
        spawn_event = next(
            event for event in guard["events"] if event["event_type"] == "process.spawn"
        )
        self.assertEqual(spawn_event["policy_decision"]["decision"], "warn")
        self.assertEqual(
            spawn_event["policy_decision"]["matched_rule"],
            "guard-spawn-warn-delete-demo",
        )
        json.dumps(payload, ensure_ascii=False)

    def test_replay_and_explain_smoke_with_guard_policy_artifact(self) -> None:
        self._import([self.health, self.spawn])
        apply_guard_policy_dry_run(
            self.run_dir, self.fixtures / "policy_guard_warn_process_spawn.yaml"
        )
        self.assertIn("TraceSeal 执行时间线回放", replay_run(self.run_dir))
        self.assertIn("未发现有害工具调用", explain_run(self.run_dir))

        old_run = self.root / "run_old"
        old_run.mkdir()
        (old_run / "manifest.json").write_text(
            json.dumps({"run_id": "run_old", "status": "completed", "exit_code": 0})
            + "\n",
            encoding="utf-8",
        )
        (old_run / "events.jsonl").write_text("", encoding="utf-8")
        self.assertIn("TraceSeal 执行时间线回放", replay_run(old_run))
        self.assertIn("未发现有害工具调用", explain_run(old_run))

    def test_invalid_policy_artifact_is_isolated_in_dashboard_summary(self) -> None:
        self._import([self.health])
        (self.run_dir / GUARD_POLICY_ARTIFACT_NAME).write_text(
            "{broken policy decision json}\n", encoding="utf-8"
        )
        summary = get_guard_policy_summary(self.run_dir)
        self.assertIs(summary["available"], False)
        self.assertEqual(summary["error"]["code"], "INVALID_GUARD_POLICY_DECISIONS")
        guard = export_dashboard_data(self.run_dir)["guard"]
        self.assertEqual(
            guard["policy"]["error"]["code"], "INVALID_GUARD_POLICY_DECISIONS"
        )

    def test_direct_event_evaluation_uses_existing_policy_dsl(self) -> None:
        policy = {
            "version": 1,
            "mode": "warn",
            "rules": [
                {
                    "id": "guard-health-allow",
                    "match": {"event_type": "guard.health"},
                    "risk_level": "low",
                    "action": "allow",
                    "reason": "health ok",
                    "suggested_policy": "allow guard.health",
                }
            ],
        }
        decision = evaluate_guard_event_policy(self.health, policy)
        self.assertEqual(decision["decision"], "allow")
        self.assertEqual(decision["matched_rule"], "guard-health-allow")
        self.assertIs(decision["enforcement_applied"], False)


if __name__ == "__main__":
    unittest.main()
