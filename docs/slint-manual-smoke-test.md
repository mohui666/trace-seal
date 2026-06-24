# Slint manual smoke test

## Status

The Slint desktop path is experimental-only.

Electron remains the default desktop implementation.

Slint remains experimental-only and has not replaced Electron.

This is not the v0.3.0 release installer or `TraceSeal-Setup.exe`.

TraceSeal-Setup.exe is still the Electron release installer.

Slint is not packaged as a release exe.

Use this guide only for local manual smoke testing of the experimental Slint UI. It does not make Slint the default desktop, does not replace Electron, and does not change release assets.

## Before running

- Work from the repository root.
- Make sure the Rust toolchain can build the Slint crate.
- This guide does not require `python -m traceseal run`.
- This guide does not require packaging, release, or installer steps.

## Run the experimental UI

Run the experimental Slint UI with:

```powershell
cargo run -p traceseal-desktop-slint
```

This opens the local experimental window from source. It is not a packaged release executable.

## What to verify

- The loading state appears at startup.
- The loaded state appears after dashboard-data loads.
- The error state is visible when dashboard-data loading fails.
- The UI uses async non-blocking loading; refresh should not freeze the window.
- The read-only dashboard summary displays data source, bridge status, latest run, latest status, event count, risk count, and policy summary when available.
- The run detail view displays latest run fields such as run ID, status, started time, finished time, title, workspace, policy mode, and risk summary when available.
- The run history view displays run ID, status, started time, event count, and risk count when `dashboard-data list` returns runs.
- The policy detail view displays policy mode, policy source, rule count, rule IDs, and decisions when `dashboard-data policy` returns policy data.
- The Load demo data action shows fixture-backed demo preview data without writing demo data into `runs/`.
- The layout remains scrollable and responsive so the bottom policy detail content is not clipped.
- This smoke test is a source-run check only; it is not the v0.3.0 release installer or a packaged release executable.

## What this does not mean

- Do not use this document to claim an Electron replacement happened.
- Do not claim Slint has been officially released.
- Do not claim any v0.3.1 release exists.
- Do not modify release assets.
- Do not treat this as the v0.3.0 installer or `TraceSeal-Setup.exe`.

## Troubleshooting

- If the window does not open, run `cargo check -p traceseal-desktop-slint` and inspect the compiler output.
- If dashboard-data does not load, confirm that the failure is shown in the UI error state.
- If the UI appears frozen during refresh, treat that as a smoke test failure for the experimental Slint path.
- If you need the default desktop app, use the Electron path rather than this experimental Slint window.

---

# Slint 手动 smoke test

## 状态

Slint 桌面路径仍是实验用途。

Electron 仍是默认桌面实现。

Slint 仍是实验用途，尚未替代 Electron。

这不是 v0.3.0 发布安装器，也不是 `TraceSeal-Setup.exe`。

TraceSeal-Setup.exe 仍是 Electron 发布安装器。

Slint 尚未作为 release exe 打包。

本指南只用于本地手动 smoke test 实验 Slint UI。它不表示 Slint 成为默认桌面，不表示 Slint 替代 Electron，也不改变 release assets。

## 运行前检查

- 在仓库根目录运行命令。
- 确认 Rust 工具链可以构建 Slint crate。
- 本指南不需要运行 `python -m traceseal run`。
- 本指南不需要执行打包、发布或安装器步骤。

## 运行实验 UI

运行实验 Slint UI：

```powershell
cargo run -p traceseal-desktop-slint
```

这会从源码打开本地实验窗口。它不是打包后的发布 exe。

## 需要检查什么

- 启动时显示 loading 状态。
- dashboard-data 加载后显示 loaded 状态。
- dashboard-data 加载失败时能看到 error 状态。
- UI 使用异步非阻塞加载；刷新时 UI 不应卡死。
- 只读 dashboard 摘要显示 data source、bridge status、latest run、latest status、event count、risk count 和 policy summary（如果可用）。
- 只读运行详情区块显示 latest run 字段，例如 run ID、状态、开始时间、结束时间、标题、workspace、policy mode 和 risk summary。
- 只读运行历史区块在 `dashboard-data list` 返回 runs 时显示 run ID、状态、开始时间、事件数量和风险数量。
- 只读策略详情区块在 `dashboard-data policy` 返回 policy 数据时显示策略模式、策略来源、规则数量、规则 ID 和决策。
- Load demo data 会显示基于 fixture 的示例预览数据，不会把 demo 数据写入 `runs/`。
- 布局保持可滚动 / 响应式，底部策略详情内容不应被裁切。
- 这个 smoke test 只是源码运行检查；不是 v0.3.0 发布安装器，也不是打包后的 release exe。

## 这不代表什么

- 不要用这个文档声称 Slint 已替代 Electron。
- 不要声称 Slint 已正式发布。
- 不要声称 v0.3.1 已发布。
- 不要修改 release assets。
- 不要把它当作 v0.3.0 发布安装器或 `TraceSeal-Setup.exe`。

## 排查

- 如果窗口无法打开，先运行 `cargo check -p traceseal-desktop-slint` 并查看编译输出。
- 如果 dashboard-data 未能加载，确认 UI 中显示 error 状态。
- 如果刷新时 UI 卡死，应视为实验 Slint 路径的 smoke test 失败。
- 如果需要默认桌面应用，请使用 Electron 路径，而不是这个实验 Slint 窗口。
