from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPLETION_REPORT = ROOT / "artifacts" / "stage4-completion-report.md"
README = ROOT / "README.md"
ROADMAP = ROOT / "docs" / "roadmap.md"


class Stage4CompletionDocsTest(unittest.TestCase):
    def test_completion_report_exists_and_lists_all_stage4_issues(self) -> None:
        self.assertTrue(COMPLETION_REPORT.exists(), "missing Stage 4 completion report")
        text = COMPLETION_REPORT.read_text(encoding="utf-8")
        for issue in range(31, 40):
            with self.subTest(issue=issue):
                self.assertIn(f"#{issue}", text)
        self.assertIn("#50", text)

    def test_completion_report_states_non_implemented_boundaries(self) -> None:
        text = COMPLETION_REPORT.read_text(encoding="utf-8")
        required = [
            "Guard remains dry-run / observe-only.",
            "Enforcement is not implemented.",
            "There is no daemon or service.",
            "There is no OS-wide process monitoring.",
            "There is no new file, network, or Git monitoring expansion.",
            "Installer and release workflows are unchanged",
            "No v0.3.1 release exists.",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_readme_contains_post_stage4_planning_boundaries(self) -> None:
        text = README.read_text(encoding="utf-8")
        required = [
            "Post-Stage 4 planning",
            "Electron remains the current desktop implementation",
            "Python Core remains the current",
            "Slint desktop feasibility",
            "Rust Core parity",
            "Enforcement is not implemented",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_roadmap_contains_stage4_completion_and_stage5_candidate_planning(self) -> None:
        text = ROADMAP.read_text(encoding="utf-8")
        required = [
            "Stage 4 status: Complete through Issue #39. Issue #50 performs the final completion audit and roadmap cleanup.",
            "Stage 5 candidates",
            "Slint desktop feasibility RFC",
            "Rust Core parity RFC",
            "Slint hello dashboard spike",
            "No v0.3.1 release.",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_completion_report_records_follow_up_planning_issues(self) -> None:
        text = COMPLETION_REPORT.read_text(encoding="utf-8")
        required = [
            "Follow-up planning issues",
            "#51",
            "Slint desktop feasibility RFC",
            "#52",
            "Rust Core parity RFC",
            "#53",
            "Slint hello dashboard spike",
            "Runtime behavior change",
            "No",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_docs_do_not_claim_enforcement_is_implemented_or_stage5_started(self) -> None:
        paths = [README, ROADMAP, COMPLETION_REPORT]
        forbidden_patterns = [
            r"\benforcement\s+is\s+implemented\b",
            r"\bimplemented\s+enforcement\b",
            r"\bGuard\s+blocks\s+process\.spawn\b",
            r"\bOS-wide\s+process\s+monitoring\s+is\s+implemented\b",
            r"\bStage\s+5\s+implementation\s+has\s+started\b",
            r"\bSlint\s+has\s+been\s+added\b",
            r"\bElectron\s+has\s+been\s+replaced\b",
            r"\bPython\s+Core\s+has\s+been\s+rewritten\b",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for pattern in forbidden_patterns:
                with self.subTest(path=path, pattern=pattern):
                    self.assertIsNone(
                        re.search(pattern, text, flags=re.IGNORECASE),
                        f"{path} contains forbidden claim: {pattern}",
                    )


if __name__ == "__main__":
    unittest.main()
