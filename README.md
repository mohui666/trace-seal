# TraceSeal MVP

TraceSeal 是 AI Agent 的操作黑匣子 + 执行前安全防火墙 + 失败回放系统。

它要解决的问题是：当 AI Agent 自动读写文件、执行 Shell、发 HTTP 请求、操作 Git 时，如果它把项目搞坏了，我们需要知道它做了什么、哪一步第一次造成错误、能否回放事故，以及下次能否提前阻断类似危险操作。

当前仓库已经实现 Python Agent 的 MVP 工程闭环：

```text
traceseal run → events.jsonl / manifest.json → traceseal replay → traceseal explain
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

- 通过 `sitecustomize` + monkey patch 拦截 Python 文件写入、Shell 命令、HTTP 请求和常见删除 API。
- `traceseal run` 在临时 sandbox workspace 中执行命令，避免 demo 直接破坏原工作区。
- `recorder/` 写入 `events.jsonl`、`manifest.json`、`workspace_before.json`、`workspace_after.json`。
- `traceseal replay` 做 transcript replay，不重新执行副作用。
- `traceseal explain` 根据事件日志定位首次高风险/有害工具调用，并输出建议规则。

## 目录结构

```text
trace-seal/
├── traceseal/          # CLI 入口：traceseal run/replay/explain
├── bootstrap/          # sitecustomize 自动安装 SDK hooks
├── sdk/                # Python Agent hooks：文件、shell、HTTP、删除 API
├── policy/             # MVP policy：rm -rf、.env 写入、git push
├── sandbox/            # 最小 sandbox：复制 workspace 到 runs/<id>/workspace
├── recorder/           # JSONL event recorder + workspace snapshot/diff
├── replay/             # transcript replay
├── minimizer/          # explain / first harmful event
├── examples/           # bad agent demo
├── tests/              # MVP 自动测试
├── docs/               # 规格、规则、事故案例、Dashboard 设计
├── attestation/        # 预留
└── dashboard/          # 预留
```

## 文档

- [项目规格说明书](docs/spec.md)（目标规格 + 当前 MVP 状态）
- [策略规则设计](docs/policy-rules.md)（下一阶段 policy.yaml DSL 草案；当前实现见 `policy/default_policy.json`）
- [事故测试案例](docs/incident-examples.md)（`bad_agent_delete.py` 已落地，其余为后续案例）
- [Dashboard 设计](docs/dashboard-design.md)（设计草案，尚未实现）
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

## 运行 demo

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
First harmful tool call:
[evt_0003] shell: rm -rf data/

Reason:
- recursive force delete requested: data/
- deleted protected path: data/
- matched policy rule: dangerous_delete

Affected files:
- data
- data/important.txt

Suggested policy:
deny shell "rm -rf data/**"
```

## MVP Policy

默认策略文件：`policy/default_policy.json`

第一版采取 `warn/mark` 模式：记录风险但不阻断，便于回放事故。

当前规则：

- `dangerous_delete`: 标记 `rm -rf` / `rmdir /s /q`
- `env_write`: 标记写入 `.env` / `.env.*`
- `git_push`: 标记 `git push`

如需把高危操作改为阻断，可设置：

```powershell
$env:TRACESEAL_POLICY_MODE = "block"
python -m traceseal run python examples/bad_agent_delete.py
```

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

## 当前 MVP 边界

- replay 是 transcript replay，不重新执行 shell/file/http 副作用。
- shell 主要拦截 Python 进程内的 `subprocess.run`；`Popen` 暂未做完整等待/输出记录。
- HTTP 拦截支持 `urllib.request.urlopen` 和已安装 `requests` 时的 `requests.Session.request`。
- sandbox 是 workspace 复制，不是 Docker/overlayfs。
- Git 操作当前主要通过 shell 命令风险识别，完整 Git diff / HEAD / staged 状态记录仍待扩展。
- 文件读取记录、`httpx`、完整 HTTP cassette、Dashboard 和 attestation 仍属于后续增强。

## 后续方向

- 补充更多事故案例：`.env` 泄露、Git 强推、外部 HTTP 数据外传、级联测试失败。
- 扩展 policy DSL：`allow / warn / deny / require_approval`、路径匹配、命令 pattern 匹配。
- 增加 Dashboard：运行总览、事件时间线、高风险操作、文件 diff、HTTP 记录、Git diff、首次错误。
- 升级 sandbox：Docker / overlayfs。
- 增加签名审计证明 attestation。
