from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPIKE_README = ROOT / "crates" / "traceseal-desktop-slint" / "README.md"
SPIKE_UI = ROOT / "crates" / "traceseal-desktop-slint" / "ui" / "app.slint"
SPIKE_MAIN = ROOT / "crates" / "traceseal-desktop-slint" / "src" / "main.rs"
README = ROOT / "README.md"
ROADMAP = ROOT / "docs" / "roadmap.md"


class SlintHelloSpikeDocsTest(unittest.TestCase):
    def test_spike_files_exist(self) -> None:
        for path in [SPIKE_README, SPIKE_UI, SPIKE_MAIN]:
            with self.subTest(path=path):
                self.assertTrue(path.exists(), f"missing Slint spike file: {path}")

    def test_spike_readme_states_bilingual_boundaries(self) -> None:
        text = SPIKE_README.read_text(encoding="utf-8")
        required_terms = [
            "does not replace Electron",
            "does not call Python Core",
            "load real",
            "does not add a project-wide i18n framework",
            "不替换 Electron",
            "不调用 Python Core",
            "不读取真实",
            "不新增全项目 i18n",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_slint_ui_contains_local_language_toggle_contract(self) -> None:
        text = SPIKE_UI.read_text(encoding="utf-8")
        required_terms = [
            "English",
            "中文",
            "toggle",
            "language",
            "toggle-language",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_readme_and_roadmap_avoid_misleading_slint_claims(self) -> None:
        combined = "\n".join(
            [
                README.read_text(encoding="utf-8"),
                ROADMAP.read_text(encoding="utf-8"),
            ]
        )
        forbidden_phrases = [
            "Slint has replaced Electron",
            "Electron has been replaced",
            "Slint dashboard is the default",
            "Slint loads real runs",
            "Stage 5 implementation is complete",
            "v0.3.1 released",
            "project-wide i18n is implemented",
        ]
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
