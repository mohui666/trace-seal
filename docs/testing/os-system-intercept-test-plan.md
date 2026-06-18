# os.system Interception Test Plan

## Goal

Validate TraceSeal's Python Core interception of `os.system()` calls.

## Scope

This plan covers Python-level `os.system()` interception only.

## Non-goals

- No file read tracking
- No httpx interception
- No Electron / Renderer feature testing
- No Rust Guard
- No OS-level process monitoring
- No v0.2.0 release artifact changes

## Test Matrix

### 1. Allow mode

Expected behavior:

- `os.system()` executes normally
- exit code is preserved or behavior is documented
- trace event is recorded
- command string is recorded
- dashboard-data includes the event
- existing subprocess interception still works

Evidence to collect:

- command used
- return code
- run_id
- event excerpt
- dashboard-data excerpt

### 2. Warn mode

Expected behavior:

- command executes
- risk is recorded
- policy action is `warn`
- explain can identify the risky event
- first harmful event points to the `os.system()` event when appropriate

Evidence to collect:

- policy rule
- risk level
- action
- explain output excerpt

### 3. Block / deny mode

Expected behavior:

- dangerous command does not execute
- protected test file remains intact
- event is recorded
- policy action is `block` or `deny`
- return behavior is documented
- no real user directory is modified

Evidence to collect:

- protected file before / after
- event excerpt
- policy action
- return code or raised exception behavior

### 4. Dangerous command patterns

Cover at least:

- `rm -rf`
- `del`
- `rmdir`
- recursive delete
- shell command touching workspace files
- command with spaces
- command with Unicode path

### 5. Cross-platform behavior

Windows:

- `cmd /c echo`
- `del`
- `rmdir /s /q`
- path with spaces
- Unicode path

Unix-like:

- `echo`
- `rm -rf`
- `sh -c`
- path with spaces
- Unicode path

### 6. Failure behavior

Cover:

- non-zero exit code
- invalid command
- command unavailable
- policy file missing, if existing Core supports this case
- malformed policy file, if existing tests cover this case

### 7. Integration commands

Required manual commands:

```powershell
python -m unittest discover -s tests -v
python -m traceseal run -- python examples\bad_agent_os_system.py
python -m traceseal dashboard-data runs/latest
python -m traceseal explain runs/latest
```

### 8. Regression checks

Confirm:

- subprocess interception still works
- existing dashboard-data tests still pass
- existing replay / explain tests still pass
- renderer contract is unchanged
- Electron / Renderer files are untouched
- v0.2.0 tag and Release artifacts are untouched

## PASS Criteria

- All existing Python tests pass
- New os.system tests pass
- allow / warn / block behavior is covered
- dashboard-data contains os.system event
- explain identifies risky os.system event
- no real user files are damaged
- no Electron / Renderer changes are introduced

## FAIL Criteria

- dangerous block/deny command still executes
- command is not recorded
- policy action is missing
- dashboard-data cannot export the event
- explain crashes
- subprocess regression appears
- v0.2.0 release artifacts are changed