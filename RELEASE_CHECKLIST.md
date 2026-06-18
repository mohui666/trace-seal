# TraceSeal Release Checklist

## Phase 1: Code Freeze

- [ ] All tests pass: Python (13), Renderer (96), Electron (33)
- [ ] All typecheck pass: Renderer, Electron
- [ ] Renderer `npm run build` succeeds
- [ ] `git status` is clean on the release branch
- [ ] Version consistency: `pyproject.toml`, `desktop/electron/package.json`, `desktop/renderer/package.json`

## Phase 2: Documentation

- [ ] `CHANGELOG.md` updated with all changes
- [ ] `README.md` reflects current capabilities and limitations
- [ ] `docs/roadmap.md` updated with current phase status
- [ ] Release notes drafted (`docs/release-notes-v0.2.0.md`)
- [ ] No claims of: clean Windows validated, officially released, installer signed

## Phase 3: Build & Package

- [ ] `scripts/build-windows.ps1` completes without errors
- [ ] `TraceSeal-Setup.exe` generated
- [ ] `SHA256SUMS.txt` generated with correct hash
- [ ] `resources/renderer/index.html` present in output
- [ ] `resources/traceseal-core/traceseal-core.exe` present in output

## Phase 4: Verification

- [ ] `scripts/verify-release.ps1 -Mode Source` returns PASS
- [ ] `scripts/verify-release.ps1 -Mode Artifacts` returns PASS (after build)
- [ ] `scripts/verify-release.ps1 -Mode Artifacts` returns FAIL when artifacts are missing
- [ ] Branch validation: `main` or `v*` tag only for Artifacts mode
- [ ] `master` branch is explicitly rejected as invalid baseline

## Phase 5: Pre-release Testing

- [ ] Installer runs on development machine
- [ ] Dashboard loads with real workspace data
- [ ] Workspace switching works correctly
- [ ] Empty state / no runs state handled gracefully
- [ ] Unicode paths work correctly
- [ ] Clean Windows VM validation (PENDING - not yet completed)

## Phase 6: Release

- [ ] Tag created: `git tag -a v0.2.0 -m "TraceSeal v0.2.0"`
- [ ] Tag pushed: `git push origin v0.2.0`
- [ ] GitHub Release created with release notes
- [ ] `TraceSeal-Setup.exe` and `SHA256SUMS.txt` uploaded to Release
- [ ] Release notes published

> **Note**: This checklist is a template. v0.2.0 has NOT been formally released.
> Clean Windows VM validation is still pending.
> The installer has NOT been code-signed.