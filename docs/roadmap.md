# Roadmap / 路线图

## Current baseline / 当前基线

TraceSeal's current stable baseline is `v0.3.0`. Python Core remains the source of truth for run, replay, explain, policy, recorder, and dashboard-data behavior. Electron remains the default desktop implementation.

TraceSeal 当前稳定基线是 `v0.3.0`。Python Core 仍是核心行为事实来源，Electron 仍是默认桌面实现。

## Completed / 已完成

- Python CLI MVP for recording agent side effects, replaying evidence, and explaining the first risky operation. / Python CLI MVP 已支持记录副作用、回放证据并解释第一处风险操作。
- Electron desktop baseline that reads real run data from Python Core outputs. / Electron 桌面基线已读取 Python Core 输出的真实 run 数据。
- Core enhancements for file-read metadata, shell and `os.system()` capture, HTTP and `httpx` metadata, Git state, redacted HTTP cassette output, YAML policy, Git push classification, domain policy, deterministic cascade analysis, and Windows build CI. / Core 增强已覆盖文件读取 metadata、Shell / `os.system()`、HTTP / `httpx`、Git 状态、脱敏 HTTP cassette、YAML policy、Git push 分类、域名策略、级联分析和 Windows CI。
- Stage 4 status: Complete through Issue #39. Issue #50 performs the final completion audit and roadmap cleanup. / Stage 4 已完成到 Issue #39，Issue #50 做最终完成审计与 roadmap 清理。
- Stage 4 outputs include Rust Guard dry-run / observe-only evidence, Windows smoke validation, dashboard metadata, policy dry-run decisions, and RFC work. Enforcement remains outside the completed scope. / Stage 4 输出包括 Rust Guard dry-run / observe-only 证据、Windows smoke validation、dashboard metadata、policy dry-run decisions 和 RFC；enforcement 不在已完成范围内。

## Active experimental tracks / 当前实验轨道

Slint remains an experimental desktop track. Completed spikes include hello dashboard, read-only dashboard-data bridge, parser tests, and read-only UI polish. Electron remains the default desktop implementation.

Slint 仍是实验桌面轨道。已完成 hello dashboard、只读 dashboard-data bridge、parser tests 与只读 UI polish；Electron 仍是默认桌面实现。

- [Slint desktop feasibility RFC](slint-desktop-feasibility-rfc.md) remains an experimental planning document tracked by Issue #51. / Slint desktop feasibility RFC 仍是实验规划文档，由 Issue #51 跟踪。
- Slint hello dashboard spike remains read-only and experimental. / Slint hello dashboard spike 仍是只读实验原型。
- The next Slint experimental steps should preserve the shared dashboard-data contract before adding deeper read-only views. / 后续 Slint 实验步骤在添加更深的只读视图前，应继续保持共享 dashboard-data 契约。
- [Rust Core parity RFC](rust-core-parity-rfc.md) remains a planning track tracked by Issue #52. Python Core remains the current implementation and compatibility baseline. / Rust Core parity RFC 仍是由 Issue #52 跟踪的规划轨道；Python Core 仍是当前实现与兼容基线。
- Rust Guard follow-up work remains design-first and evidence-first unless a later accepted plan explicitly changes the boundary. / 除非后续方案明确改变边界，Rust Guard 后续仍以设计优先和证据优先为原则。

## Stage 5 candidates / Stage 5 候选方向

- Keep documentation aligned with the released `v0.3.0` baseline and the no-`v0.3.1` release boundary. / 保持文档与 `v0.3.0` 发布基线及无 `v0.3.1` 边界一致。
- Decide whether any Slint experiment should progress beyond a read-only spike without replacing Electron. / 决定 Slint 实验是否在不替代 Electron 的前提下继续推进。
- Decide whether any Rust Core parity work should be implemented behind compatibility tests. / 决定 Rust Core parity 是否在兼容性测试后推进实现。
- Decide whether any Guard enforcement experiment should proceed only with explicit opt-in boundaries, rollback, audit evidence, and user consent. / 决定 Guard enforcement 实验是否仅在显式 opt-in、rollback、audit evidence 和 user consent 边界下推进。
- Continue improving tests that prevent README, status, and roadmap drift. / 持续改进防止 README、status 和 roadmap 漂移的测试。

## Explicit non-goals / 明确非目标

- Do not treat Slint as the default desktop implementation. / 不把 Slint 当作默认桌面实现。
- Do not treat Rust Core as a replacement for Python Core. / 不把 Rust Core 当作 Python Core 的替代品。
- Do not claim enforcement behavior before it exists. / 不在功能存在前宣称 enforcement 行为。
- Do not install a daemon or service as part of the current baseline. / 当前基线不安装 daemon 或 service。
- Do not add OS-wide monitoring as part of the current baseline. / 当前基线不新增 OS-wide monitoring。
- Do not create or imply a `v0.3.1` release. / 不创建或暗示 `v0.3.1` release。
- No v0.3.1 release. / 没有 `v0.3.1` release。
