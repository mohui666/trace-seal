from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RFC_PATH = ROOT / "docs" / "rust-core-parity-rfc.md"
README = ROOT / "README.md"
ROADMAP = ROOT / "docs" / "roadmap.md"


class RustCoreParityDocsTest(unittest.TestCase):
    def test_rfc_exists(self) -> None:
        self.assertTrue(RFC_PATH.exists(), "missing Rust Core parity RFC")

    def test_rfc_contains_required_headings(self) -> None:
        text = RFC_PATH.read_text(encoding="utf-8")
        required_headings = [
            "## Status",
            "## Background",
            "## Current Python Core responsibilities",
            "## Why evaluate Rust Core parity",
            "## Goals",
            "## Non-goals",
            "## Module classification",
            "## Behavior parity requirements",
            "## Data contracts",
            "## Fixture-based parity testing",
            "## Candidate architecture",
            "## Migration boundaries",
            "## Rust Core and Slint relationship",
            "## Compatibility and rollback rules",
            "## Risk analysis",
            "## Proposed staged plan",
            "## Validation plan",
        ]
        for heading in required_headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, text)

    def test_rfc_states_planning_boundaries(self) -> None:
        text = RFC_PATH.read_text(encoding="utf-8").replace("`", "")
        required_terms = [
            "documentation-only",
            "planning-only",
            "does not implement Rust Core",
            "does not rewrite Python Core",
            "does not change traceseal dashboard-data output",
            "does not change dashboard-data output",
            "Python Core remains source of truth",
            "does not add Slint",
            "does not replace Electron",
            "does not modify the v0.3.0 release",
            "Rust Core is a parity target, not an immediate replacement",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_readme_and_roadmap_link_to_rfc_without_misleading_claims(self) -> None:
        readme = README.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")

        self.assertIn("docs/rust-core-parity-rfc.md", readme)
        self.assertIn("Rust Core Parity RFC", readme)
        self.assertIn("rust-core-parity-rfc.md", roadmap)
        self.assertIn("Issue #52", roadmap)
        self.assertIn("Python Core remains the source of truth", roadmap)

        forbidden_phrases = [
            "Rust Core is implemented",
            "Python Core has been replaced",
            "Rust Core backend is default",
            "Slint dashboard is implemented",
            "Electron has been replaced",
            "v0.3.1 released",
        ]
        combined = f"{readme}\n{roadmap}"
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
