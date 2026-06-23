# TraceSeal 路线图

## 阶段 1：Python CLI MVP — 已完成

**时间**：2026 Q2

目标：把一次 Agent 事故完整记录下来，能够回放时间线，并指出首次有害调用。

### 已交付

| 模块 | 内容 |
|---|---|
| sdk | 文件写入、Shell、删除 API、HTTP 请求、Git push 风险拦截/模拟 |
| sandbox | workspace 复制隔离 |
| recorder | `events.jsonl` + `manifest.json` + workspace 快照 |
| replay | Transcript 回放 |
| policy | `dangerous_delete`、`env_write`、`git_push`、`suspicious_http_post` |
| minimizer | 首次有害工具调用定位 |
| cli | `run/replay/explain/dashboard-data` |
| examples | delete/env/git/http 四个 bad agent demo |
| tests | 5 个 unittest 覆盖核心链路 |
| docs | spec、policy、incident、dashboard、demo、roadmap、test-report |

### 当前指标

- 规则数：7 条
- Demo 数：9 个
- 自动测试：Python 90 个、Renderer 96 个、Electron 45 个
- Dashboard 数据接口：1 个 JSON export
- 默认安全模式：warn；可通过 `TRACESEAL_POLICY_MODE=block` 切换阻断

### 当前限制

| 限制 | 说明 | 计划解决阶段 |
|---|---|---|
| 仅支持 Python Agent | 拦截通过 monkey-patch 实现，不适用于其他语言 | Rust Guard 阶段 |
| Sandbox 为目录复制 | 不是 Docker/overlayfs，无真正资源隔离 | Core 增强 / Rust Guard |
| 无独立 Git hook | Git 操作通过 subprocess 间接捕获 | Core 增强 |
| 无 `os.system()` 拦截 | 仅拦截 `subprocess.run()` | Core 增强 |
| `httpx` 为 Python 层拦截 | 已覆盖函数式 API、`Client` 和 `AsyncClient`，非系统级防火墙 | Rust Guard |
| Policy DSL 为本地工作区文件 | 已支持 YAML DSL，暂不提供 UI/云端策略 | Core 增强 |
| Dashboard 仍是最小原型 | 已接入 Electron + Renderer + 真实 runs，交互和视觉还需打磨 | 阶段 2/3 |
| 无防篡改日志 | 审计日志当前可被修改 | Rust Guard 阶段 |

---

## 阶段 2：最小 Electron Desktop Dashboard — 已完成

**时间**：2026 Q3

目标：把 CLI MVP 升级为可展示的桌面原型。

核心原则：Electron 只负责展示和调用 Python CLI，Python Core 继续负责真实的 run / replay / explain / policy / recorder。

### 技术栈

- Electron
- React
- TypeScript
- TailwindCSS
- Python Core CLI 作为数据来源

### 已交付

| 模块 | 内容 |
|---|---|
| Electron 壳 | 已完成：本地桌面窗口，开发模式加载 Vite URL 或 renderer dist |
| 数据桥接 | 已完成：`latest/list/run/policy/runtimeInfo` Python JSON 接口和 Electron IPC runner |
| 安全边界 | 已完成：`contextIsolation: true`、`nodeIntegration: false`、固定 preload API |
| 打包分发 | 已完成：Electron Forge + PyInstaller，生成 `TraceSeal-Setup.exe` |
| 无 Python 分发 | 已完成：生产环境调用 `resources/traceseal-core/traceseal-core.exe` |
| 工作区选择 | 已完成：系统目录选择框、`settings.json` 持久化、切换/清除和数据自动刷新 |
| 正式发布检查 | 已完成：资源校验、干净 Windows VM 验证、Windows x64 安装包和 `SHA256SUMS.txt` |
| 首页 | 已最小接入：run 概览、事件数、高风险数、最近事故；后续继续视觉打磨 |
| Runs 列表 | 已最小接入：run_id、命令、时间、退出码、事件数、高风险数 |
| Run Detail | 已最小接入：事件时间线、事件详情、文件变更、Shell/HTTP 摘要 |
| Explain 卡片 | 已最小接入：展示 `first_harmful_event`、affected files、suggested policy |
| Policy 只读页 | 已最小接入：展示当前 `policy/default_policy.json` |

### 不做

- 不做云同步
- 不做用户登录
- 不做复杂图表
- 不做 policy 编辑器完整闭环
- 不把拦截逻辑搬进 Electron

### v0.2.0 正式发布状态

- 已完成开发模式真实 runs 联调。
- 已完成本机打包版和安装版验证。
- 已验证工作区持久化、无效目录、Unicode 路径和无 runs 空状态。
- 已完成独立干净 Windows VM 验证，结论为 `PASS WITH KNOWN ISSUES`。
- v0.2.0 已正式发布，Windows x64 安装包可从 GitHub Releases 获取。
- 安装包尚未代码签名，SmartScreen 可能提示未知发布者。
- 当前仅验证 Windows x64；未提供 macOS/Linux 安装包。
- 当前仍仅支持 Python Agent，Sandbox 仍为目录复制。

