from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
DOCS_README = REPO_ROOT / "docs" / "README.md"
PROJECT_STATUS = REPO_ROOT / "docs" / "project-status.md"
SLINT_MANUAL_SMOKE = REPO_ROOT / "docs" / "slint-manual-smoke-test.md"


class SlintExperimentalStatusDocsTest(unittest.TestCase):
    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def test_project_status_records_current_slint_capabilities(self) -> None:
        text = self.read_text(PROJECT_STATUS)
        required_terms = [
            "read-only dashboard summary",
            "run detail",
            "run history",
            "policy detail",
            "async",
            "fixture-backed demo preview",
            "scrollable",
            "Electron remains the default",
            "Slint remains experimental-only",
            "只读 dashboard 摘要",
            "只读运行详情",
            "只读运行历史",
            "只读策略详情",
            "异步非阻塞加载",
            "基于 fixture 的示例预览",
            "可滚动 / 响应式布局",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_slint_manual_smoke_doc_records_current_checks_and_release_boundary(self) -> None:
        text = self.read_text(SLINT_MANUAL_SMOKE)
        required_terms = [
            "cargo run -p traceseal-desktop-slint",
            "TraceSeal-Setup.exe",
            "not the v0.3.0 release installer",
            "loading",
            "loaded",
            "error",
            "run detail",
            "run history",
            "policy detail",
            "TraceSeal-Setup.exe is still the Electron release installer",
            "Slint is not packaged as a release exe",
            "Slint 尚未作为 release exe 打包",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_readme_or_docs_readme_links_slint_manual_smoke_test(self) -> None:
        combined = "\n".join(
            [self.read_text(README), self.read_text(DOCS_README)]
        )
        self.assertIn("docs/slint-manual-smoke-test.md", combined)

    def test_core_docs_do_not_claim_slint_release_or_electron_replacement(self) -> None:
        checked_docs = [README, DOCS_README, PROJECT_STATUS, SLINT_MANUAL_SMOKE]
        forbidden_terms = [
            "Slint has replaced Electron",
            "Electron has been replaced",
            "Slint is the default desktop",
            "Slint is production-ready",
            "v0.3.1 released",
        ]
        for path in checked_docs:
            text = self.read_text(path)
            for term in forbidden_terms:
                with self.subTest(path=path.relative_to(REPO_ROOT), term=term):
                    self.assertNotIn(term, text)


if __name__ == "__main__":
    unittest.main()
