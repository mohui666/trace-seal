# Stage 4 Rust Guard RFC

## Status

- **Status:** Draft RFC
- **Scope:** Design only
- **Implementation:** No implementation in this PR
- **Compatibility baseline:** TraceSeal v0.3.0
- **Latest released version:** v0.3.0

Stage 4 does not immediately replace the Python Core. This RFC defines reviewable boundaries and contracts for future work; it does not add a Rust crate, daemon, enforcement path, Electron change, installer change, tag, or release.

Related planning is tracked in [issue #28](https://github.com/mohui666/trace-seal/issues/28).

## 1. Summary

Stage 4 proposes extending TraceSeal from the Python Core SDK/hook model toward a lower-level, local Rust Guard sidecar. The Guard would provide a common observation surface for Agents written in Python and other languages, with stronger visibility into process, file, network, and Git operations.

The first implementation milestone would be observation-only. It would establish a local event producer and compatibility bridge, not a universal security boundary. Future enforcement can build on the same policy decision and audit contracts only after a separate review.

The design preserves the current evidence pipeline:

- normalized events remain associated with a TraceSeal run;
- existing `events.jsonl` and `manifest.json` fields remain readable;
- `dashboard-data` continues to be the Desktop data boundary;
- replay remains transcript replay and does not re-execute side effects;
- explain continues to identify policy decisions and harmful events;
- Guard metadata is additive and optional.

## 2. Motivation

TraceSeal v0.3.0 completes the Stage 3 Python Core. Its SDK, `sitecustomize`, and monkey-patch hooks provide useful evidence for Python Agents, but that interception layer does not naturally observe Node.js, Go, Rust, shell-only, or other Agent processes.

Stage 4 is motivated by five gaps:

1. **Cross-language coverage.** A local process-level observer can provide a shared event source without requiring equivalent hooks in every Agent runtime.
2. **Observation closer to the OS boundary.** High-risk process, file, and connection activity may happen below or outside Python APIs.
3. **Audit integrity.** Enterprise deployments need detectable log mutation, truncation, or deletion rather than only writable JSONL artifacts.
4. **Stronger policy boundaries.** Post-event recording is insufficient for operations that may eventually require an explicit allow, warn, or deny decision.
5. **Long-running local reliability.** Rust is a candidate for a memory-safe, low-overhead sidecar with explicit resource and failure handling.

These motivations do not prove that every event can be intercepted in user mode. Platform feasibility must be validated before any enforcement claim is made.

## 3. Non-goals

- Do not implement Rust Guard in this PR.
- Do not immediately replace the Python Core.
- Do not add a kernel driver in the initial design or MVP.
- Do not introduce a cloud service, remote policy lookup, hidden telemetry, or online activation dependency.
- Do not rewrite the Electron UI.
- Do not modify the v0.3.0 tag, GitHub Release, assets, or installer.
- Do not claim mandatory interception of all OS behavior.
- Do not promise macOS/Linux completion on the Windows schedule.
- Do not redesign the existing installer or release workflow in this RFC.
- Do not change the v0.3.0 run format or make Guard metadata mandatory.

## 4. Architecture

### 4.1 Layers and responsibilities

1. **Python Core — reference implementation**
   - Owns run lifecycle, current event semantics, policy authoring/validation, manifest generation, replay, explain, and `dashboard-data`.
   - Accepts optional normalized Guard events through a versioned bridge.
   - Remains fully usable when the Guard is unavailable or disabled.

2. **Rust Guard — local sidecar / daemon**
   - Owns supported platform observation and Guard health reporting.
   - Emits candidate events; it does not reinterpret the entire TraceSeal run.
   - MVP runs in user mode and observation-only mode.

3. **Event Collector**
   - Converts platform-specific observations into a versioned TraceSeal event envelope.
   - Correlates process identity, parent identity, workspace, run, source, and ordering metadata.
   - Applies redaction before events cross into durable audit storage.

4. **Policy Decision Interface**
   - Receives a validated/compiled snapshot derived from existing TraceSeal policy sources.
   - Produces stable decision metadata for observe, warn, or future enforce flows.
   - Does not invent a second user-facing policy language.

5. **Audit Log Writer**
   - Appends structured records and integrity metadata.
   - Reports write failures, dropped events, and chain discontinuities explicitly.
   - Does not claim tamper prevention when only tamper evidence is available.

6. **Desktop Bridge**
   - Exposes Guard availability, health, and optional event metadata through Python Core and `dashboard-data`.
   - Keeps Electron isolated from privileged or platform-specific Guard APIs.
   - Requires no UI rewrite for the contract milestone.

7. **Replay / Explain Bridge**
   - Maps Guard events and decisions into the existing transcript and explanation model.
   - Preserves behavior for runs without Guard data.
   - Makes observation-only versus enforced decisions explicit.

### 4.2 Trust and data boundaries

- OS-specific collection stays inside the Guard boundary.
- Policy authoring and validation stay in the Python Core boundary.
- Durable evidence contains normalized, redacted metadata rather than raw file or HTTP bodies.
- Electron consumes `dashboard-data`; it does not trust or control the Guard directly.
- Local IPC must be authenticated, versioned, length-bounded, and reject malformed messages.
- Run/workspace association is explicit metadata, never inferred solely from display names.

## 5. Process Model

| Model | Advantages | Limitations | RFC position |
|---|---|---|---|
| User-mode sidecar | Least privilege, tied to one TraceSeal session, easy shutdown and log ownership | Cannot observe every OS event; Agent may terminate it | **Recommended MVP** |
| Workspace-scoped guard | Clear evidence boundary, simpler run correlation, lower noise | Multiple workspaces need multiple instances or multiplexing | Use with MVP sidecar |
| CLI-started guard | Explicit lifecycle and failure reporting; suitable for tests | Coverage ends with CLI/session lifecycle | Primary MVP startup path |
| Dashboard-started guard | Convenient for desktop users | Couples lifecycle to Desktop availability; must not grant Electron privilege | Optional after CLI contract |
| Background daemon/service | Wider coverage and centralized health | Installation, privilege, upgrades, signing, and multi-user complexity | Long-term option only |

The MVP recommendation is a user-mode, workspace-scoped sidecar started explicitly by the CLI. The sidecar receives a generated run/session identifier and canonical workspace path, reports `guard.health`, and exits with the owning session. It is not installed as a system service and does not require administrator privileges by design.

The Dashboard may later request startup through a narrow Python Core command, but it must not launch or communicate with a privileged process directly. A persistent background daemon requires a separate lifecycle and threat-model RFC.

## 6. Event Schema

### 6.1 Compatibility principles

- Reuse v0.3.0 event, manifest, and `dashboard-data` fields when semantics match.
- Add Guard data under optional, versioned fields.
- Do not rename or change the type of existing required fields.
- Preserve deterministic event ordering with the current `seq` behavior; Guard-local monotonic ordering is additional evidence.
- Preserve current redaction rules and never store raw credentials, full sensitive files, or full HTTP bodies by default.
- Unknown event types and unknown optional fields must be ignored safely by older readers.

### 6.2 Candidate event envelope

| Field | Type | Requirement | Meaning |
|---|---|---|---|
| `event_id` | string | Required | Stable unique event identifier |
| `timestamp` | RFC 3339 string | Required | Wall-clock observation time |
| `seq` | integer | Required after Core import | Run-local deterministic order |
| `event_type` | string | Required | Normalized event type |
| `source` | string | Required | For example `python_hook` or `rust_guard` |
| `schema_version` | string | Required for Guard events | Event contract version |
| `run_id` | string | Required after association | Owning TraceSeal run |
| `pid` | integer | Optional | Observed process ID |
| `parent_pid` | integer | Optional | Observed parent process ID |
| `process_name` | string | Optional | Redacted executable/process display name |
| `command_line` | string or object | Optional | Redacted command metadata |
| `cwd` | string | Optional | Normalized/redacted working directory |
| `workspace` | string | Optional | Canonical or tokenized workspace identity |
| `target` | object | Optional | Operation-specific target metadata |
| `risk_level` | string | Optional | Existing risk scale when evaluated |
| `policy_rule_id` | string | Optional | Matched existing policy rule |
| `decision` | string | Optional | `observe`, `allow`, `warn`, or future `deny` |
| `redaction_status` | object | Required for sensitive classes | Fields redacted, omitted, or hashed |
| `guard` | object | Optional | Guard version, session, local sequence, and health context |

`command_line`, paths, URLs, and targets require the same sensitivity review as current event inputs. The schema must permit structured redaction instead of relying on a single free-form string.

### 6.3 Candidate event types

| Event type | Minimum candidate metadata | Notes |
|---|---|---|
| `process.spawn` | child PID, parent PID, executable, redacted command, cwd | Observation-only in MVP |
| `process.exit` | PID, exit code/status, duration when known | Must tolerate missing spawn |
| `file.read` | PID, normalized path/target, success, size when known | No file content |
| `file.write` | PID, normalized path/target, success, size delta when known | No file content |
| `file.delete` | PID, normalized path/target, success | Workspace relation is explicit |
| `file.rename` | PID, redacted source and destination, success | Same-volume assumptions prohibited |
| `network.connect` | PID, protocol, redacted host/IP class, port, result | No payload capture |
| `network.http` | PID, method, redacted URL/host, result when observable | User-mode feasibility varies; no bodies |
| `git.operation` | PID, push classification, remote label, refs, simulation/observation status | Reuse v0.3.0 Git classification |
| `policy.decision` | subject event ID, rule ID, mode, decision, reason | Must say dry-run or enforced |
| `guard.health` | session, version, capability set, state, dropped count | First prototype contract |
| `guard.error` | session, error class/code, operation, recoverability | Must not include secrets |

### 6.4 Manifest and dashboard additions

Candidate additions are optional:

- `manifest.guard.present`
- `manifest.guard.schema_version`
- `manifest.guard.mode`
- `manifest.guard.health_summary`
- `manifest.guard.event_count`
- `manifest.guard.integrity_summary`
- `dashboard-data.guard`
- per-event `source`, `schema_version`, `guard`, and decision metadata

The final names require M2 schema contract approval. This RFC does not modify the v0.3.0 schema.

## 7. Policy Integration

Rust Guard must not redefine TraceSeal policy syntax or maintain an incompatible rule engine.

- `policy/default_policy.json` remains the fallback baseline.
- Workspace `policy.yaml` remains the authoring DSL.
- Python Core validates policy, resolves precedence, and produces a versioned decision snapshot for the Guard.
- Domain allow/deny/warn behavior reuses normalized host classification and redaction rules.
- Git push classification reuses normal, force, force-with-lease, mirror, delete, forced refspec, `--all`, and `--tags` distinctions.
- Cascade detection remains a Core evidence aggregation over ordered normalized events, not a Guard interception primitive.

MVP policy integration is dry-run only. The Guard or bridge emits `policy.decision` records containing the subject event, policy snapshot/version, matched rule ID, action, reason, mode, and `enforced: false`. These decisions must appear consistently in replay, explain, and `dashboard-data`.

Policy snapshot transfer must define authentication, expiry, rollback, unsupported rule behavior, and stale-policy behavior before enforcement is considered.

## 8. Enforcement Modes

| Mode | Behavior | MVP status |
|---|---|---|
| `observe` | Record normalized events and health; no user notification or blocking | Required |
| `warn` | Record the event and decision, then surface a warning without blocking | Contract/dry-run only |
| `enforce` | Attempt to block a supported operation and record the outcome | Not in MVP |

The MVP operates in `observe` with policy dry-run metadata. A policy action such as deny may be reported as the decision that *would* apply, but the record must explicitly state that no block was attempted.

Enforcement requires a separate RFC covering platform capability, race conditions, authorization, user recovery, fail-open/fail-closed rules, bypasses, and safe test procedures. No generic claim that all OS behavior can be blocked is acceptable.

## 9. Audit Integrity

The candidate integrity design is:

1. Write records to an append-only logical stream.
2. Canonicalize each redacted event before hashing.
3. Store a per-event content hash.
4. Chain each record to the previous accepted record hash.
5. Store final chain head, count, schema version, and error/drop summary in the run manifest.
6. Produce checksums for Guard-specific artifacts alongside existing release/run evidence conventions.
7. Consider signing chain checkpoints as future work after key ownership and rotation are designed.

The design detects mutation, reordering, and truncation only when a trusted checkpoint is retained. A user-mode process cannot guarantee that local logs are undeletable. Documentation and UI must distinguish **tamper-evident** from **tamper-proof**.

Canonical serialization, hash algorithm agility, crash recovery, partial records, rotation, and concurrent writers must be decided in the M2 schema contract.

## 10. Security Model

### Privilege boundary

MVP runs without administrator privileges and observes only events visible to the current user/session and selected platform APIs. IPC peers must be authenticated locally, scoped to the owning user and session, and unable to submit arbitrary privileged requests.

### User-mode limitations

A user-mode sidecar can be terminated, bypassed, starved, raced, or deprived of visibility. It must report degraded capabilities and event drops rather than imply complete coverage.

### Tamper and spoofing risks

- An Agent may terminate or suspend the Guard.
- Process IDs can be reused; correlation should include start time and platform identity where available.
- Process names and command lines are untrusted metadata and may be spoofed.
- An Agent may delete or rewrite local audit files if filesystem permissions allow it.
- Local IPC messages may be replayed or forged without per-session authentication and ordering.

### Offline-first requirement

Observation, dry-run decisions, audit writing, integrity verification, replay, explain, and health reporting must work with no network access. No hidden telemetry, remote lookup, cloud policy, or online account is required.

### Failure behavior

The MVP defaults to **fail-open**: if the Guard fails, the Agent operation continues and Python Core records a clear `guard.error` or missing/degraded health state when possible. This avoids damaging user systems during an observation-only prototype.

Any future fail-closed behavior must be opt-in, operation-specific, recoverable, tested on the target platform, and approved in the enforcement RFC. Silent fallback is never acceptable.

## 11. Platform Strategy

### Windows first

Windows is the first design and validation target because v0.3.0 already has a Windows x64 desktop release. Initial research must compare user-mode process and file observation sources, event completeness, latency, required privileges, process identity, and behavior across user sessions.

Windows constraints include:

- the current installer is unsigned;
- a future Guard binary/service may increase code-signing and SmartScreen requirements;
- APIs may require privileges unavailable to a normal user;
- process observation and file operation observation may need different sources;
- MVP does not add a kernel driver;
- no capability is considered supported until Windows VM validation reproduces it.

This RFC does not select or implement a Windows API.

### macOS later

macOS work requires a separate capability assessment covering permissions, entitlements, notarization, Endpoint Security availability, user consent, and packaging. It is not promised on the Windows timeline.

### Linux later

Linux work requires a separate capability assessment across distributions, kernels, audit/eBPF availability, capabilities, namespaces, packaging, and container environments. It is not promised on the Windows timeline.

Cross-platform parity is a goal to evaluate, not a current commitment.

## 12. Compatibility

- v0.3.0 run directories and required fields remain unchanged.
- `dashboard-data` must continue reading old runs with no Guard fields.
- replay and explain must treat absent Guard metadata as a normal legacy/Python-only run.
- Guard metadata is optional, versioned, and ignored safely when unsupported.
- Python Core can run, record, replay, explain, and export dashboard data without a Guard binary.
- Mixed Python-hook and Guard events require a documented deduplication/correlation strategy before import is enabled.
- Unsupported Guard event versions produce explicit compatibility metadata rather than corrupting or rejecting the entire run.
- Existing privacy/redaction behavior is the minimum baseline; Guard collection must not widen stored content by default.

M2 must provide golden v0.3.0 fixtures and prove that new readers preserve their current output before a prototype bridge is merged.

## 13. Testing Strategy

Future implementation work must use layered tests:

1. **Rust unit tests:** serialization, redaction, ordering, hashing, error mapping, and capability reporting.
2. **Python contract tests:** Guard import and bridge behavior against versioned fixtures.
3. **Schema compatibility tests:** old readers/fixtures and optional-field behavior.
4. **Golden run tests:** deterministic expected `events.jsonl`, manifest, dashboard, replay, and explain outputs.
5. **Offline demo tests:** all prototypes work without external services.
6. **No real network tests:** network observations use local servers or mocks and prove no external connection.
7. **No real Git push tests:** Git operations use simulation or isolated local repositories with no remote transport.
8. **Destructive-operation sandbox tests:** writes, renames, and deletes are confined to disposable copied workspaces.
9. **Windows VM smoke tests:** lifecycle, permissions, non-admin behavior, dropped-event reporting, clean removal, and restart behavior.

All dangerous demos must be sandboxed, mocked, or simulated. Tests must not depend on real credentials, external targets, production repositories, system directories, or persistent privileged services.

Performance tests should measure event loss, end-to-end latency, CPU, memory, and audit growth under defined workloads. Results must include capability gaps rather than only pass/fail labels.

## 14. MVP Milestones

| Milestone | Deliverable | Exit criteria |
|---|---|---|
| M1: RFC review | Approved design boundaries and recorded decisions | Review checklist resolved; no implementation implied |
| M2: Event schema contract | Versioned envelope, fixtures, compatibility rules | Golden v0.3.0 runs remain readable |
| M3: `guard.health` prototype | Rust prototype emits health only | Local, user-mode, offline lifecycle validated |
| M4: `process.spawn` dry-run | Prototype emits redacted observation events | No blocking; capability and drop reporting tested |
| M5: Python Core import | Core imports versioned Guard fixtures/events | Python-only mode remains unchanged |
| M6: Dashboard bridge | `dashboard-data` exposes optional Guard metadata | Old runs and current Desktop contract remain valid |
| M7: Policy dry-run | Existing policy produces non-enforced decisions | Replay/explain/dashboard show rule and dry-run status |
| M8: Windows VM smoke | Non-admin Windows lifecycle and evidence smoke test | Documented pass/fail with limitations |
| M9: Enforcement experiment RFC | Separate proposal for limited enforcement | No enforcement code in MVP |

Each milestone is a separate reviewable change. Completion of one milestone does not authorize later milestones automatically.

## 15. Open Questions

1. How does the Guard reliably associate events with a canonical workspace and TraceSeal run?
2. What happens when the workspace moves, is deleted, uses symlinks, or contains nested repositories?
3. How should insufficient permissions be reported without hiding missing coverage?
4. Does any MVP capability require administrator privileges, and can it be deferred instead?
5. Which Windows user-mode sources provide acceptable process event coverage?
6. Which Windows sources can observe file operations with usable attribution and acceptable overhead?
7. When is code signing required for prototype, installer, service, or enterprise deployment?
8. How are duplicate Python-hook and Guard observations correlated without suppressing distinct events?
9. How are false positives measured, explained, and corrected without weakening high-risk rules globally?
10. What CPU, memory, latency, storage, and dropped-event budgets are acceptable?
11. How is schema versioning negotiated across Guard, Python Core, persisted runs, and Desktop readers?
12. How are canonical serialization and hash algorithm upgrades handled?
13. If future enforcement fails, which operations fail open and which, if any, may fail closed?
14. Can enterprise mode use different privilege, retention, and signing policies while local mode remains simple and offline?
15. How are Guard upgrades, crash recovery, audit rotation, and clean uninstallation proven safe?
16. Which platform gaps are acceptable without claiming cross-platform parity?

## 16. Review Checklist

- [ ] The proposal remains design-only.
- [ ] No Rust implementation, crate, daemon, service, or kernel component is added.
- [ ] v0.3.0 remains the latest released version and its tag/assets are untouched.
- [ ] Existing v0.3.0 event, manifest, and `dashboard-data` semantics are reused where applicable.
- [ ] Old runs remain readable by dashboard-data, replay, and explain.
- [ ] Python Core remains the reference implementation and works independently.
- [ ] Guard metadata is additive, optional, versioned, and redacted.
- [ ] The RFC does not promise unvalidated macOS/Linux parity.
- [ ] No cloud or hidden network dependency is introduced.
- [ ] MVP is user-mode, observation-only, dry-run, and fail-open.
- [ ] Privilege, spoofing, tamper, deletion, event-loss, and IPC boundaries are explicit.
- [ ] Dangerous future tests are constrained to mocks, simulations, local servers, disposable workspaces, and Windows VMs.
- [ ] Enforcement remains a separate RFC and is not implemented in the MVP.
