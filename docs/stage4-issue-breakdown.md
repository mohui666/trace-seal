# Stage 4 Issue Breakdown

## Status

- **Status:** Planning / issue breakdown
- **Scope:** Project management only
- **Implementation:** No Rust implementation in this PR
- **Stage:** Stage 4 remains design-first
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
| M1 | [Stage 4 RFC review](https://github.com/mohui666/trace-seal/issues/31) | Merged RFC | Review notes documented; closes on merge |
| M2 | [Define Guard event schema contract](https://github.com/mohui666/trace-seal/issues/32) | M1 | Ready for schema design after M1 merges |
| M3 | [Prototype Rust `guard.health` event emitter](https://github.com/mohui666/trace-seal/issues/33) | M2 | Blocked by M2 |
| M4 | [Emit `process.spawn` dry-run events](https://github.com/mohui666/trace-seal/issues/34) | M2, M3 | Blocked by M2/M3 |
| M5 | [Import Guard events into Python Core](https://github.com/mohui666/trace-seal/issues/35) | M2; fixtures from M3/M4 | Blocked by schema contract |
| M6 | [Expose Guard metadata in `dashboard-data`](https://github.com/mohui666/trace-seal/issues/36) | M2, M5 | Blocked by Python import |
| M7 | [Integrate policy dry-run decisions for Guard events](https://github.com/mohui666/trace-seal/issues/37) | M2, M5 | Blocked by schema/import |
| M8 | [Windows VM smoke validation for Guard prototype](https://github.com/mohui666/trace-seal/issues/38) | M3–M7 | Blocked by MVP integration |
| M9 | [Draft enforcement experiment RFC](https://github.com/mohui666/trace-seal/issues/39) | M1, M7, M8 | Blocked until observe/dry-run evidence exists |

## M1 review disposition

The M1 document review resolves the initial boundary questions as follows:

- The MVP is user-mode, workspace-scoped, observation-only, dry-run, fail-open, and offline-first.
- Python Core remains the reference implementation and remains usable without a Guard.
- M2 is the next milestone and defines the versioned schema contract plus compatibility fixtures.
- M3 and M4 cannot begin before M2 is reviewed and approved.
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

### Title

Emit process.spawn dry-run events

### Goal

Extend the Rust Guard prototype to emit `process.spawn` dry-run events without enforcement.

### Scope

- Observe supported process command metadata.
- Include PID and parent PID where the platform source provides them.
- Include redacted working directory and command-line metadata.
- Emit structured, versioned events with Guard/session correlation.
- Report capability gaps and dropped events explicitly.
- Keep observation in dry-run mode only.

### Non-goals

- No blocking.
- No process injection.
- No kernel driver.
- No system daemon requirement.
- No claim of complete process coverage.

### Acceptance criteria

- [ ] `process.spawn` event shape matches the M2 schema.
- [ ] Events can be imported into the Python Core contract-test flow.
- [ ] Command and path redaction behavior is tested.
- [ ] Unsafe commands are observed but not blocked.
- [ ] Tests run offline and do not launch destructive commands.

### Validation

- Use harmless local child processes with deterministic arguments.
- Verify PID/parent PID, cwd, ordering, redaction, and session correlation where available.
- Verify degraded capability/error metadata when observation is unavailable.
- Confirm no external network, real Git push, or destructive system action occurs.

### Dependencies

- M2 schema contract approved.
- M3 Guard lifecycle and `guard.health` prototype available.

### Suggested labels

`stage4`, `process`, `dry-run`

---

## M5 — Import Guard events into Python Core

### Title

Import Guard events into Python Core

### Goal

Allow Python Core to import future Rust Guard event artifacts without breaking existing v0.3.0 runs.

### Scope

- Define the local artifact or IPC import path.
- Validate schema version and required fields.
- Handle absent Guard metadata as a normal Python-only run.
- Merge accepted Guard events into the run timeline with deterministic ordering.
- Define duplicate/correlation behavior between Python hooks and Guard events.
- Report invalid or unsupported events safely without corrupting the run.

### Non-goals

- No Rust changes.
- No enforcement.
- No UI redesign.
- No mandatory Guard dependency for Python Core.

### Acceptance criteria

- [ ] Python Core can load valid Guard events when present.
- [ ] Old runs without Guard events continue to work unchanged.
- [ ] Replay and explain do not crash with absent, valid, invalid, or unsupported Guard metadata.
- [ ] Schema validation errors are isolated and reported safely.
- [ ] Event ordering and deduplication rules are covered by contract tests.

### Validation

- Run Python unit and contract tests against M2 golden fixtures.
- Run replay, explain, and `dashboard-data` over old and Guard-enabled fixture runs.
- Test truncated, malformed, unsupported-version, duplicate, and out-of-order inputs.
- Confirm no real Rust process or external service is required for fixture tests.

### Dependencies

- M2 schema contract approved.
- Representative fixtures from M3 and M4.

### Suggested labels

`stage4`, `python-core`, `compatibility`

---

## M6 — Expose Guard metadata in dashboard-data

### Title

Expose Guard metadata in dashboard-data

### Goal

Expose optional Guard metadata in `dashboard-data` while keeping existing dashboard consumers compatible.

### Scope

- Include an optional Guard summary.
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

- [ ] `dashboard-data` works with unchanged v0.3.0 runs.
- [ ] `dashboard-data` works with valid optional Guard metadata.
- [ ] Missing Guard metadata is represented as unavailable/absent without error.
- [ ] Existing consumers can ignore new optional fields.
- [ ] Renderer and Electron contract tests remain green.

### Validation

- Run dashboard-data tests over old, Guard-enabled, malformed, and degraded fixtures.
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

### Title

Integrate policy dry-run decisions for Guard events

### Goal

Map Guard events into existing policy decision logic in dry-run mode.

### Scope

- Reuse `policy/default_policy.json`.
- Reuse the workspace `policy.yaml` DSL where current fields map safely.
- Map supported process, file, and network fields into existing decision inputs.
- Emit `policy.decision` metadata with rule, reason, action, mode, and `enforced: false`.
- Expose dry-run decisions through replay, explain, and `dashboard-data`.
- Preserve current domain policy, Git classification, and cascade semantics.

### Non-goals

- No blocking.
- No new policy language.
- No domain policy rewrite.
- No Git classification rewrite.
- No enforcement or fail-closed path.

### Acceptance criteria

- [ ] Supported Guard events receive deterministic policy decisions.
- [ ] Dry-run decisions appear in replay, explain, and `dashboard-data`.
- [ ] Every decision clearly states that it was not enforced.
- [ ] Existing policy behavior remains unchanged for Python-only events/runs.
- [ ] Missing or invalid YAML falls back safely to the current JSON behavior.

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

### Title

Windows VM smoke validation for Guard prototype

### Goal

Validate the minimal Guard prototype in a clean Windows VM without requiring admin-only behavior.

### Scope

- Use a clean supported Windows environment.
- Validate local user-mode, dry-run execution.
- Validate `guard.health` and `process.spawn` dry-run events.
- Validate the Python import path and optional dashboard-data metadata.
- Exercise offline startup, shutdown, error, and degraded-capability behavior.
- Document permissions, performance observations, and known limitations.

### Non-goals

- No installer signing.
- No kernel driver.
- No service installation.
- No enforcement.
- No real network traffic or destructive system actions.

### Acceptance criteria

- [ ] The prototype runs in a clean Windows VM.
- [ ] Health and harmless process events are generated and schema-valid.
- [ ] Events import into Python Core and remain visible in the intended outputs.
- [ ] MVP does not rely on undocumented administrator-only assumptions, or any blocker is explicitly documented.
- [ ] Known limitations, capability gaps, event loss, and cleanup steps are documented.

### Validation

- Run a documented non-admin smoke script in a resettable Windows VM.
- Use harmless local child processes only.
- Verify no external network, real Git push, system-service install, or system-directory mutation.
- Capture versions, permissions, expected artifacts, checksums, and cleanup evidence.

### Dependencies

- M3 through M7 MVP components and contract tests complete.
- A disposable Windows VM baseline and reproducible smoke procedure.

### Suggested labels

`stage4`, `windows`, `validation`

---

## M9 — Draft enforcement experiment RFC

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

### Non-goals

- No enforcement implementation.
- No blocking behavior in the current milestone.
- No kernel driver commitment.
- No default fail-closed mode.

### Acceptance criteria

- [ ] A separate enforcement experiment RFC exists.
- [ ] Risks, bypasses, races, and unsupported operations are documented.
- [ ] Failure modes and operation-specific fail-open/fail-closed choices are explicit.
- [ ] User recovery and rollback plans are reviewable.
- [ ] Implementation remains blocked until RFC approval.

### Validation

- Review the RFC against M8 evidence and documented capability gaps.
- Threat-model termination, privilege failure, IPC failure, event loss, and partial enforcement.
- Verify proposed experiments are reversible, sandboxed, and do not target real user/system data.
- Confirm no enforcement source code is included with the RFC.

### Dependencies

- M1 boundary review complete.
- M7 policy dry-run evidence available.
- M8 Windows VM smoke results and limitations documented.

### Suggested labels

`stage4`, `enforcement`, `rfc`

## Tracking notes

- Issue #28 remains the post-release umbrella for Stage 4 requirements and release-health follow-up.
- GitHub issues #31–#39 mirror the nine drafts and carry the implementation/review lifecycle.
- Milestone state must remain planning/design until the corresponding issue is separately implemented and validated.
