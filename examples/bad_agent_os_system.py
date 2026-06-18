"""Safe cross-platform demo of TraceSeal's os.system interception.

All filesystem effects are confined to a disposable directory inside the
TraceSeal sandbox workspace.
"""

from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    demo_dir = Path("trace_os_system_demo") / "protected data 保护"
    demo_dir.mkdir(parents=True, exist_ok=True)
    protected = demo_dir / "important file.txt"
    protected.write_text("TraceSeal must protect this demo file\n", encoding="utf-8")

    success_command = "cmd /c exit 0" if os.name == "nt" else "true"
    failure_command = "cmd /c exit 7" if os.name == "nt" else "sh -c 'exit 7'"
    delete_command = (
        f'rmdir /s /q "{demo_dir}"'
        if os.name == "nt"
        else f'rm -rf -- "{demo_dir}"'
    )

    print(f"harmless os.system status: {os.system(success_command)}")
    print(f"non-zero os.system status: {os.system(failure_command)}")
    print(f"dangerous os.system status: {os.system(delete_command)}")
    print(f"protected file exists after command: {protected.exists()}")


if __name__ == "__main__":
    main()
