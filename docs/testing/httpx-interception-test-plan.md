# httpx Interception Test Plan

## Goal

Validate TraceSeal's Python Core interception and recording of httpx requests.

## Scope

This plan covers Python-level httpx instrumentation.

## Non-goals

- No requests / urllib / aiohttp interception
- No Git diff / HEAD / staged tracking
- No full HTTP cassette system
- No Electron / Renderer feature testing
- No Rust Guard
- No OS-level network firewall
- No DLP product
- No v0.2.0 release artifact changes

## Test Matrix

### 1. Basic sync APIs

Cover:

- `httpx.get()`
- `httpx.post()`
- `httpx.request()`
- `httpx.Client.get()`
- `httpx.Client.post()`
- `httpx.Client.request()`

Expected behavior:

- request succeeds
- trace event is recorded
- method is recorded
- URL / host / path are recorded
- source API is recorded
- status_code is recorded
- duration or equivalent timing metadata is recorded

### 2. Async APIs

Cover:

- `httpx.AsyncClient.get()`
- `httpx.AsyncClient.post()`
- `httpx.AsyncClient.request()`

Expected behavior:

- async request succeeds
- trace event is recorded
- event schema matches sync requests
- no unawaited coroutine warnings
- TraceSeal does not break event loop behavior

### 3. Redaction

Cover sensitive headers:

- `Authorization`
- `Proxy-Authorization`
- `Cookie`
- `Set-Cookie`
- `X-API-Key`
- `X-Auth-Token`

Cover sensitive query parameters:

- `token`
- `access_token`
- `refresh_token`
- `api_key`
- `apikey`
- `key`
- `secret`
- `client_secret`
- `password`
- `auth`
- `signature`
- `session`

Expected behavior:

- sensitive values are replaced with `<redacted>` or equivalent
- fake secret strings do not appear in `events.jsonl`
- fake secret strings do not appear in `dashboard-data`
- request body is not recorded
- response body is not recorded

### 4. Risk classification

Cover:

- ordinary localhost request
- ordinary external-style HTTPS URL via mock transport
- plain `http://` URL
- URL containing sensitive query parameter
- request containing Authorization / Cookie header

Expected behavior:

- ordinary request has low / medium risk
- plain HTTP has higher risk than HTTPS
- sensitive query/header request is high risk
- risk reasons mention network request or sensitive request metadata
- policy rule is present when applicable

### 5. Failure behavior

Cover:

- timeout
- connection error
- invalid URL or request exception
- non-2xx HTTP response

Expected behavior:

- failure event is recorded
- TraceSeal does not crash
- error text is bounded and safe
- no sensitive data leaks through exception messages

### 6. Dashboard-data integration

Required command:

```powershell
python -m traceseal dashboard-data runs/latest
```

Expected behavior:

- httpx event is present
- schema is compatible
- dashboard-data does not crash
- no full request / response body is exported
- redaction is preserved

### 7. Explain integration

Required command:

```powershell
python -m traceseal explain runs/latest
```

Expected behavior:

- sensitive network request is mentioned
- first harmful event points to sensitive httpx event when appropriate
- output remains readable
- no secret values appear in explain output

### 8. Regression

Confirm:

- os.system interception still works
- file.read tracking still works
- subprocess interception still works
- dashboard-data tests still pass
- explain tests still pass
- replay tests still pass

### 9. Architecture boundaries

Confirm:

- no Electron / Renderer files are modified
- no v0.2.0 tag / Release artifact changes
- no Rust rewrite
- no cloud sync or login
- no unrelated Git tracking feature

## Required Manual Commands

```powershell
python -m unittest discover -s tests -v
python -m traceseal run -- python examples\bad_agent_httpx.py
python -m traceseal dashboard-data runs/latest
python -m traceseal explain runs/latest
```

## PASS Criteria

- All existing Python tests pass
- New httpx tests pass
- sync httpx APIs are recorded
- async httpx APIs are recorded
- sensitive headers and query values are redacted
- no full request body is recorded
- no full response body is recorded
- dashboard-data exports httpx events
- explain reports risky httpx requests
- os.system and file.read regressions pass
- no Electron / Renderer files are changed
- v0.2.0 tag and Release artifacts are unchanged

## FAIL Criteria

- httpx request is not recorded
- async requests are not captured
- Authorization / Cookie / token leaks
- request body or response body is stored
- dashboard-data crashes
- explain crashes
- os.system or file.read regresses
- Electron / Renderer files are modified
- v0.2.0 tag / Release artifacts are modified
- documentation claims system-level monitoring or complete DLP