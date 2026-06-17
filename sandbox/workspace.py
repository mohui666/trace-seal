from __future__ import annotations

import shutil
from pathlib import Path

IGNORE_NAMES = {
    ".git",
    "runs",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".venv",
    "venv",
}


def copy_workspace(src: str | Path, dst: str | Path) -> None:
    src_path = Path(src).resolve()
    dst_path = Path(dst).resolve()
    if dst_path.exists():
        raise FileExistsError(f"sandbox already exists: {dst_path}")

    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {name for name in names if name in IGNORE_NAMES}

    shutil.copytree(src_path, dst_path, ignore=ignore)
