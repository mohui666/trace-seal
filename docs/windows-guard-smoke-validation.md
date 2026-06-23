# Windows Guard Smoke Validation

## Status and scope

- **Milestone:** Stage 4 M8 / Issue #38
- **Surface:** Windows VM or Windows local machine smoke validation
- **Script:** `scripts/windows-guard-smoke.ps1`
- **Release status:** validation only; this is not a v0.3.1 release and does not change the v0.3.0 tag or GitHub Release

Issue #38 closes the Windows smoke-validation loop for the Stage 4 Guard prototype. The smoke verifies that the current local-only Guard pieces run together on Windows:

- Rust `guard.health` emission;
- Rust `process.spawn` dry-run emission;
- Python import of Guard events;
- Guard policy dry-run decisions;
- `dashboard-data` Guard metadata and policy summary;
- Renderer and Electron regression checks when Node dependencies are available.

This validation does **not** add Guard features. It does not implement enforcement, a daemon/service, OS-wide process monitoring, file monitoring, network monitoring, Git monitoring, an Electron UI change, an installer workflow change, a tag, or a release.

In short: no enforcement, no daemon/service, no target command execution, and no release mutation.

## Prerequisites

Run on a Windows VM or Windows local machine with:

- PowerShell;
- Git;
- Python available as `python`;
- Rust toolchain with `cargo` and `rustc`;
- Node/npm for full Renderer/Electron checks.

No administrator privileges are required. The script does not install a service, register a daemon, write system directories, or download dependencies. It only invokes the dependencies already available in the checkout.

## Run commands

Full smoke:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows-guard-smoke.ps1
```

If Node/Electron dependencies are intentionally unavailable:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows-guard-smoke.ps1 -SkipNode -SkipElectron
```

To inspect generated local artifacts after a pass:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows-guard-smoke.ps1 -KeepArtifacts
```

The script supports PowerShell `-Verbose` for command discovery details.

## What the smoke validates

The script creates an ignored local run under `runs/windows-guard-smoke/`, emits Guard events into a JSONL file, imports them into a synthetic TraceSeal run, evaluates policy in dry-run mode, and exports `dashboard-data`.

Validation points:

1. `guard.health` emits schema-valid `guard.event.v1` JSONL.
2. `process.spawn` emits schema-valid metadata with `metadata.dry_run=true` and `metadata.executed=false`.
3. The Python importer attaches `guard.health` and `process.spawn` events without merging them into `events.jsonl`.
4. Guard policy evaluation writes a dry-run sidecar with `enforcement_applied=false`.
5. `dashboard-data` exposes `guard.available=true`, Guard event types, and a Guard policy summary.
6. `cargo fmt --check`, `cargo test`, Python `compileall`, Python unittest discovery, and `git diff --check` pass.
7. Renderer tests/typecheck/build and Electron tests/typecheck run when not skipped.

## Target command non-execution sentinel

The `process.spawn` dry-run event records a target command that would create:

```text
runs/windows-guard-smoke/should_not_exist.txt
```

The Guard prototype must treat that command as event metadata only. After the dry-run event is emitted, the script fails immediately if the sentinel exists:

```text
target command was executed unexpectedly
```

Expected result:

- `target command executed: no`;
- `sentinel absent: yes`;
- `process.spawn` metadata still reports `dry_run=true` and `executed=false`.

## Safety guarantees

- No `process.spawn` target command execution.
- No enforcement or blocking path.
- `enforcement_applied=false` in Guard policy summary and dashboard-data.
- No daemon or service installation.
- No administrator requirement.
- No OS-wide monitoring surface.
- No file/network/Git monitoring added.
- No Electron UI redesign.
- No installer or release workflow change.
- No new tag, no v0.3.1 release, and no v0.3.0 Release mutation.

## Output and cleanup

Generated smoke artifacts live under:

```text
runs/windows-guard-smoke/
```

`runs/` is ignored by Git. The default successful run removes the smoke directory after printing a summary. Use `-KeepArtifacts` to keep artifacts for inspection. Failure retains artifacts for debugging. These artifacts must not be committed.

The summary includes:

- PASS / FAIL;
- Rust test status and count when detectable;
- Python unittest status and count when detectable;
- Renderer/Electron status;
- target command executed: `no`;
- sentinel absent: `yes`;
- enforcement: `no`;
- daemon/service: `no`;
- artifacts committed: `no`.

## Troubleshooting

| Symptom | Check |
|---|---|
| `running scripts is disabled` | Use `powershell -ExecutionPolicy Bypass -File scripts/windows-guard-smoke.ps1`. |
| `required command not found on PATH: python` | Install Python or ensure the existing interpreter is on PATH as `python`. |
| `required command not found on PATH: cargo` / `rustc` | Install or activate the Rust toolchain before running the smoke. |
| Node checks fail because dependencies are missing | Install dependencies in `desktop/renderer` and `desktop/electron`, or run a scoped smoke with `-SkipNode -SkipElectron` and record that limitation. |
| Sentinel file exists | Treat as a hard failure: the target command executed unexpectedly and the Guard dry-run contract is broken. |
| Guard policy summary shows `enforcement_applied=true` | Treat as a hard failure: Issue #38 validation must remain non-enforcing. |

## Current limitations

This smoke is not:

- enforcement validation;
- OS-wide monitoring validation;
- daemon/service validation;
- installer validation;
- release validation;
- a productized Guard release.

Issue #39 remains a separate, not-started enforcement RFC. It must not be implemented as part of this smoke validation.
