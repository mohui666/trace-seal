from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any


GIT_TIMEOUT_SECONDS = 10


def _empty_state(workspace: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "workspace": str(workspace),
        "is_git_repo": False,
        "branch": None,
        "head": None,
        "dirty": False,
        "status_short": "",
        "staged": [],
        "unstaged": [],
        "untracked": [],
        "error": None,
    }


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.setdefault("LC_ALL", "C")
    return env


def _run_git(workspace: Path, *args: str, allow_failure: bool = False) -> tuple[str, str | None]:
    command = [
        "git",
        "--no-optional-locks",
        "-c",
        "core.fsmonitor=false",
        *args,
    ]
    completed = subprocess.run(
        command,
        cwd=workspace,
        env=_git_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )
    stdout = completed.stdout.rstrip("\r\n")
    if completed.returncode == 0:
        return stdout, None
    if allow_failure:
        return stdout, None
    detail = completed.stderr.strip() or stdout or f"exit code {completed.returncode}"
    return stdout, f"git {' '.join(args)} failed: {detail}"


def _parse_name_status(output: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in output.splitlines():
        if not line:
            continue
        fields = line.split("\t")
        status = fields[0]
        if len(fields) >= 3 and status[:1] in {"R", "C"}:
            entries.append({"status": status, "old_path": fields[1], "path": fields[2]})
        elif len(fields) >= 2:
            entries.append({"status": status, "path": fields[1]})
        else:
            entries.append({"status": status, "path": ""})
    return entries


def _parse_untracked(status_short: str) -> list[str]:
    return [line[3:] for line in status_short.splitlines() if line.startswith("?? ")]


def collect_git_state(workspace: Path) -> dict[str, Any]:
    """Collect local Git metadata without storing source diff content.

    Failures are represented in ``error`` so Git availability or repository
    problems never have to abort a TraceSeal run.
    """

    workspace = Path(workspace).resolve()
    state = _empty_state(workspace)
    errors: list[str] = []

    if not workspace.is_dir():
        state["error"] = f"workspace is not a directory: {workspace}"
        return state

    try:
        inside, error = _run_git(workspace, "rev-parse", "--is-inside-work-tree")
        if error or inside.strip().lower() != "true":
            state["error"] = error or "not a Git work tree"
            return state

        state["is_git_repo"] = True

        branch, branch_error = _run_git(workspace, "symbolic-ref", "--quiet", "--short", "HEAD", allow_failure=True)
        state["branch"] = branch or None
        if branch_error:
            errors.append(branch_error)

        head, head_error = _run_git(workspace, "rev-parse", "--verify", "HEAD")
        state["head"] = head or None
        if head_error:
            errors.append(head_error)

        status_short, status_error = _run_git(workspace, "status", "--short", "--untracked-files=all")
        state["status_short"] = status_short
        state["untracked"] = _parse_untracked(status_short)
        if status_error:
            errors.append(status_error)

        staged_raw, staged_error = _run_git(
            workspace,
            "diff",
            "--cached",
            "--name-status",
            "--no-ext-diff",
            "--no-textconv",
        )
        state["staged"] = _parse_name_status(staged_raw)
        if staged_error:
            errors.append(staged_error)

        unstaged_raw, unstaged_error = _run_git(
            workspace,
            "diff",
            "--name-status",
            "--no-ext-diff",
            "--no-textconv",
        )
        state["unstaged"] = _parse_name_status(unstaged_raw)
        if unstaged_error:
            errors.append(unstaged_error)

        state["dirty"] = bool(status_short)
        state["error"] = "; ".join(errors) or None
        return state
    except FileNotFoundError as exc:
        state["error"] = f"git executable not found: {exc}"
    except subprocess.TimeoutExpired as exc:
        state["error"] = f"git command timed out after {exc.timeout} seconds"
    except Exception as exc:  # recorder metadata must never abort an Agent run
        state["error"] = f"git state collection failed: {type(exc).__name__}: {exc}"
    return state


def _changed_paths(state: dict[str, Any]) -> set[str]:
    paths = {str(path) for path in state.get("untracked") or [] if path}
    for key in ("staged", "unstaged"):
        for entry in state.get(key) or []:
            if isinstance(entry, dict):
                for path_key in ("old_path", "path"):
                    if entry.get(path_key):
                        paths.add(str(entry[path_key]))
    return paths


def summarize_git_states(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "head_changed": before.get("head") != after.get("head"),
        "branch_changed": before.get("branch") != after.get("branch"),
        "dirty_before": bool(before.get("dirty")),
        "dirty_after": bool(after.get("dirty")),
        "staged_count": len(after.get("staged") or []),
        "unstaged_count": len(after.get("unstaged") or []),
        "untracked_count": len(after.get("untracked") or []),
        "changed_file_count": len(_changed_paths(after)),
    }


def compact_git_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "is_git_repo": bool(state.get("is_git_repo")),
        "branch": state.get("branch"),
        "head": state.get("head"),
        "dirty": bool(state.get("dirty")),
        "error": state.get("error"),
    }
