from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dashboard.export import export_dashboard_data
from minimizer.explain import explain_run
from policy.domain import evaluate_domain_policy
from policy.rules import classify_git_push
from policy.yaml_loader import load_policy_with_source
from replay.renderer import replay_run
from traceseal.cascade import detect_cascade


def _event(stage: str, seq: int, *, timestamp: str | None = None) -> dict:
    base = {
        "id": f"evt_{seq:04d}",
        "seq": seq,
        "ts": timestamp or f"2026-06-19T10:00:{seq:02d}+00:00",
        "risk": {"level": "high", "reasons": [f"synthetic {stage}"], "action": "warn"},
        "file_changes": [],
    }
    if stage == "sensitive_read":
        base.update(type="file.read", input={"path": "secrets.env"})
        base["risk"].update(policy_rule="sensitive_file_read", rule_id="sensitive_file_read")
    elif stage == "http_exfiltration_attempt":
        base.update(type="network.http", input={"method": "POST", "url": "https://example.test", "host": "example.test"})
        base["risk"].update(policy_rule="sensitive_http_request", rule_id="sensitive_http_request")
    elif stage == "configuration_corruption":
        base.update(type="file.write", input={"path": "config.json"})
        base["risk"].update(policy_rule="cascade_config_corruption", rule_id="cascade_config_corruption")
    elif stage == "destructive_shell":
        base.update(type="shell", input={"command": "rm -rf data/", "simulated": True})
        base["risk"].update(level="critical", policy_rule="dangerous_delete", rule_id="dangerous_delete")
    elif stage == "dangerous_git_push":
        operation = {"push_type": "mirror", "remote": "origin", "refs": [], "protected_branch": False}
        base.update(type="shell", input={"command": "git push --mirror origin", "simulated": True, "git_operation": operation})
        base["risk"].update(level="critical", policy_rule="git_mirror_push", rule_id="git_mirror_push", git_operation=operation)
    else:
        raise ValueError(stage)
    return base


class CascadeDetectionTest(unittest.TestCase):
    def test_three_risk_classes_produce_present_cascade(self) -> None:
        result = detect_cascade([_event("sensitive_read", 1), _event("http_exfiltration_attempt", 2), _event("configuration_corruption", 3)])
        self.assertTrue(result["present"])

    def test_three_classes_are_high(self) -> None:
        result = detect_cascade([_event("sensitive_read", 1), _event("destructive_shell", 2), _event("dangerous_git_push", 3)])
        self.assertEqual(result["severity"], "high")

    def test_four_or_more_classes_are_critical(self) -> None:
        events = [_event("sensitive_read", 1), _event("http_exfiltration_attempt", 2), _event("configuration_corruption", 3), _event("destructive_shell", 4)]
        self.assertEqual(detect_cascade(events)["severity"], "critical")

    def test_single_http_does_not_trigger(self) -> None:
        event = {
            "id": "evt_0001",
            "seq": 1,
            "type": "network.http",
            "input": {"method": "GET", "url": "https://ordinary.example.test", "host": "ordinary.example.test"},
            "risk": {"level": "medium", "policy_rule": "http_request", "action": "warn"},
        }
        result = detect_cascade([event])
        self.assertFalse(result["present"])
        self.assertEqual(result["stages"], [])

    def test_single_git_push_does_not_trigger(self) -> None:
        self.assertFalse(detect_cascade([_event("dangerous_git_push", 1)])["present"])

    def test_single_env_write_does_not_trigger(self) -> None:
        event = _event("configuration_corruption", 1)
        event["input"]["path"] = ".env"
        event["risk"].update(policy_rule="env_write", rule_id="env_write")
        self.assertFalse(detect_cascade([event])["present"])

    def test_stages_are_sorted_by_event_timestamp(self) -> None:
        events = [
            _event("configuration_corruption", 3, timestamp="2026-06-19T10:00:03+00:00"),
            _event("sensitive_read", 1, timestamp="2026-06-19T10:00:01+00:00"),
            _event("http_exfiltration_attempt", 2, timestamp="2026-06-19T10:00:02+00:00"),
        ]
        for event in events:
            event.pop("seq")
        stages = [item["stage"] for item in detect_cascade(events)["stages"]]
        self.assertEqual(stages, ["sensitive_read", "http_exfiltration_attempt", "configuration_corruption"])

    def test_first_harmful_event_is_first_high_risk_stage(self) -> None:
        setup = {"id": "evt_0001", "seq": 1, "type": "file.write", "input": {"path": "notes.txt"}, "risk": {"level": "low"}}
        events = [setup, _event("sensitive_read", 2), _event("destructive_shell", 3), _event("dangerous_git_push", 4)]
        self.assertEqual(detect_cascade(events)["first_harmful_event_id"], "evt_0002")

    def test_summary_is_human_readable(self) -> None:
        result = detect_cascade([_event("sensitive_read", 1), _event("destructive_shell", 2), _event("dangerous_git_push", 3)])
        self.assertIn("Detected a high cascade", result["summary"])
        self.assertIn("sensitive file read", result["summary"])

    def test_dashboard_exports_cascade(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "manifest.json").write_text(json.dumps({"run_id": "run_cascade", "status": "completed", "exit_code": 0}), encoding="utf-8")
            events = [_event("sensitive_read", 1), _event("http_exfiltration_attempt", 2), _event("configuration_corruption", 3)]
            (run_dir / "events.jsonl").write_text("".join(json.dumps(item) + "\n" for item in events), encoding="utf-8")
            payload = export_dashboard_data(run_dir)
        self.assertTrue(payload["cascade"]["present"])
        self.assertEqual(payload["cascade"]["event_count"], 3)

    def test_replay_outputs_cascade(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "manifest.json").write_text(json.dumps({"run_id": "run_cascade", "status": "completed", "exit_code": 0}), encoding="utf-8")
            events = [_event("sensitive_read", 1), _event("destructive_shell", 2), _event("dangerous_git_push", 3)]
            (run_dir / "events.jsonl").write_text("".join(json.dumps(item) + "\n" for item in events), encoding="utf-8")
            output = replay_run(run_dir)
        self.assertIn("级联事故: 已检测到", output)
        self.assertIn("dangerous_git_push", output)

    def test_explain_outputs_cascade(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "manifest.json").write_text(json.dumps({"run_id": "run_cascade", "status": "completed", "exit_code": 0}), encoding="utf-8")
            events = [_event("sensitive_read", 1), _event("destructive_shell", 2), _event("dangerous_git_push", 3)]
            (run_dir / "events.jsonl").write_text("".join(json.dumps(item) + "\n" for item in events), encoding="utf-8")
            output = explain_run(run_dir)
        self.assertIn("级联事故: 已检测到", output)
        self.assertIn("首次有害事件: evt_0001", output)


class CascadeDemoIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "-m", "traceseal", "run", "--", sys.executable, "examples/bad_agent_cascade_failure.py"],
            cwd=cls.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(f"cascade demo failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}")
        run_id = (cls.repo / "runs" / "latest").read_text(encoding="utf-8").strip()
        cls.run_dir = cls.repo / "runs" / run_id
        cls.events = [json.loads(line) for line in (cls.run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line]
        cls.cassette_text = (cls.run_dir / "http_cassette.jsonl").read_text(encoding="utf-8")
        cls.dashboard = export_dashboard_data(cls.run_dir)
        cls.replay = replay_run(cls.run_dir)
        cls.explain = explain_run(cls.run_dir)

    def test_demo_uses_mock_transport_without_real_network(self) -> None:
        source = (self.repo / "examples" / "bad_agent_cascade_failure.py").read_text(encoding="utf-8")
        self.assertIn("httpx.MockTransport", source)
        http_event = next(event for event in self.events if event.get("type") == "network.http")
        self.assertEqual(http_event["output"]["status"], "ok")

    def test_demo_git_push_is_simulated(self) -> None:
        git_event = next(event for event in self.events if (event.get("input") or {}).get("git_operation"))
        self.assertTrue(git_event["input"]["simulated"])
        self.assertEqual(git_event["output"]["status"], "simulated")
        self.assertEqual(git_event["input"]["git_operation"]["push_type"], "mirror")

    def test_demo_delete_is_confined_to_sandbox(self) -> None:
        delete_event = next(event for event in self.events if "rm -rf" in str((event.get("input") or {}).get("command")))
        self.assertEqual(delete_event["input"]["targets"], ["data/"])
        self.assertTrue(Path(delete_event["cwd"]).resolve().is_relative_to((self.run_dir / "workspace").resolve()))
        self.assertEqual(delete_event["output"]["status"], "blocked")

    def test_cassette_and_outputs_do_not_leak_fake_secret(self) -> None:
        secret = "demo-cascade-" + "secret-123"
        artifacts = [
            (self.run_dir / "events.jsonl").read_text(encoding="utf-8"),
            self.cassette_text,
            json.dumps(self.dashboard, ensure_ascii=False),
            self.replay,
            self.explain,
        ]
        self.assertTrue(all(secret not in artifact for artifact in artifacts))
        cassette = json.loads(self.cassette_text.strip())
        self.assertEqual(cassette["request_headers_redacted"]["authorization"], "<redacted>")
        self.assertEqual(cassette["query_redacted"], "token=<redacted>")
        self.assertNotIn("content", cassette["request_body_summary"])

    def test_policy_yaml_fallback_is_preserved(self) -> None:
        self.assertEqual(self.dashboard["policy_source"]["type"], "yaml")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy, source = load_policy_with_source(root)
            self.assertEqual(source["type"], "json_default")
            self.assertIn("cascade_failure_detected", {rule["rule_id"] for rule in policy["rules"]})
            (root / "policy.yaml").write_text("version: [broken", encoding="utf-8")
            _, source = load_policy_with_source(root)
            self.assertEqual(source["type"], "yaml_error_fallback")

    def test_domain_policy_is_preserved(self) -> None:
        domain = evaluate_domain_policy(
            "exfil.malware.test",
            {"deny_domains": ["*.malware.test"], "warn_on_unknown_external": True},
        )
        self.assertEqual(domain["matched_domain_rule"], "domain_denylist_match")
        http_event = next(event for event in self.events if event.get("type") == "network.http")
        self.assertEqual(http_event["risk"]["domain_policy"]["domain_decision"], "deny")

    def test_git_push_classification_is_preserved(self) -> None:
        operation = classify_git_push("git push --mirror origin", ["git", "push", "--mirror", "origin"])
        self.assertEqual(operation["push_type"], "mirror")
        self.assertTrue(self.dashboard["cascade"]["present"])
        self.assertEqual(self.dashboard["cascade"]["severity"], "critical")


if __name__ == "__main__":
    unittest.main()
