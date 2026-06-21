# TraceSeal v0.3.0 Release Checklist

> Status: **RELEASED**
>
> Release date: 2026-06-21 (Asia/Shanghai)
>
> Tag commit: `59ae99d6db495276963e2f4b47b137f4de846d35`

## Phase 1: Core regression

- [x] Python `compileall` passes.
- [x] Python unittest suite passes: 90/90.
- [x] File read/write, `subprocess.run()`, `os.system()`, HTTP/httpx, replay, explain and dashboard-data regressions pass.
- [x] Git state, HTTP cassette, policy YAML, Git push classification, domain policy and cascade regressions pass.
- [x] Seven Stage 3 demos create runs without crashing.
- [x] dashboard-data, replay and explain return successfully for every validated demo.

## Phase 2: Privacy and safety

- [x] No full cascade/demo token, Authorization bearer value or Cookie value appears in validated run artifacts or CLI exports.
- [x] HTTP cassette contains request/response body summaries only; no raw body fields are present.
- [x] Domain demo uses `httpx.MockTransport` and performs no DNS/network access.
- [x] Git push demos use TraceSeal simulation and do not contact a remote.
- [x] Destructive demos operate only inside copied sandbox workspaces.

## Phase 3: Dashboard and desktop

- [x] Renderer typecheck passes.
- [x] Renderer tests pass: 96/96.
- [x] Renderer production build passes.
- [x] Electron typecheck passes.
- [x] Electron tests pass: 45/45.

## Phase 4: Windows build and package

- [x] `scripts/build-windows.ps1 -SkipInstall` completes without errors.
- [x] PyInstaller bundled core builds and passes `dashboard-data policy` smoke test.
- [x] Electron Forge produces `TraceSeal-Setup.exe`.
- [x] Packaged `resources/renderer/index.html` is present.
- [x] Packaged `resources/traceseal-core/traceseal-core.exe` is present.
- [x] `SHA256SUMS.txt` matches the generated installer.
- [x] Windows GitHub Actions build passed for baseline `520276d` ([run 27829438486](https://github.com/mohui666/trace-seal/actions/runs/27829438486)).
- [x] Final Windows x64 release installer build and package verification pass.
- [ ] Code-sign the Windows installer (current known limitation).

## Phase 5: Documentation and release metadata

- [x] README covers all Stage 3 Core capabilities and records v0.3.0 as released.
- [x] Roadmap marks every Stage 3 Core item complete.
- [x] Spec and test report match the validated behavior and test counts.
- [x] `artifacts/v0.3-release-prep-report.md` records reproducible evidence.
- [x] `scripts/verify-release.ps1 -Mode Source` returns PASS; the prep branch produces the expected non-standard-branch warning.
- [x] Update Python, Renderer and Electron release version metadata from 0.2.0 to 0.3.0 in the explicit release step.
- [x] Artifacts-mode verification completed for the final `v0.3.0` release.

## Phase 6: Publication

- [x] Annotated tag `v0.3.0` created at `59ae99d6db495276963e2f4b47b137f4de846d35`.
- [x] Tag `v0.3.0` pushed without rewrite.
- [x] GitHub Release published: <https://github.com/mohui666/trace-seal/releases/tag/v0.3.0>.
- [x] `TraceSeal-Setup.exe` uploaded.
- [x] `SHA256SUMS.txt` uploaded.
- [x] Downloaded artifact checksum verified against `SHA256SUMS.txt`.
- [x] Installer SHA-256 verified as `9a5e11083377c96b5d41b97fef81875120a66debce731ff23e4ed76ca08eefac`.
- [x] Release workflow [27901748342](https://github.com/mohui666/trace-seal/actions/runs/27901748342) completed successfully.
- [x] Known limitations documented in the release report and release notes.

## Known limitations

- TraceSeal still targets Python Agents and uses process-level monkey patches.
- The sandbox is a copied workspace, not Docker/overlayfs or an OS-level guard.
- Replay is transcript replay and does not re-execute side effects.
- HTTP cassette stores privacy-preserving metadata and body hashes, not full deterministic traffic.
- Windows x64 is the primary validated desktop target; macOS/Linux desktop packaging is not release-validated.
- The generated Windows installer is unsigned.
- Rust Guard remains a future Stage 4 design item and is not included in v0.3.0.
- `origin/jimmma` remains preserved for later review.
