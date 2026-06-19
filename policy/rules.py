from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from typing import Any

from .dsl import first_matching_rule
from .yaml_loader import load_policy_with_source

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
            "rule_id": "sensitive_file_read",
            "event_type": "file.read",
            "pattern": ".env, SSH keys, PEM/key files, or credential/secret/token/password paths",
            "risk_level": "high",
            "action": "warn",
            "reason": "reading sensitive files can expose credentials or secrets",
            "suggested_policy": 'require_approval file_read "<sensitive-path>"',
        },
        {
            "rule_id": "git_push",
            "event_type": "shell",
            "pattern": "git push",
            "risk_level": "high",
            "action": "warn",
            "reason": "git push publishes local code or history to a remote repository",
            "suggested_policy": 'require_approval git "push"',
        },
        {
            "rule_id": "git_force_push",
            "event_type": "shell",
            "pattern": "git push --force or git push -f",
            "risk_level": "critical",
            "action": "warn",
            "reason": "force push can rewrite remote history and disrupt collaborators",
            "suggested_policy": 'deny git "push --force"',
        },
        {
            "rule_id": "git_force_with_lease",
            "event_type": "shell",
            "pattern": "git push --force-with-lease",
            "risk_level": "high",
            "action": "warn",
            "reason": "force-with-lease can still rewrite remote history",
            "suggested_policy": 'require_approval git "push --force-with-lease"',
        },
        {
            "rule_id": "git_mirror_push",
            "event_type": "shell",
            "pattern": "git push --mirror",
            "risk_level": "critical",
            "action": "warn",
            "reason": "mirror push can overwrite remote refs",
            "suggested_policy": 'deny git "push --mirror"',
        },
        {
            "rule_id": "git_delete_remote_branch",
            "event_type": "shell",
            "pattern": "git push --delete or a colon-prefixed delete refspec",
            "risk_level": "critical",
            "action": "warn",
            "reason": "deleting a remote branch can remove shared work",
            "suggested_policy": 'require_approval git "push --delete"',
        },
        {
            "rule_id": "git_force_refspec_push",
            "event_type": "shell",
            "pattern": "git push with a plus-prefixed refspec",
            "risk_level": "critical",
            "action": "warn",
            "reason": "plus-prefixed refspec can force-update remote refs",
            "suggested_policy": 'deny git "push +<refspec>"',
        },
        {
            "rule_id": "git_bulk_push",
            "event_type": "shell",
            "pattern": "git push --all or git push --tags",
            "risk_level": "high",
            "action": "warn",
            "reason": "pushing all branches or tags can publish more refs than intended",
            "suggested_policy": 'require_approval git "push --all/--tags"',
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
        {
            "rule_id": "sensitive_http_request",
            "event_type": "network.http",
            "pattern": "httpx request with sensitive query parameters, headers, cookies, or auth",
            "risk_level": "high",
            "action": "warn",
            "reason": "network request carries sensitive authentication metadata",
            "suggested_policy": 'require_approval httpx "<method> <url>"',
        },
        {
            "rule_id": "insecure_http_request",
            "event_type": "network.http",
            "pattern": "plaintext http:// request",
            "risk_level": "medium",
            "action": "warn",
            "reason": "plaintext HTTP can expose request metadata in transit",
            "suggested_policy": 'require_approval httpx "http://*/**"',
        },
    ]
}

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def load_policy(workspace: str | Path | None = None) -> dict[str, Any]:
    return load_policy_with_source(workspace)[0]


def policy_source(workspace: str | Path | None = None) -> dict[str, Any]:
    return load_policy_with_source(workspace)[1]


def _rules_by_id() -> dict[str, dict[str, Any]]:
    rules = load_policy().get("rules", [])
    result: dict[str, dict[str, Any]] = {}
    for item in rules:
        rule_id = item.get("rule_id") or item.get("id")
        if rule_id:
            result[str(rule_id)] = item
    return result


def _rule(rule_id: str | None) -> dict[str, Any]:
    if not rule_id:
        return {}
    selected = _rules_by_id().get(str(rule_id))
    if selected:
        return selected
    return next((item for item in DEFAULT_RULES["rules"] if item.get("rule_id") == rule_id), {})


def _policy_mode() -> str:
    configured = os.environ.get("TRACESEAL_POLICY_MODE")
    if configured:
        return configured.lower()
    return str(load_policy().get("mode", "warn")).lower()


def risk(level: str = "low", reasons: list[str] | None = None, policy_rule: str | None = None, action: str = "allow") -> dict[str, Any]:
    if _policy_mode() in {"block", "deny", "enforce"} and level in {"high", "critical"} and action == "warn":
        action = "deny"
    rule = _rule(policy_rule)
    reason_list = reasons or ([rule["reason"]] if rule.get("reason") else [])
    return {
        "level": level,
        "reasons": reason_list,
        "reason": reason_list[0] if reason_list else None,
        "policy_rule": policy_rule,
        "rule_id": policy_rule,
        "action": action,
        "suggested_policy": rule.get("suggested_policy"),
    }


