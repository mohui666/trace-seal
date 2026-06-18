## Description

<!-- Briefly describe the changes in this PR. -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Release engineering / CI
- [ ] Test improvement
- [ ] Other (please describe)

## Test Plan

<!-- How have you tested these changes? -->

- [ ] Python tests pass (`python -m unittest discover -s tests -v`)
- [ ] Renderer typecheck passes (`npm run typecheck`)
- [ ] Renderer tests pass (`npm test`)
- [ ] Renderer build succeeds (`npm run build`)
- [ ] Electron typecheck passes (`npm run typecheck`)
- [ ] Electron tests pass (`npm test`)

## Release Checklist (if applicable)

- [ ] Version consistency across `pyproject.toml`, `desktop/electron/package.json`, `desktop/renderer/package.json`
- [ ] `CHANGELOG.md` updated
- [ ] No claims of clean Windows validated, officially released, or installer signed
- [ ] `scripts/verify-release.ps1 -Mode Source` returns PASS
- [ ] `scripts/verify-release.ps1 -Mode Artifacts` returns FAIL when artifacts are missing

## Additional Notes

<!-- Any other context about the PR. -->