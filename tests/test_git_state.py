from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dashboard.export import handle_dashboard_cli
from recorder.git_state import collect_git_state


class GitStateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_repo = Path(__file__).resolve().parents[1]
        cls.git = shutil.which("git")

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        if not self.git:
            self.skipTest("git is not installed")
        return subprocess.run(
            [self.git, *args],
            cwd=cwd or self.root,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=True,
        )

    def _init_repo(self) -> tuple[str, str]:
        self._git("init")
        self._git("config", "user.email", "traceseal-tests@example.invalid")
        self._git("config", "user.name", "TraceSeal Tests")
        (self.root / "tracked.txt").write_text("baseline\n", encoding="utf-8")
        self._git("add", "tracked.txt")
        self._git("commit", "-m", "baseline")
        state = collect_git_state(self.root)
        return str(state["branch"]), str(state["head"])

    def _run_traceseal(self, command: list[str], *, path: str | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            part for part in [str(self.source_repo), env.get("PYTHONPATH", "")] if part
        )
        if path is not None:
            env["PATH"] = path
        return subprocess.run(
            [sys.executable, "-m", "traceseal", "run", "--", *command],
            cwd=self.root,
            env=env,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )

    def test_non_git_directory_returns_metadata(self) -> None:
        state = collect_git_state(self.root)
        self.assertFalse(state["is_git_repo"])
        self.assertIsNotNone(state["error"])

    def test_git_repository_records_branch_and_head(self) -> None:
        branch, head = self._init_repo()
        state = collect_git_state(self.root)
        self.assertTrue(state["is_git_repo"])
        self.assertEqual(state["branch"], branch)
        self.assertEqual(state["head"], head)
        self.assertFalse(state["dirty"])

    def test_modified_file_is_unstaged(self) -> None:
        self._init_repo()
        (self.root / "tracked.txt").write_text("modified\n", encoding="utf-8")
        state = collect_git_state(self.root)
        self.assertIn({"status": "M", "path": "tracked.txt"}, state["unstaged"])

    def test_git_add_is_staged(self) -> None:
        self._init_repo()
        (self.root / "staged.txt").write_text("staged\n", encoding="utf-8")
        self._git("add", "staged.txt")
        state = collect_git_state(self.root)
        self.assertIn({"status": "A", "path": "staged.txt"}, state["staged"])

    def test_untracked_file_is_recorded(self) -> None:
        self._init_repo()
        (self.root / "untracked.txt").write_text("untracked\n", encoding="utf-8")
        state = collect_git_state(self.root)
        self.assertIn("untracked.txt", state["untracked"])

    def test_git_missing_returns_error_metadata(self) -> None:
        with mock.patch("recorder.git_state.subprocess.run", side_effect=FileNotFoundError("git")):
            state = collect_git_state(self.root)
        self.assertFalse(state["is_git_repo"])
        self.assertIn("not found", state["error"])

    def test_git_missing_does_not_abort_run(self) -> None:
        (self.root / "agent.py").write_text("print('agent completed')\n", encoding="utf-8")
        completed = self._run_traceseal([sys.executable, "agent.py"], path="")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        run_id = (self.root / "runs" / "latest").read_text(encoding="utf-8").strip()
        run_dir = self.root / "runs" / run_id
        before = json.loads((run_dir / "git_state_before.json").read_text(encoding="utf-8"))
        after = json.loads((run_dir / "git_state_after.json").read_text(encoding="utf-8"))
        self.assertIn("not found", before["error"])
        self.assertIn("not found", after["error"])

    def test_run_and_dashboard_include_git_state_summary(self) -> None:
        self._init_repo()
        agent = self.root / "agent.py"
        agent.write_text(
            "from pathlib import Path\n"
            "import subprocess\n"
            "Path('tracked.txt').write_text('modified\\n', encoding='utf-8')\n"
            "Path('staged.txt').write_text('staged\\n', encoding='utf-8')\n"
            "subprocess.run(['git', 'add', '--', 'staged.txt'], check=True)\n"
            "Path('untracked.txt').write_text('untracked\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        self._git("add", "agent.py")
        self._git("commit", "-m", "add agent")

        completed = self._run_traceseal([sys.executable, "agent.py"])
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        run_id = (self.root / "runs" / "latest").read_text(encoding="utf-8").strip()
        payload = handle_dashboard_cli(["run", run_id], self.root)
        git_state = payload["git_state"]

        self.assertTrue(git_state["before"]["is_git_repo"])
        self.assertTrue(git_state["after"]["is_git_repo"])
        self.assertEqual(git_state["summary"]["staged_count"], 1)
        self.assertEqual(git_state["summary"]["unstaged_count"], 1)
        self.assertEqual(git_state["summary"]["untracked_count"], 1)
        self.assertEqual(git_state["summary"]["changed_file_count"], 3)
        self.assertEqual((self.root / "tracked.txt").read_text(encoding="utf-8"), "baseline\n")
        self.assertFalse((self.root / "staged.txt").exists())
        self.assertFalse((self.root / "untracked.txt").exists())


if __name__ == "__main__":
    unittest.main()
