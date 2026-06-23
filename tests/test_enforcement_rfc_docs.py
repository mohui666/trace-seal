from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RFC_PATH = ROOT / "docs" / "stage4-enforcement-experiment-rfc.md"


class EnforcementExperimentRfcDocsTest(unittest.TestCase):
    def test_rfc_exists(self) -> None:
        self.assertTrue(RFC_PATH.exists(), "missing enforcement experiment RFC")

    def test_non_goals_are_explicit_and_statically_detectable(self) -> None:
        text = RFC_PATH.read_text(encoding="utf-8")
        normalized = text.replace("`", "")

        required_terms = [
            "## Non-goals",
            "does not implement enforcement",
            "does not block process.spawn",
            "does not execute the process.spawn target command",
            "does not add a daemon or service",
            "does not add OS-wide process monitoring",
            "does not add file, network, or Git monitoring",
            "does not change Rust Guard behavior",
            "does not change Python policy behavior",
            "does not change the Electron UI",
            "does not change installer or release workflows",
            "does not create a new tag or release",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, normalized)

    def test_rfc_contains_required_safety_sections(self) -> None:
        text = RFC_PATH.read_text(encoding="utf-8")
        for heading in [
            "## Proposed experiment model",
            "## Stage gates",
            "## Safety boundaries",
            "## Kill switch",
            "## Audit",
            "## Rollback",
            "## User consent",
            "## Risks and mitigations",
            "## Validation plan",
            "## Out of scope for current PR",
        ]:
            with self.subTest(heading=heading):
                self.assertIn(heading, text)


if __name__ == "__main__":
    unittest.main()
