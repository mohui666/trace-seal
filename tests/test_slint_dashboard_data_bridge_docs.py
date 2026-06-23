from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SLINT_ROOT = ROOT / "crates" / "traceseal-desktop-slint"
SLINT_README = SLINT_ROOT / "README.md"
SLINT_UI = SLINT_ROOT / "ui" / "app.slint"
SLINT_MAIN = SLINT_ROOT / "src" / "main.rs"
SLINT_BRIDGE = SLINT_ROOT / "src" / "dashboard_data.rs"
README = ROOT / "README.md"
ROADMAP = ROOT / "docs" / "roadmap.md"


class SlintDashboardDataBridgeDocsTest(unittest.TestCase):
    def test_bridge_files_exist(self) -> None:
        for path in [SLINT_MAIN, SLINT_BRIDGE, SLINT_UI]:
            with self.subTest(path=path):
                self.assertTrue(path.exists(), f"missing Slint bridge file: {path}")

    def test_crate_readme_documents_fixed_read_only_bridge(self) -> None:
        text = SLINT_README.read_text(encoding="utf-8")
        required_terms = [
            "dashboard-data latest",
            "dashboard-data list",
            "dashboard-data policy",
            "hard-coded",
            "does not call `traceseal run`",
            "does not execute target commands",
            "只读 dashboard-data 桥接",
            "不会使用用户输入拼接命令",
            "不调用 `traceseal run`",
            "不执行目标命令",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_readme_and_roadmap_avoid_misleading_bridge_claims(self) -> None:
        combined = "\n".join(
            [
                README.read_text(encoding="utf-8"),
                ROADMAP.read_text(encoding="utf-8"),
            ]
        )
        forbidden_phrases = [
            "Slint has replaced Electron",
            "Electron has been replaced",
            "Slint is the default desktop",
            "Slint executes traceseal run",
            "Slint edits policy",
            "v0.3.1 released",
        ]
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, combined)

    def test_slint_ui_exposes_read_only_load_controls(self) -> None:
        text = SLINT_UI.read_text(encoding="utf-8")
        required_terms = [
            "Load latest",
            "Load policy",
            "dashboard-data",
            "read-only",
            "只读",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
