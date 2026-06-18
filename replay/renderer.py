from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_events(run_dir: str | Path) -> list[dict[str, Any]]:
    events_path = Path(run_dir) / "events.jsonl"
    if not events_path.exists():
        return []
    events: list[dict[str, Any]] = []
    with events_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def _event_title(event: dict[str, Any]) -> str:
    typ = event.get("type")
    inp = event.get("input") or {}
    if typ == "shell":
        source = f" ({event.get('operation')})" if event.get("operation") == "os.system" else ""
        return f"Shell 命令{source}: {inp.get('command', '')}"
    if typ == "file.write":
        return f"文件写入: {inp.get('path', '')}"
    if typ == "file.read":
        return f"文件读取 ({inp.get('source', 'unknown')}): {inp.get('path', '')}"
    if typ == "file.delete":
        return f"文件删除: {inp.get('path', '')}"
    if typ == "http":
        return f"HTTP 请求: {inp.get('method', 'GET')} {inp.get('url', '')}"
    if typ == "sdk":
        return f"SDK: {event.get('operation', '')}"
    return f"{typ}: {event.get('operation', '')}"


def _translate_status(status: Any) -> str:
    mapping = {
        "running": "运行中",
        "completed": "完成",
        "failed": "失败",
        "ok": "成功",
        "blocked": "已阻断",
        "exception": "异常",
        "simulated": "已模拟",
    }
    return mapping.get(str(status), str(status))


def _translate_change_type(change_type: Any) -> str:
    mapping = {"created": "创建", "modified": "修改", "deleted": "删除", "changed": "变更"}
    return mapping.get(str(change_type), str(change_type))


def _translate_reason(reason: str) -> str:
    if reason.startswith("recursive force delete requested: "):
        return reason.replace("recursive force delete requested: ", "请求递归强制删除: ", 1)
    if reason.startswith("write to environment/config file: "):
        return reason.replace("write to environment/config file: ", "写入环境/配置文件: ", 1)
    if reason.startswith("sensitive environment file modified: "):
        return reason.replace("sensitive environment file modified: ", "敏感环境配置文件被修改: ", 1)
    if reason.startswith("sensitive file read: "):
        return reason.replace("sensitive file read: ", "读取敏感文件: ", 1)
    if reason == "git push publishes repository state":
        return "git push 会发布仓库状态"
    if reason == "remote git push requested":
        return "请求远程 git push"
    if reason.startswith("suspicious outbound HTTP POST: "):
        return reason.replace("suspicious outbound HTTP POST: ", "可疑的出站 HTTP POST: ", 1)
    if reason.startswith("outbound HTTP request: "):
        return reason.replace("outbound HTTP request: ", "出站 HTTP 请求: ", 1)
    return reason


def replay_run(run_dir: str | Path) -> str:
    run_dir = Path(run_dir)
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    events = load_events(run_dir)

    lines: list[str] = []
    lines.append("TraceSeal 执行时间线回放")
    lines.append(f"运行编号: {manifest.get('run_id', run_dir.name)}")
    lines.append(f"执行命令: {manifest.get('command_display', manifest.get('command'))}")
    lines.append(f"运行状态: {_translate_status(manifest.get('status', 'unknown'))} exit_code={manifest.get('exit_code', 'unknown')}")
    lines.append(f"事件数量: {len(events)}")
    lines.append("")
    for event in events:
        risk = event.get("risk") or {}
        output = event.get("output") or {}
        changes = event.get("file_changes") or []
        lines.append(f"[{event.get('id')}] {_event_title(event)}")
        lines.append(f"  时间: {event.get('ts')} cwd: {event.get('cwd')}")
        lines.append(f"  风险: {risk.get('level', 'low')} 规则={risk.get('policy_rule')} 动作={risk.get('action')}")
        if risk.get("reasons"):
            lines.append(f"  原因: {'; '.join(_translate_reason(str(r)) for r in (risk.get('reasons') or []))}")
        status = output.get("status")
        if status:
            rc = output.get("returncode")
            lines.append(f"  输出: 状态={_translate_status(status)}" + (f" returncode={rc}" if rc is not None else ""))
            if event.get("type") == "file.read":
                lines.append(f"  读取字节: {output.get('bytes_read', 0)} 文件大小={output.get('file_size')}")
        if changes:
            summary: dict[str, int] = {}
            for change in changes:
                change_type = _translate_change_type(change.get("change_type", "changed"))
                summary[change_type] = summary.get(change_type, 0) + 1
            lines.append(f"  文件变更: {summary}")
            for change in changes[:5]:
                lines.append(f"    - {_translate_change_type(change.get('change_type'))}: {change.get('path')}")
            if len(changes) > 5:
                lines.append(f"    ... 还有 {len(changes) - 5} 项")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
