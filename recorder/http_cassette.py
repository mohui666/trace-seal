from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit


HTTP_EVENT_TYPES = {"http", "network.http"}
BODY_REDACTION = "body_not_stored_by_default"
REDACTED = "<redacted>"

SENSITIVE_HEADER_NAMES = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "proxy-authorization",
}
SENSITIVE_HEADER_PARTS = {"token", "secret", "key", "password", "credential", "session"}
SENSITIVE_QUERY_NAMES = {
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "key",
    "secret",
    "password",
    "passwd",
    "signature",
    "sig",
    "session",
    "auth",
    "credential",
    "client_secret",
    "authorization",
    "cookie",
}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
SAFE_ERROR_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")


def body_summary(
    *,
    present: bool = False,
    content_type: str | None = None,
    size_bytes: int | None = None,
    sha256: str | None = None,
) -> dict[str, Any]:
    return {
        "present": bool(present),
        "content_type": content_type,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "redaction": BODY_REDACTION,
    }


def summarize_body(value: Any, *, content_type: str | None = None, present: bool | None = None) -> dict[str, Any]:
    """Summarize an in-memory body without returning or persisting its content."""

    if present is None:
        present = value is not None
    if not present:
        return body_summary(content_type=content_type)

    data: bytes | None = None
    if isinstance(value, bytes):
        data = value
    elif isinstance(value, bytearray):
        data = bytes(value)
    elif isinstance(value, memoryview):
        data = value.tobytes()
    elif isinstance(value, str):
        data = value.encode("utf-8", errors="replace")

    return body_summary(
        present=True,
        content_type=content_type,
        size_bytes=len(data) if data is not None else None,
        sha256=hashlib.sha256(data).hexdigest() if data is not None else None,
    )


