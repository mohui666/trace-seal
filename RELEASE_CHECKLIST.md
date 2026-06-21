# TraceSeal v0.3.0 Release Checklist

> Status: **Core complete / release-prep validated / release finalization in progress**
>
> Validation date: 2026-06-19 (Asia/Shanghai)
>
> Validation baseline: `520276d42c90d6c528a250cb51ade473c560c08b` on `chore/v0.3-release-prep`

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
- [ ] Install and relaunch the v0.3.0 release candidate on a clean Windows VM.
- [ ] Code-sign the Windows installer (current known limitation).

## Phase 5: Documentation and release metadata

- [x] README covers all Stage 3 Core capabilities and says v0.3.0 is not released.
- [x] Roadmap marks every Stage 3 Core item complete.
- [x] Spec and test report match the validated behavior and test counts.
- [x] `artifacts/v0.3-release-prep-report.md` records reproducible evidence.
- [x] `scripts/verify-release.ps1 -Mode Source` returns PASS; the prep branch produces the expected non-standard-branch warning.
- [x] Update Python, Renderer and Electron release version metadata from 0.2.0 to 0.3.0 in the explicit release step.
- [ ] Run Artifacts-mode verification from `main` or the final `v0.3.0` tag.

## Phase 6: Publication (intentionally not done in this PR)

- [ ] Create annotated tag `v0.3.0`.
- [ ] Push tag `v0.3.0`.
- [ ] Create the GitHub Release.
- [ ] Upload the verified installer and `SHA256SUMS.txt`.
- [ ] Publish v0.3.0 release notes.

## Known limitations

- TraceSeal still targets Python Agents and uses process-level monkey patches.
- The sandbox is a copied workspace, not Docker/overlayfs or an OS-level guard.
- Replay is transcript replay and does not re-execute side effects.
- HTTP cassette stores privacy-preserving metadata and body hashes, not full deterministic traffic.
- The generated installer is unsigned and was package-verified locally, but the v0.3.0 release candidate has not yet completed a clean-VM install/relaunch gate.
- Rust Guard remains a future Stage 4 item and is not part of v0.3.0 release prep.
