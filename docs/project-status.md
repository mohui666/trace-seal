# Project status

## Stable release

- v0.3.0 is the latest stable release.
- v0.3.0 tag remains at 59ae99d6db495276963e2f4b47b137f4de846d35.
- There is no v0.3.1.
- v0.2.0 remains an older published release.

## Completed stages

- Stage 1 delivered the Python CLI MVP for recording, replay, explain, policy checks, sandboxed demo runs, and incident examples.
- Stage 2 delivered the Electron desktop baseline that reads Python Core data through fixed IPC and dashboard-data surfaces.
- Stage 3 delivered Core enhancements in v0.3.0: file-read metadata, `os.system()` capture, `httpx` capture, Git state, redacted HTTP cassette output, YAML policy, Git push classification, domain policy, cascade analysis, and Windows build CI.
- Stage 4 delivered dry-run / observe-only Guard evidence, validation notes, and RFCs. It did not turn TraceSeal into an enforcing system security product.

## Current desktop implementations

- Electron remains the default desktop implementation.
- The Electron renderer consumes Python Core `dashboard-data` output.
- Python Core remains the source of truth for run, replay, explain, policy, recorder, and dashboard-data behavior.

## Slint experimental status

- Slint remains experimental-only.
- Slint remains experimental and separate from the default Electron desktop.
- Slint has a hello dashboard spike, read-only dashboard-data bridge, parser tests, and UI polish.
- Slint is not packaged or released.
- Slint does not replace Electron.

## Rust Guard status

- Rust Guard remains dry-run / observe-only unless later implementation says otherwise.
- Guard artifacts and policy decisions are evidence outputs, not blocking controls.
- Enforcement is not implemented.
- No daemon or service is installed.
- No OS-wide process monitoring is added.

## Rust Core status

- Rust Core parity is RFC-only / planning unless later implementation exists.
- Python Core remains the source of truth.
- Rust Core has not replaced Python Core.

## Release and tag boundaries

- `v0.3.0` remains the latest stable release.
- The `v0.3.0` tag remains at `59ae99d6db495276963e2f4b47b137f4de846d35`.
- There is no `v0.3.1` tag or release.
- This status page does not modify published release assets.

## Known non-goals

- No enforcement implementation.
- No daemon or service.
- No OS-wide monitoring.
- No replacement of Electron by Slint.
- No replacement of Python Core by Rust Core.
- No packaging or release workflow change from this documentation cleanup.
