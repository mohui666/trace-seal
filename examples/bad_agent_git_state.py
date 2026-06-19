"""Create staged, unstaged, and untracked changes inside the TraceSeal sandbox."""

from pathlib import Path
import subprocess


def main() -> None:
    readme = Path("README.md")
    readme.write_text(readme.read_text(encoding="utf-8") + "\n<!-- TraceSeal unstaged demo change -->\n", encoding="utf-8")

    demo_dir = Path("trace_git_state_demo")
    demo_dir.mkdir(exist_ok=True)
    staged = demo_dir / "staged_file.txt"
    staged.write_text("created and staged by bad_agent_git_state.py\n", encoding="utf-8")
    subprocess.run(["git", "add", "--", staged.as_posix()], check=True)

    untracked = demo_dir / "untracked_file.txt"
    untracked.write_text("created but intentionally left untracked\n", encoding="utf-8")

    print("created one unstaged modification, one staged file, and one untracked file")


if __name__ == "__main__":
    main()
