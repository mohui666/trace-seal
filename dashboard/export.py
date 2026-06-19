from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from minimizer.explain import find_first_harmful_event
from policy.rules import RISK_ORDER, load_policy, policy_source, suggest_policy_for_event
from recorder.git_state import summarize_git_states
from recorder.http_cassette import read_http_cassette
from replay.renderer import load_events

RUN_ID_RE = re.compile(r"^run_[A-Za-z0-9_.-]+$")

ERROR_EXIT_CODES = {
    "RUN_NOT_FOUND": 2,
    "INVALID_RUN_ID": 3,
    "INVALID_JSON": 4,
    "INTERNAL_ERROR": 1,
}


@dataclass
class DashboardDataError(Exception):
    code: str
    message: str
    status: int = 1
    details: dict[str, Any] | None = None

    def to_response(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": False,
            "error": {
                "code": self.code,
                "message": self.message,
            },
        }
        if self.details:
            payload["error"]["details"] = self.details
        return payload


def error_response(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return DashboardDataError(code, message, ERROR_EXIT_CODES.get(code, 1), details).to_response()


def _load_json_file(path: Path, *, default: dict[str, Any] | None = None, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise DashboardDataError("RUN_NOT_FOUND", f"required file not found: {path.name}", ERROR_EXIT_CODES["RUN_NOT_FOUND"])
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DashboardDataError(
            "INVALID_JSON",
            f"invalid JSON in {path.name}: {exc.msg}",
            ERROR_EXIT_CODES["INVALID_JSON"],
            {"path": path.name, "line": exc.lineno, "column": exc.colno},
        ) from exc


def _load_manifest(run_dir: Path) -> dict[str, Any]:
    return _load_json_file(run_dir / "manifest.json")


def _load_events_safe(run_dir: Path) -> list[dict[str, Any]]:
    try:
        return load_events(run_dir)
    except json.JSONDecodeError as exc:
        raise DashboardDataError(
            "INVALID_JSON",
            f"invalid JSON in events.jsonl: {exc.msg}",
            ERROR_EXIT_CODES["INVALID_JSON"],
            {"path": "events.jsonl", "line": exc.lineno, "column": exc.colno},
        ) from exc


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


def _event_operation(event: dict[str, Any]) -> str:
    typ = event.get("type")
    inp = event.get("input") or {}
    if typ == "shell":
        return str(inp.get("command", ""))
    if typ in {"file.read", "file.write", "file.delete"}:
        return str(inp.get("path", ""))
    if typ in {"http", "network.http"}:
        return f"{inp.get('method', 'GET')} {inp.get('url', '')}"
    return str(event.get("operation", ""))


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    git_operation = (event.get("input") or {}).get("git_operation") or (event.get("risk") or {}).get("git_operation")
    if "operation" not in event or (git_operation is not None and "git_operation" not in event):
        event = dict(event)
        event.setdefault("operation", _event_operation(event))
        if git_operation is not None:
            event["git_operation"] = git_operation
    return event


def _git_state_payload(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    manifest_git = manifest.get("git") if isinstance(manifest.get("git"), dict) else {}
    before = _load_json_file(run_dir / "git_state_before.json", default=manifest_git.get("before") or {})
    after = _load_json_file(run_dir / "git_state_after.json", default=manifest_git.get("after") or {})
    summary = manifest_git.get("summary")
    if not isinstance(summary, dict):
        summary = summarize_git_states(before, after)
    return {"before": before, "after": after, "summary": summary}


def _http_cassette_payload(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    raw_summary = manifest.get("http_cassette") if isinstance(manifest.get("http_cassette"), dict) else {}
    summary = {
        "present": bool(raw_summary.get("present")),
        "entry_count": int(raw_summary.get("entry_count") or 0),
        "high_risk_count": int(raw_summary.get("high_risk_count") or 0),
        "external_host_count": int(raw_summary.get("external_host_count") or 0),
        "redacted": raw_summary.get("redacted") is not False,
    }
    entries, read_error = read_http_cassette(run_dir / "http_cassette.jsonl", limit=50)
    if read_error:
        summary["error"] = read_error
    elif raw_summary.get("error"):
        summary["error"] = str(raw_summary["error"])
    return {"summary": summary, "entries": entries}


def export_dashboard_data(run_dir: str | Path) -> dict[str, Any]:
    """Return a compact JSON-ready summary for Electron/React dashboard reads."""

    run_dir = Path(run_dir)
    manifest = _load_manifest(run_dir)
    events = [_normalize_event(event) for event in _load_events_safe(run_dir)]
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
        "git_state": _git_state_payload(run_dir, manifest),
        "http_cassette": _http_cassette_payload(run_dir, manifest),
        "policy_source": manifest.get("policy_source"),
    }


def export_dashboard_json(run_dir: str | Path) -> str:
    return json.dumps(export_dashboard_data(run_dir), indent=2, ensure_ascii=False, default=str) + "\n"


def _runs_dir(repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    return root.resolve() / "runs"


def _is_latest_selector(selector: str) -> bool:
    normalized = selector.replace("\\", "/").strip()
    return normalized in {"latest", "runs/latest"}


def validate_run_id(run_id: str) -> str:
    value = str(run_id).strip()
    if not value:
        raise DashboardDataError("INVALID_RUN_ID", "runId is empty", ERROR_EXIT_CODES["INVALID_RUN_ID"])
    if value.replace("\\", "/") != value or "/" in value:
        raise DashboardDataError("INVALID_RUN_ID", "runId must not contain path separators", ERROR_EXIT_CODES["INVALID_RUN_ID"])
    if Path(value).is_absolute() or ".." in value:
        raise DashboardDataError("INVALID_RUN_ID", "runId must not be absolute or contain '..'", ERROR_EXIT_CODES["INVALID_RUN_ID"])
    if not RUN_ID_RE.fullmatch(value):
        raise DashboardDataError("INVALID_RUN_ID", "runId must match run_<safe characters>", ERROR_EXIT_CODES["INVALID_RUN_ID"], {"run_id": value})
    return value


def _read_latest_run_id(runs_dir: Path) -> str:
    latest = runs_dir / "latest"
    if not latest.exists() or latest.is_dir():
        latest_txt = runs_dir / "latest.txt"
        if latest_txt.exists() and latest_txt.is_file():
            latest = latest_txt
    if not latest.exists() or not latest.is_file():
        raise DashboardDataError("RUN_NOT_FOUND", "latest run pointer does not exist", ERROR_EXIT_CODES["RUN_NOT_FOUND"])
    run_id = latest.read_text(encoding="utf-8").strip()
    return validate_run_id(run_id)


def resolve_dashboard_run_dir(selector: str = "latest", repo_root: str | Path | None = None) -> Path:
    runs_dir = _runs_dir(repo_root)
    if _is_latest_selector(selector):
        run_id = _read_latest_run_id(runs_dir)
    else:
        run_id = validate_run_id(selector)
    run_dir = (runs_dir / run_id).resolve()
    runs_dir_resolved = runs_dir.resolve()
    try:
        run_dir.relative_to(runs_dir_resolved)
    except ValueError as exc:
        raise DashboardDataError("INVALID_RUN_ID", "runId resolved outside runs directory", ERROR_EXIT_CODES["INVALID_RUN_ID"]) from exc
    if not run_dir.exists() or not run_dir.is_dir():
        raise DashboardDataError("RUN_NOT_FOUND", f"run not found: {run_id}", ERROR_EXIT_CODES["RUN_NOT_FOUND"], {"run_id": run_id})
    return run_dir


def export_run(selector: str = "latest", repo_root: str | Path | None = None) -> dict[str, Any]:
    return export_dashboard_data(resolve_dashboard_run_dir(selector, repo_root))


def _parse_ts(value: Any) -> tuple[int, str]:
    if isinstance(value, str) and value:
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized).astimezone(timezone.utc)
            return (1, parsed.isoformat())
        except ValueError:
            return (1, value)
    return (0, "")


def _safe_run_summary(run_dir: Path) -> dict[str, Any]:
    try:
        manifest = _load_manifest(run_dir)
        events = _load_events_safe(run_dir)
        first_harmful = find_first_harmful_event(events)
        return {
            "run_id": manifest.get("run_id", run_dir.name),
            "command": manifest.get("command_display", manifest.get("command", "")),
            "started_at": manifest.get("started_at"),
            "finished_at": manifest.get("completed_at"),
            "status": manifest.get("status", "failed"),
            "exit_code": manifest.get("exit_code"),
            "event_count": len(events),
            "high_risk_count": sum(1 for event in events if _risk_score(event) >= RISK_ORDER["high"]),
            "first_harmful_event_id": first_harmful.get("id") if first_harmful else None,
            "_sort_key": _parse_ts(manifest.get("started_at") or manifest.get("completed_at")),
        }
    except DashboardDataError as exc:
        return {
            "run_id": run_dir.name,
            "command": "",
            "started_at": None,
            "finished_at": None,
            "status": "failed",
            "exit_code": None,
            "event_count": 0,
            "high_risk_count": 0,
            "first_harmful_event_id": None,
            "error": {"code": exc.code, "message": exc.message},
            "_sort_key": (0, datetime.fromtimestamp(run_dir.stat().st_mtime, tz=timezone.utc).isoformat() if run_dir.exists() else ""),
        }


def list_runs(repo_root: str | Path | None = None) -> list[dict[str, Any]]:
    runs_dir = _runs_dir(repo_root)
    if not runs_dir.exists():
        return []
    summaries: list[dict[str, Any]] = []
    for child in runs_dir.iterdir():
        if not child.is_dir() or not RUN_ID_RE.fullmatch(child.name):
            continue
        summaries.append(_safe_run_summary(child))
    summaries.sort(key=lambda item: item.pop("_sort_key", (0, 0.0)), reverse=True)
    return summaries


def export_policy_rules(workspace: str | Path | None = None) -> list[dict[str, Any]]:
    rules = load_policy(workspace).get("rules", [])
    normalized: list[dict[str, Any]] = []
    for rule in rules:
        match = rule.get("match") if isinstance(rule.get("match"), dict) else None
        normalized.append(
            {
                "rule_id": rule.get("rule_id") or rule.get("id"),
                "event_type": rule.get("event_type") or rule.get("type") or (match or {}).get("event_type"),
                "pattern": rule.get("pattern") or match,
                "risk_level": rule.get("risk_level") or rule.get("risk"),
                "action": rule.get("action"),
                "description": rule.get("description") or rule.get("reason"),
                "reason": rule.get("reason"),
                "suggested_policy": rule.get("suggested_policy"),
            }
        )
    return normalized


def handle_dashboard_cli(argv: list[str], repo_root: str | Path | None = None) -> dict[str, Any]:
    if not argv:
        return export_run("latest", repo_root)
    command = argv[0]
    if command in {"latest", "runs/latest"}:
        if len(argv) != 1:
            raise DashboardDataError("INVALID_RUN_ID", "latest does not accept extra arguments", ERROR_EXIT_CODES["INVALID_RUN_ID"])
        return export_run(command, repo_root)
    if command in {"list", "runs", "list-runs"}:
        if len(argv) != 1:
            raise DashboardDataError("INVALID_RUN_ID", "list does not accept extra arguments", ERROR_EXIT_CODES["INVALID_RUN_ID"])
        return {"schema_version": 1, "runs": list_runs(repo_root)}
    if command == "policy":
        if len(argv) != 1:
            raise DashboardDataError("INVALID_RUN_ID", "policy does not accept extra arguments", ERROR_EXIT_CODES["INVALID_RUN_ID"])
        return {"schema_version": 1, "policy_source": policy_source(repo_root), "rules": export_policy_rules(repo_root)}
    if command == "run":
        if len(argv) != 2:
            raise DashboardDataError("INVALID_RUN_ID", "usage: dashboard-data run <run_id>", ERROR_EXIT_CODES["INVALID_RUN_ID"])
        return export_run(argv[1], repo_root)
    if len(argv) == 1:
        return export_run(command, repo_root)
    raise DashboardDataError("INVALID_RUN_ID", "unsupported dashboard-data arguments", ERROR_EXIT_CODES["INVALID_RUN_ID"], {"args": argv})


def json_dumps(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n"
