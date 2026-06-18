# TraceSeal

**Latest release: [v0.2.0](https://github.com/mohui666/trace-seal/releases/tag/v0.2.0)**

Windows x64 installer is available on GitHub Releases.

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

- 通过 `sitecustomize` + monkey patch 拦截 Python 文件写入、`subprocess.run()` / `os.system()` Shell 命令、HTTP 请求和常见删除 API。
- `traceseal run` 在临时 sandbox workspace 中执行命令，避免 demo 直接破坏原工作区。
- `recorder/` 写入 `events.jsonl`、`manifest.json`、`workspace_before.json`、`workspace_after.json`。
- `traceseal replay` 做 transcript replay，不重新执行副作用。
- `traceseal explain` 根据事件日志定位首次高风险/有害工具调用，并输出建议规则。
- `traceseal dashboard-data` 导出 Electron Dashboard 可直接读取的 JSON。

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
- [策略规则设计](docs/policy-rules.md)（下一阶段 policy.yaml DSL 草案；当前实现见 `policy/default_policy.json`）
- [事故测试案例](docs/incident-examples.md)（delete/env/git/http 案例已落地）
- [Dashboard 设计](docs/dashboard-design.md)（Renderer 已接入 Electron preload API 和真实 runs 数据）
- [演示脚本](docs/demo.md)（5 分钟展示讲稿）
- [路线图](docs/roadmap.md)（阶段计划）
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
- `git_push`: 标记 `git push`
- `suspicious_http_post`: 标记可疑 HTTP POST

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

当前完整基线：Python 17 tests、Renderer 96 tests、Electron 45 tests。

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
- Git 操作当前主要通过 shell 命令风险识别，完整 Git diff / HEAD / staged 状态记录仍待扩展。
- 文件读取记录、`httpx`、完整 HTTP cassette、policy 编辑器和 attestation 仍属于后续增强。

## 后续方向

- 已补充 `.env` 写入、Git push、HTTP POST 案例；下一步可补级联测试失败和更多真实项目事故案例。
- 扩展 policy DSL：`allow / warn / deny / require_approval`、路径匹配、命令 pattern 匹配。
- 继续增强 Dashboard：更完整的文件 diff、HTTP 记录、Git diff、首次错误可视化和 policy 只读/编辑闭环。
- 升级 sandbox：Docker / overlayfs。
- 增加签名审计证明 attestation。
