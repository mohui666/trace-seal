# Slint Desktop Feasibility RFC

## Status

- **Status:** Draft RFC
- **Scope:** Documentation-only feasibility review
- **Milestone:** Post-Stage 4 planning / Issue #51
- **Current desktop implementation:** Electron + React + TypeScript + TailwindCSS
- **Implementation:** No implementation in this PR
- **Release status:** No tag, release, installer, asset, or workflow change

TraceSeal currently ships the desktop dashboard through Electron, with a React renderer and a TypeScript preload/API boundary. This RFC evaluates whether a future native Slint desktop path is worth pursuing after Stage 4. It does not add Slint runtime code, does not add a Slint crate, does not add `.slint` UI files, does not replace Electron, and does not start Stage 5 implementation.

## Background

Stage 4 completed the Guard dry-run / observe-only track and explicitly left future desktop and Rust Core work as separate planning issues. Issue #51 is the first planning gate for a possible Slint desktop direction.

The current desktop stack has known strengths:

- Electron already reads `dashboard-data` through the existing Python Core boundary.
- Renderer state, routing, tests, and packaging are already integrated.
- The released Windows installer and v0.3.0 assets are tied to the current Electron packaging path.
- The security model is already documented around Electron main, preload, IPC, and a read-only renderer data path.

Slint may still be attractive for a future native dashboard if it can reduce runtime size, improve startup behavior, and align better with a Rust-facing roadmap. Those benefits need evidence before any implementation is accepted.

## Goals

- Define the questions that must be answered before introducing Slint.
- Compare Slint against the existing Electron dashboard without assuming replacement.
- Identify decision gates for any future prototype.
- Preserve current Electron, Python Core, Rust Guard, packaging, release, tag, and monitoring behavior.
- Record the minimum evidence needed before a separate implementation issue can start.

## Non-goals

- This RFC does not add Slint runtime code.
- This RFC does not add a Slint crate.
- This RFC does not add `.slint` UI files.
- This RFC does not replace Electron.
- This RFC does not delete React, Vite, TypeScript, or TailwindCSS.
- This RFC does not modify Electron main, preload, IPC, or renderer behavior.
- This RFC does not modify Python Core behavior.
- This RFC does not modify Rust Guard behavior.
- This RFC does not implement enforcement.
- This RFC does not execute or block target commands.
- This RFC does not add a daemon or service.
- This RFC does not add OS-wide process monitoring.
- This RFC does not expand file, network, Git, or process monitoring.
- This RFC does not modify packaging or installer behavior.
- This RFC does not modify GitHub Actions release workflows.
- This RFC does not create, move, delete, or retarget release tags.
- This RFC does not create `v0.3.1`.
- This RFC does not modify the `v0.3.0` release or assets.
- This RFC does not start Stage 5 implementation.

## Current baseline

The baseline for comparison is the current shipped desktop path:

| Area | Current baseline |
|---|---|
| Desktop shell | Electron |
| Renderer | React + TypeScript + TailwindCSS |
| Data source | Python Core `dashboard-data` JSON |
| Privilege boundary | Electron main/preload/IPC isolates renderer from Node.js |
| Packaging | Electron Forge plus PyInstaller resources |
| Release | v0.3.0 Windows x64 installer and checksums |
| Enforcement | Not implemented |
| Monitoring expansion | None |

Any Slint proposal must preserve the `dashboard-data` contract unless a separate accepted RFC changes that boundary.

## Feasibility questions

### Product and UX fit

- Can Slint represent the existing dashboard views without losing scanability, table density, event detail readability, and copy/export ergonomics?
- Can the current workflows remain recognizable for existing users?
- Does Slint improve perceived startup, memory use, or native feel enough to justify a migration or parallel prototype?
- Can accessibility, keyboard navigation, high-DPI rendering, and Windows font behavior meet the current desktop expectations?

### Architecture fit

- Should a Slint path consume the same Python Core `dashboard-data` JSON, or wait for a separate Rust Core parity decision?
- Can the data boundary remain read-only from the desktop UI to avoid expanding privilege?
- How would workspace selection, settings persistence, runtime path discovery, and error reporting map to Slint?
- Can a Slint UI remain independent of Guard internals and avoid direct privileged APIs?

