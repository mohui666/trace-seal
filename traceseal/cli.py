from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from minimizer.explain import explain_run
from recorder.workspace import snapshot_workspace
from replay.renderer import replay_run
from sandbox.workspace import copy_workspace


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id() -> str:
    return datetime.now().strftime("run_%Y%m%d_%H%M%S_%f")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def resolve_run_dir(path_arg: str | os.PathLike[str]) -> Path:
    p = Path(path_arg)
    if p.is_dir():
        return p.resolve()
    if p.is_file():
        run_id_or_path = p.read_text(encoding="utf-8").strip()
        if not run_id_or_path:
            raise SystemExit(f"empty run pointer: {p}")
        candidate = Path(run_id_or_path)
        if candidate.is_absolute() and candidate.is_dir():
            return candidate.resolve()
        sibling = p.parent / run_id_or_path
        if sibling.is_dir():
            return sibling.resolve()
    raise SystemExit(f"run directory not found: {path_arg}")


def build_child_env(project_root: Path, sandbox_root: Path, run_dir: Path, run_id: str) -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    pythonpath_parts = [
        str(project_root / "bootstrap"),
        str(project_root),
        str(sandbox_root / "bootstrap"),
        str(sandbox_root),
    ]
    if existing:
        pythonpath_parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    env["TRACESEAL_RUN_DIR"] = str(run_dir)
    env["TRACESEAL_RUN_ID"] = run_id
    env["TRACESEAL_WORKSPACE_ROOT"] = str(sandbox_root)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return env


def update_latest_pointer(runs_dir: Path, run_dir: Path) -> None:
    latest = runs_dir / "latest"
    if latest.exists() and latest.is_dir() and not latest.is_symlink():
        (runs_dir / "latest.txt").write_text(run_dir.name + "\n", encoding="utf-8")
        return
    try:
        if latest.exists() or latest.is_symlink():
            latest.unlink()
        latest.write_text(run_dir.name + "\n", encoding="utf-8")
    except OSError:
        (runs_dir / "latest.txt").write_text(run_dir.name + "\n", encoding="utf-8")


def command_for_display(command: Iterable[str]) -> str:
    return " ".join(str(x) for x in command)


def run_command(args: argparse.Namespace) -> int:
    if not args.command:
        raise SystemExit("usage: traceseal run <command...>")

    project_root = Path.cwd().resolve()
    runs_dir = project_root / "runs"
    run_id = new_run_id()
    run_dir = runs_dir / run_id
    sandbox_root = run_dir / "workspace"
    events_path = run_dir / "events.jsonl"

    run_dir.mkdir(parents=True, exist_ok=False)
    events_path.write_text("", encoding="utf-8")

    print(f"[traceseal] creating sandbox: {sandbox_root}", flush=True)
    copy_workspace(project_root, sandbox_root)

    write_json(run_dir / "workspace_before.json", snapshot_workspace(sandbox_root))

    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "command": args.command,
        "command_display": command_for_display(args.command),
        "original_cwd": str(project_root),
        "sandbox_cwd": str(sandbox_root),
        "run_dir": str(run_dir),
        "events_path": str(events_path),
        "started_at": utc_now(),
        "status": "running",
    }
    write_json(run_dir / "manifest.json", manifest)

    env = build_child_env(project_root, sandbox_root, run_dir, run_id)
    exit_code = 1
    error: str | None = None
    try:
        print(f"[traceseal] running: {manifest['command_display']}", flush=True)
        completed = subprocess.run(args.command, cwd=sandbox_root, env=env)
        exit_code = completed.returncode
    except FileNotFoundError as exc:
        error = f"command not found: {exc}"
        exit_code = 127
        print(f"[traceseal] {error}", file=sys.stderr, flush=True)
    finally:
        write_json(run_dir / "workspace_after.json", snapshot_workspace(sandbox_root))
        manifest.update(
            {
                "completed_at": utc_now(),
                "status": "completed" if exit_code == 0 else "failed",
                "exit_code": exit_code,
                "error": error,
                "event_count": sum(1 for _ in events_path.open("r", encoding="utf-8")) if events_path.exists() else 0,
            }
        )
        write_json(run_dir / "manifest.json", manifest)
        update_latest_pointer(runs_dir, run_dir)

    print(f"[traceseal] run id: {run_id}", flush=True)
    print(f"[traceseal] run dir: {run_dir}", flush=True)
    print(f"[traceseal] events: {events_path}", flush=True)
    print(f"[traceseal] latest pointer: {runs_dir / 'latest'}", flush=True)
    return exit_code


def replay_command(args: argparse.Namespace) -> int:
    run_dir = resolve_run_dir(args.run_dir)
    print(replay_run(run_dir))
    return 0


def explain_command(args: argparse.Namespace) -> int:
    run_dir = resolve_run_dir(args.run_dir)
    print(explain_run(run_dir))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="traceseal", description="TraceSeal MVP CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="run a Python agent inside a TraceSeal sandbox")
    p_run.add_argument("command", nargs=argparse.REMAINDER, help="command to run, e.g. python examples/bad_agent_delete.py")
    p_run.set_defaults(func=run_command)

    p_replay = sub.add_parser("replay", help="print transcript replay from a run directory")
    p_replay.add_argument("run_dir", help="run directory or runs/latest pointer")
    p_replay.set_defaults(func=replay_command)

    p_explain = sub.add_parser("explain", help="identify first harmful tool call")
    p_explain.add_argument("run_dir", help="run directory or runs/latest pointer")
    p_explain.set_defaults(func=explain_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
