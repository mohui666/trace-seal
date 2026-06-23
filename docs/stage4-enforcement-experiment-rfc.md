# Stage 4 Enforcement Experiment RFC

## Status

- **Status:** Draft
- **Scope:** Documentation-only RFC
- **Milestone:** Stage 4 M9 / Issue #39
- **Current behavior:** Dry-run / observe-only
- **Implementation:** No implementation in this PR
- **Release status:** No tag, release, installer, or workflow change

TraceSeal remains dry-run / observe-only for the Stage 4 Guard prototype. This RFC defines reviewable boundaries for a future opt-in enforcement experiment. It does not implement enforcement, does not change runtime behavior, and does not modify v0.3.0 or any release asset.

## Background

Stage 4 has progressed through the observe-only Guard prototype milestones:

- Guard event schema contract;
- Rust `guard.health` prototype;
- `process.spawn` dry-run event;
- Guard events imported into Python Core;
- Guard metadata exposed in `dashboard-data`;
- Guard policy dry-run decisions with `enforcement_applied=false`;
- Windows VM / Windows local smoke validation.

Issue #39 exists to define the boundary for a future controlled enforcement experiment after observe/dry-run evidence is available. The goal is to make any future enforcement work explicitly gated, reversible, auditable, and opt-in before any implementation is considered.

This RFC does not alter the current prototype. Existing `guard.health`, `process.spawn` dry-run, Python import, policy dry-run, dashboard-data, Renderer, Electron, installer, release, and tag behavior remains unchanged.

## Goals

- Define a staged path from dry-run / observe-only evidence to a future opt-in enforcement experiment.
- Make enforcement a future experiment only, never a default behavior.
- Require explicit local user consent before an experiment can begin.
- Define auditability requirements for every dry-run, would-block, blocked, allowed, rollback, and kill-switch decision.
- Define rollback and kill-switch requirements that can disable the experiment without network access.
- Define stage gates that must be satisfied before and during any experiment.
- Require that an experiment is observable, reversible, and locally disableable at every step.
- Define safety boundaries that avoid false blocking, silent breakage, irreversible user-environment changes, and monitoring-scope expansion.

## Non-goals

- This RFC does not implement enforcement.
- This RFC does not block `process.spawn`.
- This RFC does not execute the `process.spawn` target command.
- This RFC does not add a daemon or service.
- This RFC does not add OS-wide process monitoring.
- This RFC does not add file, network, or Git monitoring.
- This RFC does not change Rust Guard behavior.
- This RFC does not change Python policy behavior.
- This RFC does not change the Electron UI.
- This RFC does not change installer or release workflows.
- This RFC does not create a new tag or release.
- This RFC does not add a kernel driver, privileged installer component, startup item, background resident process, or fail-closed default mode.
- This RFC does not expand the current Stage 4 event set beyond the existing documented prototype events.

## Proposed experiment model

The future experiment model is intentionally conservative:

1. **Default mode remains observe-only / dry-run.** Existing users and runs continue to produce metadata only.
2. **Enforcement requires explicit opt-in.** The opt-in must be local, revocable, and auditable.
3. **The experiment is locally scoped.** Initial scope is limited to a controlled local demo or test fixture with no real user data, no third-party target operation, and no system-wide monitoring.
4. **The configured subject is explicit.** Each experiment must name the workspace, operation class, policy source, supported command pattern, and rollback plan before it can run.
5. **Every decision is traceable.** Each decision record must include event identity, policy identity, reason, mode, timestamp, subject command metadata, and whether the decision was dry-run, would-block, blocked, allowed, rolled back, or kill-switched.
6. **Fallback to dry-run is mandatory.** Unsupported operations, stale configuration, missing consent, validation failure, Guard degradation, or kill-switch activation must return to dry-run / observe-only.
7. **No silent enforcement.** The user must be able to tell when an experiment is enabled, what scope it covers, and how to disable it.

The experiment may only mediate a narrowly reviewed operation class after a separate implementation plan demonstrates that the operation can be safely intercepted, audited, and rolled back. A policy action such as `deny` is not enough to justify blocking. The system must also prove that the target operation is in scope, the user opted in, and the kill switch is not active.

## Stage gates

