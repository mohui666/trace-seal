# Stage 4 Rust Guard Design

## Status

Design phase only. Not implemented in v0.3.0. This document is an RFC-level productization sketch, not an implementation commitment.

The reviewable breakdown, contracts, milestones, and open decisions are tracked in [`stage4-rust-guard-rfc.md`](stage4-rust-guard-rfc.md).

The M1 review disposition is recorded in the RFC's **RFC Review Notes**: schema and dry-run flow come first, while Rust prototypes and enforcement remain blocked by their required reviews.

## Background

TraceSeal v0.3.0 completed the Python Core and Desktop evidence pipeline. Stage 4 explores a Rust Guard for lower-level monitoring and stronger enforcement while preserving the existing Python Core contracts.

## Goals

- OS-level process monitoring.
- Cross-language Agent support.
- Stronger policy enforcement.
- Tamper-resistant audit trail.
- Safer command, file, and network mediation.
- Enterprise deployment path.

## Non-goals

- Not replacing Python Core immediately.
- No Rust implementation in this PR.
- No kernel driver in the initial design.
- No cloud service dependency.
- No Electron UI rewrite.
- No installer redesign in this PR.

## Architecture sketch

1. **Python Core** remains the reference implementation for event normalization, policy semantics, replay, explain, and dashboard-data.
2. **Rust Guard daemon / sidecar** observes supported OS activity and exposes an explicit, versioned local interface.
3. **Event collector** normalizes Guard observations into the existing event schema where possible and assigns stable identity, ordering, and timestamps.
4. **Policy decision interface** evaluates an event before enforcement when the OS and operation permit mediation; otherwise it records a post-observation decision.
5. **Audit log writer** appends integrity-protected local records with explicit durability and rotation behavior.
6. **Desktop dashboard bridge** makes Guard health and normalized events available through the existing Core/dashboard-data boundary rather than coupling the UI directly to the daemon.

The intended trust boundary places OS observation and enforcement in the Guard, policy compatibility and evidence interpretation in the Core, and presentation in the Desktop layer.

## Event model

Candidate event types:

- `process.spawn`
- `file.read`
- `file.write`
- `file.delete`
- `network.connect`
- `network.http`
- `git.operation`
- `policy.decision`
- `guard.health`

Each event should carry a schema version, stable event ID, source, monotonic ordering data, wall-clock timestamp, process identity, redacted operation metadata, policy result, and integrity metadata. Sensitive file content, credentials, full HTTP bodies, and raw secrets must remain excluded by default.

## Policy boundary

The Guard should consume a compiled, versioned policy snapshot produced through the existing Core rather than independently redefining policy semantics.

- `default_policy.json` remains the compatibility fallback and baseline.
- The `policy.yaml` DSL remains the workspace-facing authoring format; the Core validates and compiles it for the Guard.
- Domain policy decisions reuse normalized host classification and redaction rules.
- Git push classification continues to distinguish normal, force, force-with-lease, mirror, delete, refspec, all, and tags operations.
- Cascade detection remains an evidence-layer aggregation over normalized events rather than an OS interception primitive.

Every decision should record the policy version, matched rule, action, reason, and whether it was enforced, observed only, or failed open/closed.

## Compatibility strategy

- Keep Python Core as the reference implementation.
- Add Rust Guard behind an explicit feature flag, disabled by default during early milestones.
- Reuse the existing event schema where possible and version intentional extensions.
- Do not break existing v0.3 `runs/` layouts or `dashboard-data` consumers.
- Support mixed runs where Python hooks and Guard events are deduplicated using stable correlation metadata.
- Preserve local-only/offline operation.

## Security model

### Privilege boundaries

Run with the minimum OS privileges needed for each enabled capability. Privileged collection or enforcement components must be isolated from unprivileged Core and Desktop clients, with authenticated local IPC and strict message validation.

### Tamper resistance and audit integrity

Use append-only records, hash chaining, authenticated checkpoints, explicit key ownership, and detectable log truncation. Tamper evidence must not be described as tamper prevention unless the deployment actually provides protected storage and process isolation.

### Offline-first operation

Collection, policy decisions, health reporting, and audit verification must work without network access. No hidden telemetry, cloud lookup, or remote policy dependency is permitted.

### Clear failure modes

The Guard must expose startup, degraded, dropped-event, policy-stale, log-write, and shutdown states. Each mediated operation class must define fail-open or fail-closed behavior explicitly; silent fallback is not acceptable.

## Risks and open questions

- How should Windows service privileges and per-user/session visibility be divided?
- Which macOS Endpoint Security and Linux audit/eBPF capabilities can reach practical parity?
- What code-signing, notarization, and enterprise trust requirements apply per platform?
- How much installer and upgrade complexity is acceptable before Guard availability is stable?
- What event volume, latency, storage, and CPU overhead budgets are required?
- How will duplicate signals and false positives be calibrated across Python hooks and OS observation?
- How can OS-level enforcement tests remain isolated, reversible, and safe in CI and local development?
- Which actions can be synchronously mediated on each platform, and which can only be observed?
- How are policy snapshots authenticated, rolled back, and recovered if invalid?

## Milestones

1. Stage 4 design RFC.
2. Rust prototype event emitter.
3. Python Core bridge.
4. Local-only process/file monitoring.
5. Policy decision dry-run.
6. Enforcement experiment.
7. Desktop dashboard integration.
8. Release candidate.

Each milestone requires separate review and acceptance criteria. This document does not authorize starting Rust implementation.
