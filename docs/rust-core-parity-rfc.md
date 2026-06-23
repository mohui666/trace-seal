# Rust Core Parity RFC

## Status

- **Status:** Draft / planning-only / documentation-only.
- **Scope:** Post-Stage 4 planning / Issue #52.
- **Current implementation:** Python Core remains the current run/replay/explain/dashboard-data implementation.
- **Current desktop:** Electron + React + TypeScript + TailwindCSS remains the current desktop implementation.
- **Current Guard:** Rust Guard remains dry-run / observe-only.
- **Release status:** No tag, release, installer, asset, or workflow change.

This RFC does not implement Rust Core. This RFC does not rewrite Python Core. This RFC does not start a runtime migration. This RFC does not change `traceseal dashboard-data` output. This RFC does not change dashboard-data output, does not replace Electron, and does not modify the v0.3.0 release. Rust Core is a parity target, not an immediate replacement.

## Background

TraceSeal has completed the current evidence pipeline through Stage 4:

- Stage 1 is done: Python CLI MVP records events, replays a transcript, and explains the first harmful event.
- Stage 2 Electron Dashboard is done: Electron, React, TypeScript, and TailwindCSS consume Python Core `dashboard-data` JSON.
- Stage 3 Core is done and `v0.3.0` has been released with file read tracking, `os.system()`, `httpx`, Git state metadata, HTTP cassette redaction, `policy.yaml`, Git push classification, domain policy, and cascade analysis.
- Stage 4 is done through Issue #50: Rust Guard dry-run / observe-only evidence and RFCs are complete, while enforcement remains unimplemented.
- Slint desktop feasibility was documented through Issue #51 in `docs/slint-desktop-feasibility-rfc.md`.
- The current `main` baseline for this RFC is `a2e722681906b08e1c46a8a50994fd0bc8c2dd75`.

Python Core remains the current run/replay/explain/dashboard-data implementation. Electron remains the current desktop implementation. Rust Guard remains dry-run / observe-only. Enforcement is not implemented. Rust Core does not currently replace Python Core.

The purpose of this RFC is to define what behavior parity would mean before any future Rust Core implementation can be considered.

## Current Python Core responsibilities

The current Python Core owns the user-visible run evidence pipeline:

- `traceseal run` orchestration.
- `traceseal replay` transcript rendering.
- `traceseal explain` and first harmful event analysis.
- `traceseal dashboard-data` JSON export for current Electron and any future desktop candidate.
- `sitecustomize` bootstrap and Python monkey-patch SDK hooks.
- File, shell, HTTP, delete API, Git-risk, and policy event recording.
- `policy.yaml` / `policy.yml` loading, validation, fallback, and behavior.
- Sandbox workspace copy.
- Recorder artifacts including `events.jsonl`, `manifest.json`, workspace snapshots, and diffs.
- Workspace snapshot / diff metadata.
- Git state metadata before and after a run.
- HTTP cassette redaction and body summary generation.
- Cascade analysis.
- Minimizer / first harmful event analysis.
- Guard artifact import and Guard dry-run summary integration.
- Test fixtures and regression behavior for old and current runs.

Python SDK hooks still must remain on the Python side. `sitecustomize` and monkey-patch behavior cannot be removed by this RFC. Current Electron and future Slint should first consume stable `dashboard-data` JSON rather than bypassing Core.

## Why evaluate Rust Core parity

Rust may be a good long-term home for selected Core responsibilities:

- Schema validation can benefit from strongly typed contracts and explicit error handling.
- Policy replay and decision summaries may become easier to compare across Guard and Core artifacts.
- `dashboard-data` generation could eventually share Rust data models with a future native desktop bridge.
- Explain/minimizer logic may benefit from deterministic data structures and fixture-driven parity tests.
- Guard integration may be simpler if artifact validation and summary generation have a Rust-compatible layer.
- A Rust Core parity path could reduce long-term confusion between Python, Rust Guard, and desktop boundaries.

These motivations do not justify a rewrite. Rust Core is a parity target, not an immediate replacement. Python hook functionality still requires Python integration, and the current Python output remains authoritative until a separate accepted migration replaces a path.

## Goals

- Classify current Python Core modules into keep-in-Python, Rust parity candidate, and long-term deprecation candidate.
- Define behavior parity requirements for existing artifacts and CLI outputs.
- Define fixture-based testing before any migration.
- Define compatibility rules for Electron, future Slint, and Python Core users.
- Define a staged migration plan that allows rollback at every step.

## Non-goals

This RFC does not:

