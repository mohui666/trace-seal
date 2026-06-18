from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from policy.rules import RISK_ORDER, suggest_policy_for_event
from replay.renderer import load_events


def _risk_score(event: dict[str, Any]) -> int:
    risk = event.get("risk") or {}
    score = RISK_ORDER.get(risk.get("level", "low"), 0)
    rule = risk.get("policy_rule")
    if rule in {"dangerous_delete", "env_write", "git_push", "suspicious_http_post"}:
        score = max(score, 2)
    for change in event.get("file_changes") or []:
        path = str(change.get("path", "")).replace("\\", "/")
        if change.get("change_type") == "deleted" and (path == "data" or path.startswith("data/")):
            score = max(score, 3)
        if path == ".env" or path.startswith(".env."):
            score = max(score, 2)
    return score


def find_first_harmful_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in events:
        if _risk_score(event) >= 2:
            return event
    return None


def _event_headline(event: dict[str, Any]) -> str:
    typ = event.get("type")
    inp = event.get("input") or {}
    if typ == "shell":
        source = f" ({event.get('operation')})" if event.get("operation") == "os.system" else ""
        return f"Shell 命令{source}: {inp.get('command', '')}"
    if typ == "file.write":
        return f"文件写入: {inp.get('path', '')}"
    if typ == "file.delete":
        return f"文件删除: {inp.get('path', '')}"
    if typ == "http":
        return f"HTTP 请求: {inp.get('method', 'GET')} {inp.get('url', '')}"
    return f"{typ}: {event.get('operation', '')}"


def _translate_reason(reason: str) -> str:
    if reason.startswith("recursive force delete requested: "):
        return reason.replace("recursive force delete requested: ", "请求递归强制删除: ", 1)
    if reason == "deleted protected path: data/":
        return "删除了受保护路径: data/"
    if reason.startswith("write to environment/config file: "):
        return reason.replace("write to environment/config file: ", "写入环境/配置文件: ", 1)
    if reason.startswith("sensitive environment file modified: "):
        return reason.replace("sensitive environment file modified: ", "敏感环境配置文件被修改: ", 1)
    if reason == "modified protected environment file":
        return "修改了受保护的环境配置文件"
    if reason == "git push publishes repository state":
        return "git push 会发布仓库状态"
    if reason == "remote git push requested":
        return "请求远程 git push"
    if reason.startswith("suspicious outbound HTTP POST: "):
        return reason.replace("suspicious outbound HTTP POST: ", "可疑的出站 HTTP POST: ", 1)
    if reason.startswith("outbound HTTP request: "):
        return reason.replace("outbound HTTP request: ", "出站 HTTP 请求: ", 1)
    if reason.startswith("matched policy rule: "):
        return reason.replace("matched policy rule: ", "命中策略规则: ", 1)
    if reason.startswith("process exited with code ") and reason.endswith(" after this event"):
        code = reason.removeprefix("process exited with code ").removesuffix(" after this event")
        return f"该事件之后进程退出码为 {code}"
    if reason == "high-risk event according to TraceSeal policy":
        return "TraceSeal 策略判定为高风险事件"
    return reason


def _reasons(event: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    risk = event.get("risk") or {}
    reasons.extend(risk.get("reasons") or [])
    deleted = [c.get("path") for c in event.get("file_changes") or [] if c.get("change_type") == "deleted"]
    if any(str(p) == "data" or str(p).startswith("data/") for p in deleted):
        reasons.append("deleted protected path: data/")
    env_changes = [c.get("path") for c in event.get("file_changes") or [] if str(c.get("path", "")).startswith(".env")]
    if env_changes:
        reasons.append("modified protected environment file")
    if risk.get("policy_rule"):
        reasons.append(f"matched policy rule: {risk.get('policy_rule')}")
    if manifest.get("exit_code") not in {None, 0}:
        reasons.append(f"process exited with code {manifest.get('exit_code')} after this event")
    deduped: list[str] = []
    for item in reasons:
        if item and item not in deduped:
            deduped.append(item)
    return deduped or ["high-risk event according to TraceSeal policy"]


def _affected_files(event: dict[str, Any]) -> list[str]:
    return [str(c.get("path")) for c in event.get("file_changes") or [] if c.get("path")][:20]


def explain_run(run_dir: str | Path) -> str:
    run_dir = Path(run_dir)
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    events = load_events(run_dir)
    event = find_first_harmful_event(events)
    if event is None:
        return "未发现有害工具调用。\n"

    lines: list[str] = []
    lines.append("首次有害工具调用:")
    lines.append(f"[{event.get('id')}] {_event_headline(event)}")
    lines.append("")
    lines.append("原因:")
    for reason in _reasons(event, manifest):
        lines.append(f"- {_translate_reason(reason)}")
    affected = _affected_files(event)
    if affected:
        lines.append("")
        lines.append("影响文件:")
        for path in affected:
            lines.append(f"- {path}")
    lines.append("")
    lines.append("建议策略:")
    lines.append(suggest_policy_for_event(event))
    lines.append("")
    return "\n".join(lines)
