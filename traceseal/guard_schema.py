from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "guard.event.v1"
RISK_LEVELS = frozenset({"info", "low", "medium", "high", "critical", "unknown"})
POLICY_DECISIONS = frozenset({"observe", "allow", "warn", "deny", "require_approval", "unknown"})
REDACTION_STATUSES = frozenset({"not_applicable", "redacted", "partial", "failed", "unknown"})

REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "event_id",
        "timestamp",
        "source",
        "event_type",
        "risk_level",
        "policy",
        "redaction",
        "guard",
        "metadata",
    }
)


class GuardEventError(ValueError):
    """Base error for Guard event parsing and validation."""


class GuardEventParseError(GuardEventError):
    """Raised when a Guard JSONL record cannot be parsed."""


class GuardEventValidationError(GuardEventError):
    """Raised when a parsed Guard event violates guard.event.v1."""


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise GuardEventValidationError(f"{field} must be an object")
    return value


def _string_or_none(value: Any, field: str) -> None:
    if value is not None and not isinstance(value, str):
        raise GuardEventValidationError(f"{field} must be a string or null")


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise GuardEventValidationError(f"{field} must be a non-empty string")
    return value


def _enum(value: Any, field: str, allowed: frozenset[str]) -> str:
    parsed = _non_empty_string(value, field)
    if parsed not in allowed:
        raise GuardEventValidationError(
            f"{field} must be one of {sorted(allowed)}, got {parsed!r}"
        )
    return parsed


def _validate_timestamp(value: Any) -> None:
    timestamp = _non_empty_string(value, "timestamp")
    if not timestamp.endswith("Z"):
        raise GuardEventValidationError("timestamp must be an RFC3339 UTC value ending in Z")
    try:
        parsed = datetime.fromisoformat(f"{timestamp[:-1]}+00:00")
    except ValueError as error:
        raise GuardEventValidationError(f"timestamp is not valid RFC3339: {timestamp!r}") from error
    if parsed.utcoffset() is None:
        raise GuardEventValidationError("timestamp must include a UTC offset")


def validate_guard_event(event: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate the common guard.event.v1 envelope without importing it into a run."""

    event = _mapping(event, "event")
    missing = sorted(REQUIRED_FIELDS.difference(event))
    if missing:
        raise GuardEventValidationError(f"missing required field(s): {', '.join(missing)}")

    if event["schema_version"] != SCHEMA_VERSION:
        raise GuardEventValidationError(
            f"schema_version must be {SCHEMA_VERSION!r}, got {event['schema_version']!r}"
        )
    _non_empty_string(event["event_id"], "event_id")
    _validate_timestamp(event["timestamp"])
    _non_empty_string(event["source"], "source")
    _non_empty_string(event["event_type"], "event_type")
    _enum(event["risk_level"], "risk_level", RISK_LEVELS)

    for field in ("run_id", "workspace"):
        if field in event:
            _string_or_none(event[field], field)

    if "process" in event and event["process"] is not None:
        process_data = _mapping(event["process"], "process")
        for field in ("pid", "parent_pid"):
            value = process_data.get(field)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                raise GuardEventValidationError(f"process.{field} must be a non-negative integer or null")
        for field in ("process_name", "cwd"):
            _string_or_none(process_data.get(field), f"process.{field}")
        command_line = process_data.get("command_line")
        if command_line is not None and not isinstance(command_line, (str, list, Mapping)):
            raise GuardEventValidationError("process.command_line must be a string, array, object, or null")

    policy = _mapping(event["policy"], "policy")
    _enum(policy.get("decision"), "policy.decision", POLICY_DECISIONS)
    _string_or_none(policy.get("rule_id"), "policy.rule_id")
    _string_or_none(policy.get("reason"), "policy.reason")

    redaction = _mapping(event["redaction"], "redaction")
    _enum(redaction.get("status"), "redaction.status", REDACTION_STATUSES)
    fields = redaction.get("fields")
    if not isinstance(fields, list) or any(not isinstance(item, str) for item in fields):
        raise GuardEventValidationError("redaction.fields must be an array of strings")

    guard = _mapping(event["guard"], "guard")
    if guard.get("mode") != "observe":
        raise GuardEventValidationError("guard.mode must be 'observe' for the Stage 4 MVP")
    _non_empty_string(guard.get("status"), "guard.status")
    for field in ("name", "guard_version", "platform"):
        if field in guard:
            _string_or_none(guard[field], f"guard.{field}")

    _mapping(event["metadata"], "metadata")
    return event


def validate_guard_health_event(event: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate the stricter minimum guard.health prototype contract."""

    event = validate_guard_event(event)
    if event["event_type"] != "guard.health":
        raise GuardEventValidationError(
            f"event_type must be 'guard.health', got {event['event_type']!r}"
        )
    if event["source"] != "rust_guard":
        raise GuardEventValidationError("guard.health source must be 'rust_guard'")
    if event["risk_level"] != "info":
        raise GuardEventValidationError("guard.health risk_level must be 'info'")
    if event["policy"]["decision"] != "observe":
        raise GuardEventValidationError("guard.health policy.decision must be 'observe'")
    if event["redaction"]["status"] != "not_applicable" or event["redaction"]["fields"]:
        raise GuardEventValidationError(
            "guard.health redaction must be not_applicable with no fields"
        )

    guard = event["guard"]
    if guard["status"] != "ok":
        raise GuardEventValidationError("guard.health guard.status must be 'ok'")
    _non_empty_string(guard.get("guard_version"), "guard.guard_version")
    _non_empty_string(guard.get("platform"), "guard.platform")
    if "name" in guard and guard["name"] != "traceseal-guard":
        raise GuardEventValidationError("guard.name must be 'traceseal-guard' when present")

    message = event["metadata"].get("message")
    _non_empty_string(message, "metadata.message")
    return event


def load_guard_events(path: str | Path) -> list[dict[str, Any]]:
    """Load JSON objects from a Guard JSONL artifact; a missing artifact means no Guard events."""

    artifact = Path(path)
    if not artifact.exists():
        return []

    events: list[dict[str, Any]] = []
    with artifact.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise GuardEventParseError(
                    f"invalid Guard JSON on line {line_number} of {artifact}: {error.msg}"
                ) from error
            if not isinstance(event, dict):
                raise GuardEventParseError(
                    f"Guard JSONL line {line_number} of {artifact} must contain an object"
                )
            events.append(event)
    return events
