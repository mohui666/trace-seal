# Project status / 项目状态

## Stable release / 稳定版本

- v0.3.0 is the latest stable release. / `v0.3.0` 是当前最新稳定版本。
- v0.3.0 tag remains at 59ae99d6db495276963e2f4b47b137f4de846d35. / `v0.3.0` tag 仍指向该提交。
- There is no v0.3.1. / 当前没有 `v0.3.1`。
- v0.2.0 remains an older published release. / `v0.2.0` 是较早的已发布版本。

## Completed stages / 已完成阶段

- Stage 1 delivered the Python CLI MVP for recording, replay, explain, policy checks, sandboxed demo runs, and incident examples. / Stage 1 交付 Python CLI MVP。
- Stage 2 delivered the Electron desktop baseline that reads Python Core data through fixed IPC and dashboard-data surfaces. / Stage 2 交付 Electron 桌面基线。
- Stage 3 delivered Core enhancements in v0.3.0: file-read metadata, `os.system()` capture, `httpx` capture, Git state, redacted HTTP cassette output, YAML policy, Git push classification, domain policy, cascade analysis, and Windows build CI. / Stage 3 在 `v0.3.0` 中完成 Core 增强。
- Stage 4 delivered dry-run / observe-only Guard evidence, validation notes, and RFCs. It did not turn TraceSeal into an enforcing system security product. / Stage 4 交付 dry-run / observe-only 证据、验证记录和 RFC，但没有把 TraceSeal 变成 enforcement 产品。

## Current desktop implementations / 当前桌面实现

- Electron remains the default desktop implementation. / Electron 仍是默认桌面实现。
- The Electron renderer consumes Python Core `dashboard-data` output. / Electron renderer 读取 Python Core 的 `dashboard-data` 输出。
- Electron and the experimental Slint desktop path share the Python Core `dashboard-data` contract documented in `docs/dashboard-data-contract.md`. / Electron 和实验性的 Slint 桌面路径共享 `docs/dashboard-data-contract.md` 中记录的 Python Core `dashboard-data` 契约。
- Python Core remains the source of truth for run, replay, explain, policy, recorder, and dashboard-data behavior. / Python Core 仍是 run、replay、explain、policy、recorder 与 dashboard-data 行为的事实来源。

## Slint experimental status / Slint 实验状态

- Slint remains experimental-only. / Slint 仍仅为实验轨道。
- Slint remains experimental and separate from the default Electron desktop. / Slint 仍是与默认 Electron 桌面分离的实验方向。
- Slint has a hello dashboard spike, read-only dashboard-data bridge, parser tests, and UI polish. / Slint 已有 hello dashboard spike、只读 dashboard-data bridge、parser tests 和 UI polish。
- Slint is not packaged or released. / Slint 未打包、未发布。
- Slint does not replace Electron. / Slint 不替代 Electron。

## Rust Guard status / Rust Guard 状态

- Rust Guard remains dry-run / observe-only unless later implementation says otherwise. / 除非后续实现明确改变边界，Rust Guard 仍保持 dry-run / observe-only。
- Guard artifacts and policy decisions are evidence outputs, not blocking controls. / Guard artifacts 与 policy decisions 是证据输出，不是阻断控制。
- Enforcement is not implemented. / 尚未实现 enforcement。
- No daemon or service is installed. / 不安装 daemon 或 service。
- No OS-wide process monitoring is added. / 不新增 OS-wide process monitoring。

## Rust Core status / Rust Core 状态

- Rust Core parity is RFC-only / planning unless later implementation exists. / 除非后续已有实现，Rust Core parity 仍是 RFC / planning。
- Python Core remains the source of truth. / Python Core 仍是事实来源。
- Rust Core has not replaced Python Core. / Rust Core 没有替代 Python Core。

## Release and tag boundaries / 发布与 tag 边界

- `v0.3.0` remains the latest stable release. / `v0.3.0` 仍是最新稳定版本。
- The `v0.3.0` tag remains at `59ae99d6db495276963e2f4b47b137f4de846d35`. / `v0.3.0` tag 仍指向 `59ae99d6db495276963e2f4b47b137f4de846d35`。
- There is no `v0.3.1` tag or release. / 当前没有 `v0.3.1` tag 或 release。
- This status page does not modify published release assets. / 本状态页不修改已发布 release assets。

## Known non-goals / 已知非目标

- No enforcement implementation. / 不实现 enforcement。
- No daemon or service. / 不提供 daemon 或 service。
- No OS-wide monitoring. / 不做 OS-wide monitoring。
- No replacement of Electron by Slint. / 不用 Slint 替代 Electron。
- No replacement of Python Core by Rust Core. / 不用 Rust Core 替代 Python Core。
- No packaging or release workflow change from this documentation cleanup. / 本次文档整理不改变 packaging 或 release workflow。
