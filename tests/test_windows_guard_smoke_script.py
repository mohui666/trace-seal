from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WindowsGuardSmokeScriptTest(unittest.TestCase):
    def test_script_exists_and_keeps_dry_run_safety_assertions(self) -> None:
        script = ROOT / "scripts" / "windows-guard-smoke.ps1"
        self.assertTrue(script.exists(), "missing Windows Guard smoke script")
        text = script.read_text(encoding="utf-8")

        required_terms = [
            "$ErrorActionPreference = \"Stop\"",
            "process-spawn",
            "should_not_exist.txt",
            "target command was executed unexpectedly",
            "metadata.dry_run",
            "metadata.executed",
            "enforcement_applied",
            "daemon_service",
            "artifacts_committed",
            "git diff --check",
            "SkipNode",
            "SkipElectron",
            "KeepArtifacts",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

        forbidden_terms = [
            "New-Service",
            "Start-Service",
            "sc.exe",
            "schtasks",
        ]
        for term in forbidden_terms:
            with self.subTest(term=term):
                self.assertNotIn(term, text)

    def test_validation_doc_covers_required_windows_smoke_boundary(self) -> None:
        doc = ROOT / "docs" / "windows-guard-smoke-validation.md"
        self.assertTrue(doc.exists(), "missing Windows Guard smoke validation doc")
        text = doc.read_text(encoding="utf-8")

        required_terms = [
            "Issue #38",
            "guard.health",
            "process.spawn",
            "policy dry-run",
            "dashboard-data",
            "no enforcement",
            "No daemon or service",
            "No `process.spawn` target command execution",
            "sentinel absent: `yes`",
            "No new tag",
            "Issue #39 remains",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_stage4_tracking_mentions_windows_smoke_validation(self) -> None:
        issue_breakdown = (ROOT / "docs" / "stage4-issue-breakdown.md").read_text(
            encoding="utf-8"
        )
        roadmap = (ROOT / "docs" / "roadmap.md").read_text(encoding="utf-8")

        self.assertIn("scripts/windows-guard-smoke.ps1", issue_breakdown)
        self.assertIn("docs/windows-guard-smoke-validation.md", issue_breakdown)
        self.assertIn("target command", issue_breakdown)
        self.assertIn("enforcement_applied=false", issue_breakdown)
        self.assertIn("Windows smoke validation", roadmap)
        self.assertIn("Issue #39", roadmap)


if __name__ == "__main__":
    unittest.main()
