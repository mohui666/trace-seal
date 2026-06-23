# TraceSeal

TraceSeal is an operation recorder, replay aid, and safety-analysis layer for AI agents that touch files, shells, HTTP, and Git.

## What TraceSeal is

TraceSeal records the side effects of a Python agent run, exports replayable evidence, and explains the first risky or harmful operation. The current command-line loop is:

```text
traceseal run -> events.jsonl / manifest.json -> traceseal replay -> traceseal explain
```

The Python Core remains the source of truth for run, replay, explain, policy, recorder, and dashboard-data behavior.

## Current status

- Latest stable release: [v0.3.0](https://github.com/mohui666/trace-seal/releases/tag/v0.3.0).
- Stage 3 Core work is complete in v0.3.0: Git state tracking, redacted HTTP cassette artifacts, local policy YAML, Git push classification, domain policy, and deterministic cascade analysis.
- Stage 4 Guard work is dry-run / observe-only evidence and RFCs; it is not productized enforcement.
- Post-Stage 4 planning is tracked separately: Electron remains the current desktop implementation, Python Core remains the current run/replay/explain/dashboard-data implementation, Slint desktop feasibility is experimental planning, and Rust Core parity is planning-only.
- There is no v0.3.1.

## Quick start

Install the package in editable mode from the repository root:

```powershell
python -m pip install -e .
python -m traceseal --help
```

Run a local demo and inspect the result:

```powershell
python -m traceseal run -- python examples/bad_agent_delete.py
python -m traceseal replay runs/latest
python -m traceseal explain runs/latest
python -m traceseal dashboard-data runs/latest
```

Demo runs write evidence under `runs/<run_id>/`. Replay and explain read recorded evidence instead of re-running the original side effects.

## Desktop status

Electron remains the default desktop implementation. The Electron + React renderer consumes Python Core `dashboard-data` output and does not own interception logic.

Slint remains experimental-only. The Slint spike is not packaged or released, and Slint does not replace Electron.

## Safety boundaries

TraceSeal is an evidence and analysis prototype, not an operating-system security product.

- Enforcement is not implemented.
- No daemon or service is installed.
- No OS-wide monitoring is performed.
- No OS-wide file, network, process, or Git monitoring expansion is present.
- The sandbox is a copied workspace directory, not a container or kernel isolation boundary.
- Slint does not replace Electron.
- There is no v0.3.1.

## Documentation

- [Documentation index](docs/README.md)
- [Project status](docs/project-status.md)
- [Roadmap](docs/roadmap.md)
- [Project specification](docs/spec.md)
- [Policy rules](docs/policy-rules.md)
- [Incident examples](docs/incident-examples.md)
- [Dashboard design](docs/dashboard-design.md)
- [Demo script](docs/demo.md)
- [Slint Desktop Feasibility RFC](docs/slint-desktop-feasibility-rfc.md)
- [Rust Core Parity RFC](docs/rust-core-parity-rfc.md)
## Release status

`v0.3.0` is the latest stable release. Windows release artifacts and checks are recorded in [the v0.3 release report](artifacts/v0.3-release-report.md). Older release notes remain available for `v0.2.0`.
