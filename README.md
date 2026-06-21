# TraceSeal

**Latest release: [v0.3.0](https://github.com/mohui666/trace-seal/releases/tag/v0.3.0) — released**

Windows x64 installer is available on GitHub Releases.

> **v0.3.0:** Stage 3 Core complete. This release adds Git state tracking, redacted HTTP cassette artifacts, local policy YAML, Git push classification, domain policy, and deterministic cascade analysis. Rust Guard remains future Stage 4 productization work and is not included.

TraceSeal 是 AI Agent 的操作黑匣子 + 执行前安全防火墙 + 失败回放系统。

它要解决的问题是：当 AI Agent 自动读写文件、执行 Shell、发 HTTP 请求、操作 Git 时，如果它把项目搞坏了，我们需要知道它做了什么、哪一步第一次造成错误、能否回放事故，以及下次能否提前阻断类似危险操作。

当前仓库已经实现 Python Agent 的 MVP 工程闭环：

```text
traceseal run → events.jsonl / manifest.json → traceseal replay → traceseal explain
```

已完成的阶段 2 桌面原型架构是：

```text
Python Core（拦截 / 记录 / policy / replay / explain / sandbox）
        ↓ dashboard-data JSON
Electron + React + TypeScript + TailwindCSS（展示真实 runs，不承载拦截逻辑）
```

## 项目背景

AI Agent 正在接管越来越多的开发工作，但 Agent 的操作对开发者来说常常是一个黑匣子。TraceSeal 通过拦截 Agent 的工具调用，实现：

- **记录**：记录 Python Agent 的核心副作用操作（文件写入、Shell、HTTP、常见删除/Git 风险）。
- **拦截**：在执行前检查操作风险，标记或阻止危险行为。
- **回放**：根据日志重建 Agent 的执行轨迹。
- **定位**：精确定位首次造成错误或高风险影响的工具调用。

第一版不做万能 Agent 平台，只聚焦 Python Agent 的核心副作用边界。

## 当前 MVP 能力

当前 MVP 聚焦 Python Agent：

- 通过 `sitecustomize` + monkey patch 记录 Python 文件读取/写入、`subprocess.run()` / `os.system()` Shell 命令、HTTP 请求和常见删除 API。
- `traceseal run` 在临时 sandbox workspace 中执行命令，避免 demo 直接破坏原工作区。
- `recorder/` 写入 `events.jsonl`、`manifest.json`、workspace 快照、run 前后 Git 状态和脱敏 `http_cassette.jsonl`。
- `traceseal replay` 做 transcript replay，不重新执行副作用。
- `traceseal explain` 根据事件日志定位首次高风险/有害工具调用，并输出建议规则。
- `traceseal dashboard-data` 导出 Electron Dashboard 可直接读取的 JSON，包括 Git、HTTP cassette、policy、domain 和 cascade 摘要。
- 工作区 `policy.yaml` 支持本地规则 DSL；Git push 类型、域名 allow/deny/warn 和多阶段 cascade 均有离线 demo 与回归测试。

## 目录结构

```text
trace-seal/
├── traceseal/          # CLI 入口：traceseal run/replay/explain
├── bootstrap/          # sitecustomize 自动安装 SDK hooks
├── sdk/                # Python Agent hooks：文件、shell、HTTP、删除 API
├── policy/             # MVP policy：rm -rf、.env 写入、git push、可疑 HTTP POST
├── sandbox/            # 最小 sandbox：复制 workspace 到 runs/<id>/workspace
├── recorder/           # JSONL event recorder + workspace snapshot/diff
├── replay/             # transcript replay
├── minimizer/          # explain / first harmful event
├── examples/           # bad agent demo
├── tests/              # MVP 自动测试
├── docs/               # 规格、规则、事故案例、Dashboard 设计
├── desktop/electron/   # Electron main/preload/IPC/Python runner 数据运行层
├── desktop/renderer/   # React + TypeScript + TailwindCSS Renderer
├── packaging/          # PyInstaller 入口与打包输出目录
├── scripts/            # Windows 一键构建脚本
├── attestation/        # 预留
└── dashboard/          # Dashboard JSON export；Electron 通过 IPC 消费
```

## 文档

- [项目规格说明书](docs/spec.md)（目标规格 + 当前 MVP 状态）
- [策略规则设计](docs/policy-rules.md)（`policy.yaml` DSL 与默认 JSON fallback）
- [事故测试案例](docs/incident-examples.md)（delete/env/git/http 案例已落地）
- [Dashboard 设计](docs/dashboard-design.md)（Renderer 已接入 Electron preload API 和真实 runs 数据）
- [演示脚本](docs/demo.md)（5 分钟展示讲稿）
- [路线图](docs/roadmap.md)（阶段计划）
- [v0.3 release report](artifacts/v0.3-release-report.md)（正式发布、工件、校验和与限制）
- [v0.3 release prep 验证报告](artifacts/v0.3-release-prep-report.md)（Core 回归、隐私扫描与 Windows 打包证据）
- [Stage 4 Rust Guard design](docs/stage4-rust-guard-design.md)（仅设计，尚未实现）
- [飞书项目文档](docs/feishu_project_doc.md)

## 安装

在项目目录安装为可编辑包：

```powershell
cd C:\Users\mohui666\Documents\projectA\trace-seal
python -m pip install -e .
```

也可以不安装，直接用模块方式运行：

```powershell
python -m traceseal --help
```

## policy.yaml DSL（v0.3.0）

TraceSeal 支持在工作区根目录放置 `policy.yaml`（其次为 `policy.yml`）定义安全规则。当前 DSL 支持 `event_type`、`path`、`command`、`method`、`host`、`url`、`risk_level`、`sensitive` 匹配字段，支持标量 exact 简写以及 `exact`、`contains`、`contains_any`、`glob`、`any_of`、`regex` 操作符，action 支持 `allow`、`warn`、`deny`、`require_approval`。

加载顺序为工作区 `policy.yaml` → `policy.yml` → `policy/default_policy.json`。YAML 缺失时保持旧 JSON 行为；解析或 schema 校验失败时记录 `yaml_error_fallback`、路径和错误信息，再安全回退到默认 JSON，不中断 run。`TRACESEAL_POLICY_MODE` 继续优先于 YAML 顶层 `mode`。

可从示例开始：

```powershell
Copy-Item examples/policy.yaml policy.yaml
python -m traceseal dashboard-data policy
python -m traceseal run -- python examples/bad_agent_policy_yaml.py
```

`dashboard-data policy` 返回 `policy_source.type/path/error`；run 事件和 explain 保留旧 `policy_rule` 字段，同时增加/展示 `rule_id`、`action`、`reason`、`suggested_policy`。

## Git push 风险细分（v0.3.0）

TraceSeal 会区分普通 `git push`、force push、force-with-lease、mirror push、删除远端分支、plus-prefixed force refspec，以及 `--all` / `--tags` bulk push。force、mirror、delete 和 force-refspec 默认标记为 critical，普通、force-with-lease 和 bulk push 标记为 high。

事件的 `input.git_operation`（以及 dashboard-data 的事件顶层 `git_operation`）包含 `push_type`、`remote`、`refs` 和 `protected_branch`；replay/explain 同步展示分类。所有 Git push 仍由 SDK 离线模拟，demo 和测试不会调用真实 Git 远端。

## 域名白名单 / 黑名单（v0.3.0）

TraceSeal 支持对 HTTP 请求目标 host 做策略判断。工作区 `policy.yaml` 可配置 `domain_policy.allow_domains`、`deny_domains`、`warn_domains`、localhost/private-network 开关、未知外部域名告警和 deny 阻断开关；默认 JSON policy 提供兼容 fallback。

host 分类包括 `localhost`、`loopback`、`private`、`external`、公网 `ip` 和 `unknown`，全程只解析 URL/host 字符串，不执行 DNS 查询。域名 pattern 使用现有 host `glob`，例如 `*.example.com`；同样可使用 exact、contains、contains_any、any_of 和 regex。

HTTP 事件、HTTP cassette、dashboard-data、replay 和 explain 会展示 `domain_policy` metadata，包括 `domain_decision`、`matched_domain_rule`、allow/deny/warn list 命中状态。`examples/bad_agent_domain_policy.py` 使用 `httpx.MockTransport`，不会访问真实外网。

## 级联错误案例（v0.3.0）

TraceSeal 提供 `examples/bad_agent_cascade_failure.py`，把敏感文件读取、带合成 secret 的 HTTP 外发尝试、配置破坏、危险删除和危险 Git push 串成一条完整事故链。detector 按 event `seq`（缺失时按 timestamp / 输入顺序）确定性归类；同一 run 出现至少 3 类 stage 时标记为 high cascade，4 类或更多标记为 critical。

demo 使用 `httpx.MockTransport` 和现有 Git push simulation，不访问真实外网、不执行真实 push，也只在复制的 sandbox workspace 内尝试删除。HTTP query/header 继续脱敏，body 只保存摘要，合成 secret 会在 demo 结束前从 workspace 删除。`dashboard-data`、`replay` 和 `explain` 会展示 `cascade.present`、有序 stages、first harmful event、整体 severity 和 human-readable summary。

## 运行 bad agent demo

```powershell
cd C:\Users\mohui666\Documents\projectA\trace-seal
python -m traceseal run python examples/bad_agent_delete.py
```

安装 console script 后也可以运行：

```powershell
traceseal run python examples/bad_agent_delete.py
```

运行后会生成：

```text
runs/<run_id>/events.jsonl
runs/<run_id>/manifest.json
runs/<run_id>/workspace_before.json
runs/<run_id>/workspace_after.json
runs/<run_id>/git_state_before.json
runs/<run_id>/git_state_after.json
runs/<run_id>/http_cassette.jsonl
runs/<run_id>/workspace/
runs/latest                 # 文本指针，内容是最新 run_id
```

说明：demo 中的 `rm -rf data/` 会在 sandbox 中执行。Windows 上没有原生 `rm -rf`，TraceSeal SDK 会模拟该删除动作并记录为 shell 事件，保证跨平台 demo 可运行。

已落地的事故案例：

| 示例 | 触发风险 | 说明 |
|---|---|---|
| `examples/bad_agent_delete.py` | `dangerous_delete` | 创建 `data/important.txt` 后执行 `rm -rf data/`；SDK 跨平台模拟删除并记录 diff。 |
| `examples/bad_agent_env.py` | `env_write` | 写入 `.env`，内容类似 `OPENAI_API_KEY=sk-demo-secret` 和 `DATABASE_URL=postgres://demo:demo@localhost/demo`。 |
| `examples/bad_agent_git.py` | `git_push` | 模拟 `git push origin main`；TraceSeal 记录风险但不会接触真实远端。 |
| `examples/bad_agent_http.py` | `suspicious_http_post` | 模拟向外部 URL POST 敏感数据；默认离线模拟，不真实访问危险 URL。 |
| `examples/bad_agent_os_system.py` | `dangerous_delete` | 用 `os.system()` 尝试删除 sandbox 内含 Unicode/空格的 demo 目录；warn 执行，block/deny 阻断并保留文件。 |
| `examples/bad_agent_file_read.py` | `sensitive_file_read` | 读取 sandbox 内合成的普通/敏感 demo 文件，只记录路径、API、模式和字节数，不记录文件全文。 |
| `examples/bad_agent_httpx.py` | `sensitive_http_request` | 向本地临时 HTTP server 发起同步/异步 `httpx` 请求，验证元数据记录与敏感参数脱敏。 |
| `examples/bad_agent_git_state.py` | Git 状态审计 | 在 sandbox 中稳定制造一个 unstaged 修改、一个 staged 新文件和一个 untracked 文件，不 commit、不 push。 |
| `examples/bad_agent_http_cassette.py` | HTTP cassette 脱敏 | 使用本地 HTTP server 生成 GET/POST cassette，验证 query、header 和 body 摘要脱敏。 |
| `examples/bad_agent_policy_yaml.py` | YAML policy DSL | 在 sandbox 内加载示例 YAML，触发 `.env`、危险删除和本地脱敏 HTTP 规则。 |
| `examples/bad_agent_git_push_classification.py` | Git push 分类 | 离线模拟 normal/force/lease/mirror/delete/refspec/all/tags push，不访问远端。 |
| `examples/bad_agent_domain_policy.py` | 域名策略 | 通过 MockTransport 离线触发 localhost、loopback、denylist、warnlist、unknown external 与 insecure HTTP。 |
| `examples/bad_agent_cascade_failure.py` | 级联事故 | 离线串联 sensitive read、HTTP exfiltration attempt、config corruption、destructive shell 与 mirror push。 |

分别运行：

```powershell
python -m traceseal run python examples/bad_agent_env.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_git.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_http.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_os_system.py
python -m traceseal dashboard-data runs/latest
python -m traceseal explain runs/latest

python -m traceseal run -- python examples/bad_agent_file_read.py
python -m traceseal dashboard-data runs/latest
python -m traceseal explain runs/latest

python -m traceseal run -- python examples/bad_agent_git_state.py
python -m traceseal dashboard-data runs/latest

python -m traceseal run -- python examples/bad_agent_http_cassette.py
python -m traceseal dashboard-data runs/latest

python -m traceseal run -- python examples/bad_agent_cascade_failure.py
python -m traceseal dashboard-data runs/latest
python -m traceseal replay runs/latest
python -m traceseal explain runs/latest
```

## Python 文件读取记录（v0.3.0）

TraceSeal v0.3.0 开始记录 Python 层的 `open(..., "r")`、`open(..., "rb")`、`Path.open()`、`Path.read_text()` 和 `Path.read_bytes()`。`file.read` 事件包含路径、读取模式、来源 API、成功/失败状态、读取字节数和文件大小；**默认不保存完整文件内容**。

`.env`、SSH 私钥、`*.pem` / `*.key` 以及 credential/secret/token/password 类路径会命中 `sensitive_file_read` 并提高风险级别。这是 `sitecustomize` + monkey patch 实现的 **Python-level instrumentation**，不是系统或内核级 EDR；C 扩展、外部进程或未被 patch 覆盖的底层 I/O 可能不会被捕获。

## Python httpx 请求记录（v0.3.0）

TraceSeal v0.3.0 支持 `httpx.get/post/put/patch/delete/request`、`httpx.Client` 和 `httpx.AsyncClient` 的常见请求 API。`network.http` 事件记录 method、脱敏 URL、host、scheme、path、来源 API、status code、成功/失败和耗时；**不记录完整请求体或响应体**。

`Authorization`、`Cookie`、`X-API-Key` 等敏感 header 值，以及 token、api_key、secret、password、signature、session 等 query 参数会替换为 `<redacted>`。这是 Python-level instrumentation，不是系统级网络防火墙；该 hook 不保证捕获 `requests`、`urllib`、`aiohttp`、`curl`、浏览器或外部进程的流量（TraceSeal 对部分 `requests` / `urllib` API 另有独立的 MVP hook）。

```powershell
python -m traceseal run -- python examples/bad_agent_httpx.py
python -m traceseal dashboard-data runs/latest
python -m traceseal explain runs/latest
```

## HTTP cassette 脱敏记录（v0.3.0）

TraceSeal 会基于 HTTP / httpx / requests / urllib 事件生成已脱敏的 `http_cassette.jsonl` artifact。该 artifact 通过 `event_id` 关联原始事件，记录 method、脱敏 URL、host、状态码、耗时、风险规则和请求/响应 body 摘要。默认不保存完整请求体、响应体或敏感 header/query 值，也不会额外发送 HTTP 请求或改变原请求行为。

请求/响应 body 只保存 `present`、`content_type`、`size_bytes`、`sha256` 和固定的 `body_not_stored_by_default` 标记。`Authorization`、Cookie、API key、token、password、credential、session 等 header/query 值统一替换为 `<redacted>`。生成失败只会写入 manifest error metadata，不会导致 `traceseal run` 失败。

```powershell
python -m traceseal run -- python examples/bad_agent_http_cassette.py
python -m traceseal dashboard-data runs/latest
```

## Git 状态记录（v0.3.0）

TraceSeal 会在 Agent 运行前后记录 Git branch、HEAD、`git status --short`、staged、unstaged 和 untracked 文件，分别写入 `git_state_before.json` 与 `git_state_after.json`。`manifest.json` 同时保存 before/after 简要信息和计数摘要，`dashboard-data run <run_id>` 通过新增的 `git_state` 字段导出完整元数据。

采集器只执行本地只读 Git 命令，不 fetch、pull、push、remote、clone 或 commit，不访问远端，也不保存完整源码 diff。正常仓库的 `.git` 目录会复制到 sandbox，Agent 的 `git add` 等操作只修改该副本；副本会移除 remote/include 配置与 hooks，并禁用 Agent 进程的 Git transport。若源 workspace 使用 `.git` 指针文件（linked worktree），TraceSeal 会丢弃该指针以避免触及原仓库。Git 未安装、非 Git 目录或命令失败时，错误会写入 `error` metadata，不会让 `traceseal run` 崩溃。

```powershell
python -m traceseal run -- python examples/bad_agent_git_state.py
python -m traceseal dashboard-data runs/latest
```

## 查看 replay

```powershell
python -m traceseal replay runs/latest
```

输出是 transcript replay，只重建时间线，不重新执行副作用。

## 查看 explain

```powershell
python -m traceseal explain runs/latest
```

示例输出：

```text
首次有害工具调用:
[evt_0003] shell: rm -rf data/

原因:
- 请求递归强制删除: data/
- 删除了受保护路径: data/
- 命中策略规则: dangerous_delete

影响文件:
- data
- data/important.txt

建议策略:
deny shell "rm -rf data/**"
```

## 导出 Dashboard 数据

Electron Dashboard 不直接实现拦截逻辑，而是读取 Python Core 导出的机器可读 JSON。兼容旧命令：

```powershell
python -m traceseal dashboard-data runs/latest
```

阶段 2 新增命令：

```powershell
python -m traceseal dashboard-data latest
python -m traceseal dashboard-data list
python -m traceseal dashboard-data run <run_id>
python -m traceseal dashboard-data policy
```

约束：

- stdout 只输出 JSON。
- 诊断信息输出到 stderr。
- runId 拒绝绝对路径、`../` 和路径穿越。
- list 会按时间倒序返回 runs，单个损坏 run 不影响其他 run。

单个 run 输出包含：

- `run_id`
- `command`
- `started_at` / `finished_at`
- `event_count`
- `high_risk_count`
- `first_harmful_event`
- `events`
- `affected_files`
- `suggested_policy`
- `git_state.before` / `git_state.after` / `git_state.summary`
- `http_cassette.summary` / `http_cassette.entries`（entries 最多 50 条）

## Electron 数据运行层

Electron runtime 位于 `desktop/electron/`，包含 main process、preload、IPC 和 Python CLI runner。React Renderer 位于 `desktop/renderer/`，只展示数据，不直接访问 Node.js。

Renderer 通过 preload 暴露的固定 API 访问数据：

```typescript
window.traceSeal.getLatestRun()
window.traceSeal.listRuns()
window.traceSeal.getRun(runId)
window.traceSeal.getPolicy()
window.traceSeal.getRuntimeInfo()
window.traceSeal.selectWorkspace()
window.traceSeal.getWorkspace()
window.traceSeal.clearWorkspace()
```

安全配置：

- `contextIsolation: true`
- `nodeIntegration: false`
- Renderer 不直接访问 Node.js、`fs`、`child_process` 或任意 IPC channel。

开发模式启动：

```powershell
cd C:\Users\mohui666\Documents\projectA\trace-seal

cd desktop\renderer
npm install
npm run build

cd ..\electron
npm install
npm start
```

首次启动时点击“选择工作区”，选择 TraceSeal 项目目录。顶部栏会显示当前目录，并提供“切换工作区”和“清除工作区”。工作区设置保存在：

```text
%APPDATA%\TraceSeal\settings.json
```

工作区只要求目录存在且可访问；可以暂时没有 `runs/` 或 `policy/`。切换后首页、Runs 和 Policy 会通过统一 API 自动刷新，不需要重启或刷新窗口。

如果需要接 Vite dev server，可先启动 Renderer：

```powershell
cd desktop\renderer
npm run dev
```

然后在 Electron 侧设置：

```powershell
cd ..\electron
$env:TRACESEAL_RENDERER_URL = "http://localhost:5173"
npm start
```

## Windows EXE / 安装包构建

一键构建脚本：

```powershell
cd C:\Users\mohui666\Documents\projectA\trace-seal
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1
```

脚本会按顺序执行：

1. Python unittest
2. PyInstaller 打包 Python Core
3. Renderer install / typecheck / test / build
4. Electron install / typecheck / test
5. Electron Forge make
6. 校验 Renderer/Python Core 资源并生成 SHA256

主要输出：

```text
packaging/dist/traceseal-core/traceseal-core.exe
desktop/electron/out/TraceSeal-win32-x64/resources/renderer/index.html
desktop/electron/out/TraceSeal-win32-x64/resources/traceseal-core/traceseal-core.exe
desktop/electron/out/make/squirrel.windows/x64/TraceSeal-Setup.exe
desktop/electron/out/make/squirrel.windows/x64/SHA256SUMS.txt
```

开发环境下 Electron 调用：

```text
python -m traceseal dashboard-data ...
```

打包环境下 Electron 根据 `app.isPackaged` 自动改为调用：

```text
resources/traceseal-core/traceseal-core.exe dashboard-data ...
```

因此安装包在没有单独安装 Python 的 Windows 环境中，也能打开 Dashboard、读取 policy，并通过 bundled Core 读取 runs。安装版不再要求设置 `TRACESEAL_REPOSITORY_ROOT`，直接通过系统目录选择框选择工作区。

当前安装包目标平台是 **Windows x64**，尚未提供 macOS/Linux 安装包。安装包尚未代码签名，Windows SmartScreen 可能显示未知发布者提示。v0.2.0 已完成独立干净 Windows VM 验证并正式发布；验证结论为 `PASS WITH KNOWN ISSUES`。当前仍只支持 Python Agent，sandbox 仍是目录复制而非 Docker/overlayfs。

## MVP Policy

默认策略文件：`policy/default_policy.json`

第一版采取 `warn/mark` 模式：记录风险但不阻断，便于回放事故。

当前规则：

- `dangerous_delete`: 标记 `rm -rf` / `rmdir /s /q`
- `env_write`: 标记写入 `.env` / `.env.*`
- `cascade_config_corruption`: 标记写坏 `config.json` / `settings.json` / `settings.yaml` / `settings.yml`
- `git_push`: 普通 push（high）
- `git_force_push` / `git_mirror_push` / `git_delete_remote_branch` / `git_force_refspec_push`: 高破坏性 push（critical）
- `git_force_with_lease` / `git_bulk_push`: 可能改写历史或批量发布 refs（high）
- `domain_denylist_match` / `domain_warnlist_match`: deny/warn 域名命中
- `domain_unknown_external`: 未在 allowlist 中的外部 host
- `domain_allowlist_match` / `domain_localhost_allowed`: trusted/local host 放行 metadata
- `suspicious_http_post`: 标记可疑 HTTP POST
- `sensitive_http_request`: 标记并脱敏带敏感 query/header/auth/cookie 的 `httpx` 请求
- `insecure_http_request`: 标记明文 `http://` 请求
- `cascade_failure_detected`: 同一 run 内至少 3 类有序风险 stage 形成级联事故

如需把高危操作改为阻断，可设置：

```powershell
$env:TRACESEAL_POLICY_MODE = "block"
python -m traceseal run python examples/bad_agent_delete.py
```

`os.system()` 使用同一套 Shell risk/policy 判断：低风险 `allow` 和高风险 `warn` 会调用原始 API，`block` / `deny` / `enforce` 模式下的 high/critical 命令不会执行。事件保留 `os.system()` 的原始返回值（POSIX 上为 wait status），并额外记录跨平台易读的 `output.exit_code`。被阻断时返回等价于 shell exit code 126 的非零状态。

## 演示流程

典型演示场景是 Agent 误删 `data/` 目录：

1. `bad_agent_delete.py` 创建 `data/important.txt`。
2. Agent 错误执行 `rm -rf data/`。
3. TraceSeal 记录 shell 事件和文件删除 diff。
4. `replay` 重建事件时间线。
5. `explain` 输出首次有害调用和建议规则。

## 运行测试

```powershell
python -m unittest discover -s tests -v
```

Python 核心案例测试覆盖：

- `test_bad_agent_delete_detected`
- `test_env_write_detected`
- `test_git_push_detected`
- `test_replay_latest`
- `test_explain_latest`
- `test_os_system_allow_warn_and_nonzero_status`
- `test_os_system_block_does_not_execute`
- `test_os_system_dashboard_and_first_harmful_event`
- `test_os_system_replay_and_explain`
- `FileReadTrackingTest` 的 5 个文件读取/敏感风险/Dashboard/replay/explain 测试
- `HttpxInterceptionTest` 的 5 个同步/异步 API、脱敏、失败、Dashboard/replay/explain 测试
- `GitPushClassificationTest` 的 push 类型、规则、metadata、YAML、dashboard/explain 和零远端调用测试
- `DomainPolicyTest` / `DomainPolicyIntegrationTest` 的名单、host 分类、fallback、cassette 脱敏和离线 demo 测试

当前完整基线：Python 90 tests、Renderer 96 tests、Electron 45 tests。

完整 Python 验证：

```powershell
python -m compileall -q traceseal sdk recorder replay minimizer policy sandbox dashboard examples tests
python -m unittest discover -s tests -v
```

Electron runtime 验证：

```powershell
cd desktop/electron
npm install
npm run typecheck
npm test
```

Renderer 验证：

```powershell
cd desktop/renderer
npm run typecheck
npm test
npm run build
```

完整桌面打包验证：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1
```

## 当前架构说明

第一版继续使用 Python 做拦截引擎，不现在重构成 Rust：

- 目标用户是 Python Agent，`sitecustomize` + monkey patch 可以最快接入 `open` / `pathlib` / `subprocess` / `urllib` / `requests`。
- recorder、policy、sandbox、replay、explain 都已经在 Python Core 跑通，继续补案例和测试比重写更重要。
- Rust 更适合后续做高强度 syscall/audit/跨语言 agent 监控，但会增加 FFI、跨平台权限、构建分发成本。
- Electron + React + TypeScript + TailwindCSS 只负责桌面展示层，通过 `dashboard-data` JSON 消费 Python Core 结果。

## 当前 MVP 边界

- replay 是 transcript replay，不重新执行 shell/file/http 副作用。
- shell 拦截 Python 进程内的 `subprocess.run` 和 `os.system`；`Popen` 暂未做完整等待/输出记录。
- HTTP 拦截支持 `urllib.request.urlopen` 和已安装 `requests` 时的 `requests.Session.request`。
- `bad_agent_http.py` 默认启用 `TRACESEAL_OFFLINE_HTTP=1` 离线模拟，避免测试和演示依赖真实外网。
- sandbox 是 workspace 复制，不是 Docker/overlayfs。
- Git 状态采集只保存 branch、HEAD、文件路径和状态等元数据，不保存完整源码 diff；linked worktree 的 `.git` 指针不会带入 sandbox。
- 文件读取是 Python 层 monkey patch，不保证捕获 C 扩展、外部进程或所有底层读取。
- `httpx` 记录为 Python 层 monkey patch，不是系统级防火墙，不捕获外部进程或所有 HTTP 客户端。
- HTTP cassette 只保存脱敏元数据与 body 摘要，不是包含完整请求/响应内容的确定性网络重放。

## 后续方向

- 阶段 3 Core 增强项已全部完成，包括 deterministic cascade failure 检测与离线事故链 demo。
- v0.3.0 已正式发布；Windows x64 是当前主要且已验证的桌面安装目标。
- Stage 4 Rust Guard 仍处于设计阶段，不属于 v0.3.0，也尚未进入实现。
- 后续可补更多真实项目事故案例，但不纳入本次 v0.3.0 Core 范围。
- 继续增强 Dashboard：Git/HTTP cassette 可视化、首次错误可视化和 policy 只读/编辑闭环。
- 升级 sandbox：Docker / overlayfs。
- 增加签名审计证明 attestation。
