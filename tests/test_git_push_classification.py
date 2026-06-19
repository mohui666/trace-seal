from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dashboard.export import export_dashboard_data
from minimizer.explain import explain_run
from policy.dsl import first_matching_rule
from policy.rules import classify_git_push, evaluate_shell_command
from policy.yaml_loader import load_policy_with_source
from sdk.hooks import traced_os_system, traced_subprocess_run


class GitPushClassificationTest(unittest.TestCase):
    CASES = [
        ("git push", "normal", "git_push", "high"),
        ("git push origin main", "normal", "git_push", "high"),
        ("git push --force", "force", "git_force_push", "critical"),
        ("git push -f", "force", "git_force_push", "critical"),
        ("git push origin main --force", "force", "git_force_push", "critical"),
        ("git push --force origin main", "force", "git_force_push", "critical"),
        ("git push --force-with-lease origin main", "force_with_lease", "git_force_with_lease", "high"),
        ("git push --mirror origin", "mirror", "git_mirror_push", "critical"),
        ("git push origin --delete branch-name", "delete_remote_branch", "git_delete_remote_branch", "critical"),
        ("git push --delete origin branch-name", "delete_remote_branch", "git_delete_remote_branch", "critical"),
        ("git push origin :branch-name", "delete_remote_branch", "git_delete_remote_branch", "critical"),
        ("git push origin +main", "force_refspec", "git_force_refspec_push", "critical"),
        ("git push origin +main:main", "force_refspec", "git_force_refspec_push", "critical"),
        ("git push origin +refs/heads/main:refs/heads/main", "force_refspec", "git_force_refspec_push", "critical"),
        ("git push --all", "all", "git_bulk_push", "high"),
        ("git push --tags", "tags", "git_bulk_push", "high"),
    ]

    def test_push_types_and_policy_rules(self) -> None:
        with patch.dict(os.environ, {"TRACESEAL_POLICY_MODE": "warn"}):
            for command, push_type, rule_id, level in self.CASES:
                with self.subTest(command=command):
                    operation = classify_git_push(command)
                    self.assertIsNotNone(operation)
                    self.assertEqual(operation["push_type"], push_type)
                    risk = evaluate_shell_command(command)
                    self.assertEqual(risk["rule_id"], rule_id)
                    self.assertEqual(risk["level"], level)
                    self.assertEqual(risk["git_operation"]["push_type"], push_type)
                    self.assertTrue(risk["reason"])
                    self.assertTrue(risk["suggested_policy"])

    def test_normal_and_force_with_lease_are_not_misclassified(self) -> None:
        self.assertEqual(classify_git_push("git push origin feature/foo")["push_type"], "normal")
        self.assertEqual(classify_git_push("git push --force-with-lease origin main")["push_type"], "force_with_lease")
        self.assertNotEqual(evaluate_shell_command("git push origin main")["rule_id"], "git_force_push")

    def test_remote_refs_and_protected_branch_metadata(self) -> None:
        protected = classify_git_push("git push origin +main:main")
        self.assertEqual(protected["remote"], "origin")
        self.assertEqual(protected["refs"], ["+main:main"])
        self.assertTrue(protected["protected_branch"])
        feature = classify_git_push("git push origin feature/foo")
        self.assertFalse(feature["protected_branch"])
        self.assertIsNone(classify_git_push("python agent.py"))

    def test_subprocess_and_os_system_never_call_real_git(self) -> None:
        with patch("sdk.hooks._ORIG_SUBPROCESS_RUN") as original_run:
            completed = traced_subprocess_run(["git", "push", "--mirror", "origin"], check=False)
            self.assertEqual(completed.returncode, 0)
            original_run.assert_not_called()
        with patch("sdk.hooks._ORIG_OS_SYSTEM") as original_system:
            status = traced_os_system("git push --force origin main")
            self.assertEqual(status, 0)
            original_system.assert_not_called()
        with patch.dict(os.environ, {"TRACESEAL_POLICY_MODE": "block"}), patch("sdk.hooks._ORIG_SUBPROCESS_RUN") as blocked_original:
            blocked = traced_subprocess_run(["git", "push", "--force", "origin", "main"], check=False)
            self.assertEqual(blocked.returncode, 126)
            blocked_original.assert_not_called()

    def test_example_yaml_matches_force_push_before_normal_push(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "policy.yaml").write_text(Path("examples/policy.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            policy, source = load_policy_with_source(root)
        self.assertEqual(source["type"], "yaml")
        matched = first_matching_rule(policy, {"event_type": "shell", "command": "git push --force origin main"})
        self.assertEqual(matched["id"], "warn-git-force-push")

    def test_dashboard_and_explain_show_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_git_push"
            run_dir.mkdir()
            operation = classify_git_push("git push origin +main:main")
            risk = evaluate_shell_command("git push origin +main:main")
            event = {
                "id": "evt_0001",
                "type": "shell",
                "operation": "subprocess.run",
                "input": {"command": "git push origin +main:main", "git_operation": operation, "simulated": True},
                "output": {"status": "simulated", "returncode": 0},
                "risk": risk,
                "file_changes": [],
            }
            (run_dir / "manifest.json").write_text(json.dumps({"run_id": "run_git_push", "status": "completed", "exit_code": 0}), encoding="utf-8")
            (run_dir / "events.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
            dashboard = export_dashboard_data(run_dir)
            explanation = explain_run(run_dir)
        exported = dashboard["events"][0]
        self.assertEqual(exported["git_operation"]["push_type"], "force_refspec")
        self.assertEqual(exported["risk"]["rule_id"], "git_force_refspec_push")
        self.assertIn("push_type: force_refspec", explanation)
        self.assertIn("plus-prefixed refspec can force-update remote refs", explanation)
        self.assertIn('deny git "push +<refspec>"', explanation)


if __name__ == "__main__":
    unittest.main()
