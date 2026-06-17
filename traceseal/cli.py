from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from dashboard.export import DashboardDataError, handle_dashboard_cli, json_dumps
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
            raise SystemExit(f"运行指针为空: {p}")
        candidate = Path(run_id_or_path)
        if candidate.is_absolute() and candidate.is_dir():
            return candidate.resolve()
        sibling = p.parent / run_id_or_path
        if sibling.is_dir():
            return sibling.resolve()
    raise SystemExit(f"找不到运行目录: {path_arg}")


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
    # Prevent tools such as git from walking out of runs/<id>/workspace and
    # discovering the real repository .git directory above runs/.
    env["GIT_CEILING_DIRECTORIES"] = str(run_dir)
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

    print(f"[traceseal] 正在创建沙箱: {sandbox_root}", flush=True)
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
        print(f"[traceseal] 正在执行: {manifest['command_display']}", flush=True)
        completed = subprocess.run(args.command, cwd=sandbox_root, env=env)
        exit_code = completed.returncode
    except FileNotFoundError as exc:
        error = f"命令不存在: {exc}"
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

    print(f"[traceseal] 运行编号: {run_id}", flush=True)
    print(f"[traceseal] 运行目录: {run_dir}", flush=True)
    print(f"[traceseal] 事件日志: {events_path}", flush=True)
    print(f"[traceseal] latest 指针: {runs_dir / 'latest'}", flush=True)
    return exit_code


def replay_command(args: argparse.Namespace) -> int:
    run_dir = resolve_run_dir(args.run_dir)
    print(replay_run(run_dir))
    return 0


def explain_command(args: argparse.Namespace) -> int:
    run_dir = resolve_run_dir(args.run_dir)
    print(explain_run(run_dir))
    return 0


def dashboard_data_command(args: argparse.Namespace) -> int:
    try:
        payload = handle_dashboard_cli(args.dashboard_args)
    except DashboardDataError as exc:
        print(exc.message, file=sys.stderr)
        print(json_dumps(exc.to_response()), end="")
        return exc.status
    except Exception as exc:  # keep stdout machine-readable for Electron callers
        wrapped = DashboardDataError("INTERNAL_ERROR", str(exc), 1)
        print(str(exc), file=sys.stderr)
        print(json_dumps(wrapped.to_response()), end="")
        return wrapped.status
    print(json_dumps(payload), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="traceseal", description="TraceSeal MVP 命令行工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="在 TraceSeal 沙箱中运行 Python Agent")
    p_run.add_argument("command", nargs=argparse.REMAINDER, help="要运行的命令，例如 python examples/bad_agent_delete.py")
    p_run.set_defaults(func=run_command)

    p_replay = sub.add_parser("replay", help="从运行目录输出中文 transcript 回放")
    p_replay.add_argument("run_dir", help="运行目录或 runs/latest 指针")
    p_replay.set_defaults(func=replay_command)

    p_explain = sub.add_parser("explain", help="定位首次有害工具调用")
    p_explain.add_argument("run_dir", help="运行目录或 runs/latest 指针")
    p_explain.set_defaults(func=explain_command)

    p_dashboard = sub.add_parser("dashboard-data", help="导出桌面 Dashboard 可读取的 JSON")
    p_dashboard.add_argument(
        "dashboard_args",
        nargs="*",
        help="latest | runs/latest | list | policy | run <run_id> | <run_id>",
    )
    p_dashboard.set_defaults(func=dashboard_data_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
