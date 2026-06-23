# Stage 4 Issue Breakdown

## Status

- **Status:** Complete through Issue #39; completion audit tracked by Issue #50
- **Scope:** Project management plus milestone acceptance status
- **Implementation:** Stage 4 dry-run / observe-only deliverables are complete; no productized Guard
- **Stage:** Stage 4 complete; future Stage 5 candidates are planning-only
- **Latest released version:** v0.3.0

This document converts the approved Stage 4 RFC structure into reviewable work items. It does not authorize implementation automatically: each milestone remains subject to its dependencies, acceptance criteria, review, and the design boundaries in [`stage4-rust-guard-rfc.md`](stage4-rust-guard-rfc.md).

## Planning principles

- Python Core remains the reference implementation and must continue to run without Guard metadata.
- v0.3.0 run artifacts, replay, explain, and `dashboard-data` remain the compatibility baseline.
- Observation and policy dry-run precede enforcement.
- Dangerous tests must remain offline, mocked, simulated, or confined to disposable workspaces/VMs.
- Windows is the first validation target; macOS/Linux parity is not promised.
- Issue completion does not imply that a later dependent milestone may skip review.

## Milestone overview

| Milestone | Issue draft | Depends on | Planning state |
|---|---|---|---|
| M1 | [Stage 4 RFC review](https://github.com/mohui666/trace-seal/issues/31) | Merged RFC | Completed and merged |
| M2 | [Define Guard event schema contract](https://github.com/mohui666/trace-seal/issues/32) | M1 | [Draft contract](guard-event-schema-contract.md) completed and merged |
| M3 | [Prototype Rust `guard.health` event emitter](https://github.com/mohui666/trace-seal/issues/33) | M2 | Completed and merged; local-only health emitter only |
| M4 | [Emit `process.spawn` dry-run events](https://github.com/mohui666/trace-seal/issues/34) | M2, M3 | [Local-only intent prototype implemented](guard-process-spawn-dry-run.md); no target execution or OS monitoring |
| M5 | [Import Guard events into Python Core](https://github.com/mohui666/trace-seal/issues/35) | M2; fixtures from M3/M4 | [Optional local import implemented](guard-event-import.md); Python timeline remains separate |
| M6 | [Expose Guard metadata in `dashboard-data`](https://github.com/mohui666/trace-seal/issues/36) | M2, M5 | [Additive Guard data contract implemented](dashboard-guard-metadata.md); no UI change |
| M7 | [Integrate policy dry-run decisions for Guard events](https://github.com/mohui666/trace-seal/issues/37) | M2, M5 | [Dry-run sidecar implemented](guard-policy-dry-run.md); no enforcement |
| M8 | [Windows VM smoke validation for Guard prototype](https://github.com/mohui666/trace-seal/issues/38) | M3–M7 | Windows smoke script and validation doc implemented; no enforcement |
| M9 | [Draft enforcement experiment RFC](https://github.com/mohui666/trace-seal/issues/39) | M1, M7, M8 | [Draft enforcement experiment RFC](stage4-enforcement-experiment-rfc.md) added; documentation only |
| Audit | [Stage 4 completion audit and roadmap cleanup](https://github.com/mohui666/trace-seal/issues/50) | M1-M9 | [Completion report](../artifacts/stage4-completion-report.md) and Stage 5 planning references added; documentation only |

## M1 review disposition

The M1 document review resolves the initial boundary questions as follows:

- The MVP is user-mode, workspace-scoped, observation-only, dry-run, fail-open, and offline-first.
- Python Core remains the reference implementation and remains usable without a Guard.
- M2 is the next milestone and defines the versioned schema contract plus compatibility fixtures.
- M3 and M4 required M2 review and approval before implementation; that prerequisite was satisfied before their prototype work.
- v0.3.0 runs, `dashboard-data`, replay, and explain must remain backward compatible.
- Enforcement remains blocked until a separate RFC is approved after observe/dry-run validation.
- Windows API selection, IPC transport, signing, service packaging, other platforms, and enforcement details remain deferred to their owning milestones.

Full accepted assumptions, deferred decisions, risks, and M2 prerequisites are recorded in the RFC's [`RFC Review Notes`](stage4-rust-guard-rfc.md#rfc-review-notes). This disposition is a documentation decision, not an implementation milestone.

---

## M1 — Stage 4 RFC review

### Title

Stage 4 RFC review

### Goal

Review the Stage 4 Rust Guard RFC and resolve design-level ambiguities before implementation starts.

### Scope

- Review architecture boundaries.
- Confirm the user-mode, workspace-scoped MVP process model.
- Confirm design-only and observation-first assumptions.
- Triage open questions and identify blockers for the first Rust prototype.
- Record accepted decisions and deferred questions in the RFC or linked decision notes.

### Non-goals

- No Rust code.
- No Python Core changes.
- No enforcement implementation.
- No Electron, installer, tag, or release changes.

### Acceptance criteria

- [ ] RFC review comments are resolved or explicitly deferred with owners/reasons.
- [ ] MVP boundary and process model are agreed.
- [ ] Open questions are triaged by milestone.
- [ ] Blocking security and compatibility decisions are identified.
- [ ] M2 is unblocked or its remaining blockers are explicit.

### Validation

- Review the RFC checklist line by line.
- Confirm v0.3.0 remains the compatibility and release baseline.
- Confirm no implementation files are included in the review change.
- Record reviewer decisions and unresolved risks in GitHub.

### Dependencies

- Merged [`stage4-rust-guard-rfc.md`](stage4-rust-guard-rfc.md).
- Tracking context from issue #28.

### Suggested labels

`stage4`, `rfc`, `design`

---

## M2 — Define Guard event schema contract

### Title

Define Guard event schema contract

### Goal

Define a versioned event schema contract for future Rust Guard events while preserving compatibility with v0.3.0 run artifacts.

Draft contract: [`guard-event-schema-contract.md`](guard-event-schema-contract.md). The draft does not complete M2 until reviewed and merged, and it does not unblock M3 before approval.

### Scope

- Define `event_id`, `timestamp`, `pid`, `parent_pid`, `process_name`, `command_line`, `cwd`, and `workspace`.
- Define `event_type`, `target`, `risk_level`, `policy_rule_id`, `decision`, and `redaction_status`.
- Define optional versioned Guard metadata and source/correlation fields.
- Specify schema versioning, unknown-field behavior, ordering, redaction, and validation errors.
- Specify additive manifest and `dashboard-data` metadata without changing required v0.3.0 fields.

### Non-goals

- No Rust implementation.
- No dashboard UI change.
- No enforcement.
- No migration that rewrites existing runs.

### Acceptance criteria

- [ ] A reviewable schema draft exists with required/optional field types.
- [ ] Schema versioning and compatibility strategy are documented.
- [ ] Golden v0.3.0 fixtures remain valid and readable.
- [ ] Replay/explain fallback behavior for missing or unknown Guard metadata is documented.
- [ ] Redaction requirements cover commands, paths, URLs, and sensitive targets.

### Validation

- Run schema examples against representative v0.3.0 events and manifests.
- Test old-run fixtures with the current `dashboard-data`, replay, and explain readers.
- Review malformed, unsupported-version, missing-field, and unknown-field cases.
- Confirm examples contain no credentials, real network targets, or raw sensitive content.

### Dependencies

- M1 RFC review complete.
- Existing v0.3.0 event, manifest, replay, explain, and `dashboard-data` contracts.

### Suggested labels

`stage4`, `schema`, `compatibility`

---

## M3 — Prototype Rust guard.health event emitter

### Title

Prototype Rust guard.health event emitter

### Goal

Create the first minimal Rust Guard prototype that emits `guard.health` events only.

Prototype documentation: [`guard-health-prototype.md`](guard-health-prototype.md). This milestone does not start M4 or authorize any process/file/network/Git observation.

### Scope

- Create a minimal Rust project only when this issue is implemented later.
- Emit `guard.health` as structured JSON matching the approved schema.
- Report version, session, capabilities, state, and dropped-event count where defined.
- Keep execution local, user-mode, offline, and explicitly dry-run.
- Provide a narrow Python-side fixture reader or validator for the emitted health event.

### Non-goals

- No daemon installation.
- No OS-level hooks.
- No administrator requirement.
- No dashboard UI redesign.
- No process, file, network, Git, or enforcement observation.

### Acceptance criteria

- [ ] A `guard.health` event can be generated locally.
- [ ] The event matches the approved M2 schema contract.
- [ ] Python-side validation can read the event in dry-run mode.
- [ ] Startup, normal shutdown, and an error/degraded state are testable.
- [ ] The prototype performs no network access.

### Validation

- Run Rust unit tests introduced by the future prototype.
- Validate emitted JSON with schema contract fixtures.
- Prove offline execution with no external service dependency.
- Confirm a non-admin user can execute the MVP path or document the blocker.

### Dependencies

- M2 event schema contract approved.
- M1 process model and security boundary decisions.

### Suggested labels

`stage4`, `rust`, `prototype`

---

## M4 — Emit process.spawn dry-run events

**Prototype status:** Implemented as a local-only, non-executing intent emitter for Issue #34. This is not OS-level observation. See [`guard-process-spawn-dry-run.md`](guard-process-spawn-dry-run.md).

### Title

Emit process.spawn dry-run events

### Goal

Extend the Rust Guard prototype to emit `process.spawn` dry-run events without enforcement.

### Scope

- Record caller-supplied target process command metadata without launching it.
- Emit null PID and parent PID because the dry-run creates no target process.
- Include redacted working directory and command-line metadata.
- Emit structured, versioned events with Guard/session correlation.
- Mark the event explicitly as `dry_run: true` and `executed: false`.
- Keep observation in dry-run mode only.

### Non-goals

- No blocking.
- No process injection.
- No kernel driver.
- No system daemon requirement.
- No claim of complete process coverage.

### Acceptance criteria

- [x] `process.spawn` event shape matches the M2 schema.
- [x] Events can be loaded and validated by the Python contract-test helper without run import.
- [x] Command and path field behavior plus sensitive argument redaction are tested.
- [x] Unsafe target intent is recorded but never executed or blocked.
- [x] Tests run offline and do not launch target or destructive commands.

### Validation

- Use deterministic command intent strings; do not launch a child process.
- Verify null PID/parent PID, cwd, argument ordering, redaction, and explicit non-execution metadata.
- Verify the emitter makes no OS observation or complete-coverage claim.
- Confirm no external network, real Git push, or destructive system action occurs.

### Dependencies

- M2 schema contract approved.
- M3 Guard lifecycle and `guard.health` prototype available.

### Suggested labels

`stage4`, `process`, `dry-run`

---

## M5 — Import Guard events into Python Core

**Implementation status:** Optional local artifact import is implemented for Issue #35. Dashboard output and policy decisions remain separate milestones. See [`guard-event-import.md`](guard-event-import.md).

### Title

Import Guard events into Python Core

### Goal

Allow Python Core to import future Rust Guard event artifacts without breaking existing v0.3.0 runs.

### Scope

- Define the local `guard_events.jsonl` artifact import path.
- Validate schema version and required fields.
- Handle absent Guard metadata as a normal Python-only run.
- Preserve Guard source order in a separate artifact; do not merge it into `events.jsonl`.
- Reject duplicate Guard event IDs; defer Python/Guard cross-source correlation.
- Report invalid or unsupported events safely without corrupting the run.

### Non-goals

- No Rust changes.
- No enforcement.
- No UI redesign.
- No mandatory Guard dependency for Python Core.

### Acceptance criteria

- [x] Python Core can load valid Guard events when present.
- [x] Old runs without Guard events continue to work unchanged.
- [x] Replay and explain do not crash with absent, valid, invalid, or unsupported optional Guard metadata.
- [x] Schema validation errors are isolated before run modification and reported safely.
- [x] Source-order preservation and duplicate-ID rejection are covered by contract tests.

### Validation

- Run Python unit and contract tests against M2/M3/M4 fixtures.
- Run replay, explain, and unchanged `dashboard-data` over old and Guard-enabled fixture runs.
- Test malformed, unsupported-version, duplicate, out-of-order, mismatched-run, and unknown-type inputs.
- Confirm fixture tests execute no recorded target and require no Rust process or external service.

### Dependencies

- M2 schema contract approved.
- Representative fixtures from M3 and M4.

### Suggested labels

`stage4`, `python-core`, `compatibility`

---

## M6 — Expose Guard metadata in dashboard-data

**Implementation status:** Run-level `dashboard-data` exposes an additive, compact Guard summary for Issue #36. Renderer/Electron UI remains unchanged. See [`dashboard-guard-metadata.md`](dashboard-guard-metadata.md).

### Title

Expose Guard metadata in dashboard-data

### Goal

Expose optional Guard metadata in `dashboard-data` while keeping existing dashboard consumers compatible.

### Scope

- Include an additive Guard summary object.
- Include Guard event count and health status.
- Preserve all existing `dashboard-data` required fields and types.
- Document behavior when Guard metadata is absent, invalid, degraded, or unsupported.
- Keep Electron consumption through the existing Python CLI/preload boundary.

### Non-goals

- No Electron UI redesign.
- No new visual dashboard feature unless separately reviewed and necessary.
- No Rust implementation.
- No requirement that old runs synthesize Guard data.

### Acceptance criteria

- [x] `dashboard-data` works with unchanged v0.3.0 runs.
- [x] `dashboard-data` works with valid optional Guard metadata.
- [x] Missing Guard metadata is represented as unavailable without error.
- [x] Existing consumers can ignore the new additive field.
- [x] Renderer and Electron contract tests remain green without UI changes.

### Validation

- Run dashboard-data tests over old, Guard-enabled, malformed, and degraded events.
- Run Renderer and Electron contract/type tests without adding a UI redesign.
- Verify optional-field serialization and backwards-compatible defaults.
- Confirm no sensitive command/path content bypasses redaction.

### Dependencies

- M2 schema contract approved.
- M5 Python Core import path complete.

### Suggested labels

`stage4`, `dashboard-data`, `compatibility`

---

## M7 — Integrate policy dry-run decisions for Guard events

**Implementation status:** Guard policy dry-run metadata is implemented for Issue #37. It evaluates imported `guard.health` and `process.spawn` events against the existing policy DSL, writes a non-enforcing sidecar, and exposes a dashboard-data summary. It does not execute target commands, enforce, block, start a daemon/service, or add OS-wide/file/network/Git monitoring.

### Title

Integrate policy dry-run decisions for Guard events

### Goal

Map Guard events into existing policy decision logic in dry-run mode.

### Scope

- Reuse `policy/default_policy.json`.
- Reuse the workspace `policy.yaml` DSL where current fields map safely.
- Map supported process intent fields into existing decision inputs.
- Emit Guard policy sidecar metadata with rule, reason, action, dry-run mode, and `enforcement_applied: false`.
- Expose dry-run decisions through `dashboard-data`; replay and explain remain compatible and do not crash.
- Preserve current domain policy, Git classification, and cascade semantics.

### Non-goals

- No blocking.
- No new policy language.
- No domain policy rewrite.
- No Git classification rewrite.
- No enforcement or fail-closed path.

### Acceptance criteria

- [x] Supported Guard events receive deterministic policy decisions.
- [x] Dry-run decisions appear in `dashboard-data`; replay and explain compatibility is preserved.
- [x] Every decision clearly states that it was not enforced.
- [x] Existing policy behavior remains unchanged for Python-only events/runs.
- [x] Missing or invalid YAML is reported clearly or follows the existing discovery fallback when no explicit policy is supplied.

### Validation

- Run existing policy tests plus Guard fixture contract tests.
- Test allow, warn, deny/require-approval-as-dry-run, unmatched, and invalid-policy cases.
- Verify domain and Git classification regressions remain green.
- Confirm tests use local fixtures/mocks with no real network or Git push.

### Dependencies

- M2 schema contract approved.
- M5 Python Core import path complete.
- Existing v0.3.0 policy YAML/JSON fallback semantics.

### Suggested labels

`stage4`, `policy`, `dry-run`

---

## M8 — Windows VM smoke validation for Guard prototype

**Implementation status:** Windows smoke validation is implemented in [`scripts/windows-guard-smoke.ps1`](../scripts/windows-guard-smoke.ps1) and documented in [`docs/windows-guard-smoke-validation.md`](windows-guard-smoke-validation.md). It validates `guard.health`, `process.spawn` dry-run, Python import, Guard policy dry-run, and dashboard-data Guard metadata on Windows. The script includes a sentinel proving the `process.spawn` target command is not executed and verifies `enforcement_applied=false`. It does not add enforcement, daemon/service behavior, OS-wide process monitoring, file/network/Git monitoring, Electron UI changes, installer/release workflow changes, or any release/tag mutation.

### Title

Windows VM smoke validation for Guard prototype

### Goal

Validate the minimal Guard prototype in a clean Windows VM without requiring admin-only behavior.

### Scope

- Use a clean supported Windows environment.
- Validate local user-mode, dry-run execution.
- Validate `guard.health` and `process.spawn` dry-run events.
- Validate the Python import path, Guard policy dry-run sidecar, and optional dashboard-data metadata.
- Exercise offline startup, shutdown, error, and degraded-capability behavior.
- Document permissions, performance observations, and known limitations.

### Non-goals

- No installer signing.
- No kernel driver.
- No service installation.
- No enforcement.
- No daemon/service implementation.
- No OS-wide process monitoring.
- No file, network, or Git monitoring.
- No Electron UI or installer/release workflow change.
- No real network traffic or destructive system actions.

### Acceptance criteria

- [x] The prototype has a reproducible Windows smoke script.
- [x] Health and harmless process dry-run events are generated and schema-valid.
- [x] Events import into Python Core and remain visible in dashboard-data.
- [x] Guard policy dry-run summary remains non-enforcing with `enforcement_applied=false`.
- [x] The sentinel check proves the `process.spawn` target command is not executed.
- [x] MVP does not rely on undocumented administrator-only assumptions, or any blocker is explicitly documented.
- [x] Known limitations, capability gaps, event loss, and cleanup steps are documented.

### Validation

- Run `powershell -ExecutionPolicy Bypass -File scripts/windows-guard-smoke.ps1` in a resettable Windows VM or Windows local machine.
- If Node/Electron dependencies are intentionally unavailable, run `powershell -ExecutionPolicy Bypass -File scripts/windows-guard-smoke.ps1 -SkipNode -SkipElectron` and record that limitation.
- Use harmless local command metadata only; the target command must remain unexecuted.
- Verify no external network, real Git push, system-service install, or system-directory mutation.
- Capture versions, permissions, expected artifacts, sentinel evidence, `enforcement_applied=false`, and cleanup evidence.

### Dependencies

- M3 through M7 MVP components and contract tests complete.
- A disposable Windows VM baseline or Windows local machine and reproducible smoke procedure.

### Suggested labels

`stage4`, `windows`, `validation`

---

## M9 — Draft enforcement experiment RFC

**Documentation status:** The separate [`Stage 4 Enforcement Experiment RFC`](stage4-enforcement-experiment-rfc.md) defines the future opt-in experiment model, gates, kill switch, audit, rollback, user consent, risks, validation plan, and safety boundaries. It is documentation only and does not implement enforcement, block `process.spawn`, execute target commands, add daemon/service behavior, add OS-wide/file/network/Git monitoring, change Rust Guard behavior, change Python policy behavior, change Electron UI, change installer/release workflows, create a tag, or publish a release.

### Title

Draft enforcement experiment RFC

### Goal

Design a separate RFC for future enforcement modes after observe/dry-run mode is validated.

### Scope

- Define the observe/warn/enforce boundary per operation class.
- Define fail-open versus fail-closed behavior.
- Define user safety, recovery, and approval requirements.
- Define platform privilege and capability requirements.
- Define decision/audit evidence and attempted-versus-effective enforcement reporting.
- Define rollback, disable, crash recovery, and safe experiment plans.
- Define kill switch, explicit user consent, and local-only experiment gates.

### Non-goals

- No enforcement implementation.
- No blocking behavior in the current milestone.
- No `process.spawn` target command execution.
- No daemon/service implementation.
- No OS-wide process monitoring.
- No file, network, or Git monitoring.
- No Rust Guard behavior change.
- No Python policy behavior change.
- No Electron UI, installer, release workflow, tag, or release change.
- No kernel driver commitment.
- No default fail-closed mode.

### Acceptance criteria

- [x] A separate enforcement experiment RFC exists.
- [x] Risks, bypasses, races, and unsupported operations are documented.
- [x] Failure modes and operation-specific fail-open/fail-closed choices are explicit.
- [x] User recovery, rollback, kill switch, and consent plans are reviewable.
- [x] Implementation remains blocked until a future implementation RFC/PR satisfies the documented gates.

### Validation

- Review the RFC against M8 evidence and documented capability gaps.
- Threat-model termination, privilege failure, IPC failure, event loss, and partial enforcement.
- Verify proposed experiments are reversible, sandboxed, and do not target real user/system data.
- Confirm no enforcement source code is included with the RFC.
- Run documentation static checks for the RFC non-goals.

### Dependencies

- M1 boundary review complete.
- M7 policy dry-run evidence available.
- M8 Windows VM smoke results and limitations documented.

### Suggested labels

`stage4`, `enforcement`, `rfc`

## Tracking notes

- Issue #28 remains the post-release umbrella for Stage 4 requirements and release-health follow-up.
- GitHub issues #31–#39 are complete and mirror the nine Stage 4 review milestones.
- Issue #50 tracks the final Stage 4 completion audit and roadmap cleanup.
- Follow-up planning issues are #51 Slint desktop feasibility RFC, #52 Rust Core parity RFC, and #53 Slint hello dashboard spike.
- See [Stage 4 Completion Report](../artifacts/stage4-completion-report.md) for delivered capabilities, non-outcomes, release/tag integrity, and planning issue links.
- Milestone state must remain planning/design until the corresponding issue is separately implemented and validated.
