# Changelog

All notable changes to TraceSeal will be documented in this file.

## [v0.3.0] - 2026-06-21

### Added

- Git branch, HEAD, dirty, staged, unstaged, and untracked state captured before and after Agent runs.
- Privacy-preserving `http_cassette.jsonl` artifacts with redacted headers/query values and body summaries.
- Workspace `policy.yaml` / `policy.yml` DSL with safe default-JSON fallback.
- Git push classification for normal, force, force-with-lease, mirror, delete, force-refspec, branches, and tags.
- Domain allow/deny/warn policy without DNS resolution.
- Deterministic cascade detection across sensitive reads, HTTP exfiltration attempts, configuration corruption, destructive shell commands, and dangerous Git pushes.

### Changed

- dashboard-data, replay, and explain now expose Stage 3 Git, HTTP cassette, policy, domain, and cascade evidence.
- Python regression baseline increased to 90 tests; Renderer remains 96 tests and Electron 45 tests.

### Safety and packaging

- Release demos use loopback or mocked HTTP and simulated Git push; they do not access real external targets.
- HTTP request/response bodies and sensitive header/query values are not stored in full.
- Windows x64 remains the primary validated desktop target.
- The Windows installer is unsigned; macOS and Linux desktop packages are not release-validated.
- Rust Guard remains future productization work and is not part of v0.3.0.

## [v0.2.0] - 2026-06 (Release Candidate)

### Added

- **Electron data runtime layer** (`desktop/electron/`): main process, preload, IPC, and Python CLI runner. Production mode calls bundled `traceseal-core.exe` instead of requiring a system Python installation.
- **React + TypeScript + TailwindCSS Renderer** (`desktop/renderer/`): 5 pages (Home, Runs, Run Detail, Explain, Policy) with 20 components and comprehensive test coverage.
- **Workspace management**: system directory picker, `settings.json` persistence, workspace switching with automatic data refresh.
- **Windows installer packaging**: Electron Forge + PyInstaller producing `TraceSeal-Setup.exe` with SHA256 checksums.
- **One-click build script** (`scripts/build-windows.ps1`): automated Python tests, PyInstaller packaging, Renderer/Electron build and test, and resource verification.
- **Release verification script** (`scripts/verify-release.ps1`): Source and Artifacts mode validation.
- **GitHub Actions CI**: Windows build workflow (`windows-build.yml`) and release workflow (`release.yml`).
- New `dashboard-data` subcommands: `latest`, `list`, `run <run_id>`, `policy`.
- Dashboard JSON export safety: path traversal rejection, corrupt run isolation, stderr diagnostics.
- `examples/bad_agent_env.py`, `examples/bad_agent_git.py`, `examples/bad_agent_http.py` demo cases.
- `docs/demo.md`, `docs/test-report.md`, `docs/dashboard-design.md`.

### Changed

- Dashboard data JSON now includes `high_risk_count`, `first_harmful_event`, `affected_files`, `suggested_policy` fields.
- `runId` validation rejects absolute paths, `../`, and path traversal.
- Policy mode defaults to `warn`; configurable via `TRACESEAL_POLICY_MODE=block`.
- `policy/default_policy.json` expanded to 4 rules: `dangerous_delete`, `env_write`, `git_push`, `suspicious_http_post`.

### Fixed

- Various safety and null-safety improvements across Renderer pages.
- Electron IPC channel hardening: `contextIsolation: true`, `nodeIntegration: false`, fixed preload API.

### Test Baseline

| Suite | Tests |
|-------|-------|
| Python | 13 |
| Renderer | 96 |
| Electron | 33 |

---

## [v0.1.0] - 2026-06

### Added

- Initial Python CLI MVP: `traceseal run`, `traceseal replay`, `traceseal explain`.
- `sitecustomize` + monkey-patch hooks for file write, shell, HTTP, and delete API interception.
- Sandbox workspace isolation via directory copy.
- JSONL event recorder with manifest and workspace snapshots.
- Policy engine with `warn/mark` mode and `default_policy.json`.
- First harmful event minimizer / explainer.
- `examples/bad_agent_delete.py` demo.
- `tests/test_mvp.py` with 5 core test cases.
- Project documentation: spec, policy rules, incident examples, roadmap.
