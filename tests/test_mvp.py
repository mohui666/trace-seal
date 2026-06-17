from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class TraceSealMvpTest(unittest.TestCase):
    def test_bad_agent_delete_records_and_explains(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "-m", "traceseal", "run", sys.executable, "examples/bad_agent_delete.py"],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        )
        latest = repo / "runs" / "latest"
        self.assertTrue(latest.exists(), completed.stdout + completed.stderr)
        run_id = latest.read_text(encoding="utf-8").strip()
        run_dir = repo / "runs" / run_id
        events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line]
        self.assertTrue(any(e["type"] == "file.write" and e["input"].get("path") == "data/important.txt" for e in events))
        self.assertTrue(any(e["type"] == "shell" and e["risk"].get("policy_rule") == "dangerous_delete" for e in events))

        replay = subprocess.run([sys.executable, "-m", "traceseal", "replay", "runs/latest"], cwd=repo, text=True, capture_output=True, check=True)
        self.assertIn("TraceSeal transcript replay", replay.stdout)
        self.assertIn("rm -rf data/", replay.stdout)

        explain = subprocess.run([sys.executable, "-m", "traceseal", "explain", "runs/latest"], cwd=repo, text=True, capture_output=True, check=True)
        self.assertIn("First harmful tool call", explain.stdout)
        self.assertIn("dangerous_delete", explain.stdout)
        self.assertIn("deny shell", explain.stdout)


if __name__ == "__main__":
    unittest.main()
