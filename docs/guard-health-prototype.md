# Rust Guard Health Prototype

## Status

- **Milestone:** Issue #33 / M3
- **Scope:** Minimal local-only `guard.health` prototype
- **Mode:** Observe / dry-run only
- **Schema:** `guard.event.v1`
- **Release status:** Prototype only; not included in v0.3.0 and not a Stage 4 release

## What it does

`traceseal-guard` is a one-shot CLI that emits one `guard.health` JSON object, appends the compact form to a requested JSONL file, prints the same event to stdout, and exits.

The event includes schema identity, a unique event ID, UTC RFC3339 timestamp, optional workspace/process context, `risk_level: info`, `policy.decision: observe`, `redaction.status: not_applicable`, Guard version/platform/status, and a health message.

The prototype uses no platform observation API. It does not scan the workspace, read sensitive files, access the network, start a child/background process, remain resident, or require administrator privileges.

## Run

From the repository root:

```powershell
cargo run -p traceseal-guard -- health --out runs/guard-health.jsonl --workspace .
```

Use `--pretty` to pretty-print stdout; the JSONL artifact remains one compact JSON object per line:

```powershell
cargo run -p traceseal-guard -- health --out runs/guard-health.jsonl --workspace . --pretty
```

The output directory is created when needed, and subsequent invocations append one line. The `runs/` path is ignored and must not be committed.

## Python validation

```powershell
@'
from traceseal.guard_schema import load_guard_events, validate_guard_health_event

events = load_guard_events("runs/guard-health.jsonl")
assert events, "no guard events loaded"
for event in events:
    validate_guard_health_event(event)
print("guard.health validation ok", len(events))
'@ | python -
```

`traceseal.guard_schema` provides:

- `load_guard_events(path)`: loads JSONL, skips empty lines, returns `[]` for a missing artifact, and reports line-numbered parse errors;
- `validate_guard_event(event)`: validates the common `guard.event.v1` envelope and enums;
- `validate_guard_health_event(event)`: validates the stricter `guard.health` prototype contract.

These helpers do not import Guard events into recorder, replay, explain, `dashboard-data`, or existing runs.

## Validation

```powershell
cargo fmt --check
cargo test
python -m unittest tests.test_guard_health_schema -v
```

The repository-wide Python suite remains the regression gate.

## Limitations and non-goals

- No `process.spawn` or `process.exit` observation.
- No file, network, HTTP, or Git monitoring.
- No policy enforcement, blocking, warn flow, or fail-closed behavior.
- No daemon, service, kernel driver, persistence, or administrator privilege.
- No automatic Guard artifact import into Python Core.
- No Electron UI or installer/release integration.
- No audit hash chain or signing.
- No macOS/Linux parity claim beyond portable CLI serialization.
