"""Exercise Git push classification without contacting any remote.

TraceSeal intercepts every subprocess call below and returns a simulated result.
"""

from __future__ import annotations

import subprocess


COMMANDS = [
    ["git", "push", "origin", "main"],
    ["git", "push", "--force", "origin", "main"],
    ["git", "push", "--force-with-lease", "origin", "main"],
    ["git", "push", "--mirror", "origin"],
    ["git", "push", "origin", "--delete", "old-branch"],
    ["git", "push", "origin", "+main:main"],
    ["git", "push", "--all", "origin"],
    ["git", "push", "--tags", "origin"],
]


def main() -> None:
    for command in COMMANDS:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        print(f"simulated: {' '.join(command)} -> {completed.returncode}")


if __name__ == "__main__":
    main()
