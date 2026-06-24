# Slint preview artifact

## Status

The Slint preview artifact is experimental-only.

It is built by the manual `Slint Preview` workflow.

It is uploaded only as a GitHub Actions workflow artifact.

It is not a GitHub Release.

It is not `TraceSeal-Setup.exe`.

It is not the v0.3.0 release installer.

Electron remains the default desktop implementation.

Slint has not replaced Electron.

The workflow does not create or modify tags.

The workflow does not create v0.3.1.

The workflow does not modify v0.3.0 release assets.

## How to build

Use GitHub Actions to run the manual preview workflow:

```text
GitHub Actions -> Slint Preview -> Run workflow
```

The workflow builds `traceseal-desktop-slint` on a Windows runner in release mode and uploads only a workflow artifact.

## How to download

After the workflow completes, download the preview from:

```text
GitHub Actions -> Slint Preview -> completed run -> Artifacts
```

Download the `traceseal-slint-preview-windows-experimental` artifact.

## What the artifact contains

The artifact contains:

- `TraceSeal-Slint-Preview.exe`
- `SHA256SUMS.txt`

`TraceSeal-Slint-Preview.exe` is the experimental Slint preview binary copied from the `traceseal-desktop-slint` release build output.

## What this is not

This preview artifact is not a published release, not a release asset, and not an installer for the stable desktop path.

It does not replace Electron, does not make Slint the default desktop, does not create or modify tags, does not create v0.3.1, and does not modify v0.3.0 release assets.

## Verification

After downloading and extracting the workflow artifact, compute the SHA256 hash:

```powershell
Get-FileHash .\TraceSeal-Slint-Preview.exe -Algorithm SHA256
```

Compare the hash with the value recorded in the artifact's `SHA256SUMS.txt`.

---

# Slint 预览构建产物

## 状态

Slint 预览构建产物仅用于实验。

它由手动触发的 `Slint Preview` workflow 构建。

它只作为 GitHub Actions workflow artifact 上传。

它不是 GitHub Release。

它不是 `TraceSeal-Setup.exe`。

它不是 v0.3.0 发布安装器。

Electron 仍是默认桌面实现。

Slint 尚未替代 Electron。

该 workflow 不创建或修改 tag。

该 workflow 不创建 v0.3.1。

该 workflow 不修改 v0.3.0 release assets。

## 如何构建

在 GitHub Actions 中手动运行预览 workflow：

```text
GitHub Actions -> Slint Preview -> Run workflow
```

该 workflow 在 Windows runner 上以 release mode 构建 `traceseal-desktop-slint`，并且只上传 workflow artifact。

## 如何下载

workflow 完成后，从这里下载预览产物：

```text
GitHub Actions -> Slint Preview -> completed run -> Artifacts
```

下载 `traceseal-slint-preview-windows-experimental` artifact。

## 产物包含什么

artifact 包含：

- `TraceSeal-Slint-Preview.exe`
- `SHA256SUMS.txt`

`TraceSeal-Slint-Preview.exe` 是从 `traceseal-desktop-slint` release build 输出复制出的实验 Slint 预览二进制。

## 这不是什么

该预览 artifact 不是已发布 release，不是 release asset，也不是稳定桌面路径的安装器。

它不替代 Electron，不让 Slint 成为默认桌面，不创建或修改 tag，不创建 v0.3.1，也不修改 v0.3.0 release assets。

## 校验

下载并解压 workflow artifact 后，计算 SHA256 hash：

```powershell
Get-FileHash .\TraceSeal-Slint-Preview.exe -Algorithm SHA256
```

将 hash 与 artifact 中的 `SHA256SUMS.txt` 记录值进行比对。
