# Guard Event Schema Contract

## Status

- **Status:** Draft contract
- **Scope:** Stage 4 schema design
- **Implementation:** No Rust implementation in this PR
- **Core behavior:** No Core behavior change in this PR
- **Compatibility baseline:** TraceSeal v0.3.0
- **Initial schema version:** `guard.event.v1`
- **Intended next milestone:** [Issue #33 — `guard.health` prototype](https://github.com/mohui666/trace-seal/issues/33)

Issue #33 implements the first local-only emitter against this contract; see [`guard-health-prototype.md`](guard-health-prototype.md). The contract remains additive and does not authorize later event types or enforcement.

This document defines the proposed producer/consumer contract for future Guard events. It does not create an executable JSON Schema, Rust crate, Guard emitter, Python importer, dashboard integration, enforcement path, or release artifact.

The contract is additive. It does not replace the v0.3.0 `events.jsonl` schema, change existing run artifacts, or require a Guard to read an old run.

## 1. Contract goals

The contract must:

- give future Guard producers a stable, versioned event envelope;
- allow Python Core and other readers to validate Guard artifacts later;
- preserve v0.3.0 run, `dashboard-data`, replay, and explain behavior;
- make optional/nullable data and redaction state explicit;
- support unknown future fields and event types safely;
- start with `guard.health` only, followed by `process.spawn` dry-run work;
- avoid implying that observation or policy decisions are enforced.

## 2. Canonical event envelope

The following JSON object is the canonical `guard.event.v1` envelope example. It shows every top-level field, including optional/nullable fields.

```json
{
  "schema_version": "guard.event.v1",
  "event_id": "guard_evt_000001",
  "timestamp": "2026-06-22T00:00:00.000000Z",
  "source": "rust_guard",
  "event_type": "guard.health",
  "run_id": null,
  "workspace": null,
  "process": {
    "pid": null,
    "parent_pid": null,
    "process_name": null,
    "command_line": null,
    "cwd": null
  },
  "target": null,
  "risk_level": "info",
  "policy": {
    "decision": "observe",
    "rule_id": null,
    "reason": null
  },
  "redaction": {
    "status": "not_applicable",
    "fields": []
  },
  "guard": {
    "guard_version": null,
    "mode": "observe",
    "platform": null,
    "status": "ok"
  },
  "metadata": {}
}
```

JSON examples in this contract are illustrative contract fixtures. They do not prove that an emitter or reader exists.

## 3. Field contract

### 3.1 Required top-level fields

Every `guard.event.v1` record must contain these fields. A field is still required when its value is an object containing nullable subfields.

| Field | Type | Contract |
|---|---|---|
| `schema_version` | string | Must equal `guard.event.v1` for this contract. Readers use it to select validation and compatibility behavior. |
| `event_id` | string | Non-empty producer-assigned event identity. The recommended v1 form is `guard_evt_` followed by a unique token/sequence. It must be unique within the artifact and stable across retries. |
| `timestamp` | string | RFC 3339 UTC timestamp. Producers should emit a `Z` timestamp with sufficient precision to preserve observed ordering. |
| `source` | string | Producer identity. The first planned producer value is `rust_guard`; readers must not assume that it is the only future source. |
| `event_type` | string | Normalized event type. Unknown values are retained as generic events rather than crashing the run reader. |
| `risk_level` | string | One of the risk values defined in section 7. |
| `policy` | object | Required decision container with a required `decision` and nullable `rule_id`/`reason`. |
| `redaction` | object | Required redaction result with required `status` and `fields`. |
| `guard` | object | Required Guard context with required `mode` and `status`; version/platform may be unknown. |
| `metadata` | object | Required extension object. It may be empty. Event-specific optional data belongs here only when no normalized field exists. |

`process` is optional at the top level because lifecycle events such as `guard.health` do not describe an observed process. When present, it must be an object with the fields in section 3.3. `run_id`, `workspace`, and `target` are also optional/nullable.

### 3.2 Optional / nullable top-level fields

| Field | Type | Null/absence behavior |
|---|---|---|
| `run_id` | string or null | May be null/absent before association with a TraceSeal run. If stored under a run, a non-null value must match the containing run identity. |
| `workspace` | string or null | May be null/absent when no canonical workspace is known. Future values must already be normalized/redacted before persistence. |
| `process` | object or absent | May be absent when the event is not process-associated. If present, its known keys are nullable. |
| `target` | object/string/null | Event-specific redacted target. May be null/absent for `guard.health` and other targetless events. |

Missing optional fields must not make a run unreadable. Readers may normalize absence to `null` in an internal representation, but they must not rewrite existing artifacts merely to add optional fields.

### 3.3 Process object

When `process` is present, it uses this shape:

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `pid` | integer or null | Yes | Observed process ID. PID alone is not a durable process identity. |
| `parent_pid` | integer or null | Yes | Observed parent PID when available. |
| `process_name` | string or null | Yes | Redacted/normalized process or executable display name. |
| `command_line` | string/array/object or null | Yes | Redacted command metadata. A future schema revision may narrow the representation after platform research. |
| `cwd` | string or null | Yes | Redacted/normalized working directory when available. |

All five keys are recommended when a `process` object is emitted, even when values are null. A v1 reader must also tolerate a missing optional key. Negative PIDs are invalid; zero is platform-dependent and must not be invented when unknown.

### 3.4 Policy object

| Field | Type | Required | Nullable | Meaning |
|---|---|---|---|---|
| `decision` | string | Yes | No | Decision value from section 8. |
| `rule_id` | string or null | No | Yes | Existing/mapped TraceSeal rule identifier, if a rule matched. |
| `reason` | string or null | No | Yes | Redacted human-readable explanation. |

The policy object records a decision result, not proof of enforcement. During the Stage 4 MVP, decisions are observations/dry-run results and must not be interpreted as blocked operations.

### 3.5 Redaction object

| Field | Type | Required | Meaning |
|---|---|---|---|
| `status` | string | Yes | Redaction status from section 9. |
| `fields` | array of strings | Yes | JSON-style field paths that were redacted, partially handled, or could not be captured safely. Empty for `not_applicable`. |

If redaction fails for a sensitive field, the raw sensitive value must not be persisted as a fallback. The producer may omit the value and emit safe error metadata.

### 3.6 Guard object

| Field | Type | Required | Nullable | Meaning |
|---|---|---|---|---|
| `guard_version` | string or null | No | Yes | Producer version, for example `0.0.0-dev`. |
| `name` | string or null | No | Yes | Optional producer name. The Issue #33 prototype emits `traceseal-guard`. |
| `mode` | string | Yes | No | Runtime mode. The only approved MVP value is `observe`. |
| `platform` | string or null | No | Yes | Normalized platform label such as `windows`; null when unknown. |
| `status` | string | Yes | No | Producer/event health state. Initial health values may include `ok`, `degraded`, `error`, or `unknown`. |

The Guard object is event context. It must not claim complete OS coverage or successful enforcement.

### 3.7 Metadata object

`metadata` is always a JSON object and may be empty. It carries event-specific, non-secret extensions that do not yet have normalized fields. Extension keys must not shadow or reinterpret required top-level fields. Adding metadata keys is backward-compatible; making a metadata key required is not.

Readers must ignore unknown metadata keys while preserving them when safely forwarding the record.

## 4. Validation outcomes

A future validator should distinguish these outcomes:

| Outcome | Meaning | Reader behavior |
|---|---|---|
| valid | Required v1 fields and enums are valid | Import/display as the normalized event type |
| valid with unknown fields | Known contract is valid and extra fields exist | Ignore/preserve extras; do not fail |
| unknown event type | Envelope is valid but `event_type` is unrecognized | Import/display as unknown/generic with original type retained |
| unsupported schema version | `schema_version` is not supported | Isolate the Guard record and report compatibility metadata; old run remains readable |
| schema validation error | Required field is missing or known field type/enum is invalid | Reject/isolate this Guard record; do not fail the entire run |
| redaction failure | Sensitive data cannot be safely represented | Omit sensitive value, record safe failure metadata, and do not persist raw content |

This table defines behavior only. No validator or importer is implemented in this PR.

## 5. Compatibility rules

1. Old v0.3.0 runs contain no Guard artifact or Guard events and must remain readable without migration.
2. Guard metadata is optional at run, manifest, dashboard, and event levels.
3. Existing v0.3.0 event and `manifest.json` schemas are not replaced by this contract.
4. `dashboard-data`, replay, and explain readers must not crash on unknown Guard fields, unknown metadata keys, or unknown event types.
5. Unknown `event_type` values are represented as unknown/generic events while retaining the original string for diagnosis.
6. Missing optional/nullable fields do not fail a Guard record or run.
7. Missing/invalid required Guard fields produce a Guard schema validation error isolated from existing run data.
8. Unsupported Guard schema versions are isolated/reported; they do not make old v0.3.0 artifacts unreadable.
9. Readers must ignore unknown fields for forward compatibility and must not silently reinterpret them.
10. Python Core remains the reference implementation and remains usable with no Guard artifact.
11. A future importer must preserve deterministic run ordering and document how it correlates/deduplicates Python and Guard events.

## 6. Event type registry

The event type registry separates contract reservation from implementation. Listing an event type here does not mean that observation exists.

| `event_type` | Contract status | Intended milestone | Minimum contract meaning |
|---|---|---|---|
| `guard.health` | **First supported event / MVP target** | Issue #33 (M3) | Guard lifecycle/health heartbeat only; no OS activity observation |
| `process.spawn` | Next dry-run candidate | Issue #34 (M4) | Observation of a supported child/process start with redacted metadata |
| `process.exit` | Future | Later design | Observed process termination/exit status when available |
| `file.read` | Future | Later design | Metadata-only read observation; no file body/content |
| `file.write` | Future | Later design | Metadata-only write observation; no file body/content |
| `file.delete` | Future | Later design | Metadata-only delete observation |
| `file.rename` | Future | Later design | Redacted source/destination rename observation |
| `network.connect` | Future | Later design | Connection metadata only; no payload capture |
| `network.http` | Future | Later design | Redacted HTTP metadata consistent with cassette privacy rules |
| `git.operation` | Future | Later design | Reuses existing Git operation/push classification semantics |
| `policy.decision` | Future dry-run | Issue #37 (M7) | Links a non-enforced policy decision to a subject event |
| `guard.error` | Future MVP-supporting event | Later M3/M4 review | Safe Guard error/degraded metadata without secrets |

Only `guard.health` is the implementation target immediately following approval of this contract. `process.spawn` is the next candidate, remains dry-run, and depends on the health/lifecycle prototype. All other types require their own design/implementation review.

Enforcement is not implemented by this schema PR. Event registration does not authorize blocking, injection, kernel hooks, a service, administrator privileges, or fail-closed behavior.

## 7. Risk level

`risk_level` is required and uses this enum:

| Value | Contract meaning |
|---|---|
| `info` | Health/status or other informational evidence with no identified risk |
| `low` | Low-severity concern consistent with existing TraceSeal risk interpretation |
| `medium` | Material concern requiring review but not high/critical classification |
| `high` | High-risk operation/error under existing policy semantics |
| `critical` | Highest-risk evidence under existing policy semantics |
| `unknown` | Risk cannot be classified safely or event type is unknown |

- `guard.health` defaults to `info`.
- `guard.error` may be `low`, `medium`, or `high` depending on lost capability, event loss, or integrity impact; the classification requires a later error taxonomy.
- Unknown/generic event types default to `unknown` unless a trusted reader can classify them without inventing semantics.
- This contract does not change existing policy risk meanings or downgrade existing high/critical rules.

## 8. Policy decision

`policy.decision` is required and uses this enum:

| Value | Meaning in the event record |
|---|---|
| `observe` | Recorded without a matched allow/warn/deny action; default Stage 4 MVP decision |
| `allow` | Existing policy logic would allow the event |
| `warn` | Existing policy logic would warn for the event |
| `deny` | Existing policy logic would deny the event if enforcement were active |
| `require_approval` | Existing policy logic would require approval if such a flow were active |
| `unknown` | Decision unavailable, unsupported, invalid, or not safely mapped |

Stage 4 MVP defaults to `observe`. A future dry-run may emit `warn`, `deny`, or `require_approval`, but the event must remain non-enforcing. Consumers must not infer that a `deny` decision means an operation was blocked.

Enforce mode and proof of effective blocking require a separate enforcement RFC. This contract and PR contain no blocking logic.

## 9. Redaction status

`redaction.status` is required and uses this enum:

| Value | Meaning |
|---|---|
| `not_applicable` | Event contains no fields requiring redaction; `fields` is empty |
| `redacted` | All identified sensitive fields were redacted/omitted safely |
| `partial` | Some safe metadata remains while sensitive portions were omitted; details appear in `fields` |
| `failed` | Safe capture/redaction could not be completed; raw sensitive values are still omitted |
| `unknown` | Producer cannot determine redaction applicability/status |

- `guard.health` uses `not_applicable`.
- Future `network.http` events must follow the v0.3.0 HTTP cassette privacy model: sensitive headers/query values are redacted and bodies are metadata/hash summaries only.
- Complete secrets, Authorization values, Cookie values, API keys, tokens, passwords, credentials, session values, or signatures must not be persisted.
- Request/response bodies are not stored in full by default.
- Redaction applies before JSONL persistence and before forwarding data to any importer or dashboard surface.

## 10. Schema versioning

- The initial version is `guard.event.v1`.
- Additive optional fields and new metadata keys must remain backward-compatible.
- New event types may be added without a schema-version bump when the envelope and existing field meanings remain compatible; old readers treat them as unknown/generic.
- A breaking change to required fields, field types, enum semantics, or canonical meaning requires a new schema version.
- Readers ignore unknown fields but preserve the original event type/schema version in diagnostics.
- Missing required v1 fields produce a Guard schema validation error.
- Validation failure is scoped to the Guard record/artifact and must not break reading an otherwise valid old run.
- The v0.3.0 event schema is not replaced, migrated, or rewritten by `guard.event.v1`.
- Readers must not guess a missing `schema_version` for a Guard record.

Version negotiation between an executable Guard and Python Core is deferred to the producer/import milestones; the persisted record always declares its schema version.

## 11. Proposed artifact format

The proposed future run artifact is:

```text
runs/<run_id>/guard_events.jsonl
```

Contract requirements:

- JSON Lines: exactly one complete Guard event JSON object per non-empty line.
- UTF-8 encoding; producers should omit a byte-order mark.
- Append-only direction: accepted records are appended, not edited in place.
- A trailing newline is recommended.
- Partial/truncated lines are validation errors isolated from previously complete lines.
- Artifact absence means the run has no Guard events and is not an error.
- Each non-null `run_id` must match the containing run.
- A future manifest may contain an optional Guard summary/checksum, but this PR does not define required v0.3.0 manifest changes.
- Per-event hashes, chained hashes, checkpoints, rotation, and signing remain future audit-integrity work and are not implemented here.

For a pre-run `guard.health` event with `run_id: null`, the future producer/importer milestone must define whether the event is attached to a newly created run or retained as session-scoped transient evidence. This contract does not invent a persistence location outside the proposed run artifact.

## 12. Minimum guard.health contract

Issue #33 may implement only the following minimal event class after this contract is reviewed. The fixture intentionally omits optional `run_id`, `workspace`, `process`, and `target` fields.

```json
{
  "schema_version": "guard.event.v1",
  "event_id": "guard_evt_000001",
  "timestamp": "2026-06-22T00:00:00.000000Z",
  "source": "rust_guard",
  "event_type": "guard.health",
  "risk_level": "info",
  "policy": {
    "decision": "observe",
    "rule_id": null,
    "reason": "guard health event"
  },
  "redaction": {
    "status": "not_applicable",
    "fields": []
  },
  "guard": {
    "name": "traceseal-guard",
    "guard_version": "0.0.0-dev",
    "mode": "observe",
    "platform": "windows",
    "status": "ok"
  },
  "metadata": {
    "message": "guard health check ok"
  }
}
```

The Issue #33 prototype boundary is:

- output one or more locally generated schema-conforming `guard.health` records;
- make no network request and require no cloud service;
- observe no real process, file, network, or Git activity;
- perform no enforcement, blocking, injection, or privileged operation;
- prove only that a future Rust Guard can serialize the agreed event shape;
- allow Python Core to import or validate the event only in a later separately reviewed milestone.

The schema contract itself does not perform emission. Issue #33 provides the separately tested one-shot emitter described in [`guard-health-prototype.md`](guard-health-prototype.md).

## 13. dashboard-data, replay, and explain compatibility

Future integration may add an optional `guard` summary to `dashboard-data`, including schema version, health state, event count, and validation/degraded metadata. Existing fields and types must remain unchanged, and old consumers must be able to ignore the new object.

Replay may display normalized Guard events in timestamp/sequence order. A run without `guard_events.jsonl` behaves exactly as before.

Explain may cite a Guard event or dry-run policy decision when valid Guard metadata exists. Without Guard metadata, it emits no Guard-specific output and retains v0.3.0 behavior.

Unknown Guard fields/types are displayed generically or omitted safely; they do not crash the command. Invalid Guard records produce isolated compatibility/validation metadata rather than aborting old run processing.

This PR defines expectations only. It does not modify Python Core, `dashboard-data`, replay, explain, Electron, or run artifacts.

## 14. Contract review checklist

- [ ] Required, optional, and nullable fields are unambiguous.
- [ ] `guard.event.v1` versioning and validation outcomes are accepted.
- [ ] `guard.health` is the only immediate implementation target.
- [ ] `process.spawn` remains the next dry-run candidate and is not implemented here.
- [ ] Risk, policy decision, and redaction enums preserve existing TraceSeal semantics.
- [ ] Old v0.3.0 runs remain readable without migration.
- [ ] Unknown fields/event types and malformed Guard records have safe fallback behavior.
- [ ] JSONL artifact absence is a normal Python-only run state.
- [ ] No Rust, Python Core, Electron, installer, enforcement, tag, or release implementation is included.
