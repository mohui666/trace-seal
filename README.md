# TraceSeal

TraceSeal is an operation recorder, replay aid, and safety-analysis layer for AI agents that touch files, shells, HTTP, and Git.

TraceSeal 是面向 AI Agent 的操作记录器、回放辅助工具和安全分析层，用来观察文件、Shell、HTTP 与 Git 等副作用操作。

## What TraceSeal is / TraceSeal 是什么

TraceSeal records the side effects of a Python agent run, exports replayable evidence, and explains the first risky or harmful operation.

TraceSeal 会记录 Python Agent 运行过程中的副作用，导出可回放证据，并解释第一处高风险或有害操作。

```text
traceseal run -> events.jsonl / manifest.json -> traceseal replay -> traceseal explain
```

The Python Core remains the source of truth for run, replay, explain, policy, recorder, and dashboard-data behavior.

Python Core 仍是 run、replay、explain、policy、recorder 与 dashboard-data 行为的事实来源。

## Current status / 当前状态

- Latest stable release: [v0.3.0](https://github.com/mohui666/trace-seal/releases/tag/v0.3.0). / 当前稳定版本是 `v0.3.0`。
- Stage 3 Core work is complete in v0.3.0: Git state tracking, redacted HTTP cassette artifacts, local policy YAML, Git push classification, domain policy, and deterministic cascade analysis. / Stage 3 Core 能力已在 `v0.3.0` 完成。
- Stage 4 Guard work is dry-run / observe-only evidence and RFCs; it is not productized enforcement. / Stage 4 Guard 仍是 dry-run / observe-only 证据与 RFC，不是产品化拦截。
- Post-Stage 4 planning is tracked separately: Electron remains the current desktop implementation, Python Core remains the current run/replay/explain/dashboard-data implementation, Slint desktop feasibility is experimental planning, and Rust Core parity is planning-only. / Post-Stage 4 规划单独跟踪：Electron 仍是当前桌面实现，Python Core 仍是当前核心实现，Slint desktop feasibility 与 Rust Core parity 仍是规划或实验轨道。
- There is no v0.3.1. / 当前没有 `v0.3.1`。

## Quick start / 快速开始

Install the package in editable mode from the repository root. / 在仓库根目录以 editable 模式安装：

```powershell
python -m pip install -e .
python -m traceseal --help
```

Run a local demo and inspect the result. / 运行本地 demo 并查看结果：

```powershell
python -m traceseal run -- python examples/bad_agent_delete.py
python -m traceseal replay runs/latest
python -m traceseal explain runs/latest
python -m traceseal dashboard-data runs/latest
```

Demo runs write evidence under `runs/<run_id>/`. Replay and explain read recorded evidence instead of re-running the original side effects.

Demo 会把证据写入 `runs/<run_id>/`。Replay 和 explain 只读取已记录证据，不重新执行原始副作用。

## Desktop status / 桌面状态

Electron remains the default desktop implementation. The Electron + React renderer consumes Python Core `dashboard-data` output and does not own interception logic.

Electron 仍是默认桌面实现。Electron + React renderer 读取 Python Core 的 `dashboard-data` 输出，不承载拦截逻辑。

Slint remains experimental-only. The Slint spike is not packaged or released, and Slint does not replace Electron.

Slint 仍仅为实验轨道。Slint spike 未打包、未发布，也不替代 Electron。

## Safety boundaries / 安全边界

TraceSeal is an evidence and analysis prototype, not an operating-system security product.

TraceSeal 是证据记录与分析原型，不是操作系统级安全产品。

- Enforcement is not implemented. / 尚未实现 enforcement。
- No daemon or service is installed. / 不安装 daemon 或 service。
- No OS-wide monitoring is performed. / 不做 OS-wide monitoring。
- No OS-wide file, network, process, or Git monitoring expansion is present. / 不扩展到系统级文件、网络、进程或 Git 监控。
- The sandbox is a copied workspace directory, not a container or kernel isolation boundary. / sandbox 是复制出的工作区目录，不是容器或内核隔离边界。
- Slint does not replace Electron. / Slint 不替代 Electron。
- There is no v0.3.1. / 当前没有 `v0.3.1`。

## Documentation / 文档导航

- [Documentation index / 文档索引](docs/README.md)
- [Project status / 项目状态](docs/project-status.md)
- [Roadmap / 路线图](docs/roadmap.md)
- [Project specification / 项目规格](docs/spec.md)
- [Policy rules / 策略规则](docs/policy-rules.md)
- [Incident examples / 事故案例](docs/incident-examples.md)
- [Dashboard design / Dashboard 设计](docs/dashboard-design.md)
- [Demo script / Demo 脚本](docs/demo.md)
- [Windows install and SmartScreen troubleshooting / Windows 安装与 SmartScreen 排查](docs/windows-install-troubleshooting.md)
- Release verification checklist: [`docs/release-verification-checklist.md`](docs/release-verification-checklist.md). / Release 校验清单：[`docs/release-verification-checklist.md`](docs/release-verification-checklist.md)。
- [Slint Desktop Feasibility RFC / Slint 桌面可行性 RFC](docs/slint-desktop-feasibility-rfc.md)
- [Rust Core Parity RFC / Rust Core 对齐 RFC](docs/rust-core-parity-rfc.md)

## Release status / Release 状态

`v0.3.0` is the latest stable release. Windows release artifacts and checks are recorded in [the v0.3 release report](artifacts/v0.3-release-report.md). Older release notes remain available for `v0.2.0`.

`v0.3.0` 是当前最新稳定版本。Windows 发布工件与校验记录见 [v0.3 release report](artifacts/v0.3-release-report.md)，`v0.2.0` 的历史 release notes 仍保留。
