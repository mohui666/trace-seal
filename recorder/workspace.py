from __future__ import annotations

import fnmatch
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_EXCLUDES = {
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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_excluded(path: Path, root: Path) -> bool:
    try:
        rel_parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        rel_parts = path.parts
    return any(part in DEFAULT_EXCLUDES for part in rel_parts)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def state_for_path(path: Path, root: Path) -> dict[str, Any]:
    path = path.resolve()
    state: dict[str, Any] = {"path": relpath(path, root), "abs_path": str(path), "exists": path.exists()}
    if not path.exists():
        return state
    stat = path.stat()
    state.update(
        {
            "type": "dir" if path.is_dir() else "file",
            "size": stat.st_size if path.is_file() else None,
            "mtime_ns": stat.st_mtime_ns,
        }
    )
    if path.is_file():
        try:
            state["sha256"] = sha256_file(path)
        except OSError as exc:
            state["sha256_error"] = str(exc)
    return state


def snapshot_tree(target: str | os.PathLike[str], root: str | os.PathLike[str] | None = None) -> dict[str, dict[str, Any]]:
    root_path = Path(root or os.getcwd()).resolve()
    target_path = Path(target)
    target_path = (root_path / target_path).resolve() if not target_path.is_absolute() else target_path.resolve()
    if not target_path.exists():
        return {}

    records: dict[str, dict[str, Any]] = {}
    if target_path.is_file():
        records[relpath(target_path, root_path)] = state_for_path(target_path, root_path)
        return records

    if not _is_excluded(target_path, root_path):
        records[relpath(target_path, root_path)] = state_for_path(target_path, root_path)

    for current, dirnames, filenames in os.walk(target_path):
        current_path = Path(current)
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDES and not _is_excluded(current_path / d, root_path)]
        for dirname in dirnames:
            p = current_path / dirname
            records[relpath(p, root_path)] = state_for_path(p, root_path)
        for filename in filenames:
            p = current_path / filename
            if not _is_excluded(p, root_path):
                records[relpath(p, root_path)] = state_for_path(p, root_path)
    return records


def snapshot_workspace(root: str | os.PathLike[str]) -> dict[str, Any]:
    root_path = Path(root).resolve()
    records = snapshot_tree(root_path, root_path)
    return {
        "schema_version": 1,
        "root": str(root_path),
        "generated_at": utc_now(),
        "files": [records[key] for key in sorted(records)],
    }


def diff_trees(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for path in sorted(set(before) | set(after)):
        b = before.get(path)
        a = after.get(path)
        if b is None and a is not None:
            changes.append({"path": path, "change_type": "created", "before": None, "after": a})
        elif b is not None and a is None:
            changes.append({"path": path, "change_type": "deleted", "before": b, "after": None})
        elif b is not None and a is not None:
            changed = b.get("type") != a.get("type")
            if b.get("type") == "file":
                changed = changed or b.get("sha256") != a.get("sha256") or b.get("size") != a.get("size")
            if changed:
                changes.append({"path": path, "change_type": "modified", "before": b, "after": a})
    return changes


def path_matches_any(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)
