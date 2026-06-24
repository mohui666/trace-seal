from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "slint-preview.yml"
DOC = REPO_ROOT / "docs" / "slint-preview-artifact.md"
README = REPO_ROOT / "README.md"
DOCS_README = REPO_ROOT / "docs" / "README.md"


class SlintPreviewArtifactDocsTest(unittest.TestCase):
    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def test_slint_preview_workflow_exists_and_is_manual_artifact_only(self) -> None:
        self.assertTrue(WORKFLOW.exists(), "missing Slint preview workflow")
        text = self.read_text(WORKFLOW)
        required_terms = [
            "workflow_dispatch",
            "windows-latest",
            "cargo check -p traceseal-desktop-slint",
            "cargo test -p traceseal-desktop-slint",
            "cargo build --release -p traceseal-desktop-slint",
            "actions/upload-artifact",
            "traceseal-slint-preview-windows-experimental",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

        forbidden_terms = [
            "on: push",
            "tags:",
            "softprops/action-gh-release",
            "gh release create",
            "TraceSeal-Setup.exe",
        ]
        for term in forbidden_terms:
            with self.subTest(term=term):
                self.assertNotIn(term, text)

    def test_slint_preview_artifact_doc_exists_and_is_linked(self) -> None:
        self.assertTrue(DOC.exists(), "missing Slint preview artifact doc")
        readme_text = self.read_text(README)
        docs_readme_text = self.read_text(DOCS_README)
        for text, source in (
            (readme_text, "README.md"),
            (docs_readme_text, "docs/README.md"),
        ):
            with self.subTest(source=source):
                self.assertIn("docs/slint-preview-artifact.md", text)

    def test_slint_preview_artifact_doc_records_release_boundaries(self) -> None:
        text = self.read_text(DOC)
        required_terms = [
            "experimental-only",
            "Slint Preview",
            "workflow artifact",
            "not a GitHub Release",
            "not `TraceSeal-Setup.exe`",
            "Electron remains the default",
            "Slint has not replaced Electron",
            "does not create v0.3.1",
            "does not modify v0.3.0 release assets",
            "Slint 预览构建产物仅用于实验",
            "Electron 仍是默认桌面实现",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

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
