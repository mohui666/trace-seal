from __future__ import annotations

import fnmatch
import re
from typing import Any

from .domain import normalized_domain_config

ALLOWED_ACTIONS = {"allow", "warn", "deny", "require_approval"}
ALLOWED_RISK_LEVELS = {"low", "medium", "high", "critical"}
ALLOWED_MATCH_FIELDS = {"event_type", "path", "command", "method", "host", "url", "risk_level", "sensitive", "host_class", "host_allowed"}
ALLOWED_OPERATORS = {"exact", "contains", "contains_any", "glob", "any_of", "regex"}
ALLOWED_MODES = {"warn", "block", "deny", "enforce"}


class PolicyValidationError(ValueError):
    pass


def validate_policy(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise PolicyValidationError("policy document must be a mapping")
    if data.get("version") != 1:
        raise PolicyValidationError("version must be 1")
    mode = str(data.get("mode", "warn")).lower()
    if mode not in ALLOWED_MODES:
        raise PolicyValidationError(f"unsupported mode: {mode}")
    rules = data.get("rules")
    if not isinstance(rules, list):
        raise PolicyValidationError("rules must be a list")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_rule in enumerate(rules):
        if not isinstance(raw_rule, dict):
            raise PolicyValidationError(f"rules[{index}] must be a mapping")
        rule_id = raw_rule.get("id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise PolicyValidationError(f"rules[{index}].id must be a non-empty string")
        if rule_id in seen_ids:
            raise PolicyValidationError(f"duplicate rule id: {rule_id}")
        seen_ids.add(rule_id)
        action = str(raw_rule.get("action", "")).lower()
        risk_level = str(raw_rule.get("risk_level", "")).lower()
        if action not in ALLOWED_ACTIONS:
            raise PolicyValidationError(f"rule {rule_id}: unsupported action: {action}")
        if risk_level not in ALLOWED_RISK_LEVELS:
            raise PolicyValidationError(f"rule {rule_id}: unsupported risk_level: {risk_level}")
        match = raw_rule.get("match")
        if not isinstance(match, dict) or not match:
            raise PolicyValidationError(f"rule {rule_id}: match must be a non-empty mapping")
        unknown_fields = set(match) - ALLOWED_MATCH_FIELDS
        if unknown_fields:
            raise PolicyValidationError(f"rule {rule_id}: unsupported match fields: {', '.join(sorted(unknown_fields))}")
        for field, condition in match.items():
            _validate_condition(rule_id, field, condition)
        normalized.append(
            {
                "id": rule_id,
                "description": str(raw_rule.get("description", "")),
                "match": match,
                "risk_level": risk_level,
                "action": action,
                "reason": str(raw_rule.get("reason", "")),
                "suggested_policy": str(raw_rule.get("suggested_policy", "")),
            }
        )
    result = {"version": 1, "mode": mode, "rules": normalized}
    if "domain_policy" in data:
        if not isinstance(data["domain_policy"], dict):
            raise PolicyValidationError("domain_policy must be a mapping")
        unknown_domain_fields = set(data["domain_policy"]) - {
            "allow_domains",
            "deny_domains",
            "warn_domains",
            "allow_localhost",
            "allow_private_networks",
            "warn_on_unknown_external",
            "block_on_deny",
        }
        if unknown_domain_fields:
            raise PolicyValidationError(f"unsupported domain_policy fields: {', '.join(sorted(unknown_domain_fields))}")
        for key in ("allow_domains", "deny_domains", "warn_domains"):
            if key in data["domain_policy"] and not isinstance(data["domain_policy"][key], list):
                raise PolicyValidationError(f"domain_policy.{key} must be a list")
        for key in ("allow_localhost", "allow_private_networks", "warn_on_unknown_external", "block_on_deny"):
            if key in data["domain_policy"] and not isinstance(data["domain_policy"][key], bool):
                raise PolicyValidationError(f"domain_policy.{key} must be a boolean")
        result["domain_policy"] = normalized_domain_config(data["domain_policy"])
    return result


def _validate_condition(rule_id: str, field: str, condition: Any) -> None:
    if isinstance(condition, (str, bool, int, float)):
        return
    if not isinstance(condition, dict) or len(condition) != 1:
        raise PolicyValidationError(f"rule {rule_id}: match.{field} must be a scalar or one operator mapping")
    operator, expected = next(iter(condition.items()))
    if operator not in ALLOWED_OPERATORS:
        raise PolicyValidationError(f"rule {rule_id}: unsupported operator {operator} for {field}")
    if operator in {"contains_any", "any_of"}:
        if not isinstance(expected, list) or not expected:
            raise PolicyValidationError(f"rule {rule_id}: {operator} for {field} must be a non-empty list")
    elif not isinstance(expected, (str, bool, int, float)):
        raise PolicyValidationError(f"rule {rule_id}: {operator} for {field} must be a scalar")
    if operator == "regex":
        try:
            re.compile(str(expected))
        except re.error as exc:
            raise PolicyValidationError(f"rule {rule_id}: invalid regex for {field}: {exc}") from exc


def _equal(actual: Any, expected: Any, field: str) -> bool:
    if isinstance(expected, bool):
        return bool(actual) is expected
    left = str(actual if actual is not None else "")
    right = str(expected)
    if field == "method":
        return left.upper() == right.upper()
    return left.lower() == right.lower()


def match_condition(actual: Any, condition: Any, field: str) -> bool:
    if not isinstance(condition, dict):
        return _equal(actual, condition, field)
    operator, expected = next(iter(condition.items()))
    actual_text = str(actual if actual is not None else "")
    if operator == "exact":
        return _equal(actual, expected, field)
    if operator == "contains":
        return str(expected).lower() in actual_text.lower()
    if operator == "contains_any":
        return any(str(item).lower() in actual_text.lower() for item in expected)
    if operator == "glob":
        return fnmatch.fnmatch(actual_text.lower(), str(expected).lower())
    if operator == "any_of":
        return any(_equal(actual, item, field) for item in expected)
    if operator == "regex":
        try:
            return re.search(str(expected), actual_text, flags=re.IGNORECASE) is not None
        except re.error:
            return False
    return False


def match_rule(rule: dict[str, Any], event: dict[str, Any]) -> bool:
    return all(match_condition(event.get(field), condition, field) for field, condition in rule.get("match", {}).items())


def first_matching_rule(policy: dict[str, Any], event: dict[str, Any]) -> dict[str, Any] | None:
    for rule in policy.get("rules", []):
        if match_rule(rule, event):
            return rule
    return None
