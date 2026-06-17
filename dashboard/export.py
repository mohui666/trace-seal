from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minimizer.explain import find_first_harmful_event
from policy.rules import RISK_ORDER, suggest_policy_for_event
from replay.renderer import load_events


def _load_manifest(run_dir: Path) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _risk_score(event: dict[str, Any]) -> int:
    risk = event.get("risk") or {}
    return RISK_ORDER.get(str(risk.get("level", "low")), 0)


def _affected_files(events: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for event in events:
        for change in event.get("file_changes") or []:
            path = change.get("path")
            if path and path not in seen:
                seen.add(str(path))
                paths.append(str(path))
    return paths


def export_dashboard_data(run_dir: str | Path) -> dict[str, Any]:
    """Return a compact JSON-ready summary for Electron/React dashboard reads."""

    run_dir = Path(run_dir)
    manifest = _load_manifest(run_dir)
    events = load_events(run_dir)
    first_harmful = find_first_harmful_event(events)

    return {
        "schema_version": 1,
        "run_id": manifest.get("run_id", run_dir.name),
        "command": manifest.get("command_display", manifest.get("command")),
        "started_at": manifest.get("started_at"),
        "finished_at": manifest.get("completed_at"),
        "status": manifest.get("status"),
        "exit_code": manifest.get("exit_code"),
        "event_count": len(events),
        "high_risk_count": sum(1 for event in events if _risk_score(event) >= RISK_ORDER["high"]),
        "first_harmful_event": first_harmful,
        "events": events,
        "affected_files": _affected_files(events),
        "suggested_policy": suggest_policy_for_event(first_harmful) if first_harmful else None,
    }


def export_dashboard_json(run_dir: str | Path) -> str:
    return json.dumps(export_dashboard_data(run_dir), indent=2, ensure_ascii=False, default=str) + "\n"
