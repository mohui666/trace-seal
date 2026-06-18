from __future__ import annotations

import contextvars
import functools
import time
from typing import Any, Callable
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from policy.rules import evaluate_httpx_request
from recorder.core import record_event

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover - optional import fallback
    httpx = None  # type: ignore


SENSITIVE_HEADERS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "x-csrf-token",
}

SENSITIVE_QUERY = {
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
}

_SOURCE: contextvars.ContextVar[str | None] = contextvars.ContextVar("traceseal_httpx_source", default=None)
_INSTALLED = False

if httpx is not None:
    _USE_CLIENT_DEFAULT = getattr(httpx, "USE_CLIENT_DEFAULT", object())
    _ORIG_CLIENT_REQUEST = httpx.Client.request
    _ORIG_ASYNC_CLIENT_REQUEST = httpx.AsyncClient.request
    _ORIG_MODULE_APIS = {name: getattr(httpx, name) for name in ("request", "get", "post", "put", "patch", "delete")}
    _ORIG_CLIENT_APIS = {name: getattr(httpx.Client, name) for name in ("get", "post", "put", "patch", "delete")}
    _ORIG_ASYNC_CLIENT_APIS = {name: getattr(httpx.AsyncClient, name) for name in ("get", "post", "put", "patch", "delete")}
else:  # pragma: no cover - dependency is declared by the package
    _USE_CLIENT_DEFAULT = object()
    _ORIG_CLIENT_REQUEST = None
    _ORIG_ASYNC_CLIENT_REQUEST = None
    _ORIG_MODULE_APIS: dict[str, Any] = {}
    _ORIG_CLIENT_APIS: dict[str, Any] = {}
    _ORIG_ASYNC_CLIENT_APIS: dict[str, Any] = {}


def _resolved_url(client: Any, url: Any, params: Any = None) -> Any:
    value = httpx.URL(url)
    if not value.is_absolute_url:
        value = client.base_url.join(value)
    if params is not None:
        value = value.copy_merge_params(params)
    return value


def _redact_url(value: Any) -> dict[str, Any]:
    split = urlsplit(str(value))
    sensitive_query = False
    redacted_pairs: list[tuple[str, str]] = []
    for name, item in parse_qsl(split.query, keep_blank_values=True):
        if name.lower() in SENSITIVE_QUERY:
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
        "has_userinfo": split.username is not None or split.password is not None,
    }


def _redact_headers(client: Any, request_headers: Any, cookies: Any, auth: Any) -> tuple[dict[str, str], bool]:
    combined = httpx.Headers(getattr(client, "headers", None))
    if request_headers is not None:
        combined.update(request_headers)

    result: dict[str, str] = {}
    sensitive = False
    for name, value in combined.items():
        if name.lower() in SENSITIVE_HEADERS:
            result[name] = "<redacted>"
            sensitive = True
        else:
            result[name] = str(value)

    client_cookies = getattr(client, "cookies", None)
    cookies_supplied = cookies is not None and cookies is not _USE_CLIENT_DEFAULT
    if cookies_supplied or (client_cookies is not None and len(client_cookies) > 0):
        result["cookie"] = "<redacted>"
        sensitive = True
    client_auth = getattr(client, "_auth", None)
    auth_supplied = auth is not None and auth is not _USE_CLIENT_DEFAULT
    if auth_supplied or client_auth is not None:
        result["authorization"] = "<redacted>"
        sensitive = True
    return result, sensitive