def normalize_body_summary(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return body_summary()
    size = value.get("size_bytes")
    digest = str(value.get("sha256") or "")
    return body_summary(
        present=bool(value.get("present")),
        content_type=str(value["content_type"]) if value.get("content_type") else None,
        size_bytes=size if isinstance(size, int) and size >= 0 else None,
        sha256=digest.lower() if SHA256_RE.fullmatch(digest) else None,
    )


def sanitize_error(value: Any) -> str | None:
    if not value:
        return None
    text = str(value)
    return text if SAFE_ERROR_RE.fullmatch(text) else "http_request_error"


def is_sensitive_header(name: str) -> bool:
    normalized = name.strip().lower()
    return normalized in SENSITIVE_HEADER_NAMES or any(part in normalized for part in SENSITIVE_HEADER_PARTS)


def redact_headers(headers: Any) -> dict[str, str]:
    if not isinstance(headers, dict):
        try:
            headers = dict(headers or {})
        except Exception:
            return {}
    return {
        str(name): REDACTED if is_sensitive_header(str(name)) else str(value)
        for name, value in headers.items()
    }


def redact_url(url: Any) -> dict[str, str]:
    value = str(url or "")
    try:
        split = urlsplit(value)
        pairs = [
            (name, REDACTED if name.lower() in SENSITIVE_QUERY_NAMES else item)
            for name, item in parse_qsl(split.query, keep_blank_values=True)
        ]
        query = urlencode(pairs, doseq=True, quote_via=quote, safe="<>")
        host = split.hostname or ""
        display_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
        if split.port is not None:
            display_host = f"{display_host}:{split.port}"
        return {
            "url_redacted": urlunsplit((split.scheme, display_host, split.path, query, "")),
            "scheme": split.scheme,
            "host": host,
            "path": split.path or "/",
            "query_redacted": query,
        }
    except Exception:
        return {
            "url_redacted": "<invalid-url>",
            "scheme": "",
            "host": "",
            "path": "",
            "query_redacted": "",
        }


def _matched_rules(risk: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for item in risk.get("matched_rules") or []:
        if item and str(item) not in values:
            values.append(str(item))
    for key in ("policy_rule", "rule_id"):
        item = risk.get(key)
        if item and str(item) not in values:
            values.append(str(item))
    return values


def cassette_entry_from_event(event: dict[str, Any], index: int) -> dict[str, Any] | None:
    if event.get("type") not in HTTP_EVENT_TYPES:
        return None

    inp = event.get("input") if isinstance(event.get("input"), dict) else {}
    out = event.get("output") if isinstance(event.get("output"), dict) else {}
    risk = event.get("risk") if isinstance(event.get("risk"), dict) else {}
    url_data = redact_url(inp.get("url"))
    status_code = out.get("status_code", out.get("code"))
    error = out.get("exception_type") or out.get("error_type") or out.get("error") or out.get("exception")
    return {
        "cassette_id": f"cassette_{index:04d}",
        "event_id": event.get("id"),
        "timestamp": event.get("ts"),
        "source_api": inp.get("source") or event.get("operation"),
        "method": str(inp.get("method", "GET")).upper(),
        **url_data,
        "request_headers_redacted": redact_headers(inp.get("headers") or inp.get("request_headers")),
        "request_body_summary": normalize_body_summary(inp.get("body_summary") or inp.get("request_body_summary")),
        "response_status_code": status_code if isinstance(status_code, int) else None,
        "response_headers_redacted": redact_headers(out.get("headers") or out.get("response_headers")),
        "response_body_summary": normalize_body_summary(out.get("body_summary") or out.get("response_body_summary")),
        "duration_ms": event.get("duration_ms", out.get("duration_ms")),
        "error": sanitize_error(error),
        "risk_level": str(risk.get("level", "low")),
        "matched_rules": _matched_rules(risk),
    }


def _is_external_host(host: str) -> bool:
    normalized = host.strip().strip("[]").lower()
    if not normalized or normalized == "localhost" or normalized.endswith(".localhost"):
        return False
    try:
        return not ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return True


def summarize_entries(entries: Iterable[dict[str, Any]], *, path: str | None) -> dict[str, Any]:
    items = list(entries)
    return {
        "present": path is not None,
        "entry_count": len(items),
        "high_risk_count": sum(
            1 for entry in items if RISK_ORDER.get(str(entry.get("risk_level", "low")), 0) >= RISK_ORDER["high"]
        ),
        "external_host_count": len(
            {str(entry.get("host")) for entry in items if _is_external_host(str(entry.get("host") or ""))}
        ),
        "redacted": True,
        "path": path,
        "error": None,
    }


def failed_summary(error: Any) -> dict[str, Any]:
    summary = summarize_entries([], path=None)
    summary["error"] = str(error)
    return summary


def generate_http_cassette(events_path: Path, cassette_path: Path) -> dict[str, Any]:
    """Generate a redacted JSONL cassette from existing TraceSeal events."""

    events_path = Path(events_path)
    cassette_path = Path(cassette_path)
    temporary = cassette_path.with_suffix(cassette_path.suffix + ".tmp")
    try:
        entries: list[dict[str, Any]] = []
        with events_path.open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                event = json.loads(line)
                entry = cassette_entry_from_event(event, len(entries) + 1)
                if entry is not None:
                    entries.append(entry)

        cassette_path.parent.mkdir(parents=True, exist_ok=True)
        with temporary.open("w", encoding="utf-8") as target:
            for entry in entries:
                target.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        temporary.replace(cassette_path)
        return summarize_entries(entries, path=cassette_path.name)
    except Exception as exc:
        for path in (temporary, cassette_path):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        return failed_summary(f"{type(exc).__name__}: {exc}")


def read_http_cassette(path: Path, *, limit: int = 50) -> tuple[list[dict[str, Any]], str | None]:
    entries: list[dict[str, Any]] = []
    if not path.is_file() or limit <= 0:
        return entries, None
    try:
        with path.open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                raw = json.loads(line)
                if not isinstance(raw, dict):
                    continue
                # Re-normalize the artifact before exposing it to Dashboard so
                # hand-edited files cannot smuggle raw bodies or secrets.
                synthetic_event = {
                    "id": raw.get("event_id"),
                    "ts": raw.get("timestamp"),
                    "type": "network.http",
                    "operation": raw.get("source_api"),
                    "duration_ms": raw.get("duration_ms"),
                    "input": {
                        "source": raw.get("source_api"),
                        "method": raw.get("method"),
                        "url": raw.get("url_redacted"),
                        "headers": raw.get("request_headers_redacted"),
                        "body_summary": raw.get("request_body_summary"),
                    },
                    "output": {
                        "status_code": raw.get("response_status_code"),
                        "headers": raw.get("response_headers_redacted"),
                        "body_summary": raw.get("response_body_summary"),
                        "error": raw.get("error"),
                    },
                    "risk": {"level": raw.get("risk_level"), "matched_rules": raw.get("matched_rules")},
                }
                entry = cassette_entry_from_event(synthetic_event, len(entries) + 1)
                if entry is not None:
                    entry["cassette_id"] = str(raw.get("cassette_id") or entry["cassette_id"])
                    entries.append(entry)
                if len(entries) >= max(0, limit):
                    break
        return entries, None
    except Exception as exc:
        return entries, f"{type(exc).__name__}: {exc}"
