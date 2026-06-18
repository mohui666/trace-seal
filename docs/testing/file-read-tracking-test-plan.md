# File Read Tracking Test Plan

## Goal

Validate TraceSeal's Python Core recording of file read operations.

## Scope

This plan covers Python-level file read instrumentation.

## Non-goals

- No httpx interception
- No Git diff / HEAD / staged tracking
- No Electron / Renderer feature testing
- No Rust Guard
- No OS-level file system monitor
- No DLP product
- No v0.2.0 release artifact changes

## Test Matrix

### 1. Basic read APIs

Cover:

- `open(path, "r")`
- `open(path, "rb")`
- `Path.open()`
- `Path.read_text()`
- `Path.read_bytes()`

Expected behavior:

- read succeeds
- trace event is recorded
- path is recorded
- source API is recorded
- mode is recorded when available
- bytes read or file size is recorded
- full file content is not recorded by default

### 2. Sensitive file reads

Cover:

- `.env`
- `secret.txt`
- `token.txt`
- `credentials.json`
- `.pem` / `.key` test files
- fake `.ssh` path inside a temp workspace

Expected behavior:

- event is recorded
- risk level is higher than ordinary file reads
- reasons mention sensitive file read or equivalent wording
- no real user secret is read
- no file content is stored in clear text

### 3. Path handling

Cover:

- path with spaces
- Unicode path
- relative path
- absolute path inside test workspace
- missing file
- permission error if easy to simulate safely

Expected behavior:

- success and failure are both handled
- failed read does not crash TraceSeal
- error information is safe and bounded

### 4. Dashboard-data integration

Required command:

```powershell
python -m traceseal dashboard-data runs/latest
```

Expected behavior:

- file read event is present
- event schema is compatible
- dashboard-data does not crash
- existing file write/delete fields remain compatible

### 5. Explain integration

Required command:

```powershell
python -m traceseal explain runs/latest
```

Expected behavior:

- sensitive file read is mentioned
- first harmful event points to sensitive read if it is the earliest risky event
- explain output remains readable

### 6. Replay / regression

Confirm:

- existing replay tests still pass
- existing explain tests still pass
- existing dashboard-data tests still pass
- `os.system()` interception still works
- subprocess interception still works
- file write/delete tracking still works

### 7. Noise control

Confirm:

- TraceSeal internal reads do not flood user-visible events
- reading `events.jsonl`, `manifest.json`, policy files, or dashboard data does not create recursive noise
- output remains useful for real agent runs

### 8. Safety and privacy

Confirm:

- no complete file contents are stored by default
- sensitive values are not printed into event JSON
- hashes or metadata are acceptable if implemented
- test fixtures use fake secrets only

## Required Manual Commands

```powershell
python -m unittest discover -s tests -v
python -m traceseal run -- python examples\bad_agent_file_read.py
python -m traceseal dashboard-data runs/latest
python -m traceseal explain runs/latest
```

## PASS Criteria

- All existing Python tests pass
- New file read tests pass
- dashboard-data exports file read events
- explain reports sensitive reads
- no full sensitive content is recorded
- no Electron / Renderer files are changed
- v0.2.0 tag and Release artifacts are unchanged

## FAIL Criteria

- reads are not recorded
- sensitive reads are indistinguishable from ordinary reads
- full file content is stored by default
- dashboard-data crashes
- explain crashes
- existing os.system or subprocess tests regress
- Electron / Renderer or release artifacts are modified