Each gate must include entry criteria, exit criteria, and stop conditions. Failing a stop condition returns the project to dry-run / observe-only until the issue is reviewed.

### Gate 0: RFC accepted

- **Entry criteria:** Stage 4 observe/dry-run milestones through Windows smoke validation are documented.
- **Exit criteria:** The enforcement experiment RFC is reviewed and accepted as a documentation boundary.
- **Stop condition:** The RFC implies current enforcement, weakens non-goals, or omits rollback, kill switch, user consent, or audit requirements.

### Gate 1: Dry-run telemetry stable

- **Entry criteria:** Guard events and policy dry-run metadata are stable across local and Windows smoke runs.
- **Exit criteria:** Dry-run decision records are deterministic enough to replay and compare without executing target commands.
- **Stop condition:** Event identity, policy source, decision reason, or `enforcement_applied=false` evidence is missing or ambiguous.

### Gate 2: Policy decision audit coverage

- **Entry criteria:** Policy dry-run decisions include enough context to explain would-block versus allow outcomes.
- **Exit criteria:** A reviewer can trace every decision to event, policy, rule, reason, mode, and timestamp without reading sensitive payloads.
- **Stop condition:** Audit records leak unnecessary sensitive data, cannot distinguish dry-run from blocked behavior, or fail to record unsupported operations.

### Gate 3: Explicit user consent UX / config design reviewed

- **Entry criteria:** A proposed consent mechanism exists as a reviewed design, not as hidden defaults.
- **Exit criteria:** Consent is explicit, local, visible, revocable, and scoped to a named experiment.
- **Stop condition:** Consent can be inherited silently, enabled by an installer, enabled by a remote update, or hidden in an unrelated config.

### Gate 4: Kill switch and rollback validated

- **Entry criteria:** A local kill switch and rollback plan are specified before implementation.
- **Exit criteria:** The system can prove that kill-switch activation and rollback return to dry-run / observe-only and leave no enforcement side effect.
- **Stop condition:** Kill switch depends on network access, policy evaluation, remote service availability, or a background daemon that may already be unhealthy.

### Gate 5: Controlled local experiment only

- **Entry criteria:** A local fixture, sentinel, and expected audit output are reviewed.
- **Exit criteria:** The experiment runs only inside the approved local scope and records blocked/allowed/would-block decisions accurately.
- **Stop condition:** The experiment targets real user data, third-party systems, system directories, production credentials, or any command outside the reviewed fixture.

### Gate 6: Post-experiment review before broader rollout

- **Entry criteria:** Controlled experiment evidence, failures, rollback logs, and audit samples are available.
- **Exit criteria:** Reviewers explicitly decide whether to continue, revise, or stop; no broader rollout is automatic.
- **Stop condition:** False positives, rollback gaps, audit leaks, kill-switch gaps, user confusion, or scope creep remain unresolved.

## Safety boundaries

Any future experiment must preserve these boundaries:

- No OS-wide monitoring.
- No background daemon.
- No silent interception.
- No upload of command content, sensitive paths, credentials, or policy context.
- No default enforcement.
- No blocking of commands outside the explicit experiment scope.
- No irreversible modification to real user environments.
- No bypass of the operating-system permission model.
- No third-party target operation.
- No persistent resident behavior.
- No installer-time enablement.
- No release-time behavior change.
- No automatic expansion from one operation class to another.

Unsupported operations must fail open to dry-run / observe-only with an auditable reason. The project must not claim generic OS enforcement unless each operation class is separately demonstrated and reviewed.

## Kill switch

The future experiment requires a kill switch with these properties:

- A global local kill switch disables enforcement experiment behavior.
- The kill switch has higher priority than all policy decisions.
- The kill switch works without network access.
- The kill switch takes effect locally and predictably.
- Activating the kill switch returns the system to dry-run / observe-only.
- Kill-switch activation, reason, timestamp, and resulting mode are audited.
- Kill-switch state is visible enough for a user to confirm that enforcement is disabled.
- Failure to read kill-switch state is treated as disabled enforcement, not fail-closed enforcement.

Policy cannot override the kill switch. A deny rule cannot block when the kill switch is active.

## Audit

