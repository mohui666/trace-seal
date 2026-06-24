from __future__ import annotations

import re
import shutil
from pathlib import Path

DEFAULT_WORKSPACE_COPY_EXCLUDES = {
    "runs",
    "target",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".vite",
    ".git",
    "node_modules",
    "dist",
    "build",
    "out",
    "coverage",
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


def should_exclude_workspace_entry(name: str, *, keep_source_git_metadata: bool = False) -> bool:
    if name == ".git" and keep_source_git_metadata:
        return False
    return name in DEFAULT_WORKSPACE_COPY_EXCLUDES


def copy_workspace(src: str | Path, dst: str | Path) -> None:
    src_path = Path(src).resolve()
    dst_path = Path(dst).resolve()
    if dst_path.exists():
        raise FileExistsError(f"sandbox already exists: {dst_path}")

    source_git = src_path / ".git"

    def ignore(current_dir: str, names: list[str]) -> set[str]:
        current_path = Path(current_dir).resolve()
        keep_source_git_metadata = current_path == src_path and source_git.is_dir()
        return {
            name
            for name in names
            if should_exclude_workspace_entry(name, keep_source_git_metadata=keep_source_git_metadata)
        }

    shutil.copytree(src_path, dst_path, ignore=ignore)

    copied_git = dst_path / ".git"
    if copied_git.is_dir():
        # The sandbox needs an independent index for staged-state auditing, but
        # it must not inherit network remotes, include files, or executable
        # hooks from the user's repository.
        _sanitize_git_metadata(copied_git)
