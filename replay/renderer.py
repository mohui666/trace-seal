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
        return f"shell: {inp.get('command', '')}"
    if typ in {"file.write", "file.delete"}:
        return f"{typ}: {inp.get('path', '')}"
    if typ == "http":
        return f"http: {inp.get('method', 'GET')} {inp.get('url', '')}"
    return f"{typ}: {event.get('operation', '')}"


def replay_run(run_dir: str | Path) -> str:
    run_dir = Path(run_dir)
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    events = load_events(run_dir)

    lines: list[str] = []
    lines.append("TraceSeal transcript replay")
    lines.append(f"Run: {manifest.get('run_id', run_dir.name)}")
    lines.append(f"Command: {manifest.get('command_display', manifest.get('command'))}")
    lines.append(f"Status: {manifest.get('status', 'unknown')} exit_code={manifest.get('exit_code', 'unknown')}")
    lines.append(f"Events: {len(events)}")
    lines.append("")
    for event in events:
        risk = event.get("risk") or {}
        output = event.get("output") or {}
        changes = event.get("file_changes") or []
        lines.append(f"[{event.get('id')}] {_event_title(event)}")
        lines.append(f"  time: {event.get('ts')} cwd: {event.get('cwd')}")
        lines.append(f"  risk: {risk.get('level', 'low')} rule={risk.get('policy_rule')} action={risk.get('action')}")
        if risk.get("reasons"):
            lines.append(f"  reason: {'; '.join(risk.get('reasons') or [])}")
        status = output.get("status")
        if status:
            rc = output.get("returncode")
            lines.append(f"  output: status={status}" + (f" returncode={rc}" if rc is not None else ""))
        if changes:
            summary: dict[str, int] = {}
            for change in changes:
                change_type = change.get("change_type", "changed")
                summary[change_type] = summary.get(change_type, 0) + 1
            lines.append(f"  file_changes: {summary}")
            for change in changes[:5]:
                lines.append(f"    - {change.get('change_type')}: {change.get('path')}")
            if len(changes) > 5:
                lines.append(f"    ... {len(changes) - 5} more")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
