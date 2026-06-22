# Dashboard Guard Metadata Contract

## Status and scope

- **Milestone:** Stage 4 M6 / Issue #36
- **Surface:** Python `dashboard-data` JSON only
- **Input:** Optional imported `guard_events.jsonl`
- **Electron UI:** Unchanged
- **Policy:** No Guard policy dry-run decisions
- **Release status:** Prototype integration only; Stage 4 is not released

The run-level `dashboard-data` payload now contains an additive `guard` object. Existing fields, Python timeline events, Renderer behavior, and Electron UI remain unchanged. Consumers that do not know this field can ignore it.

## Valid imported artifact

```json
{
  "guard": {
    "available": true,
    "schema_version": "guard.event.v1",
    "artifact_path": "guard_events.jsonl",
    "imported_at": "2026-06-22T00:00:00+00:00",
    "event_count": 2,
    "event_types": ["guard.health", "process.spawn"],
    "risk_levels": {"info": 2},
    "decisions": {"observe": 2},
    "redaction_statuses": {"not_applicable": 1, "redacted": 1},
    "health_status": "ok",
    "events": [],
    "error": null
  }
}
```

`events` contains compact records with:

- `event_id`, `timestamp`, `event_type`, and `risk_level`;
- recorded `decision` and `redaction_status` values;
- `guard_status` and non-secret `message` metadata;
- for `process.spawn`, a `process` object containing program, redacted arguments, cwd, PID fields, `dry_run`, and `executed`.

Guard events remain separate from the existing top-level Python `events` timeline. Aggregate maps use deterministic string keys, and `event_types` remains unique and sorted by the importer.

## Missing and invalid artifacts

A Python-only/old run receives a stable unavailable object:

```json
{
  "guard": {
    "available": false,
    "schema_version": null,
    "artifact_path": null,
    "imported_at": null,
    "event_count": 0,
    "event_types": [],
    "risk_levels": {},
    "decisions": {},
    "redaction_statuses": {},
    "health_status": null,
    "events": [],
    "error": null
  }
}
```

If the optional artifact exists but cannot be parsed or validated, the run payload still succeeds. `available` remains false, summaries remain empty, and `error` contains `code: "INVALID_GUARD_EVENTS"` plus a clear message. The invalid Guard artifact does not corrupt or replace old run data.

## Redaction and safety

Dashboard output uses the already validated/redacted Guard event values. It also defensively masks common token, password, secret, authorization, cookie, API-key, access-token, and client-secret argument forms before exposing `process.spawn` arguments.

A `process.spawn` record is metadata only. Dashboard generation never invokes the recorded program, opens a network connection, evaluates Guard policy, blocks an operation, or starts a service.

## Non-goals

- No Electron/React/CSS changes or new visual component.
- No Guard events merged into the Python event timeline.
- No policy dry-run decisions; Issue #37 remains separate.
- No enforcement, daemon, service, OS observation, or new monitoring surface.
- No installer, release workflow, tag, or GitHub Release changes.
