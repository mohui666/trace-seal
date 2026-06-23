from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOCS_README = ROOT / "docs" / "README.md"
PROJECT_STATUS = ROOT / "docs" / "project-status.md"
ROADMAP = ROOT / "docs" / "roadmap.md"
WINDOWS_INSTALL_TROUBLESHOOTING = ROOT / "docs" / "windows-install-troubleshooting.md"
RELEASE_VERIFICATION_CHECKLIST = ROOT / "docs" / "release-verification-checklist.md"
CORE_DOCS = (README, DOCS_README, PROJECT_STATUS, ROADMAP)

FORBIDDEN_ASSERTIONS = (
    "Slint has replaced Electron",
    "Electron has been replaced",
    "Slint is the default desktop",
    "Stage 5 is complete",
    "v0.3.1 released",
    "Rust Core replaced Python Core",
    "enforcement is implemented",
    "installer is signed",
    "SmartScreen will not appear",
    "packaging workflow changed",
)


class DocsStructureTests(unittest.TestCase):
    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def test_required_docs_exist(self) -> None:
        for path in CORE_DOCS[:3]:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertTrue(path.exists(), f"missing {path.relative_to(ROOT)}")

    def test_readme_is_concise_entrypoint(self) -> None:
        text = self.read_text(README)
        for expected in (
            "TraceSeal",
            "Quick start",
            "快速开始",
            "Documentation",
            "文档导航",
            "v0.3.0",
            "Electron",
            "Slint",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

        self.assertLessEqual(text.count("Issue #"), 3)
        self.assertLessEqual(text.count("PR #"), 3)
        self.assertLessEqual(len(text.splitlines()), 180)

    def test_core_docs_are_bilingual(self) -> None:
        for path in CORE_DOCS:
            text = self.read_text(path)
            with self.subTest(path=path.relative_to(ROOT), language="english"):
                self.assertRegex(text, r"[A-Za-z]")
            with self.subTest(path=path.relative_to(ROOT), language="chinese"):
                self.assertRegex(text, r"[\u4e00-\u9fff]")

    def test_project_status_records_release_and_desktop_boundaries(self) -> None:
        text = self.read_text(PROJECT_STATUS)
        for expected in (
            "v0.3.0",
            "59ae99d6db495276963e2f4b47b137f4de846d35",
            "Electron remains the default",
            "Slint remains experimental",
            "There is no v0.3.1",
            "当前没有 `v0.3.1`",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_core_docs_avoid_misleading_assertions(self) -> None:
        for path in CORE_DOCS:
            text = self.read_text(path)
            for forbidden in FORBIDDEN_ASSERTIONS:
                with self.subTest(path=path.relative_to(ROOT), forbidden=forbidden):
                    self.assertNotIn(forbidden, text)

    def test_windows_install_troubleshooting_doc_is_linked_and_bounded(self) -> None:
        self.assertTrue(
            WINDOWS_INSTALL_TROUBLESHOOTING.exists(),
            "missing docs/windows-install-troubleshooting.md",
        )

        readme_text = self.read_text(README)
        docs_index_text = self.read_text(DOCS_README)
        for text, source in (
            (readme_text, "README.md"),
            (docs_index_text, "docs/README.md"),
        ):
            with self.subTest(source=source):
                self.assertIn("docs/windows-install-troubleshooting.md", text)

        doc_text = self.read_text(WINDOWS_INSTALL_TROUBLESHOOTING)
        for expected in (
            "SmartScreen",
            "SHA256",
            "unsigned",
            "v0.3.0",
            "未签名",
            "校验 SHA256",
            "不修改 release assets",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, doc_text)

        for forbidden in (
            "v0.3.1 released",
            "installer is signed",
            "SmartScreen will not appear",
            "packaging workflow changed",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, doc_text)

    def test_release_verification_checklist_is_linked_and_bounded(self) -> None:
        self.assertTrue(
            RELEASE_VERIFICATION_CHECKLIST.exists(),
            "missing docs/release-verification-checklist.md",
        )

        readme_text = self.read_text(README)
        docs_index_text = self.read_text(DOCS_README)
        for text, source in (
            (readme_text, "README.md"),
            (docs_index_text, "docs/README.md"),
        ):
            with self.subTest(source=source):
                self.assertIn("docs/release-verification-checklist.md", text)

        doc_text = self.read_text(RELEASE_VERIFICATION_CHECKLIST)
        for expected in (
            "v0.3.0",
            "59ae99d6db495276963e2f4b47b137f4de846d35",
            "SHA256SUMS.txt",
            "TraceSeal-Setup.exe",
            "There is no v0.3.1",
            "不存在 v0.3.1",
            "does not modify tags",
            "不修改 tag",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, doc_text)

        for forbidden in (
            "v0.3.1 released",
            "created v0.3.1",
            "release assets changed",
            "packaging workflow changed",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, doc_text)


if __name__ == "__main__":
    unittest.main()