---

## 阶段 3：Core 增强 — 已完成

目标：补齐当前 Python Core 的工程缺口。

**发布状态**：Stage 3 Core 已全部完成，并于 2026-06-19 通过 release-prep 回归；v0.3.0 已于 2026-06-21 正式发布。Rust Guard 属于阶段 4 远期规划，目前仅处于 design phase，不在 v0.3.0 范围。

| 能力 | 状态 |
|---|---|
| 文件读取记录 | 已完成：Python `open` / `Path` 常见读取 API，只记录元数据 |
| `os.system()` 拦截 | 已完成 |
| `httpx` 拦截 | 已完成：同步/异步 API、元数据记录、敏感 header/query 脱敏 |
| Git diff / HEAD / staged 记录 | 已完成：run 前后记录 branch、HEAD、status、staged、unstaged、untracked 元数据，并导出 dashboard-data 摘要 |
| HTTP cassette 脱敏记录 | 已完成：从 HTTP 事件生成脱敏 JSONL，记录 header/query 脱敏、body 摘要、风险与 dashboard-data 摘要 |
| `policy.yaml` DSL | 已完成：schema/加载/校验/匹配、JSON fallback、policy source 与 explain metadata |
| force push 与普通 push 细分 | 已完成：normal/force/force-with-lease/mirror/delete/refspec/all/tags 分类与离线模拟 metadata |
| 域名白名单 / 黑名单 | 已完成：allow/deny/warn/unknown external、localhost/loopback/private 分类及 HTTP/cassette metadata |
| 级联错误案例 | 已完成：5 类 deterministic stage 检测、high/critical 聚合、离线 demo 与 dashboard-data/replay/explain summary |
| GitHub Actions Windows 构建 CI | 已完成 |

---

## 阶段 4：Rust Guard dry-run / observe-only — 已完成（未发布为产品化 Guard）

Stage 4 status: Complete through Issue #39. Issue #50 performs the final completion audit and roadmap cleanup.

Stage 4 明确不做 Rust Core 重构，也不替代当前 Python MVP。它已完成 `guard.event.v1` schema、Rust `guard.health` prototype、非执行型 `process.spawn` dry-run event、可选 Python Core import、只读 `dashboard-data` Guard metadata、Guard policy dry-run decisions、Windows VM smoke validation，以及 [Stage 4 Enforcement Experiment RFC](stage4-enforcement-experiment-rfc.md)。Stage 4 completion report 见 [stage4-completion-report.md](../artifacts/stage4-completion-report.md)。

当前 Guard 仍是 dry-run / observe-only。Enforcement is not implemented. There is no daemon or service. There is no OS-wide process monitoring. There is no new file, network, or Git monitoring expansion. Installer and release workflows are unchanged. No v0.3.1 release exists.

| 方面 | Python MVP（阶段 1-3） | Rust Guard（Stage 4 已完成边界） |
|---|---|---|
| 当前实现 | Python Core 是当前 run/replay/explain/dashboard-data 实现 | Stage 4 仅提供 dry-run / observe-only 原型与 RFC 文档 |
| 桌面实现 | Electron + React + TypeScript + TailwindCSS | 没有 Electron UI 改动；Slint 仅为未来可行性 RFC |
| `process.spawn` | Python shell hooks 仍按现有 MVP 行为 | local-only dry-run event；不执行 target command、不阻断 |
| 监控范围 | Python-level hooks 与本地 metadata | 不做 OS-wide monitoring；不新增 file/network/Git monitoring |
| policy | 现有 `policy.yaml` / default policy | Guard policy dry-run 只写 sidecar；不 enforcement |
| release | v0.3.0 正式 release | 不创建 tag、不发布 v0.3.1、不修改 release assets |

### Stage 4 completed issues and outcomes

