# TraceSeal v0.2.0 Release Notes (Draft)

> **Status**: Release Candidate. This version has NOT been formally released.
> Clean Windows VM validation is still pending.
> The installer has NOT been code-signed.

## Overview

TraceSeal v0.2.0 introduces the Electron Desktop Dashboard, a React + TypeScript + TailwindCSS renderer that connects to the Python Core CLI for real-time data display. This release also adds Windows installer packaging via Electron Forge + PyInstaller.

## Key Features

### Desktop Dashboard

- **5 pages**: Home, Runs, Run Detail, Explain, Policy
- **20 components**: StatCard, RunsTable, EventTimeline, FileDiff, ShellOutput, HttpDetail, PolicyList, RiskBadge, etc.
- **Real data**: reads from the same `runs/` directory that the CLI produces
- **Workspace management**: choose any directory containing `runs/` and `policy/`

### Windows Installer

- Single `TraceSeal-Setup.exe` for Windows x64
- Bundled Python Core (`traceseal-core.exe`) — no Python installation required
- Bundled Renderer (`resources/renderer/index.html`) — no dev server needed
- SHA256 checksums for integrity verification

### Safety & Security

- `contextIsolation: true`, `nodeIntegration: false` in Electron
- Renderer only accesses data through fixed preload API
- `runId` validation rejects path traversal and absolute paths
- Corrupt individual runs do not break the entire run list

## Test Baseline

| Suite | Tests | Status |
|-------|-------|--------|
| Python | 13 | All passing |
| Renderer | 96 | All passing |
| Electron | 33 | All passing |

## Known Limitations

- Clean Windows VM validation has not been completed
- Installer is not code-signed (SmartScreen may show unknown publisher warning)
- No macOS or Linux installers
- Dashboard is read-only (no policy editing, no run triggering)
- Policy editor and attestation remain in future phases

## Installation

1. Download `TraceSeal-Setup.exe`
2. Verify `SHA256SUMS.txt` checksum
3. Run the installer
4. Launch TraceSeal from the Start menu or desktop shortcut
5. On first launch, select a workspace directory containing `runs/` and `policy/`

## Upgrading from v0.1.0

v0.2.0 is fully backward compatible with v0.1.0 `runs/` data. The CLI commands (`traceseal run`, `replay`, `explain`) remain unchanged. The new `dashboard-data` subcommands are additive.

## What's Next

- Clean Windows VM validation
- Code signing
- Phase 3: Core enhancements (file read interception, `os.system()`, `httpx`, Git diff, `policy.yaml` DSL)
- Phase 4: Rust Guard (OS-level process monitoring, cross-language agent support)