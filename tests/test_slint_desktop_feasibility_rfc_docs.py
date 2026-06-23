from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RFC_PATH = ROOT / "docs" / "slint-desktop-feasibility-rfc.md"
README = ROOT / "README.md"
ROADMAP = ROOT / "docs" / "roadmap.md"


class SlintDesktopFeasibilityRfcDocsTest(unittest.TestCase):
    def test_rfc_exists(self) -> None:
        self.assertTrue(RFC_PATH.exists(), "missing Slint desktop feasibility RFC")

    def test_non_goals_are_explicit_and_statically_detectable(self) -> None:
        text = RFC_PATH.read_text(encoding="utf-8")
        normalized = text.replace("`", "")

        required_terms = [
            "## Non-goals",
            "does not add Slint runtime code",
            "does not add a Slint crate",
            "does not add .slint UI files",
            "does not replace Electron",
            "does not delete React, Vite, TypeScript, or TailwindCSS",
            "does not modify Electron main, preload, IPC, or renderer behavior",
            "does not modify Python Core behavior",
            "does not modify Rust Guard behavior",
            "does not implement enforcement",
            "does not execute or block target commands",
            "does not add a daemon or service",
            "does not add OS-wide process monitoring",
            "does not expand file, network, Git, or process monitoring",
            "does not modify packaging or installer behavior",
            "does not modify GitHub Actions release workflows",
            "does not create, move, delete, or retarget release tags",
            "does not create v0.3.1",
            "does not modify the v0.3.0 release or assets",
            "does not start Stage 5 implementation",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, normalized)

    def test_rfc_contains_required_feasibility_sections(self) -> None:
        text = RFC_PATH.read_text(encoding="utf-8")
        for heading in [
            "## Current baseline",
            "## Feasibility questions",
            "## Options",
            "## Proposed position",
            "## Decision gates",
            "## Validation plan for this RFC",
            "## Out of scope for current PR",
        ]:
            with self.subTest(heading=heading):
                self.assertIn(heading, text)

    def test_readme_and_roadmap_link_to_rfc(self) -> None:
        readme = README.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")

        self.assertIn("docs/slint-desktop-feasibility-rfc.md", readme)
        self.assertIn("Slint Desktop Feasibility RFC", readme)
        self.assertIn("slint-desktop-feasibility-rfc.md", roadmap)
        self.assertIn("Issue #51", roadmap)


if __name__ == "__main__":
    unittest.main()
