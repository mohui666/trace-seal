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
    if rule in {"dangerous_delete", "env_write", "git_push"}:
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
        return f"shell: {inp.get('command', '')}"
    if typ in {"file.write", "file.delete"}:
        return f"{typ}: {inp.get('path', '')}"
    if typ == "http":
        return f"http: {inp.get('method', 'GET')} {inp.get('url', '')}"
    return f"{typ}: {event.get('operation', '')}"


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
        return "No harmful tool call found.\n"

    lines: list[str] = []
    lines.append("First harmful tool call:")
    lines.append(f"[{event.get('id')}] {_event_headline(event)}")
    lines.append("")
    lines.append("Reason:")
    for reason in _reasons(event, manifest):
        lines.append(f"- {reason}")
    affected = _affected_files(event)
    if affected:
        lines.append("")
        lines.append("Affected files:")
        for path in affected:
            lines.append(f"- {path}")
    lines.append("")
    lines.append("Suggested policy:")
    lines.append(suggest_policy_for_event(event))
    lines.append("")
    return "\n".join(lines)