def _yaml_risk(event: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    policy, source = load_policy_with_source()
    if source["type"] != "yaml":
        return fallback
    context = dict(event)
    context.setdefault("risk_level", fallback.get("level", "low"))
    matched = first_matching_rule(policy, context)
    if matched is None:
        return fallback
    action = str(matched["action"])
    level = str(matched["risk_level"])
    if _policy_mode() in {"block", "deny", "enforce"} and level in {"high", "critical"} and action == "warn":
        action = "deny"
    reason = str(matched.get("reason") or matched.get("description") or f"matched policy rule: {matched['id']}")
    return {
        "level": level,
        "reasons": [reason],
        "reason": reason,
        "policy_rule": matched["id"],
        "rule_id": matched["id"],
        "action": action,
        "suggested_policy": matched.get("suggested_policy") or None,
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


def _is_protected_ref(ref: str) -> bool:
    value = str(ref).lstrip("+:")
    candidates = [part for part in value.split(":") if part]
    protected = {"main", "master", "trunk", "production", "prod"}
    for candidate in candidates:
        normalized = candidate.removeprefix("refs/heads/").strip("/").lower()
        if normalized in protected or normalized.startswith("release/"):
            return True
    return False


def classify_git_push(command: str, tokens: list[str] | None = None) -> dict[str, Any] | None:
    """Classify supported git push forms without contacting a remote."""

    raw = [str(item).strip().strip("\"'") for item in (tokens if tokens is not None else tokenize_command(command))]
    normalized = [item.lower() for item in raw]
    if len(normalized) < 2 or normalized[0] != "git" or normalized[1] != "push":
        return None

    arguments = raw[2:]
    lowered = normalized[2:]
    positionals = [item for item in arguments if item and not item.startswith("-")]
    remote = positionals[0] if positionals else None
    refs = positionals[1:] if len(positionals) > 1 else []

    has_force_with_lease = any(item == "--force-with-lease" or item.startswith("--force-with-lease=") for item in lowered)
    has_force = any(item in {"--force", "-f"} for item in lowered)
    has_mirror = "--mirror" in lowered
    has_delete = "--delete" in lowered or any(item.startswith(":") and len(item) > 1 for item in refs)
    has_force_refspec = any(item.startswith("+") and len(item) > 1 for item in refs)
    has_all = "--all" in lowered
    has_tags = "--tags" in lowered

    if has_mirror:
        push_type = "mirror"
    elif has_force_with_lease:
        push_type = "force_with_lease"
    elif has_force:
        push_type = "force"
    elif has_delete:
        push_type = "delete_remote_branch"
    elif has_force_refspec:
        push_type = "force_refspec"
    elif has_all:
        push_type = "all"
    elif has_tags:
        push_type = "tags"
    else:
        push_type = "normal"

    return {
        "kind": "push",
        "push_type": push_type,
        "remote": remote,
        "refs": refs,
        "protected_branch": any(_is_protected_ref(ref) for ref in refs) if refs else None,
    }


def evaluate_shell_command(command: str, tokens: list[str] | None = None) -> dict[str, Any]:
    git_operation = classify_git_push(command, tokens)
    if is_rm_rf(command, tokens):
        targets = rm_targets(command, tokens)
        target_text = ", ".join(targets) if targets else "unknown target"
        fallback = risk("critical", [f"recursive force delete requested: {target_text}"], "dangerous_delete", "warn")
    elif git_operation is not None:
        push_rules = {
            "normal": ("high", "git_push", "git push publishes local code or history to a remote repository"),
            "force": ("critical", "git_force_push", "force push can rewrite remote history and disrupt collaborators"),
            "force_with_lease": ("high", "git_force_with_lease", "force-with-lease can still rewrite remote history"),
            "mirror": ("critical", "git_mirror_push", "mirror push can overwrite remote refs"),
            "delete_remote_branch": ("critical", "git_delete_remote_branch", "deleting a remote branch can remove shared work"),
            "force_refspec": ("critical", "git_force_refspec_push", "plus-prefixed refspec can force-update remote refs"),
            "all": ("high", "git_bulk_push", "pushing all branches or tags can publish more refs than intended"),
            "tags": ("high", "git_bulk_push", "pushing all branches or tags can publish more refs than intended"),
        }
        level, rule_id, reason = push_rules.get(str(git_operation["push_type"]), ("high", "git_push", "remote git push requested"))
        fallback = risk(level, [reason], rule_id, "warn")
    else:
        fallback = risk("low", [], None, "allow")
    result = _yaml_risk({"event_type": "shell", "command": command}, fallback)
    if git_operation is not None:
        result["git_operation"] = git_operation
    return result


def evaluate_file_write(path: str) -> dict[str, Any]:
    name = Path(path).name
    normalized = path.replace("\\", "/")
    if name == ".env" or name.startswith(".env.") or normalized.endswith("/.env"):
        fallback = risk("high", [f"sensitive environment file modified: {path}"], "env_write", "warn")
    else:
        fallback = risk("low", [], None, "allow")
    return _yaml_risk({"event_type": "file.write", "path": normalized}, fallback)


def evaluate_file_read(path: str) -> dict[str, Any]:
    normalized = path.replace("\\", "/").lower()
    parts = [part for part in normalized.split("/") if part]
    name = parts[-1] if parts else normalized
    sensitive_names = {"id_rsa", "id_ed25519", "credentials", "credential", "secret", "secrets", "token", "tokens", "password", "passwd"}
    sensitive_word = re.search(r"(?:^|[._-])(credentials?|secrets?|tokens?|password|passwd)(?:[._-]|$)", name) is not None
    sensitive = (
        name == ".env"
        or name.startswith(".env.")
        or name in sensitive_names
        or sensitive_word
        or name.endswith((".pem", ".key"))
        or ".ssh" in parts
        or any(marker in parts for marker in {"credentials", "secrets", "tokens"})
    )
    if sensitive:
        fallback = risk("high", [f"sensitive file read: {path}"], "sensitive_file_read", "warn")
    else:
        fallback = risk("low", [], None, "allow")
    return _yaml_risk({"event_type": "file.read", "path": normalized}, fallback)


def evaluate_http_request(method: str, url: str) -> dict[str, Any]:
    method_upper = method.upper()
    normalized = url.lower()
    is_local = any(host in normalized for host in ["localhost", "127.0.0.1", "::1"])
    if method_upper == "POST":
        fallback = risk("high", [f"suspicious outbound HTTP POST: {method_upper} {url}"], "suspicious_http_post", "warn")
    elif not is_local:
        fallback = risk("medium", [f"outbound HTTP request: {method_upper} {url}"], "http_request", "warn")
    else:
        fallback = risk("low", [], None, "allow")
    host = url.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
    return _yaml_risk({"event_type": "http", "method": method_upper, "url": url, "host": host, "sensitive": False}, fallback)


def evaluate_httpx_request(
    method: str,
    url: str,
    *,
    scheme: str,
    host: str,
    sensitive_query: bool = False,
    sensitive_headers: bool = False,
    has_userinfo: bool = False,
) -> dict[str, Any]:
    method_upper = method.upper()
    if sensitive_query or sensitive_headers or has_userinfo:
        reasons: list[str] = []
        if sensitive_query:
            reasons.append("sensitive query parameter redacted")
        if sensitive_headers:
            reasons.append("sensitive request header or authentication metadata redacted")
        if has_userinfo:
            reasons.append("URL user information redacted")
        fallback = risk("high", reasons, "sensitive_http_request", "warn")
    elif scheme.lower() == "http":
        fallback = risk("medium", [f"plaintext HTTP request: {method_upper} {url}"], "insecure_http_request", "warn")
    elif host.lower() not in {"localhost", "127.0.0.1", "::1"}:
        fallback = risk("medium", [f"outbound HTTP request: {method_upper} {url}"], "http_request", "warn")
    else:
        fallback = risk("low", [], None, "allow")
    return _yaml_risk(
        {
            "event_type": "network.http",
            "method": method_upper,
            "url": url,
            "host": host,
            "sensitive": sensitive_query or sensitive_headers or has_userinfo,
        },
        fallback,
    )


def suggest_policy_for_event(event: dict[str, Any]) -> str:
    configured = (event.get("risk") or {}).get("suggested_policy")
    if configured:
        return str(configured)
    rule = (event.get("risk") or {}).get("policy_rule")
    command = (event.get("input") or {}).get("command", "")
    if rule == "dangerous_delete":
        targets = (event.get("input") or {}).get("targets") or rm_targets(command)
        target = targets[0] if targets else "<path>"
        clean = str(target).rstrip("/\\")
        return f'deny shell "rm -rf {clean}/**"'
    if rule == "env_write":
        return 'deny file_write ".env*"'
    if rule == "sensitive_file_read":
        path = (event.get("input") or {}).get("path", "<sensitive-path>")
        return f'require_approval file_read "{path}"'
    if rule == "git_push":
        return 'require_approval git "push"'
    if rule == "suspicious_http_post":
        url = (event.get("input") or {}).get("url", "<url>")
        return f'deny http "POST {url}"'
    if rule == "sensitive_http_request":
        inp = event.get("input") or {}
        return f'require_approval httpx "{inp.get("method", "GET")} {inp.get("url", "<url>")}"'
    if rule == "insecure_http_request":
        return 'require_approval httpx "http://*/**"'
    if event.get("type") in {"http", "network.http"}:
        return 'review http "<method> <url>"'
    return "review event and add a targeted deny rule"
