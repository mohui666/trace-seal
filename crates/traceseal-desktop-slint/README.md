# TraceSeal Slint Desktop Spike

English | 中文

## Status

Experimental spike only.

This crate is a standalone Slint hello dashboard prototype. It is present only to evaluate a very small native desktop surface after the Slint feasibility RFC. It now includes a narrow read-only bridge to existing `dashboard-data` JSON so the spike can display conservative summaries without becoming the default desktop path.

## What this prototype does

- Opens a minimal Slint desktop window.
- Shows static mock dashboard values as the fallback state.
- Can load conservative summaries from fixed read-only `dashboard-data` commands.
- Provides a local English/Chinese text toggle inside the spike window.
- Documents how to build and run the spike manually.

## Read-only dashboard-data bridge

The bridge can invoke only these fixed commands:

```text
python -m traceseal dashboard-data latest
python -m traceseal dashboard-data list
python -m traceseal dashboard-data policy
```

The commands are hard-coded. User input is not used to build commands.

The Slint UI exposes read-only buttons for loading the latest run summary, run list summary, and policy summary. It parses JSON conservatively, keeps a mock fallback, reports command or parse failures in a short error field, and does not panic on malformed or missing fields.

## What this prototype does not do

This prototype does not:

- replace Electron;
- become the default desktop implementation;
- call `traceseal run`;
- load real `runs/` data;
- read `events.jsonl`;
- read `manifest.json`;
- execute target commands;
- implement enforcement;
- change Rust Guard behavior;
- change packaging or installer behavior;
- change release workflows;
- create or modify release tags;
- modify the `v0.3.0` release or assets;
- add a project-wide i18n framework;
- persist language settings;
- detect system locale.

## Build

```powershell
cargo check -p traceseal-desktop-slint
```

## Run

```powershell
cargo run -p traceseal-desktop-slint
```

`cargo run` opens a GUI window, so it is not required for automated validation.

## Boundaries

Electron remains the default desktop implementation. Python Core remains the source of truth for real run, replay, explain, and dashboard-data behavior. This spike is connected only through the fixed read-only `dashboard-data` commands above and is not connected to Electron, Rust Guard, packaging, release workflows, tags, or release assets.

This prototype does not call `traceseal run`, does not execute target commands, does not write workspace state, does not edit policy, does not replace Electron, and does not change packaging or release workflows.

It does not add a project-wide i18n framework.

## Follow-up path

Any future Slint work needs a separate accepted issue or RFC before it can add workspace selection, call arbitrary run-specific commands, share fixtures with the existing desktop, participate in packaging, or be considered for Stage 5 implementation.

---

# TraceSeal Slint 桌面实验原型

## 状态

仅实验用途。

这个 crate 是一个独立的 Slint hello dashboard 原型，只用于在 Slint 可行性 RFC 之后验证极小的原生桌面界面。它现在包含一个很窄的只读 `dashboard-data` 桥接，用来展示保守摘要，不会成为默认桌面路径。

## 这个原型做什么

- 打开一个最小 Slint 桌面窗口。
- 以静态 mock dashboard 数值作为兜底状态。
- 可以通过固定只读 `dashboard-data` 命令加载保守摘要。
- 在实验窗口内部提供本地 English / 中文文案切换。
- 记录手动构建和运行命令。

## 只读 dashboard-data 桥接

桥接只会调用这些固定命令：

```text
python -m traceseal dashboard-data latest
python -m traceseal dashboard-data list
python -m traceseal dashboard-data policy
```

这些命令由代码固定写死，不会使用用户输入拼接命令。

Slint UI 提供只读按钮，用于加载最新运行摘要、运行列表摘要和策略摘要。解析 JSON 时保持保守兜底；命令失败或解析失败只展示简短错误，不因缺失字段或格式错误 panic。

## 这个原型不做什么

这个原型不替换 Electron，不会成为默认桌面实现，不调用 `traceseal run`，不直接读取 `runs/`、`events.jsonl` 或 `manifest.json`，不执行目标命令，不写入 workspace，不编辑 policy，不实现 enforcement，不修改 Rust Guard 行为，不修改打包/安装器/release 流程，不创建或修改 release tag，也不修改 v0.3.0 release 或 assets。

这个原型也不新增全项目 i18n 框架，不持久化语言设置，不读取系统 locale。

## 构建

```powershell
cargo check -p traceseal-desktop-slint
```

## 运行

```powershell
cargo run -p traceseal-desktop-slint
```

`cargo run` 会打开 GUI 窗口，因此自动验证不要求运行它。

## 边界

Electron 仍是默认桌面实现。Python Core 仍是真实 run、replay、explain 和 dashboard-data 行为的来源。这个 spike 只通过上面的固定只读 `dashboard-data` 命令连接 Python Core，不连接 Electron、Rust Guard、打包流程、release workflow、tag 或 release assets。

这个原型不调用 `traceseal run`，不执行目标命令，不写入 workspace，不编辑 policy，不替换 Electron，也不修改打包或 release 流程。

## 后续路径

任何后续 Slint 工作都需要单独接受的 issue 或 RFC，之后才可以增加 workspace 选择、调用任意 run-specific 命令、复用现有桌面 fixture、进入打包流程，或被视为 Stage 5 implementation 候选。
