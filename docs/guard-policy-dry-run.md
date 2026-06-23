# Guard Policy Dry-Run Decisions

## Status and scope

- **Milestone:** Stage 4 M7 / Issue #37
- **Input:** Optional imported `guard_events.jsonl`
- **Policy source:** Existing TraceSeal `policy.yaml` DSL, or existing default policy discovery when no explicit policy is provided
- **Output artifact:** `runs/<run_id>/guard-policy-decisions.json`
- **Mode:** Dry-run / observe-only
- **Enforcement:** Not implemented; `enforcement_applied` is always `false`
- **Electron UI:** Unchanged
- **Release status:** Prototype integration only; Stage 4 is not released

Issue #37 maps imported Guard events into existing TraceSeal policy evaluation and stores the result as metadata. It does not execute any recorded target command, block `process.spawn`, start a daemon/service, add OS-wide monitoring, add file/network/Git monitoring, redesign Electron UI, modify installer/release workflows, create a tag, or publish v0.3.1.

## Supported events

The dry-run bridge supports the currently imported prototype event classes:

- `guard.health`
- `process.spawn`

Unknown valid `guard.event.v1` event types remain import-compatible, but they receive the default dry-run `observe` decision unless an existing policy rule safely matches the mapped context.

## Python API

```python
from traceseal.guard_policy import (
    apply_guard_policy_dry_run,
    get_guard_policy_summary,
    load_guard_policy_decisions,
)

summary = apply_guard_policy_dry_run(
    "runs/run_20260622_example",
    "policy.yaml",
)
payload = load_guard_policy_decisions("runs/run_20260622_example")
dashboard_summary = get_guard_policy_summary("runs/run_20260622_example")
```

`apply_guard_policy_dry_run()` validates the imported Guard artifact first, loads the selected policy, evaluates each Guard event, and writes a sidecar artifact. It never mutates `guard_events.jsonl` and never merges Guard events into the Python `events.jsonl` timeline.

If a run has no Guard artifact, the API returns an unavailable zero-count summary and does not create a decision artifact. If the Guard artifact or policy is malformed, the API raises a clear `GuardPolicyError` without executing target commands or applying enforcement.

## CLI

Module form:

```powershell
python -m traceseal.guard_policy `
  --run runs/run_20260622_example `
  --policy policy.yaml
```

TraceSeal CLI form:

```powershell
python -m traceseal guard-policy-dry-run `
  --run runs/run_20260622_example `
  --policy policy.yaml
```

`--policy` is optional. When omitted, TraceSeal uses the existing policy discovery path for the run directory. Missing Guard artifacts are treated as zero-event dry-run results. Missing explicit policy files and malformed policy files return non-zero status with a clear message.

## Policy mapping

Guard dry-run uses the existing policy DSL instead of inventing a second language. The current bridge maps Guard events into these existing match fields:

| Policy match field | Guard source |
|---|---|
| `event_type` | Guard `event_type`, for example `guard.health` or `process.spawn` |
| `command` | Joined `process.command_line` for `process.spawn` |
| `path` | `process.cwd` or `workspace` when available |
| `risk_level` | Guard event `risk_level` |
| `sensitive` | True when Guard redaction metadata indicates redacted/partial/failed fields |

For example:

```yaml
version: 1
mode: warn
rules:
  - id: guard-spawn-warn-delete-demo
    match:
      event_type: process.spawn
      command:
        contains: bad_agent_delete.py
    risk_level: high
    action: warn
    reason: Guard process.spawn would run a delete demo
    suggested_policy: require_approval process.spawn bad_agent_delete.py
```

Unmatched Guard events receive:

```json
{
  "decision": "observe",
  "matched_rule": null,
  "dry_run": true,
  "enforcement_applied": false
}
```

## Decision artifact

The sidecar artifact is:

```text
runs/<run_id>/guard-policy-decisions.json
```

Shape:

```json
{
  "available": true,
  "artifact_path": "guard-policy-decisions.json",
  "artifact_type": "guard.policy.decisions.v1",
  "generated_at": "2026-06-22T00:00:00+00:00",
  "policy_source": {
    "type": "yaml",
    "path": "C:/workspace/policy.yaml",
    "error": null
  },
  "dry_run": true,
  "event_count": 2,
  "evaluated_event_count": 2,
  "decision_counts": {
    "observe": 1,
    "warn": 1
  },
  "enforcement_applied": false,
  "error": null,
  "decisions": [
    {
      "event_id": "guard_evt_000002",
      "event_type": "process.spawn",
      "decision": "warn",
      "matched_rule": "guard-spawn-warn-delete-demo",
      "rule_id": "guard-spawn-warn-delete-demo",
      "reason": "Guard process.spawn would run a delete demo",
      "risk_level": "high",
      "dry_run": true,
      "enforcement_applied": false
    }
  ]
}
```

Every decision states `dry_run: true` and `enforcement_applied: false`. A `deny` result means the policy would deny the event if a future enforcement mode existed; it does **not** mean anything was blocked in this milestone.

## dashboard-data contract

`dashboard-data` includes the policy summary under the existing additive `guard` object:

```json
{
  "guard": {
    "available": true,
    "event_count": 2,
    "policy": {
      "available": true,
      "dry_run": true,
      "evaluated_event_count": 2,
      "decision_counts": {
        "observe": 1,
        "warn": 1
      },
      "enforcement_applied": false
    },
    "events": [
      {
        "event_id": "guard_evt_000002",
        "event_type": "process.spawn",
        "decision": "observe",
        "policy_decision": {
          "decision": "warn",
          "matched_rule": "guard-spawn-warn-delete-demo",
          "dry_run": true,
          "enforcement_applied": false
        }
      }
    ]
  }
}
```

The original event-level `policy.decision` remains the producer-side value, usually `observe`. The new `policy_decision` object is the Core dry-run result from the sidecar artifact.

If no Guard policy dry-run has been applied, `guard.policy.available` is `false`, counts are empty, and `enforcement_applied` remains `false`. Invalid policy sidecar data is isolated as `INVALID_GUARD_POLICY_DECISIONS` inside `guard.policy.error`; the rest of `dashboard-data` remains readable.

## replay and explain compatibility

Replay and explain continue to read the existing Python `events.jsonl` timeline. Runs that include `guard-policy-decisions.json` remain loadable, and old runs without Guard artifacts remain unchanged.

This milestone does not rewrite explain output or claim that dry-run `deny` decisions blocked anything. A later display milestone may surface Guard policy metadata more prominently after a separate review.

## Safety and non-goals

- No target command execution.
- No policy enforcement, blocking, fail-closed behavior, or warn UI.
- No daemon, service, kernel driver, administrator privilege, injection, or OS-wide process monitoring.
- No new file, network, HTTP, or Git monitoring surface.
- No Electron UI redesign.
- No installer/build-system/release workflow change.
- No v0.3.1 release, new tag, tag rewrite, or v0.3.0 Release modification.
- Issue #38 Windows VM smoke validation remains unstarted.
- Issue #39 enforcement experiment RFC remains unstarted.
