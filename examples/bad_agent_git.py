"""Bad agent demo: attempts a git push without pushing anything real.

TraceSeal's subprocess hook simulates git push, so this command cannot publish
to a remote. It still exercises the git_push policy matcher.
"""

import subprocess


def main() -> None:
    command = "git push origin main"
    completed = subprocess.run(command, shell=True, text=True, capture_output=True, check=False)
    print(f"bad agent attempted: {command}")
    print(f"git returned: {completed.returncode}")
    if completed.stderr:
        print(completed.stderr.strip().splitlines()[0])


if __name__ == "__main__":
    main()
