from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs" / "slint-manual-smoke-test.md"
README_PATH = REPO_ROOT / "README.md"
DOCS_README_PATH = REPO_ROOT / "docs" / "README.md"


class SlintManualSmokeDocsTest(unittest.TestCase):
    def test_slint_manual_smoke_doc_exists(self) -> None:
        self.assertTrue(DOC_PATH.is_file(), f"missing document: {DOC_PATH}")

    def test_readmes_link_slint_manual_smoke_doc(self) -> None:
        for path in [README_PATH, DOCS_README_PATH]:
            text = path.read_text(encoding="utf-8")
            self.assertIn("docs/slint-manual-smoke-test.md", text)

    def test_slint_manual_smoke_doc_covers_required_checks_and_boundaries(self) -> None:
        text = DOC_PATH.read_text(encoding="utf-8")

        required_terms = [
            "cargo run -p traceseal-desktop-slint",
            "experimental-only",
            "Electron remains the default",
            "TraceSeal-Setup.exe",
            "loading state",
            "loaded state",
            "error state",
            "run detail",
            "refresh",
            "Slint 桌面路径仍是实验用途",
            "Electron 仍是默认桌面实现",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_slint_manual_smoke_doc_avoids_misleading_release_claims(self) -> None:
        text = DOC_PATH.read_text(encoding="utf-8")

        forbidden_terms = [
            "Slint has replaced Electron",
            "Electron has been replaced",
            "Slint is the default desktop",
            "Slint is production-ready",
            "v0.3.1 released",
            "TraceSeal-Setup.exe is Slint",
            "Slint installer",
        ]
        for term in forbidden_terms:
            with self.subTest(term=term):
                self.assertNotIn(term, text)


if __name__ == "__main__":
    unittest.main()
