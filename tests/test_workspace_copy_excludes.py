from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sandbox.workspace import copy_workspace, should_exclude_workspace_entry


class WorkspaceCopyExcludesTest(unittest.TestCase):
    def test_copy_workspace_excludes_build_artifacts_and_caches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src"
            dst = root / "dst"
            src.mkdir()

            (src / "src.txt").write_text("source content\n", encoding="utf-8")
            (src / "policy").mkdir()
            (src / "policy" / "default_policy.json").write_text("{}\n", encoding="utf-8")
            (src / "examples").mkdir()
            (src / "examples" / "agent.py").write_text("print('ok')\n", encoding="utf-8")

            excluded_files = [
                "target/nested/file.txt",
                "runs/old-run/events.jsonl",
                "node_modules/pkg/file.txt",
                ".pytest_cache/cache.txt",
                "__pycache__/module.pyc",
                ".mypy_cache/cache.txt",
                ".ruff_cache/cache.txt",
                "out/app.bin",
                "dist/app.bin",
                "coverage/report.txt",
            ]
            for relative in excluded_files:
                path = src / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("generated\n", encoding="utf-8")

            copy_workspace(src, dst)

            self.assertEqual((dst / "src.txt").read_text(encoding="utf-8"), "source content\n")
            self.assertTrue((dst / "policy" / "default_policy.json").exists())
            self.assertTrue((dst / "examples" / "agent.py").exists())
            for relative in excluded_files:
                self.assertFalse((dst / relative).exists(), relative)

    def test_workspace_copy_exclude_helper_names_generated_directories(self) -> None:
        for name in [
            "target",
            "runs",
            "node_modules",
            ".pytest_cache",
            "__pycache__",
            ".mypy_cache",
            ".ruff_cache",
            "out",
            "dist",
            "coverage",
            ".git",
        ]:
            self.assertTrue(should_exclude_workspace_entry(name), name)

        self.assertFalse(should_exclude_workspace_entry("src"))
        self.assertFalse(should_exclude_workspace_entry("tests"))


if __name__ == "__main__":
    unittest.main()