### Build and release fit

- What Windows build dependencies would be required?
- Can CI build and test the Slint path without destabilizing the current release workflow?
- Would packaging produce a smaller, simpler, or more maintainable artifact than the current Electron package?
- How would signing, installer behavior, checksums, and release assets be validated?

### Testability

- What unit and integration test strategy covers Slint UI state, data parsing, and view rendering?
- Can dashboard fixtures be shared with existing Python, Electron, and renderer tests?
- What smoke validation is required before a Slint prototype can be compared fairly?
- How will regressions be detected without weakening the current Electron test baseline?

### Maintenance

- Does the team have enough Rust/Slint familiarity to maintain the UI?
- How much UI code would be duplicated during a parallel evaluation?
- What documentation, examples, and debugging tools are needed for contributors?
- What support matrix would be realistic for Windows first, and later macOS/Linux only if separately accepted?

## Options

### Option A: Keep Electron as the only desktop path

Electron remains the sole desktop implementation. Slint is not pursued until a future issue identifies a stronger need.

Advantages:

- Lowest immediate risk.
- No duplicate UI stack.
- No packaging disruption.
- Existing tests and release evidence remain directly applicable.

Limitations:

- Does not explore native runtime size or startup improvements.
- Keeps the current Electron dependency surface.

### Option B: Build a narrow Slint hello dashboard spike

After this RFC is accepted, a separate spike issue may build a tiny read-only dashboard using fixture or `dashboard-data` input. The spike must not replace Electron or affect releases.

Advantages:

- Produces evidence on build complexity, runtime size, UI expressiveness, and testability.
- Keeps risk isolated behind a dedicated prototype.
- Allows side-by-side comparison against current Electron behavior.

Limitations:

- Creates temporary duplicate UI concepts.
- Requires clear cleanup criteria if the spike is not promising.
- Must not be mistaken for the default desktop path.

### Option C: Plan an eventual Slint migration

A later RFC could propose Slint as the default desktop after a successful spike, parity checklist, packaging plan, and rollback plan.

Advantages:

- Could simplify a future Rust-oriented desktop story.
- May reduce runtime footprint if evidence supports it.

Limitations:

- Highest risk.
- Requires broad parity, packaging, support, accessibility, and release evidence.
- Not acceptable from this RFC alone.

## Proposed position

This RFC recommends **Option B only as a future gated spike**, not as an implementation in this PR.

The next acceptable step, if reviewers agree, is a separate Slint hello dashboard spike issue. That spike must be read-only, fixture-driven or `dashboard-data` driven, clearly labeled experimental, and excluded from installer and release workflows unless a later RFC changes that.

Electron remains the current and default desktop implementation.

## Decision gates

A future Slint spike may start only after these gates are satisfied:

1. This feasibility RFC is reviewed and accepted.
2. The spike scope is limited to a read-only hello dashboard.
3. The spike does not modify Electron runtime behavior.
4. The spike does not modify Python Core or Rust Guard behavior.
5. The spike does not modify packaging, installer, release workflow, tags, or v0.3.0 assets.
6. The spike has explicit cleanup and comparison criteria.

A future Slint migration proposal may start only after:

1. A spike demonstrates comparable dashboard workflows.
2. Build and packaging evidence is documented.
3. Test coverage is at least as clear as the current Electron baseline for the affected surface.
4. Accessibility, keyboard, and high-DPI behavior are reviewed.
5. Rollback to Electron remains possible.
6. A separate accepted RFC approves replacing or complementing Electron.

## Validation plan for this RFC

This documentation-only RFC is validated by static checks:

- The RFC file exists.
- README and roadmap link to the RFC.
- Non-goals explicitly state that no Slint runtime, crate, `.slint` file, Electron replacement, enforcement, monitoring expansion, release workflow change, tag change, or Stage 5 implementation is introduced.
- Repository tests continue to pass.

## Out of scope for current PR

- Slint dependencies, crates, generated files, or `.slint` UI assets.
- Desktop runtime behavior changes.
- Python Core or Rust Guard changes.
- Electron main/preload/IPC/renderer behavior changes.
- Packaging, installer, release workflow, tag, or GitHub Release changes.
- Any enforcement or monitoring implementation.
