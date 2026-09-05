"""Pure URL redaction shared by live HTTP capture and cassette export."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

SENSITIVE_QUERY_NAMES = {
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "key",
    "secret",
    "client_secret",
    "password",
    "passwd",
    "auth",
    "authorization",
    "signature",
    "sig",
    "session",
    "cookie",
    "credential",
}


def redact_url_details(value: Any) -> dict[str, Any]:
    split = urlsplit(str(value))
    sensitive_query = False
    redacted_pairs: list[tuple[str, str]] = []
    for name, item in parse_qsl(split.query, keep_blank_values=True):
        if name.lower() in SENSITIVE_QUERY_NAMES:
            sensitive_query = True
            redacted_pairs.append((name, "<redacted>"))
        else:
            redacted_pairs.append((name, item))

    host = split.hostname or ""
    if ":" in host and not host.startswith("["):
        display_host = f"[{host}]"
    else:
        display_host = host
    if split.port is not None:
        display_host = f"{display_host}:{split.port}"
    query = urlencode(redacted_pairs, doseq=True, quote_via=quote, safe="<>")
    safe_url = urlunsplit((split.scheme, display_host, split.path, query, ""))
    return {
        "url": safe_url,
        "host": host,
        "scheme": split.scheme,
        "path": split.path or "/",
        "sensitive_query": sensitive_query,
        "query_redacted": query,
        "has_userinfo": split.username is not None or split.password is not None,
    }
