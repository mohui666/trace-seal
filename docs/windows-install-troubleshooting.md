# Windows install and SmartScreen troubleshooting

## Status

`v0.3.0` is the latest stable release. This guide covers the Windows x64 installer published for that release.

The installer is unsigned. SmartScreen warnings may appear on Windows because the installer is not code-signed.

## Download

Download `TraceSeal-Setup.exe` from the GitHub Release page for `v0.3.0`.

Use only the release asset from the project release page. Do not install files copied from unknown mirrors or chat attachments.

## Verify SHA256

Verify SHA256 before installing. Download `SHA256SUMS.txt` from the same `v0.3.0` release and compare it with the downloaded installer.

From PowerShell:

```powershell
Get-FileHash .\TraceSeal-Setup.exe -Algorithm SHA256
Get-Content .\SHA256SUMS.txt
```

The hash printed for `TraceSeal-Setup.exe` should match the value recorded in `SHA256SUMS.txt`.

## SmartScreen warning

Because the installer is unsigned, Windows SmartScreen may show an unknown publisher or reputation warning.

Before continuing:

- Confirm the file name is `TraceSeal-Setup.exe`.
- Confirm the file came from the `v0.3.0` GitHub Release.
- Confirm the SHA256 value matches `SHA256SUMS.txt`.

If those checks pass and you choose to continue, use the Windows SmartScreen details link and continue option shown by Windows.

## Install

Run `TraceSeal-Setup.exe` on Windows x64 and follow the installer prompts.

After installation, open the desktop app from the Start menu or the installed shortcut. The desktop app remains the Electron implementation for this release.

## Uninstall / reinstall

Use Windows Settings or Control Panel to uninstall TraceSeal.

For a clean reinstall:

1. Close TraceSeal.
2. Uninstall the existing version.
3. Download the `v0.3.0` installer again from the GitHub Release page.
4. Verify SHA256 again.
5. Run the installer.

## What this does not change

This document does not modify release assets, packaging, tags, or installer behavior.

It does not create `v0.3.1`, change release workflows, sign the installer, or change Python Core, Rust Guard, Electron, or Slint behavior.

---

# Windows 安装与 SmartScreen 排查

## 状态

`v0.3.0` 是当前最新稳定版本。本文档说明该版本 Windows x64 安装器的安装与排查步骤。

安装器未签名。由于安装器没有代码签名，Windows 可能出现 SmartScreen 警告。

## 下载

请从 `v0.3.0` 的 GitHub Release 页面下载 `TraceSeal-Setup.exe`。

只使用项目 Release 页面上的 release asset。不要安装来自未知镜像或聊天附件的文件。

## 校验 SHA256

安装前应校验 SHA256。请从同一个 `v0.3.0` release 下载 `SHA256SUMS.txt`，并与安装器文件进行比对。

在 PowerShell 中运行：

```powershell
Get-FileHash .\TraceSeal-Setup.exe -Algorithm SHA256
Get-Content .\SHA256SUMS.txt
```

`TraceSeal-Setup.exe` 打印出的 hash 应与 `SHA256SUMS.txt` 中记录的值一致。

## SmartScreen 警告

因为安装器未签名，Windows SmartScreen 可能显示未知发布者或信誉提示。

继续前请确认：

- 文件名是 `TraceSeal-Setup.exe`。
- 文件来自 `v0.3.0` GitHub Release。
- SHA256 值与 `SHA256SUMS.txt` 一致。

如果以上检查通过，并且你决定继续安装，可以使用 Windows SmartScreen 界面中的详细信息和继续选项。

## 安装

在 Windows x64 上运行 `TraceSeal-Setup.exe`，并按安装器提示操作。

安装完成后，可从开始菜单或已安装的快捷方式打开桌面应用。本 release 的桌面应用仍是 Electron 实现。

## 卸载 / 重装

使用 Windows 设置或控制面板卸载 TraceSeal。

如需干净重装：

1. 关闭 TraceSeal。
2. 卸载已有版本。
3. 再次从 GitHub Release 页面下载 `v0.3.0` 安装器。
4. 重新校验 SHA256。
5. 运行安装器。

## 本文档不改变什么

本文档不修改 release assets、packaging、tag 或安装器行为。

本文档不会创建 `v0.3.1`，不会修改 release workflow，不会给安装器签名，也不会修改 Python Core、Rust Guard、Electron 或 Slint 行为。
