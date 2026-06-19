from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

STAGE_LABELS = {
    "sensitive_read": "sensitive file read",
    "http_exfiltration_attempt": "HTTP exfiltration attempt",
    "configuration_corruption": "configuration corruption",
    "destructive_shell": "destructive shell command",
    "dangerous_git_push": "dangerous Git push",
}

DANGEROUS_GIT_TYPES = {"force", "force_with_lease", "mirror", "delete_remote_branch", "force_refspec", "all", "tags"}
HTTP_RULES = {
    "suspicious_http_post",
    "sensitive_http_request",
    "domain_denylist_match",
    "domain_warnlist_match",
    "domain_unknown_external",
    "cascade_http_exfiltration_attempt",
}


def _risk(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("risk")
    return value if isinstance(value, dict) else {}


def _rule_id(event: dict[str, Any]) -> str | None:
    risk = _risk(event)
    value = risk.get("rule_id") or risk.get("policy_rule")
    return str(value) if value else None


def _path(event: dict[str, Any]) -> str:
    return str((event.get("input") or {}).get("path") or "").replace("\\", "/").lower()


def _is_sensitive_path(path: str) -> bool:
    name = Path(path).name.lower()
    markers = (".env", "secret", "credential", "token", "password", ".pem", ".key")
    return any(marker in name for marker in markers) or "/.ssh/" in f"/{path.strip('/')}/"


def _is_protected_config(path: str) -> bool:
    name = Path(path).name.lower()
    return name in {".env", "config.json", "settings.json", "settings.yaml", "settings.yml"} or name.startswith(".env.")


def _git_operation(event: dict[str, Any]) -> dict[str, Any]:
    risk = _risk(event)
    value = (event.get("input") or {}).get("git_operation") or risk.get("git_operation")
    return value if isinstance(value, dict) else {}


def _stage_for_event(event: dict[str, Any]) -> str | None:
    event_type = str(event.get("type") or "")
    rule_id = _rule_id(event)
    risk = _risk(event)
    matched_rules = {str(item) for item in risk.get("matched_rules") or [] if item}

    if event_type == "file.read" and (rule_id in {"sensitive_file_read", "cascade_sensitive_read"} or _is_sensitive_path(_path(event))):
        return "sensitive_read"

    if event_type in {"http", "network.http"}:
        domain = (event.get("input") or {}).get("domain_policy") or risk.get("domain_policy")
        domain_decision = domain.get("domain_decision") if isinstance(domain, dict) else None
        if rule_id in HTTP_RULES or matched_rules.intersection(HTTP_RULES) or domain_decision in {"warn", "deny"} or _risk_score(event) >= RISK_ORDER["high"]:
            return "http_exfiltration_attempt"

    if event_type == "file.write" and (rule_id in {"env_write", "cascade_config_corruption"} or _is_protected_config(_path(event))):
        return "configuration_corruption"

    command = str((event.get("input") or {}).get("command") or "").lower()
    if event_type == "shell" and (rule_id in {"dangerous_delete", "cascade_destructive_shell", "deny-dangerous-delete"} or "rm -rf" in command or "rmdir /s /q" in command):
        return "destructive_shell"

    git_type = str(_git_operation(event).get("push_type") or "")
    if event_type == "shell" and (git_type in DANGEROUS_GIT_TYPES or rule_id in {
        "git_force_push",
        "git_force_with_lease",
        "git_mirror_push",
        "git_delete_remote_branch",
        "git_force_refspec_push",
        "git_bulk_push",
        "cascade_dangerous_git_push",
    }):
        return "dangerous_git_push"
    return None


def _parse_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return value


def _ordered_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indexed = list(enumerate(events))

    def key(item: tuple[int, dict[str, Any]]) -> tuple[int, Any, int]:
        index, event = item
        seq = event.get("seq")
        if isinstance(seq, int):
            return (0, seq, index)
        timestamp = _parse_timestamp(event.get("ts"))
        if timestamp:
            return (1, timestamp, index)
        return (2, index, index)

    return [event for _, event in sorted(indexed, key=key)]


def _risk_score(event: dict[str, Any]) -> int:
    risk = _risk(event)
    score = RISK_ORDER.get(str(risk.get("level", "low")), 0)
    if _rule_id(event) in {
        "dangerous_delete",
        "env_write",
        "sensitive_file_read",
        "git_push",
        "suspicious_http_post",
        "cascade_config_corruption",
    }:
        score = max(score, RISK_ORDER["high"])
    for change in event.get("file_changes") or []:
        path = str(change.get("path", "")).replace("\\", "/")
        if change.get("change_type") == "deleted" and (path == "data" or path.startswith("data/")):
            score = max(score, RISK_ORDER["critical"])
        if path == ".env" or path.startswith(".env."):
            score = max(score, RISK_ORDER["high"])
    return score


def find_first_harmful_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in _ordered_events(events):
        if _risk_score(event) >= RISK_ORDER["high"]:
            return event
    return None


def _stage_reason(event: dict[str, Any], stage: str) -> str:
    reasons = _risk(event).get("reasons") or []
    if reasons:
        return str(reasons[0])
    return {
        "sensitive_read": "sensitive file metadata was read",
        "http_exfiltration_attempt": "sensitive or disallowed HTTP request was attempted",
        "configuration_corruption": "protected configuration was modified",
        "destructive_shell": "destructive shell command was attempted",
        "dangerous_git_push": "dangerous Git push was attempted through offline simulation",
    }[stage]


def detect_cascade(events: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = _ordered_events(events)
    first_harmful = find_first_harmful_event(ordered)
    stages: list[dict[str, Any]] = []
    seen_stages: set[str] = set()
    fallback_rules = {
        "sensitive_read": "cascade_sensitive_read",
        "http_exfiltration_attempt": "cascade_http_exfiltration_attempt",
        "configuration_corruption": "cascade_config_corruption",
        "destructive_shell": "cascade_destructive_shell",
        "dangerous_git_push": "cascade_dangerous_git_push",
    }
    for event in ordered:
        stage = _stage_for_event(event)
        if stage is None or stage in seen_stages:
            continue
        seen_stages.add(stage)
        stages.append(
            {
                "stage": stage,
                "event_id": event.get("id"),
                "rule_id": _rule_id(event) or fallback_rules[stage],
                "reason": _stage_reason(event, stage),
            }
        )

    present = len(stages) >= 3
    severity = "critical" if len(stages) >= 4 else "high" if present else None
    labels = [STAGE_LABELS[item["stage"]] for item in stages]
    if present:
        summary = f"Detected a {severity} cascade across {len(stages)} ordered stages: {' -> '.join(labels)}."
    else:
        summary = f"No cascade detected: {len(stages)} of 3 required risk stages observed."
    return {
        "present": present,
        "severity": severity,
        "event_count": len(stages),
        "stages": stages,
        "summary": summary,
        "first_harmful_event_id": first_harmful.get("id") if first_harmful else None,
        "suggested_policy": 'require_approval cascade "3+ ordered risk stages"' if present else None,
        "rule_id": "cascade_failure_detected" if present else None,
    }


def render_cascade_lines(cascade: dict[str, Any], *, prefix: str = "") -> list[str]:
    if not cascade.get("present"):
        return [f"{prefix}级联事故: 未检测到"]
    lines = [
        f"{prefix}级联事故: 已检测到 severity={cascade.get('severity')} events={cascade.get('event_count')}",
        f"{prefix}首次有害事件: {cascade.get('first_harmful_event_id')}",
    ]
    for item in cascade.get("stages") or []:
        lines.append(
            f"{prefix}- {item.get('stage')}: event={item.get('event_id')} rule={item.get('rule_id')} reason={item.get('reason')}"
        )
    lines.append(f"{prefix}摘要: {cascade.get('summary')}")
    return lines