- implement Rust Core;
- rewrite Python Core;
- delete Python SDK hooks;
- remove `sitecustomize` or monkey-patch behavior;
- change `traceseal run`;
- change `traceseal replay`;
- change `traceseal explain`;
- change `traceseal dashboard-data` output;
- change `events.jsonl`;
- change `manifest.json`;
- change policy YAML behavior;
- change Git state metadata behavior;
- change HTTP cassette redaction behavior;
- change cascade analysis behavior;
- change Rust Guard behavior;
- implement enforcement;
- execute or block target commands;
- add daemon or service behavior;
- add OS-wide process monitoring;
- add file, network, Git, or process monitoring expansion;
- add Slint runtime code;
- add Slint;
- add a Slint crate;
- add `.slint` UI files;
- replace Electron;
- change Electron main/preload/IPC/renderer behavior;
- change packaging or installer behavior;
- change GitHub Actions release workflow;
- create, move, or delete any release tag;
- create `v0.3.1`;
- modify the `v0.3.0` release or its assets;
- delete or modify `origin/jimmma`.

## Module classification

This table is conservative. It does not approve implementation and does not mark any current production path for immediate removal.

| Module or responsibility | Classification | Rationale |
|---|---|---|
| CLI command dispatch | Keep in Python | Current commands remain stable; Rust can be considered only behind a later opt-in backend. |
| `traceseal run` orchestration | Keep in Python | Run setup depends on Python hook bootstrap and sandbox behavior. |
| `sitecustomize` bootstrap | Keep in Python | Python runtime interception requires Python integration. |
| SDK monkey patches | Keep in Python | Python `open`, `pathlib`, `subprocess`, `os.system`, HTTP, and delete hooks cannot be replaced by this RFC. |
| Event schema validation | Rust parity candidate | A Rust validator can compare artifacts without changing writers. |
| `events.jsonl` reading | Rust parity candidate | Artifact readers are good parity targets when Python output remains source of truth. |
| `manifest.json` reading | Rust parity candidate | Manifest parsing can be compared against Python golden fixtures. |
| `dashboard-data` generation | Rust parity candidate | Rust output can be compared to Python JSON before any consumer changes. |
| Replay transcript generation | Rust parity candidate | Transcript rendering can be compared against golden text output. |
| Explain / minimizer | Rust parity candidate | Deterministic analysis is a candidate after golden behavior is locked. |
| Policy YAML parsing | Rust parity candidate | A Rust parser may validate parity, but Python remains authoritative first. |
| Policy decision replay | Rust parity candidate | Policy decisions must match Python fixture outcomes before any opt-in use. |
| Sandbox workspace copy | Keep in Python | It is tied to current run orchestration and must not change in this RFC. |
| Workspace snapshot / diff | Rust parity candidate | A read-only comparator may be useful; writer behavior stays Python-owned. |
| Git state metadata | Rust parity candidate | Rust can validate shape and summaries against Python fixtures. |
| HTTP cassette redaction | Rust parity candidate | High-risk parity target because redaction mismatches are security-sensitive. |
| Cascade analysis | Rust parity candidate | Deterministic classifier can be compared against golden runs. |
| Guard artifact import | Rust parity candidate | Guard schema validation may share Rust models later while Python import remains compatible. |
| Electron IPC bridge | Keep in Python | Electron currently calls Python dashboard-data; no IPC behavior changes are in scope. |
| Future Slint bridge | Rust parity candidate | Slint may later benefit from Rust data models, but must first use stable dashboard-data JSON. |
| Legacy duplicate reader helpers | Long-term deprecation candidate | Only after parity tests prove a replacement and a separate migration removes dead code. |
| Experimental bridge adapters | Long-term deprecation candidate | Only future opt-in shims with clear cleanup criteria qualify, not current production paths. |

## Behavior parity requirements

Existing Python output is the source of truth until explicitly replaced. Rust parity must be fixture-driven and must compare output against Python golden fixtures for:

- `events.jsonl`.
- `manifest.json`.
- `dashboard-data` JSON.
- Replay output.
- Explain output.
- Policy YAML decisions.
- Git state metadata.
- HTTP cassette redaction.
- Cascade analysis.
- Guard metadata import.

Rust output must preserve field names, stable JSON shape, risk labels, timestamp handling rules, redaction behavior, and error semantics. It must preserve old-run behavior, optional Guard metadata behavior, and malformed artifact isolation. Any intentional output change requires a separate migration note and versioning.

## Data contracts

Current stable contracts include:

- `runs/<run_id>/events.jsonl`.
- `runs/<run_id>/manifest.json`.
- `runs/<run_id>/workspace`.
- `runs/<run_id>/http_cassette.jsonl`.
- `traceseal dashboard-data latest`.
- `traceseal dashboard-data list`.
- `traceseal dashboard-data run <run_id>`.
- `traceseal dashboard-data policy`.

Electron depends on `dashboard-data` JSON. Future Slint should also depend on `dashboard-data` JSON first. Rust Core parity must not break these contracts, must not bypass Python Core output in the current desktop path, and must not require a run migration.

No command should accept arbitrary renderer-provided shell commands. Renderer and future desktop surfaces should continue to use fixed operations rather than command strings supplied by UI code.

## Fixture-based parity testing

Future Rust work must define golden fixtures before replacement:

- Fixed sample runs.
- Golden `events.jsonl`.
- Golden `manifest.json`.
- Golden dashboard-data JSON.
- Golden replay transcript.
- Golden explain output.
- Policy YAML fixture.
- Git metadata fixture.
- HTTP cassette redaction fixture.
- Cascade analysis fixture.
- Guard metadata fixture.

