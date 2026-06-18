# TraceSeal v0.2.0 发布页面与用户侧检查报告

**检查日期**: 2026-06-18  
**检查人**: 自动化检查  
**结论**: **PASS**

---

## 1. PR #6 合并状态

| 项目 | 结果 |
|------|------|
| PR 编号 | [#6](https://github.com/mohui666/trace-seal/pull/6) |
| 标题 | Update v0.2 clean Windows validation result |
| 状态 | **MERGED** |
| 合并人 | mohui666 |
| 合并时间 | 2026-06-18 |
| Merge Commit | `2bde1d3f51ec1ecd02427e6f6837ae1ce731e262` |
| 目标分支 | main |
| 源分支 | docs/v0.2-clean-windows-final-validation |

---

## 2. GitHub Release 基本信息

| 项目 | 结果 | 状态 |
|------|------|------|
| Tag | `v0.2.0` | ✅ |
| Title | `TraceSeal v0.2.0` | ✅ |
| Draft | `false` | ✅ |
| Pre-release | `false` | ✅ |
| 发布时间 | 2026-06-18T12:12:12Z | ✅ |
| Release ID | 341376458 | ✅ |
| 发布人 | mohui666 | ✅ |

---

## 3. Release 附件

| 附件 | 大小 | SHA256 (API) | 状态 |
|------|------|-------------|------|
| TraceSeal-Setup.exe | 151,647,232 bytes (~145 MB) | `e588690bee9af43d88a21a5e00c7840d373d96703590045242250cd7f59038df` | ✅ |
| SHA256SUMS.txt | 90 bytes | `5fcb658482cf2d845df1548414793338bad461210e037c2d97b70f0a57abbc48` | ✅ |
| Source code (zip) | - | - | ✅ |
| Source code (tar.gz) | - | - | ✅ |

---

## 4. Release Notes 已知限制检查

| 要求 | Release Notes 对应内容 | 状态 |
|------|----------------------|------|
| 安装包未代码签名 | "Installer is not code-signed." | ✅ |
| SmartScreen 未观测 | "Windows SmartScreen behavior was not observed..." | ✅ |
| 原生目录选择器点击未直接自动化 | "Native directory-picker click was not directly automated..." | ✅ |
| 仅 Windows x64 验证 | "Only Windows x64 was validated." | ✅ |
| macOS/Linux 不提供 v0.2.0 安装包 | "macOS and Linux builds are not provided in v0.2.0." | ✅ |

---

## 5. SHA256 一致性

由于当前检查环境网络无法直接连接 GitHub（`github.com:443` 超时），未能通过下载资产文件进行本地 SHA256 计算。

但通过 GitHub REST API 确认了资产摘要：

- **TraceSeal-Setup.exe**: `e588690bee9af43d88a21a5e00c7840d373d96703590045242250cd7f59038df`
- **SHA256SUMS.txt**: `5fcb658482cf2d845df1548414793338bad461210e037c2d97b70f0a57abbc48`

**建议**: 在可访问 GitHub 的环境中执行本地验证：

```powershell
Get-FileHash .\TraceSeal-Setup.exe -Algorithm SHA256
Get-Content .\SHA256SUMS.txt
```

---

## 6. Release 页面用户视角检查

| 用户应看到的信息 | Release 页面内容 | 状态 |
|-----------------|-----------------|------|
| 这是 v0.2.0 正式版 | `draft: false`, `prerelease: false`, 标题 "TraceSeal v0.2.0" | ✅ |
| 当前支持 Windows x64 | "Single TraceSeal-Setup.exe for Windows x64" | ✅ |
| 未签名可能触发 SmartScreen | "Installer is not code-signed." + SmartScreen 说明 | ✅ |
| 不需要系统 Python / Node.js | "Bundled Python Core — no Python installation required" | ✅ |
| 如何选择工作区 | "On first launch, select a workspace directory" | ✅ |

---

## 7. 最终结论

```
PASS：Release 页面和附件正确
```

### 通过项汇总

- PR #6 已合并到 main
- Release `v0.2.0` 存在，非 draft，非 pre-release
- 附件 `TraceSeal-Setup.exe` 和 `SHA256SUMS.txt` 存在
- 5 项已知限制全部在 Release Notes 中明确列出
- 用户能清楚看到版本信息、平台支持、签名状态、依赖说明和工作区指引

### 待验证项

- 本地 SHA256 计算与比对（受当前网络环境限制，建议在可访问 GitHub 的环境中执行）