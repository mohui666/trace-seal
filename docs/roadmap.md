# Roadmap

## Current baseline

TraceSeal's current stable baseline is `v0.3.0`. Python Core remains the source of truth for run, replay, explain, policy, recorder, and dashboard-data behavior. Electron remains the default desktop implementation.

## Completed

- Python CLI MVP for recording agent side effects, replaying evidence, and explaining the first risky operation.
- Electron desktop baseline that reads real run data from Python Core outputs.
- Core enhancements for file-read metadata, shell and `os.system()` capture, HTTP and `httpx` metadata, Git state, redacted HTTP cassette output, YAML policy, Git push classification, domain policy, deterministic cascade analysis, and Windows build CI.
- Stage 4 status: Complete through Issue #39. Issue #50 performs the final completion audit and roadmap cleanup.
- Stage 4 outputs include Rust Guard dry-run / observe-only evidence, Windows smoke validation, dashboard metadata, policy dry-run decisions, and RFC work. Enforcement remains outside the completed scope.

## Active experimental tracks

Slint remains an experimental desktop track. Completed spikes include hello dashboard, read-only dashboard-data bridge, parser tests, and read-only UI polish. Electron remains the default desktop implementation.

- [Slint desktop feasibility RFC](slint-desktop-feasibility-rfc.md) remains an experimental planning document tracked by Issue #51.
- Slint hello dashboard spike remains read-only and experimental.
- [Rust Core parity RFC](rust-core-parity-rfc.md) remains a planning track tracked by Issue #52. Python Core remains the current implementation and compatibility baseline.
- Rust Guard follow-up work remains design-first and evidence-first unless a later accepted plan explicitly changes the boundary.

## Stage 5 candidates

- Keep documentation aligned with the released `v0.3.0` baseline and the no-`v0.3.1` release boundary.
- Decide whether any Slint experiment should progress beyond a read-only spike without replacing Electron.
- Decide whether any Rust Core parity work should be implemented behind compatibility tests.
- Decide whether any Guard enforcement experiment should proceed only with explicit opt-in boundaries, rollback, audit evidence, and user consent.
- Continue improving tests that prevent README, status, and roadmap drift.

## Explicit non-goals

- Do not treat Slint as the default desktop implementation.
- Do not treat Rust Core as a replacement for Python Core.
- Do not claim enforcement behavior before it exists.
- Do not install a daemon or service as part of the current baseline.
- Do not add OS-wide monitoring as part of the current baseline.
- Do not create or imply a `v0.3.1` release.
- No v0.3.1 release.