def _metadata(client: Any, method: Any, url: Any, kwargs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        resolved = _resolved_url(client, url, kwargs.get("params"))
        url_data = _redact_url(resolved)
    except Exception:
        url_data = {
            "url": "<invalid-url>",
            "host": "",
            "scheme": "",
            "path": "",
            "sensitive_query": False,
            "has_userinfo": False,
        }
    try:
        headers, sensitive_headers = _redact_headers(
            client,
            kwargs.get("headers"),
            kwargs.get("cookies"),
            kwargs.get("auth"),
        )
    except Exception:
        # Invalid header input should still fail through httpx itself and be
        # recorded without risking disclosure from the malformed value.
        headers, sensitive_headers = {}, False
    method_text = str(method).upper()
    source = _SOURCE.get() or (
        "httpx.AsyncClient.request" if isinstance(client, httpx.AsyncClient) else "httpx.Client.request"
    )
    event_input = {
        "method": method_text,
        "url": url_data["url"],
        "host": url_data["host"],
        "scheme": url_data["scheme"],
        "path": url_data["path"],
        "source": source,
        "headers": headers,
    }
    risk = evaluate_httpx_request(
        method_text,
        url_data["url"],
        scheme=url_data["scheme"],
        host=url_data["host"],
        sensitive_query=url_data["sensitive_query"],
        sensitive_headers=sensitive_headers,
        has_userinfo=url_data["has_userinfo"],
    )
    return event_input, risk


def _record(event_input: dict[str, Any], risk: dict[str, Any], start: float, *, response: Any = None, exception: Exception | None = None, blocked: bool = False) -> None:
    duration_ms = int((time.perf_counter() - start) * 1000)
    if blocked:
        output = {"status": "blocked", "success": False, "status_code": None, "duration_ms": duration_ms, "exception_type": "PermissionError"}
    elif exception is not None:
        output = {
            "status": "exception",
            "success": False,
            "status_code": None,
            "duration_ms": duration_ms,
            "exception_type": type(exception).__name__,
        }
    else:
        status_code = getattr(response, "status_code", None)
        success = bool(getattr(response, "is_success", status_code is not None and 200 <= status_code < 400))
        output = {
            "status": "ok" if success else "failed",
            "success": success,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }
    record_event(
        {
            "type": "network.http",
            "operation": "httpx.request",
            "duration_ms": duration_ms,
            "input": event_input,
            "output": output,
            "risk": risk,
            "file_changes": [],
        }
    )


def traced_client_request(self: Any, method: Any, url: Any, **kwargs: Any) -> Any:
    start = time.perf_counter()
    event_input, risk = _metadata(self, method, url, kwargs)
    if risk.get("action") == "deny":
        _record(event_input, risk, start, blocked=True)
        raise PermissionError(f"TraceSeal policy denied httpx request: {event_input['method']} {event_input['url']}")
    try:
        response = _ORIG_CLIENT_REQUEST(self, method, url, **kwargs)
    except Exception as exc:
        _record(event_input, risk, start, exception=exc)
        raise
    _record(event_input, risk, start, response=response)
    return response


async def traced_async_client_request(self: Any, method: Any, url: Any, **kwargs: Any) -> Any:
    start = time.perf_counter()
    event_input, risk = _metadata(self, method, url, kwargs)
    if risk.get("action") == "deny":
        _record(event_input, risk, start, blocked=True)
        raise PermissionError(f"TraceSeal policy denied httpx request: {event_input['method']} {event_input['url']}")
    try:
        response = await _ORIG_ASYNC_CLIENT_REQUEST(self, method, url, **kwargs)
    except Exception as exc:
        _record(event_input, risk, start, exception=exc)
        raise
    _record(event_input, risk, start, response=response)
    return response


def _sync_source_wrapper(original: Callable[..., Any], source: str) -> Callable[..., Any]:
    @functools.wraps(original)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        token = _SOURCE.set(source)
        try:
            return original(*args, **kwargs)
        finally:
            _SOURCE.reset(token)

    return wrapped


def _async_source_wrapper(original: Callable[..., Any], source: str) -> Callable[..., Any]:
    @functools.wraps(original)
    async def wrapped(*args: Any, **kwargs: Any) -> Any:
        token = _SOURCE.set(source)
        try:
            return await original(*args, **kwargs)
        finally:
            _SOURCE.reset(token)

    return wrapped


def install() -> bool:
    global _INSTALLED
    if _INSTALLED or httpx is None:
        return httpx is not None
    _INSTALLED = True

    httpx.Client.request = traced_client_request
    httpx.AsyncClient.request = traced_async_client_request
    for name, original in _ORIG_MODULE_APIS.items():
        setattr(httpx, name, _sync_source_wrapper(original, f"httpx.{name}"))
    for name, original in _ORIG_CLIENT_APIS.items():
        setattr(httpx.Client, name, _sync_source_wrapper(original, f"httpx.Client.{name}"))
    for name, original in _ORIG_ASYNC_CLIENT_APIS.items():
        setattr(httpx.AsyncClient, name, _async_source_wrapper(original, f"httpx.AsyncClient.{name}"))
    return True
