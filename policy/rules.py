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
        {"id": "dangerous_delete", "type": "shell", "match": "rm -rf or rmdir /s /q", "risk": "critical", "action": "warn"},
        {"id": "env_write", "type": "file.write", "match": ".env or .env.*", "risk": "high", "action": "warn"},
        {"id": "git_push", "type": "shell", "match": "git push", "risk": "high", "action": "warn"},
    ]
}

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def load_policy() -> dict[str, Any]:
    try:
        text = resources.files("policy").joinpath("default_policy.json").read_text(encoding="utf-8")
        return json.loads(text)
    except Exception:
        return DEFAULT_RULES


def risk(level: str = "low", reasons: list[str] | None = None, policy_rule: str | None = None, action: str = "allow") -> dict[str, Any]:
    if os.environ.get("TRACESEAL_POLICY_MODE", "warn").lower() in {"block", "deny", "enforce"} and level in {"high", "critical"}:
        action = "deny"
    return {"level": level, "reasons": reasons or [], "policy_rule": policy_rule, "action": action}


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
        return risk("high", ["git push publishes repository state"], "git_push", "warn")
    return risk("low", [], None, "allow")


def evaluate_file_write(path: str) -> dict[str, Any]:
    name = Path(path).name
    normalized = path.replace("\\", "/")
    if name == ".env" or name.startswith(".env.") or normalized.endswith("/.env"):
        return risk("high", [f"write to environment/config file: {path}"], "env_write", "warn")
    return risk("low", [], None, "allow")


def evaluate_http_request(method: str, url: str) -> dict[str, Any]:
    return risk("medium", [f"outbound HTTP request: {method.upper()} {url}"], "http_request", "warn")


def suggest_policy_for_event(event: dict[str, Any]) -> str:
    rule = (event.get("risk") or {}).get("policy_rule")
    command = (event.get("input") or {}).get("command", "")
    if rule == "dangerous_delete":
        targets = (event.get("input") or {}).get("targets") or rm_targets(command)
        target = targets[0] if targets else "<path>"
        clean = str(target).rstrip("/\\")
        return f'deny shell "rm -rf {clean}/**"'
    if rule == "env_write":
        path = (event.get("input") or {}).get("path", ".env")
        return f'deny file.write "{path}"'
    if rule == "git_push":
        return 'deny shell "git push"'
    if event.get("type") == "http":
        return 'review http "<method> <url>"'
    return "review event and add a targeted deny rule"
