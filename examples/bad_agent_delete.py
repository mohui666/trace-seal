"""Bad agent demo for TraceSeal MVP.

It creates a protected data file and then deletes the whole data directory with
an rm -rf style shell command. TraceSeal records both the file write and the
dangerous shell operation. On Windows, the SDK simulates rm -rf so this demo is
cross-platform.
"""

from pathlib import Path
import subprocess


def main() -> None:
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    important = data_dir / "important.txt"
    important.write_text("do not delete this file\n", encoding="utf-8")
    print(f"created {important}")

    subprocess.run(["rm", "-rf", "data/"], check=True)
    print("bad agent deleted data/ with rm -rf")

    if not important.exists():
        print("simulated failure: important data is gone")


if __name__ == "__main__":
    main()
