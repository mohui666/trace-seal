from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


class TraceSealMvpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[1]

    def _run_agent(self, script_name: str) -> tuple[subprocess.CompletedProcess[str], Path, list[dict[str, Any]]]:
        env = os.environ.copy()
        env.pop("TRACESEAL_POLICY_MODE", None)
        env.pop("TRACESEAL_OFFLINE_HTTP", None)
        completed = subprocess.run(
            [sys.executable, "-m", "traceseal", "run", sys.executable, f"examples/{script_name}"],
            cwd=self.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"TraceSeal agent run failed with exit code {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}",
        )
        latest = self.repo / "runs" / "latest"
        self.assertTrue(latest.exists(), completed.stdout + completed.stderr)
        run_id = latest.read_text(encoding="utf-8").strip()
        run_dir = self.repo / "runs" / run_id
        events_path = run_dir / "events.jsonl"
        self.assertTrue(events_path.exists(), completed.stdout + completed.stderr)
        events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line]
        return completed, run_dir, events

    def _explain(self, run_dir: str = "runs/latest") -> str:
        completed = subprocess.run(
            [sys.executable, "-m", "traceseal", "explain", run_dir],
            cwd=self.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=True,
        )
        return completed.stdout

    def test_bad_agent_delete_detected(self) -> None:
        _completed, _run_dir, events = self._run_agent("bad_agent_delete.py")
        self.assertTrue(any(e["type"] == "file.write" and e["input"].get("path") == "data/important.txt" for e in events))
        self.assertTrue(any(e["type"] == "shell" and e["risk"].get("policy_rule") == "dangerous_delete" for e in events))

    def test_env_write_detected(self) -> None:
        _completed, run_dir, events = self._run_agent("bad_agent_env.py")
        env_events = [e for e in events if e["type"] == "file.write" and e["input"].get("path") == ".env"]
        self.assertTrue(env_events)
        self.assertEqual(env_events[0]["risk"].get("policy_rule"), "env_write")
        self.assertIn("sensitive environment file modified", " ".join(env_events[0]["risk"].get("reasons") or []))
        env_file = run_dir / "workspace" / ".env"
        self.assertIn("OPENAI_API_KEY=sk-demo-secret", env_file.read_text(encoding="utf-8"))
        self.assertIn("DATABASE_URL=postgres://demo:demo@localhost/demo", env_file.read_text(encoding="utf-8"))

    def test_git_push_detected(self) -> None:
        _completed, _run_dir, events = self._run_agent("bad_agent_git.py")
        git_events = [e for e in events if e["type"] == "shell" and e["risk"].get("policy_rule") == "git_push"]
        self.assertTrue(git_events)
        self.assertIn("git push origin main", git_events[0]["input"].get("command", ""))
        self.assertEqual(git_events[0]["output"].get("status"), "simulated")

    def test_replay_latest(self) -> None:
        self._run_agent("bad_agent_delete.py")
        replay = subprocess.run(
            [sys.executable, "-m", "traceseal", "replay", "runs/latest"],
            cwd=self.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=True,
        )
        self.assertIn("TraceSeal 执行时间线回放", replay.stdout)
        self.assertIn("rm -rf data/", replay.stdout)

    def test_explain_latest(self) -> None:
        self._run_agent("bad_agent_git.py")
        explain = self._explain()
        self.assertIn("首次有害工具调用", explain)
        self.assertIn("git_push", explain)
        self.assertIn("请求远程 git push", explain)
        self.assertIn("require_approval git \"push\"", explain)


if __name__ == "__main__":
    unittest.main()
