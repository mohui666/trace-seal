from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from policy.dsl import first_matching_rule, validate_policy
from policy.yaml_loader import load_policy_with_source
from traceseal.guard_import import (
    GuardImportError,
    load_imported_guard_events,
    maybe_find_guard_events,
)
from traceseal.guard_schema import (
    GuardEventError,
    validate_guard_event,
    validate_guard_health_event,
    validate_guard_process_spawn_event,
)

GUARD_POLICY_ARTIFACT_NAME = "guard-policy-decisions.json"
GUARD_POLICY_ARTIFACT_TYPE = "guard.policy.decisions.v1"


class GuardPolicyError(ValueError):
    """Raised when Guard policy dry-run evaluation cannot complete safely."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _validate_guard_event_for_policy(event: Mapping[str, Any]) -> Mapping[str, Any]:
    event_type = event.get("event_type")
    try:
        if event_type == "guard.health":
            return validate_guard_health_event(event)
        if event_type == "process.spawn":
            return validate_guard_process_spawn_event(event)
        return validate_guard_event(event)
    except GuardEventError as error:
        raise GuardPolicyError(f"Guard event failed validation: {error}") from error


def _command_text(event: Mapping[str, Any]) -> str:
    process = event.get("process")
    if not isinstance(process, Mapping):
        return ""
    command_line = process.get("command_line")
    if isinstance(command_line, list):
        return " ".join(str(item) for item in command_line)
    if isinstance(command_line, str):
        return command_line
    process_name = process.get("process_name")
    return str(process_name) if process_name is not None else ""


def _guard_policy_context(event: Mapping[str, Any]) -> dict[str, Any]:
    process = event.get("process") if isinstance(event.get("process"), Mapping) else {}
    redaction = event.get("redaction") if isinstance(event.get("redaction"), Mapping) else {}
    metadata = event.get("metadata") if isinstance(event.get("metadata"), Mapping) else {}
    command = _command_text(event)
    return {
        "event_type": event.get("event_type"),
        "command": command,
        "path": process.get("cwd") or event.get("workspace") or "",
        "risk_level": event.get("risk_level"),
        "sensitive": bool(redaction.get("fields"))
        or redaction.get("status") in {"redacted", "partial", "failed"},
        "dry_run": metadata.get("dry_run") is True,
        "executed": metadata.get("executed") is True,
    }


def evaluate_guard_event_policy(
    event: Mapping[str, Any], policy: Mapping[str, Any]
) -> dict[str, Any]:
    """Evaluate one Guard event against existing policy DSL as dry-run metadata."""

    event = _validate_guard_event_for_policy(event)
    policy_data = dict(policy)
    context = _guard_policy_context(event)
    matched = first_matching_rule(policy_data, context)
    if matched is None:
        decision = "observe"
        matched_rule = None
        reason = "no matching Guard policy rule"
        risk_level = event.get("risk_level")
    else:
        decision = str(matched["action"])
        matched_rule = str(matched["id"])
        reason = str(matched.get("reason") or f"matched Guard policy rule: {matched_rule}")
        risk_level = str(matched.get("risk_level") or event.get("risk_level"))

    return {
        "event_id": event.get("event_id"),
        "event_type": event.get("event_type"),
        "decision": decision,
        "matched_rule": matched_rule,
        "rule_id": matched_rule,
        "reason": reason,
        "risk_level": risk_level,
        "dry_run": True,
        "enforcement_applied": False,
        "context": {
            "event_type": context["event_type"],
            "command": context["command"],
            "path": context["path"],
            "risk_level": context["risk_level"],
            "sensitive": context["sensitive"],
            "dry_run": context["dry_run"],
            "executed": context["executed"],
        },
    }


def evaluate_guard_events_policy(
    events: list[Mapping[str, Any]], policy: Mapping[str, Any]
) -> list[dict[str, Any]]:
    return [evaluate_guard_event_policy(event, policy) for event in events]


def _load_explicit_policy(policy_path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = Path(policy_path).resolve()
    if not path.exists():
        raise GuardPolicyError(f"policy file does not exist: {path}")
    if not path.is_file():
        raise GuardPolicyError(f"policy path is not a file: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        policy = validate_policy(raw)
    except Exception as error:
        raise GuardPolicyError(f"cannot load policy file {path}: {type(error).__name__}: {error}") from error
    return policy, {"type": "yaml", "path": str(path), "error": None}


def _load_policy(
    *, run_dir: Path, policy_path: str | Path | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    if policy_path is not None:
        return _load_explicit_policy(policy_path)
    try:
        policy, source = load_policy_with_source(run_dir)
    except Exception as error:
        raise GuardPolicyError(f"cannot load policy for run {run_dir}: {error}") from error
    return policy, source


def _default_policy_summary(
    *,
    artifact_path: str | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "available": False,
        "artifact_path": artifact_path,
        "artifact_type": GUARD_POLICY_ARTIFACT_TYPE,
        "generated_at": None,
        "policy_source": None,
        "dry_run": True,
        "event_count": 0,
        "evaluated_event_count": 0,
        "decision_counts": {},
        "enforcement_applied": False,
        "error": error,
    }


def _summary_from_decisions(
    decisions: list[dict[str, Any]],
    *,
    policy_source: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "available": True,
        "artifact_path": GUARD_POLICY_ARTIFACT_NAME,
        "artifact_type": GUARD_POLICY_ARTIFACT_TYPE,
        "generated_at": generated_at,
        "policy_source": dict(policy_source),
        "dry_run": True,
        "event_count": len(decisions),
        "evaluated_event_count": len(decisions),
        "decision_counts": dict(Counter(str(item.get("decision")) for item in decisions)),
        "enforcement_applied": False,
        "error": None,
    }


def _artifact_payload(
    decisions: list[dict[str, Any]], *, policy_source: Mapping[str, Any]
) -> dict[str, Any]:
    generated_at = _utc_now()
    summary = _summary_from_decisions(
        decisions,
        policy_source=policy_source,
        generated_at=generated_at,
    )
    return {
        **summary,
        "decisions": decisions,
    }


def apply_guard_policy_dry_run(
    run_dir: str | Path, policy_path: str | Path | None = None
) -> dict[str, Any]:
    """Evaluate imported Guard events and persist non-enforcing decision metadata."""

    run_path = Path(run_dir).resolve()
    if not run_path.exists():
        raise GuardPolicyError(f"run directory does not exist: {run_path}")
    if not run_path.is_dir():
        raise GuardPolicyError(f"run path is not a directory: {run_path}")

    if maybe_find_guard_events(run_path) is None:
        return _default_policy_summary()
    try:
        events = load_imported_guard_events(run_path)
    except GuardImportError as error:
        raise GuardPolicyError(f"cannot load imported Guard events: {error}") from error

    policy, source = _load_policy(run_dir=run_path, policy_path=policy_path)
    decisions = evaluate_guard_events_policy(events, policy)
    payload = _artifact_payload(decisions, policy_source=source)
    _write_atomic(
        run_path / GUARD_POLICY_ARTIFACT_NAME,
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
    )
    return _summary_from_decisions(
        decisions,
        policy_source=source,
        generated_at=str(payload["generated_at"]),
    )


def _policy_artifact_path(run_dir: str | Path) -> Path:
    return Path(run_dir).resolve() / GUARD_POLICY_ARTIFACT_NAME


def load_guard_policy_decisions(run_dir: str | Path) -> dict[str, Any]:
    """Load the optional Guard policy dry-run artifact."""

    artifact = _policy_artifact_path(run_dir)
    if not artifact.exists():
        return _default_policy_summary()
    try:
        payload = json.loads(artifact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GuardPolicyError(f"cannot read Guard policy artifact {artifact}: {error}") from error
    if not isinstance(payload, dict):
        raise GuardPolicyError(f"Guard policy artifact must be a JSON object: {artifact}")
    if payload.get("artifact_type") != GUARD_POLICY_ARTIFACT_TYPE:
        raise GuardPolicyError(
            f"Guard policy artifact_type must be {GUARD_POLICY_ARTIFACT_TYPE!r}"
        )
    decisions = payload.get("decisions")
    if not isinstance(decisions, list) or any(not isinstance(item, dict) for item in decisions):
        raise GuardPolicyError("Guard policy decisions must be a list of objects")
    if payload.get("dry_run") is not True:
        raise GuardPolicyError("Guard policy artifact must declare dry_run=true")
    if payload.get("enforcement_applied") is not False:
        raise GuardPolicyError("Guard policy artifact must declare enforcement_applied=false")
    return payload


def get_guard_policy_summary(run_dir: str | Path) -> dict[str, Any]:
    """Return dashboard-ready Guard policy dry-run summary without raising for absence."""

    artifact = _policy_artifact_path(run_dir)
    try:
        payload = load_guard_policy_decisions(run_dir)
    except GuardPolicyError as error:
        return _default_policy_summary(
            artifact_path=artifact.name,
            error={"code": "INVALID_GUARD_POLICY_DECISIONS", "message": str(error)},
        )
    if not payload.get("available"):
        return payload
    return {
        "available": True,
        "artifact_path": payload.get("artifact_path"),
        "artifact_type": payload.get("artifact_type"),
        "generated_at": payload.get("generated_at"),
        "policy_source": payload.get("policy_source"),
        "dry_run": payload.get("dry_run") is True,
        "event_count": int(payload.get("event_count") or 0),
        "evaluated_event_count": int(payload.get("evaluated_event_count") or 0),
        "decision_counts": dict(payload.get("decision_counts") or {}),
        "enforcement_applied": payload.get("enforcement_applied") is True,
        "error": None,
    }


def decisions_by_event_id(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in decisions:
        if not isinstance(item, Mapping):
            continue
        event_id = item.get("event_id")
        if isinstance(event_id, str) and event_id:
            result[event_id] = {
                "decision": item.get("decision"),
                "matched_rule": item.get("matched_rule"),
                "rule_id": item.get("rule_id"),
                "reason": item.get("reason"),
                "risk_level": item.get("risk_level"),
                "dry_run": item.get("dry_run") is True,
                "enforcement_applied": item.get("enforcement_applied") is True,
            }
    return result


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m traceseal.guard_policy",
        description="Evaluate imported Guard events against policy.yaml as dry-run metadata.",
    )
    parser.add_argument("--run", required=True, help="TraceSeal run directory")
    parser.add_argument("--policy", help="Optional policy.yaml path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        summary = apply_guard_policy_dry_run(args.run, args.policy)
    except GuardPolicyError as error:
        print(f"guard policy dry-run failed: {error}", file=sys.stderr)
        return 2
    print(
        "guard policy dry-run evaluated "
        f"{summary.get('evaluated_event_count', 0)} Guard event(s); "
        f"decision_counts={summary.get('decision_counts', {})}; "
        f"enforcement_applied={summary.get('enforcement_applied')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
