from __future__ import annotations

import re
import shutil
from pathlib import Path

IGNORE_NAMES = {
    "runs",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".vite",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
}

_CONFIG_SECTION_RE = re.compile(r'^\s*\[\s*([A-Za-z0-9.-]+)(?:\s+"[^"]*")?\s*\]')


def _sanitize_git_config(path: Path) -> None:
    if not path.is_file():
        return

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    kept: list[str] = []
    skip_section = False
    current_section = ""
    for line in lines:
        section = _CONFIG_SECTION_RE.match(line)
        if section:
            current_section = section.group(1).lower()
            section_family = current_section.split(".", 1)[0]
            skip_section = section_family in {"remote", "include", "includeif"}
            if skip_section:
                continue
        if skip_section:
            continue
        if current_section == "core" and re.match(r"^\s*hookspath\s*=", line, flags=re.IGNORECASE):
            continue
        kept.append(line)
    path.write_text("".join(kept), encoding="utf-8")


def _sanitize_git_metadata(git_dir: Path) -> None:
    _sanitize_git_config(git_dir / "config")
    _sanitize_git_config(git_dir / "config.worktree")
    hooks = git_dir / "hooks"
    if hooks.exists():
        shutil.rmtree(hooks)


def copy_workspace(src: str | Path, dst: str | Path) -> None:
    src_path = Path(src).resolve()
    dst_path = Path(dst).resolve()
    if dst_path.exists():
        raise FileExistsError(f"sandbox already exists: {dst_path}")

    source_git = src_path / ".git"

    def ignore(current_dir: str, names: list[str]) -> set[str]:
        ignored = {name for name in names if name in IGNORE_NAMES}
        current_path = Path(current_dir).resolve()
        if ".git" in names and (current_path != src_path or not source_git.is_dir()):
            ignored.add(".git")
        return ignored

    shutil.copytree(src_path, dst_path, ignore=ignore)

    copied_git = dst_path / ".git"
    if copied_git.is_dir():
        # The sandbox needs an independent index for staged-state auditing, but
        # it must not inherit network remotes, include files, or executable
        # hooks from the user's repository.
        _sanitize_git_metadata(copied_git)