A future Rust implementation must compare Rust output against Python golden fixtures before it can replace any path. These fixtures should cover clean runs, high-risk runs, malformed artifacts, missing optional fields, unknown optional Guard fields, and redaction-sensitive examples.

## Candidate architecture

The future candidate architecture is proposed only:

```text
Python SDK hooks / sitecustomize
  ->
events.jsonl + manifest.json + artifacts
  ->
Rust Core parity layer
  ->
dashboard-data JSON / replay / explain summaries
  ->
Electron today / Slint candidate later
```

The Python hook layer remains authoritative for Python runtime interception. Rust Core may become an artifact reader, validator, and summarizer first. Rust Core should not initially execute `traceseal run`, modify workspaces, enforce policy, start a daemon/service, or execute target commands.

## Migration boundaries

Any future migration must remain narrow and reviewable:

- Start with read-only artifact validation.
- Keep Python Core as the default path.
- Require dual-run or side-by-side comparison before opt-in use.
- Keep run artifacts compatible with v0.3.0 readers unless a separate migration version is accepted.
- Do not modify Electron runtime behavior while testing Rust parity.
- Do not combine Rust Core migration with Slint implementation.
- Do not merge Guard observation events into Python timelines as part of this RFC.
- Do not change packaging, installers, release workflows, tags, or release assets.

## Rust Core and Slint relationship

Issue #51 Slint feasibility RFC is complete. Slint should not directly cause a Python Core rewrite. A future Slint spike should first call existing Python `dashboard-data` and preserve the same data boundary used by Electron today.

Rust Core parity could later simplify Slint integration by providing Rust-native artifact readers or summaries, but Rust Core parity and Slint implementation must remain separate issues. This RFC does not add Slint, does not add a Slint crate, and does not add `.slint` UI files.

## Compatibility and rollback rules

Python Core remains source of truth until explicit replacement. Any Rust parity feature must be opt-in first. Dual-run comparison should be possible wherever output is user-visible.

If Rust output differs from Python output, Python path wins. Electron current path must remain unaffected. The `v0.3.0` release remains untouched.

Rollback means disabling the Rust parity path and returning to Python-only behavior. Rollback must not require tag movement, asset changes, workflow changes, or installer changes.

## Risk analysis

| Risk | Impact | Mitigation |
|---|---|---|
| Behavior drift between Python and Rust | Users see different evidence for the same run | Golden fixtures and dual-run comparison. |
| JSON field compatibility risk | Electron, Slint, or scripts may break | Preserve field names and stable shapes; version intentional changes. |
| Redaction mismatch risk | Sensitive data could leak or evidence could be over-redacted | Treat HTTP cassette, headers, query, paths, and body summaries as security-sensitive fixtures. |
| Policy decision mismatch risk | Warnings, deny metadata, or suggested policies may diverge | Compare `policy.yaml` decisions against Python golden output. |
| Replay/explain semantic drift | Investigations could identify different first harmful events | Golden transcript and explain fixtures. |
| Duplicated maintenance burden | Python and Rust logic may diverge over time | Limit Rust work to explicit parity candidates and remove only after separate review. |
| Rust/Python boundary complexity | Extra bridge code can create new failure modes | Keep initial Rust layer read-only and optional. |
| Test fixture incompleteness | Parity can pass while real cases drift | Include clean, high-risk, redaction, malformed, Guard, and cascade fixtures. |
| Accidental migration before parity | Current production paths could change prematurely | Keep all Rust parity behind opt-in gates. |
| Confusion with Slint / Stage 5 work | Desktop migration and Core migration could blur | Keep Slint, Rust Core, and Stage 5 implementation separate. |
| Release workflow contamination risk | Planning work could accidentally affect release artifacts | Do not change packaging, workflows, tags, or v0.3.0 assets. |

## Proposed staged plan

This RFC proposes future issue candidates only. It does not create these issues and does not implement them:

- Issue candidate A: Rust artifact schema validator.
- Issue candidate B: Rust events/manifest reader parity.
- Issue candidate C: Rust dashboard-data parity prototype.
- Issue candidate D: Rust explain/minimizer parity prototype.
- Issue candidate E: dual-run parity test harness.
- Issue candidate F: opt-in Rust Core backend RFC.

Each candidate needs its own scope, non-goals, tests, rollback plan, and compatibility review before implementation.

## Validation plan

This documentation-only RFC is validated by static checks:

- The RFC file exists.
- README and roadmap link to the RFC and Issue #52.
- Required sections are present.
- Non-goals explicitly state that this RFC does not implement Rust Core, rewrite Python Core, change dashboard-data output, add Slint, replace Electron, modify v0.3.0, create tags, or change release assets.
- README and roadmap avoid misleading claims that Rust Core is implemented, Python Core has been replaced, Rust Core is default, Slint is implemented, Electron has been replaced, or `v0.3.1` has been released.
- Repository tests continue to pass.