| Issue | Milestone | Outcome |
|---|---|---|
| [#31](https://github.com/mohui666/trace-seal/issues/31) | RFC review | 已完成并合并；Stage 4 保持 design-first / dry-run-first |
| [#32](https://github.com/mohui666/trace-seal/issues/32) | Guard event schema contract | [`guard.event.v1` Draft contract](guard-event-schema-contract.md) 已完成并合并 |
| [#33](https://github.com/mohui666/trace-seal/issues/33) | Rust `guard.health` prototype | 最小 local-only prototype 已完成并合并；仅 health event |
| [#34](https://github.com/mohui666/trace-seal/issues/34) | `process.spawn` dry-run event | [local-only dry-run prototype](guard-process-spawn-dry-run.md) 已完成；不执行目标、不做 OS 监控 |
| [#35](https://github.com/mohui666/trace-seal/issues/35) | Import Guard events into Python Core | [可选 Guard artifact import](guard-event-import.md) 已完成；不合并 Python timeline |
| [#36](https://github.com/mohui666/trace-seal/issues/36) | Expose Guard metadata in `dashboard-data` | [dashboard-data Guard metadata](dashboard-guard-metadata.md) 已完成；无 UI 改动 |
| [#37](https://github.com/mohui666/trace-seal/issues/37) | Guard policy dry-run decisions | [Guard policy dry-run metadata](guard-policy-dry-run.md) 已完成；不执行目标、不 enforcement |
| [#38](https://github.com/mohui666/trace-seal/issues/38) | Windows VM smoke validation | [Windows smoke validation](windows-guard-smoke-validation.md) 已完成；验证 target command 未执行、`enforcement_applied=false`、无 daemon/service |
| [#39](https://github.com/mohui666/trace-seal/issues/39) | Enforcement Experiment RFC | [Stage 4 Enforcement Experiment RFC](stage4-enforcement-experiment-rfc.md) 已完成；future opt-in gates / kill switch / audit / rollback / consent，不实现 enforcement |
| [#50](https://github.com/mohui666/trace-seal/issues/50) | Stage 4 completion audit and roadmap cleanup | 当前 audit PR 关闭；文档、状态一致性、completion report、Stage 5 candidates 与静态检查 |

### Stage 4 non-outcomes

- No enforcement implementation.
- No daemon/service.
- No OS-wide process monitoring.
- No file/network/Git monitoring expansion.
- No installer/release workflow change.
- No v0.3.1 release.
- No Slint implementation.
- No Rust Core parity implementation.
- No Electron replacement.
- No Python Core rewrite.

### Stage 4 outcome summary

- Guard event schema contract.
- Rust `guard.health` prototype.
- `process.spawn` dry-run event model.
- Guard event import path into Python Core.
- Guard metadata in `dashboard-data`.
- Guard policy dry-run decisions.
- Windows VM smoke validation.
- Enforcement Experiment RFC.
- Stage 4 completion report and static documentation checks.

```text
阶段 1：Python Agent → Python hooks
阶段 2：Python hooks → dashboard-data → Electron Dashboard
阶段 3：增强 Python Core
阶段 4：Guard dry-run / observe-only evidence and RFCs（complete）
```

---

## Stage 5 candidates

Formal Stage 5 implementation has not started. Candidate and spike tracks are tracked as separate issues:

1. [Slint desktop feasibility RFC](slint-desktop-feasibility-rfc.md) ([Issue #51](https://github.com/mohui666/trace-seal/issues/51))
   - Evaluate replacing or complementing the Electron dashboard with a native Slint desktop path.
   - Documentation-only until accepted.
   - Does not replace Electron.
   - Does not add Slint runtime code, a Slint crate, or `.slint` UI files.

2. [Rust Core parity RFC](rust-core-parity-rfc.md) ([Issue #52](https://github.com/mohui666/trace-seal/issues/52))
   - Evaluate moving selected Python Core responsibilities to Rust through parity-first planning.
   - Python hook shim remains necessary for Python Agent instrumentation.
   - RFC / planning-only until separately accepted.
   - Rust Core implementation has not started.
   - Python Core remains the source of truth for run/replay/explain/dashboard-data.
   - Electron remains the current desktop implementation.
   - Slint and Rust Core remain separate planning tracks.
   - Does not modify v0.3.0, release assets, tags, packaging, or release workflows.

3. [Slint hello dashboard spike](https://github.com/mohui666/trace-seal/issues/53)
   - Experimental prototype only after the Slint RFC is accepted.
   - Adds `crates/traceseal-desktop-slint` as a minimal code spike.
   - Shows static mock dashboard values only.
   - Includes a local English/Chinese text toggle inside the Slint spike window only.
   - Does not become the default desktop path.
   - Electron remains the current desktop implementation.
   - Python Core is not called by this spike.
   - Does not load real `runs/`, `events.jsonl`, `manifest.json`, or `dashboard-data`.
   - Does not add a project-wide i18n framework.
   - Does not modify installer or release workflows.
   - Does not modify v0.3.0, release assets, tags, packaging, or GitHub Actions release workflows.

Formal Stage 5 implementation must not modify v0.3.0 release assets, create v0.3.1, implement enforcement, promote the Slint spike beyond its experimental boundary, replace Electron, rewrite Python Core, add a project-wide i18n framework, or expand monitoring scope without a dedicated accepted RFC.

---

## 版本历史

| 版本 | 日期 | 内容 |
|---|---|---|
| v0.1.0 | 2026-06 | Python CLI MVP：run/replay/explain |
| v0.1.1 | 2026-06 | 补 env/git/http 案例与 dashboard-data JSON |
| v0.2.0 | 2026-06 | 已发布：Electron 数据运行层、Renderer 真实数据联调、Windows x64 安装包 |
| v0.3.0 | 2026-06-21 | 已发布：文件读取、os.system、httpx、Git 状态、HTTP cassette、policy.yaml DSL、Git push 细分、域名策略与级联事故检测 |
| v1.0.0 | 远期 | 产品化 Guard + Dashboard |
