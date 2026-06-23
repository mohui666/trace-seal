# Release verification checklist

## Status

`v0.3.0` is the latest stable release.

This checklist is for verifying the existing `v0.3.0` release after download. It is documentation-only.

## Verify tag

Confirm the release tag resolves to the expected commit:

```powershell
git fetch --all --prune
git tag --list
git rev-parse "v0.3.0^{commit}"
```

v0.3.0 points to 59ae99d6db495276963e2f4b47b137f4de846d35.

## Verify GitHub Release

Confirm the GitHub Release exists and is still attached to `v0.3.0`:

```powershell
gh release view v0.3.0 --repo mohui666/trace-seal --json name,isDraft,isPrerelease,tagName,assets
```

The release assets are `SHA256SUMS.txt` and `TraceSeal-Setup.exe`.

The release should not be a draft or prerelease.

## Verify SHA256

Download both `TraceSeal-Setup.exe` and `SHA256SUMS.txt` from the `v0.3.0` GitHub Release.

Verify SHA256 before installing:

```powershell
Get-FileHash .\TraceSeal-Setup.exe -Algorithm SHA256
Get-Content .\SHA256SUMS.txt
```

The hash for `TraceSeal-Setup.exe` should match the value recorded in `SHA256SUMS.txt`.

## Confirm no new release

Confirm there is no newer release boundary:

```powershell
git tag --list "v0.3.1"
gh release view v0.3.1 --repo mohui666/trace-seal
```

There is no v0.3.1 tag or release.

## What this does not change

This document does not modify tags, release assets, packaging, or release workflows.

It does not create a release, create `v0.3.1`, change installer behavior, or modify Python Core, Rust Guard, Electron, or Slint.

---

# Release 校验清单

## 状态

`v0.3.0` 是当前最新稳定版本。

本清单用于在下载后校验现有的 `v0.3.0` release。本文档仅修改文档。

## 校验 tag

确认 release tag 指向预期 commit：

```powershell
git fetch --all --prune
git tag --list
git rev-parse "v0.3.0^{commit}"
```

v0.3.0 指向 59ae99d6db495276963e2f4b47b137f4de846d35。

## 校验 GitHub Release

确认 GitHub Release 存在，并且仍关联到 `v0.3.0`：

```powershell
gh release view v0.3.0 --repo mohui666/trace-seal --json name,isDraft,isPrerelease,tagName,assets
```

release assets 包含 `SHA256SUMS.txt` 和 `TraceSeal-Setup.exe`。

该 release 不应是 draft 或 prerelease。

## 校验 SHA256

从 `v0.3.0` GitHub Release 下载 `TraceSeal-Setup.exe` 和 `SHA256SUMS.txt`。

安装前校验 SHA256：

```powershell
Get-FileHash .\TraceSeal-Setup.exe -Algorithm SHA256
Get-Content .\SHA256SUMS.txt
```

`TraceSeal-Setup.exe` 的 hash 应与 `SHA256SUMS.txt` 中记录的值一致。

## 确认没有新 release

确认没有新的 release 边界：

```powershell
git tag --list "v0.3.1"
gh release view v0.3.1 --repo mohui666/trace-seal
```

不存在 v0.3.1 tag 或 release。

## 本文档不改变什么

本文档不修改 tag、release assets、packaging 或 release workflow。

本文档不会创建 release，不会创建 `v0.3.1`，不会修改安装器行为，也不会修改 Python Core、Rust Guard、Electron 或 Slint。