Every decision must produce an auditable record. The audit model must distinguish:

- `dry-run`: a decision was evaluated but not enforced;
- `would-block`: policy would block if the experiment were active, but no block occurred;
- `blocked`: an in-scope experimental operation was actually blocked;
- `allowed`: an in-scope experimental operation was allowed;
- `rollback`: the experiment was reverted to dry-run / observe-only;
- `kill-switch`: enforcement experiment behavior was disabled by kill switch.

Audit records must include decision ID, event ID, event type, policy source, rule ID if matched, reason, mode, timestamp, subject command metadata, experiment scope ID, and the effective enforcement state. Audit records must avoid unnecessary sensitive content and should prefer redacted command metadata consistent with the existing Guard event and dashboard-data direction.

This RFC does not change the current Guard event schema or dashboard-data implementation. Any future audit schema change must be proposed separately and remain backward compatible with old runs.

## Rollback

Rollback is mandatory for the future experiment:

- The rollback path returns the system to dry-run / observe-only.
- Rollback must be available locally without network access.
- Rollback must be auditable with timestamp, previous mode, new mode, and reason.
- Rollback must not leave enforcement side effects, background processes, service state, startup entries, or modified installer state.
- Rollback must be verifiable by a local command or documented check.
- Incomplete rollback is a stop condition for the experiment.

Rollback is not the same as allowing the next operation. It must also prove that the experiment can no longer block later operations until explicitly re-enabled with consent.

## User consent

The future experiment requires explicit user consent:

- Enforcement experiment mode is default off.
- A user must explicitly enable it for a named local experiment.
- The user must see the operation class, workspace, policy source, possible impact, rollback path, and kill-switch path before enabling.
- Consent must be revocable.
- Consent must not be hidden in unrelated config, installed silently, inherited from a release, enabled through a tag, or activated by a remote service.
- Consent state must be auditable.
- Consent expiration should be considered for experiments that run longer than a single local validation session.

If consent is missing, malformed, expired, or out of scope, the system must stay in dry-run / observe-only.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| False positive blocking | Start with local fixtures only, require explicit scope, preserve dry-run fallback, and review every blocked sample. |
| Data loss or task interruption | Do not target real user data; require rollback validation and user-visible stop controls before any block. |
| User misunderstands enforcement scope | Display exact experiment scope, operation class, and current mode before enabling; audit consent. |
| Monitoring scope grows beyond review | Treat each new operation class as a separate RFC/design review with its own gates. |
| Audit leaks sensitive information | Store redacted metadata only; avoid command bodies, credentials, full paths when not necessary. |
| Kill switch fails | Make kill-switch failure fail open to dry-run / observe-only and require offline local verification. |
| Rollback is incomplete | Treat incomplete rollback as a stop condition; validate no service, daemon, startup item, or installer state remains. |
| Release or installer unexpectedly changes behavior | Keep experiments out of release workflows and require explicit review before any installer or release behavior changes. |
| Race condition or unsupported platform behavior | Block only operation classes with demonstrated mediation capability; unsupported cases remain dry-run. |
| Policy ambiguity | Record policy source, matched rule, reason, and effective mode for each decision. |

## Validation plan

Future validation should happen in documentation and dry-run first:

- Documentation static checks for non-goals and safety boundaries.
- Dry-run test fixtures that replay policy decisions without executing target commands.
- Policy decision replay to compare expected would-block / allow decisions.
- Local-only experiment fixtures with no real user data.
- Sentinel checks proving target command execution remains controlled and never happens during dry-run.
- Kill-switch verification that returns to dry-run / observe-only without network access.
- Rollback verification that leaves no enforcement side effect.
- Audit completeness checks for dry-run, would-block, blocked, allowed, rollback, and kill-switch records.

This plan does not authorize implementation. It defines review criteria for future work.

## Out of scope for current PR

This PR only adds and links documentation plus a documentation check. It does not change runtime behavior, Rust Guard behavior, Python policy behavior, Electron UI, installer workflows, release workflows, tags, GitHub Releases, or release assets.

The current system remains dry-run / observe-only. Issue #39 closes when this RFC is merged, but future enforcement work remains blocked until a separate implementation proposal satisfies the gates above.
