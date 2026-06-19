from __future__ import annotations

import fnmatch
import ipaddress
from typing import Any

HOST_CLASSES = {"localhost", "loopback", "private", "external", "ip", "unknown"}
DOMAIN_DECISIONS = {"allow", "warn", "deny", "unknown"}

DEFAULT_DOMAIN_POLICY = {
    "allow_domains": [],
    "deny_domains": [],
    "warn_domains": [],
    "allow_localhost": True,
    "allow_private_networks": False,
    "warn_on_unknown_external": False,
    "block_on_deny": False,
}


def normalize_host(host: Any) -> str | None:
    value = str(host or "").strip().strip("[]").rstrip(".").lower()
    return value or None


def classify_host(host: Any) -> str:
    normalized = normalize_host(host)
    if not normalized:
        return "unknown"
    if normalized == "localhost" or normalized.endswith(".localhost"):
        return "localhost"
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        return "external"
    if address.is_loopback:
        return "loopback"
    if address.is_private or address.is_link_local:
        return "private"
    return "ip"


def domain_matches(host: Any, pattern: Any) -> bool:
    normalized = normalize_host(host)
    expected = normalize_host(pattern)
    if not normalized or not expected:
        return False
    return fnmatch.fnmatchcase(normalized, expected)


def _first_match(host: str | None, patterns: Any) -> str | None:
    if not host or not isinstance(patterns, list):
        return None
    for pattern in patterns:
        if domain_matches(host, pattern):
            return str(pattern)
    return None


def normalized_domain_config(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    result = dict(DEFAULT_DOMAIN_POLICY)
    for key in ("allow_domains", "deny_domains", "warn_domains"):
        items = raw.get(key, [])
        if isinstance(items, list):
            result[key] = [str(item).strip().lower() for item in items if str(item).strip()]
    for key in ("allow_localhost", "allow_private_networks", "warn_on_unknown_external", "block_on_deny"):
        if key in raw:
            result[key] = bool(raw[key])
    return result


def evaluate_domain_policy(host: Any, config: Any = None) -> dict[str, Any]:
    normalized = normalize_host(host)
    host_class = classify_host(normalized)
    settings = normalized_domain_config(config)
    deny_pattern = _first_match(normalized, settings["deny_domains"])
    warn_pattern = _first_match(normalized, settings["warn_domains"])
    allow_pattern = _first_match(normalized, settings["allow_domains"])
    local_allowed = host_class in {"localhost", "loopback"} and settings["allow_localhost"]
    private_allowed = host_class == "private" and settings["allow_private_networks"]

    matched_rule: str | None = None
    decision = "unknown"
    if deny_pattern:
        matched_rule = "domain_denylist_match"
        decision = "deny"
    elif warn_pattern:
        matched_rule = "domain_warnlist_match"
        decision = "warn"
    elif local_allowed:
        matched_rule = "domain_localhost_allowed"
        decision = "allow"
    elif private_allowed:
        matched_rule = "domain_allowlist_match"
        decision = "allow"
    elif allow_pattern:
        matched_rule = "domain_allowlist_match"
        decision = "allow"
    elif host_class in {"external", "ip"} and settings["warn_on_unknown_external"]:
        matched_rule = "domain_unknown_external"
        decision = "warn"

    return {
        "host": str(host) if host not in {None, ""} else None,
        "normalized_host": normalized,
        "host_class": host_class,
        "matched_domain_rule": matched_rule,
        "domain_decision": decision,
        "allowlisted": bool(allow_pattern or local_allowed or private_allowed),
        "denylisted": bool(deny_pattern),
        "warnlisted": bool(warn_pattern),
        "matched_pattern": deny_pattern or warn_pattern or allow_pattern,
        "block_on_deny": bool(settings["block_on_deny"]),
    }
