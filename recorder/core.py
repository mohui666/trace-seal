from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_EVENT_LOCK = threading.Lock()
RUN_DIR_ENV = "TRACESEAL_RUN_DIR"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def current_run_dir() -> Path | None:
    value = os.environ.get(RUN_DIR_ENV)
    return Path(value).resolve() if value else None


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def summarize_env(env: dict[str, str] | None = None) -> dict[str, Any]:
    """Return a small non-secret environment summary."""

    env = dict(os.environ if env is None else env)
    summary: dict[str, Any] = {}
    for key in ["USERNAME", "USER", "OS", "SHELL", "COMSPEC", "TRACESEAL_RUN_ID"]:
        if key in env:
            summary[key] = env[key]
    for key in ["PATH", "PYTHONPATH", "VIRTUAL_ENV", "CONDA_PREFIX"]:
        if key in env:
            value = env[key]
            summary[key] = {"length": len(value), "sha256_16": _hash_value(value)}
    return summary


def _next_event_id(events_path: Path) -> tuple[int, str]:
    try:
        with events_path.open("r", encoding="utf-8") as fh:
            seq = sum(1 for _ in fh) + 1
    except FileNotFoundError:
        seq = 1
    return seq, f"evt_{seq:04d}"


def record_event(event: dict[str, Any]) -> dict[str, Any]:
    """Append a single event to events.jsonl and return the written event."""

    run_dir = current_run_dir()
    if run_dir is None:
        return event

    events_path = run_dir / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)

    with _EVENT_LOCK:
        seq, event_id = _next_event_id(events_path)
        enriched = {
            "id": event.get("id", event_id),
            "seq": event.get("seq", seq),
            "ts": event.get("ts", utc_now()),
            "type": event.get("type", "unknown"),
            "operation": event.get("operation"),
            "cwd": event.get("cwd", os.getcwd()),
            "env": event.get("env", summarize_env()),
            "input": event.get("input", {}),
            "output": event.get("output", {}),
            "risk": event.get("risk", {"level": "low", "reasons": [], "policy_rule": None, "action": "allow"}),
            "file_changes": event.get("file_changes", []),
        }
        for key, value in event.items():
            if key not in enriched:
                enriched[key] = value
        with events_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(enriched, ensure_ascii=False, default=str) + "\n")
    return enriched
