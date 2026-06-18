from __future__ import annotations

import json
import os
import re
import shlex
from importlib import resources
from pathlib import Path
from typing import Any

DEFAULT_RULES = {
    "rules": [
        {
            "rule_id": "dangerous_delete",
            "event_type": "shell",
            "pattern": "rm -rf or rmdir /s /q",
            "risk_level": "critical",
            "action": "warn",
            "reason": "recursive force delete can remove protected workspace data",
            "suggested_policy": 'deny shell "rm -rf <path>/**"',
        },
        {
            "rule_id": "env_write",
            "event_type": "file.write",
            "pattern": ".env or .env.*",
            "risk_level": "high",
            "action": "warn",
            "reason": "writing environment files can corrupt secrets/configuration",
            "suggested_policy": 'deny file_write ".env*"',
        },
        {
            "rule_id": "git_push",
            "event_type": "shell",
            "pattern": "git push",
            "risk_level": "high",
            "action": "warn",
            "reason": "git push publishes code or history outside the local workspace",
            "suggested_policy": 'require_approval git "push"',
        },
        {
            "rule_id": "suspicious_http_post",
            "event_type": "http",
            "pattern": "POST request to non-local URL or request carrying secret-like fields",
            "risk_level": "high",
            "action": "warn",
            "reason": "HTTP POST can exfiltrate sensitive data outside the workspace",
            "suggested_policy": 'deny http "POST https://*/**"',
        },
    ]
}

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def load_policy() -> dict[str, Any]:
    try:
        text = resources.files("policy").joinpath("default_policy.json").read_text(encoding="utf-8")
        return json.loads(text)
    except Exception:
        return DEFAULT_RULES


def _rules_by_id() -> dict[str, dict[str, Any]]:
    rules = load_policy().get("rules", [])
    result: dict[str, dict[str, Any]] = {}
    for item in rules:
        rule_id = item.get("rule_id") or item.get("id")
        if rule_id:
            result[str(rule_id)] = item
    return result


def _rule(rule_id: str | None) -> dict[str, Any]:
    return _rules_by_id().get(str(rule_id), {}) if rule_id else {}


def risk(level: str = "low", reasons: list[str] | None = None, policy_rule: str | None = None, action: str = "allow") -> dict[str, Any]:
    if os.environ.get("TRACESEAL_POLICY_MODE", "warn").lower() in {"block", "deny", "enforce"} and level in {"high", "critical"}:
        action = "deny"
    rule = _rule(policy_rule)
    return {
        "level": level,
        "reasons": reasons or ([rule["reason"]] if rule.get("reason") else []),
        "policy_rule": policy_rule,
        "action": action,
        "suggested_policy": rule.get("suggested_policy"),
    }


def tokenize_command(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=os.name != "nt")
    except ValueError:
        return command.split()


def command_to_string(args: Any, shell: bool = False) -> str:
    if isinstance(args, (list, tuple)):
        return " ".join(str(part) for part in args)
    return str(args)


def _normalized_tokens(command: str, tokens: list[str] | None = None) -> list[str]:
    tokens = tokens if tokens is not None else tokenize_command(command)
    return [str(t).strip().strip("\"'").lower() for t in tokens if str(t).strip()]


def is_rm_rf(command: str, tokens: list[str] | None = None) -> bool:
    t = _normalized_tokens(command, tokens)
    if not t:
        return False
    if t[0] in {"rm", "/bin/rm", "busybox"}:
        joined_flags = "".join(x[1:] for x in t[1:] if x.startswith("-"))
        return "r" in joined_flags and "f" in joined_flags
    normalized = " ".join(t)
    return "rm -rf" in normalized or "rm -fr" in normalized or re.search(r"\brmdir\s+/s\s+/q\b", normalized) is not None


def rm_targets(command: str, tokens: list[str] | None = None) -> list[str]:
    t = [str(x) for x in (tokens if tokens is not None else tokenize_command(command))]
    if not t:
        return []
    low0 = t[0].strip("\"'").lower()
    if low0 in {"rm", "/bin/rm", "busybox"}:
        return [x for x in t[1:] if not str(x).startswith("-")]
    if low0 in {"rmdir", "rd"}:
        return [
            str(x).strip("\"'")
            for x in t[1:]
            if str(x).strip("\"'").lower() not in {"/s", "/q"}
        ]
    m = re.search(r"rm\s+-[rfRF]+\s+(.+)$", command)
    if m:
        rest = m.group(1).strip()
        try:
            return [x for x in shlex.split(rest, posix=os.name != "nt") if not x.startswith("-")]
        except ValueError:
            return [rest]
    return []


def is_git_push(command: str, tokens: list[str] | None = None) -> bool:
    t = _normalized_tokens(command, tokens)
    return len(t) >= 2 and t[0] == "git" and t[1] == "push"


def evaluate_shell_command(command: str, tokens: list[str] | None = None) -> dict[str, Any]:
    if is_rm_rf(command, tokens):
        targets = rm_targets(command, tokens)
        target_text = ", ".join(targets) if targets else "unknown target"
        return risk("critical", [f"recursive force delete requested: {target_text}"], "dangerous_delete", "warn")
    if is_git_push(command, tokens):
        return risk("high", ["remote git push requested"], "git_push", "warn")
    return risk("low", [], None, "allow")


def evaluate_file_write(path: str) -> dict[str, Any]:
    name = Path(path).name
    normalized = path.replace("\\", "/")
    if name == ".env" or name.startswith(".env.") or normalized.endswith("/.env"):
        return risk("high", [f"sensitive environment file modified: {path}"], "env_write", "warn")
    return risk("low", [], None, "allow")


def evaluate_http_request(method: str, url: str) -> dict[str, Any]:
    method_upper = method.upper()
    normalized = url.lower()
    is_local = any(host in normalized for host in ["localhost", "127.0.0.1", "::1"])
    if method_upper == "POST":
        return risk("high", [f"suspicious outbound HTTP POST: {method_upper} {url}"], "suspicious_http_post", "warn")
    if not is_local:
        return risk("medium", [f"outbound HTTP request: {method_upper} {url}"], "http_request", "warn")
    return risk("low", [], None, "allow")


def suggest_policy_for_event(event: dict[str, Any]) -> str:
    rule = (event.get("risk") or {}).get("policy_rule")
    command = (event.get("input") or {}).get("command", "")
    if rule == "dangerous_delete":
        targets = (event.get("input") or {}).get("targets") or rm_targets(command)
        target = targets[0] if targets else "<path>"
        clean = str(target).rstrip("/\\")
        return f'deny shell "rm -rf {clean}/**"'
    if rule == "env_write":
        return 'deny file_write ".env*"'
    if rule == "git_push":
        return 'require_approval git "push"'
    if rule == "suspicious_http_post":
        url = (event.get("input") or {}).get("url", "<url>")
        return f'deny http "POST {url}"'
    if event.get("type") == "http":
        return 'review http "<method> <url>"'
    return "review event and add a targeted deny rule"
