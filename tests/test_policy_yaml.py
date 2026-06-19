from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from dashboard.export import export_dashboard_data, handle_dashboard_cli
from minimizer.explain import explain_run
from policy.dsl import PolicyValidationError, match_rule, validate_policy
from policy.rules import evaluate_file_read, evaluate_file_write, evaluate_httpx_request, evaluate_shell_command, load_policy, policy_source
from sdk.hooks import _is_read_noise


@contextmanager
def working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def policy_text(*, action: str = "warn", command: str = "rm -rf") -> str:
    return f"""version: 1
mode: warn
rules:
  - id: yaml-shell-rule
    description: YAML shell test
    match:
      event_type: shell
      command:
        contains: {json.dumps(command)}
    risk_level: critical
    action: {action}
    reason: YAML rule matched
    suggested_policy: deny shell test
  - id: yaml-env-rule
    match:
      event_type: file.write
      path:
        glob: ".env*"
    risk_level: high
    action: warn
    reason: YAML env matched
    suggested_policy: deny file_write .env*
  - id: yaml-sensitive-read
    match:
      event_type: file.read
      path:
        contains_any: [secret, token]
    risk_level: high
    action: require_approval
    reason: YAML sensitive read matched
    suggested_policy: require_approval file_read sensitive
  - id: yaml-http-rule
    match:
      event_type:
        any_of: [http, network.http]
      method:
        any_of: [POST, PUT]
      sensitive: true
    risk_level: high
    action: warn
    reason: YAML HTTP matched
    suggested_policy: require_approval http request
"""


class PolicyYamlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {}, clear=False)
        self.env.start()
        os.environ.pop("TRACESEAL_WORKSPACE_ROOT", None)
        os.environ.pop("TRACESEAL_POLICY_MODE", None)

    def tearDown(self) -> None:
        self.env.stop()
        self.tmp.cleanup()

    def test_missing_yaml_falls_back_to_default_json(self) -> None:
        source = policy_source(self.root)
        self.assertEqual(source["type"], "json_default")
        self.assertIn("dangerous_delete", {rule["rule_id"] for rule in load_policy(self.root)["rules"]})

    def test_valid_yaml_loads_and_yaml_extension_has_priority(self) -> None:
        (self.root / "policy.yaml").write_text(policy_text(), encoding="utf-8")
        (self.root / "policy.yml").write_text(policy_text(command="git push"), encoding="utf-8")
        self.assertEqual(policy_source(self.root)["type"], "yaml")
        self.assertEqual(load_policy(self.root)["rules"][0]["match"]["command"]["contains"], "rm -rf")

    def test_invalid_yaml_falls_back_with_error_metadata(self) -> None:
        (self.root / "policy.yaml").write_text("version: [broken", encoding="utf-8")
        source = policy_source(self.root)
        self.assertEqual(source["type"], "yaml_error_fallback")
        self.assertTrue(source["error"])
        self.assertIn("dangerous_delete", {rule["rule_id"] for rule in load_policy(self.root)["rules"]})

    def test_invalid_regex_is_rejected_without_runtime_crash(self) -> None:
        with self.assertRaises(PolicyValidationError):
            validate_policy({"version": 1, "rules": [{"id": "bad", "match": {"path": {"regex": "["}}, "risk_level": "high", "action": "warn"}]})

    def test_policy_yaml_reads_are_internal_noise(self) -> None:
        (self.root / "policy.yaml").write_text(policy_text(), encoding="utf-8")
        with patch.dict(os.environ, {"TRACESEAL_WORKSPACE_ROOT": str(self.root), "TRACESEAL_RUN_DIR": str(self.root.parent / "run")}):
            self.assertTrue(_is_read_noise(self.root / "policy.yaml"))

    def test_exact_glob_contains_any_and_any_of_matching(self) -> None:
        rule = {
            "match": {
                "event_type": "file.write",
                "path": {"glob": ".env*"},
                "command": {"contains_any": ["safe", "write"]},
                "method": {"any_of": ["POST", "PUT"]},
            }
        }
        self.assertTrue(match_rule(rule, {"event_type": "file.write", "path": ".env.demo", "command": "write config", "method": "post"}))

    def test_command_contains_warn_metadata(self) -> None:
        (self.root / "policy.yaml").write_text(policy_text(), encoding="utf-8")
        with working_directory(self.root):
            result = evaluate_shell_command("rm -rf data")
        self.assertEqual((result["rule_id"], result["action"], result["reason"]), ("yaml-shell-rule", "warn", "YAML rule matched"))
        self.assertEqual(result["suggested_policy"], "deny shell test")

    def test_deny_metadata_is_preserved(self) -> None:
        (self.root / "policy.yaml").write_text(policy_text(action="deny"), encoding="utf-8")
        with working_directory(self.root):
            result = evaluate_shell_command("rm -rf data")
        self.assertEqual(result["action"], "deny")
        self.assertEqual(result["level"], "critical")

    def test_require_approval_is_metadata(self) -> None:
        (self.root / "policy.yaml").write_text(policy_text(), encoding="utf-8")
        with working_directory(self.root):
            result = evaluate_file_read("config/secret-token.txt")
        self.assertEqual(result["action"], "require_approval")
        self.assertEqual(result["rule_id"], "yaml-sensitive-read")

    def test_path_glob_and_http_sensitive_match(self) -> None:
        (self.root / "policy.yaml").write_text(policy_text(), encoding="utf-8")
        with working_directory(self.root):
            write_risk = evaluate_file_write(".env.demo")
            http_risk = evaluate_httpx_request("POST", "http://localhost/api", scheme="http", host="localhost", sensitive_headers=True)
        self.assertEqual(write_risk["rule_id"], "yaml-env-rule")
        self.assertEqual(http_risk["rule_id"], "yaml-http-rule")

    def test_environment_mode_overrides_yaml_warn(self) -> None:
        (self.root / "policy.yaml").write_text(policy_text(), encoding="utf-8")
        with working_directory(self.root), patch.dict(os.environ, {"TRACESEAL_POLICY_MODE": "block"}):
            result = evaluate_shell_command("rm -rf data")
        self.assertEqual(result["action"], "deny")

    def test_dashboard_policy_includes_source(self) -> None:
        (self.root / "policy.yaml").write_text(policy_text(), encoding="utf-8")
        (self.root / "runs").mkdir()
        payload = handle_dashboard_cli(["policy"], self.root)
        self.assertEqual(payload["policy_source"]["type"], "yaml")
        self.assertEqual(payload["rules"][0]["rule_id"], "yaml-shell-rule")
        self.assertEqual(payload["rules"][0]["event_type"], "shell")
        self.assertEqual(payload["rules"][0]["reason"], "YAML rule matched")

    def test_dashboard_run_and_explain_show_yaml_metadata(self) -> None:
        run_dir = self.root / "runs" / "run_yaml"
        run_dir.mkdir(parents=True)
        source = {"type": "yaml", "path": str(self.root / "policy.yaml"), "error": None}
        (run_dir / "manifest.json").write_text(json.dumps({"run_id": "run_yaml", "status": "completed", "exit_code": 0, "policy_source": source}), encoding="utf-8")
        event = {"id": "evt_0001", "type": "shell", "input": {"command": "rm -rf data"}, "risk": {"level": "critical", "policy_rule": "yaml-shell-rule", "rule_id": "yaml-shell-rule", "action": "deny", "reason": "YAML rule matched", "reasons": ["YAML rule matched"], "suggested_policy": "deny shell test"}, "file_changes": []}
        (run_dir / "events.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
        dashboard = export_dashboard_data(run_dir)
        self.assertEqual(dashboard["first_harmful_event"]["risk"]["rule_id"], "yaml-shell-rule")
        self.assertEqual(dashboard["policy_source"]["type"], "yaml")
        explanation = explain_run(run_dir)
        self.assertIn("rule_id: yaml-shell-rule", explanation)
        self.assertIn("suggested_policy: deny shell test", explanation)


if __name__ == "__main__":
    unittest.main()
