# Guard `process.spawn` Dry-Run Prototype

## Status and scope

- **Milestone:** Stage 4 M4 / Issue #34
- **Status:** Local-only prototype
- **Schema:** `guard.event.v1`
- **Mode:** `observe` / dry-run only
- **Target execution:** Never
- **Python Core import:** Not included; Issue #35 remains separate

This prototype extends the one-shot Rust Guard CLI with a `process-spawn` command. It records an intent to start a program as one JSON Lines event, but it never invokes the program or observes operating-system process activity.

## Run the emitter

From the repository root:

```powershell
cargo run -p traceseal-guard -- process-spawn `
  --out runs/guard-process-spawn.jsonl `
  --workspace . `
  --program python `
  --arg examples/bad_agent_delete.py
```

Optional flags:

- repeat `--arg <value>` to record additional target arguments;
- use `--cwd <path>` to record the intended target working directory (the current directory is the default);
- use `--pretty` to format stdout without changing the compact JSONL record.

The CLI creates the output directory when needed and appends exactly one UTF-8 JSON object plus a newline. Generated `runs/` artifacts are ignored and must not be committed.

## Event semantics

The event contains:

- `event_type: "process.spawn"`;
- `risk_level: "info"`;
- `policy.decision: "observe"`;
- `guard.mode: "observe"` and `guard.status: "ok"`;
- the target program, redacted command-line array, and intended cwd in `process`;
- `process.pid: null` and `process.parent_pid: null`, because no target process exists;
- `metadata.dry_run: true` and `metadata.executed: false`;
- `metadata.message: "process.spawn dry-run event emitted"`.

The prototype redacts common key/value and flag forms for tokens, passwords, secrets, authorization values, cookies, and API/client credentials before persistence. For example, `--arg token=secret` is stored as `token=<redacted>`, and the affected command-line field is listed in `redaction.fields`.

No environment variables are captured. The emitter does not scan the workspace or read target files.

## Python validation

The artifact can be checked independently without importing it into a TraceSeal run:

```python
from traceseal.guard_schema import (
    load_guard_events,
    validate_guard_process_spawn_event,
)

events = load_guard_events("runs/guard-process-spawn.jsonl")
for event in events:
    validate_guard_process_spawn_event(event)
```

`validate_guard_process_spawn_event` verifies the common envelope, required process fields, observe-only policy, redaction shape, and the explicit dry-run/non-execution metadata. Missing Guard artifacts remain valid for old Python-only runs.

## Limitations and non-goals

- No target command execution or child-process launch.
- No OS-wide process monitoring or complete process coverage claim.
- No file, network, or Git monitoring.
- No daemon, service, administrator privilege, injection, or kernel driver.
- No policy enforcement or blocking.
- No recorder, replay, explain, dashboard-data, Electron, installer, or release integration.
- No Stage 4 release; this remains a local prototype.
