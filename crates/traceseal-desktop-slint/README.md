# TraceSeal Slint Desktop Spike

English | 中文

## Status

Experimental spike only.

This crate is a standalone Slint hello dashboard prototype. It is present only to evaluate a very small native desktop surface after the Slint feasibility RFC.

## What this prototype does

- Opens a minimal Slint desktop window.
- Shows static mock dashboard values for latest run, event count, risk count, and policy mode.
- Provides a local English/Chinese text toggle inside the spike window.
- Documents how to build and run the spike manually.

## What this prototype does not do

This prototype does not:

- replace Electron;
- become the default desktop implementation;
- call Python Core;
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

Electron remains the default desktop implementation. Python Core remains the source of truth for real run, replay, explain, and dashboard-data behavior. This spike uses static mock values only and is not connected to Electron, Python Core, Rust Guard, packaging, release workflows, tags, or release assets.

It does not replace Electron, does not call Python Core, does not load real runs, and does not add a project-wide i18n framework.

## Follow-up path

Any future Slint work needs a separate accepted issue or RFC before it can load real `dashboard-data`, share fixtures with the existing desktop, participate in packaging, or be considered for Stage 5 implementation.

---

# TraceSeal Slint 桌面实验原型

## 状态

仅实验用途。

这个 crate 是一个独立的 Slint hello dashboard 原型，只用于在 Slint 可行性 RFC 之后验证极小的原生桌面界面。

## 这个原型做什么

- 打开一个最小 Slint 桌面窗口。
- 显示静态 mock dashboard 数值：最新运行、事件数量、风险数量和策略模式。
- 在实验窗口内部提供本地 English / 中文文案切换。
- 记录手动构建和运行命令。

## 这个原型不做什么

这个原型不替换 Electron，不会成为默认桌面实现，不调用 Python Core，不调用 `traceseal run`，不读取真实 `runs/` 数据，不读取 `events.jsonl`，不读取 `manifest.json`，不执行目标命令，不实现 enforcement，不修改 Rust Guard 行为，不修改打包/安装器/release 流程，不创建或修改 release tag，也不修改 v0.3.0 release 或 assets。

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

Electron 仍是默认桌面实现。Python Core 仍是真实 run、replay、explain 和 dashboard-data 行为的来源。这个 spike 只使用静态 mock 数值，不连接 Electron、Python Core、Rust Guard、打包流程、release workflow、tag 或 release assets。

## 后续路径

任何后续 Slint 工作都需要单独接受的 issue 或 RFC，之后才可以加载真实 `dashboard-data`、复用现有桌面 fixture、进入打包流程，或被视为 Stage 5 implementation 候选。
