# Import Guard Events into Python Core

## Status and scope

- **Milestone:** Stage 4 M5 / Issue #35
- **Status:** Optional local import path
- **Schema:** `guard.event.v1`
- **Canonical artifact:** `runs/<run_id>/guard_events.jsonl`
- **Manifest metadata:** optional `guard` object
- **Timeline behavior:** existing Python `events.jsonl` is unchanged
- **Release status:** prototype integration only; Stage 4 is not released

The importer attaches a validated Guard JSONL artifact to an existing TraceSeal run. It does not start the Rust Guard, execute a recorded `process.spawn` command, merge Guard records into the Python event timeline, or evaluate policy. Issue #36 can now expose a compact read-only summary through `dashboard-data`.

## Python API

```python
from traceseal.guard_import import (
    get_guard_event_summary,
    import_guard_events,
    load_imported_guard_events,
    maybe_find_guard_events,
)

result = import_guard_events(
    "runs/run_20260622_example",
    "runs/guard-source.jsonl",
)
events = load_imported_guard_events("runs/run_20260622_example")
summary = get_guard_event_summary("runs/run_20260622_example")
artifact = maybe_find_guard_events("runs/run_20260622_example")
```

`import_guard_events` returns the same optional metadata stored under `manifest.json` → `guard`:

```json
{
  "guard_events_path": "guard_events.jsonl",
  "guard_event_count": 2,
  "guard_event_types": ["guard.health", "process.spawn"],
  "guard_schema_version": "guard.event.v1",
  "guard_imported_at": "2026-06-22T00:00:00+00:00"
}
```

The existing manifest fields remain unchanged. Runs without the `guard` object and without `guard_events.jsonl` are normal Python-only runs; loading them returns an empty event list and a zero-count summary.

## Module CLI

```powershell
python -m traceseal.guard_import `
  --run runs/run_20260622_example `
  --guard-events runs/guard-source.jsonl
```

Success prints the imported count, event types, and canonical artifact name. A missing run/source path, malformed JSONL, invalid schema, mismatched non-null `run_id`, or duplicate `event_id` produces a clear error and non-zero status.

## Validation and storage rules

1. Every record is parsed with `load_guard_events`.
2. `guard.health` and `process.spawn` use their strict event validators.
3. Unknown `event_type` values use the common `guard.event.v1` validator and are retained for forward compatibility.
4. All records are validated before the run artifact or manifest is modified.
5. Non-null event `run_id` values must match the target run manifest/run directory identity.
6. Duplicate `event_id` values are rejected.
7. Source JSONL order is preserved exactly. The importer does not sort or merge records into `events.jsonl`.
8. Event types in manifest metadata are unique and sorted for deterministic output.
9. The canonical artifact is written atomically as UTF-8 JSON Lines with one event per line.
10. An existing imported artifact is not silently overwritten.

Source-order preservation is the M5 ordering rule. Cross-source correlation and deduplication between Python hooks and future OS observations remain deferred because M5 keeps the two timelines separate.

## Replay, explain, and dashboard compatibility

Replay and explain continue reading only the existing Python `events.jsonl`. They tolerate the optional manifest metadata and a Guard-enabled run without changing their output format. Invalid or unknown optional Guard metadata is ignored by these existing readers.

Issue #36 adds one optional top-level `guard` object to run-level `dashboard-data` while preserving every existing field and the Python timeline. See [`dashboard-guard-metadata.md`](dashboard-guard-metadata.md). No Electron UI consumes or displays the object in this milestone.

Policy evaluation is not run during import. Guard policy dry-run decisions remain Issue #37.

## Safety and non-goals

- Import is local file parsing and atomic local artifact persistence only.
- A `process.spawn` record is data; its target command is never executed.
- No OS-wide process observation or new file/network/Git monitoring.
- Read-only dashboard-data metadata only; no Electron UI visualization or redesign.
- No policy dry-run, blocking, enforcement, fail-closed behavior, daemon, or service.
- No installer, release workflow, tag, or GitHub Release change.
