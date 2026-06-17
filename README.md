# TraceSeal MVP

TraceSeal 是 AI Agent 的操作黑匣子 + 执行前安全防火墙 + 失败回放系统。

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
├── attestation/        # 预留
└── dashboard/          # 预留
```

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
traceseal run python examples/bad_agent_delete.py
```

未安装 console script 时：

```powershell
python -m traceseal run python examples/bad_agent_delete.py
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
traceseal replay runs/latest
```

或：

```powershell
python -m traceseal replay runs/latest
```

输出是 transcript replay，只重建时间线，不重新执行副作用。

## 查看 explain

```powershell
traceseal explain runs/latest
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
traceseal run python examples/bad_agent_delete.py
```

## 运行测试

```powershell
python -m unittest discover -s tests
```

## 当前 MVP 边界

- replay 是 transcript replay，不重新执行 shell/file/http 副作用。
- shell 主要拦截 Python 进程内的 `subprocess.run`；`Popen` 暂未做完整等待/输出记录。
- HTTP 拦截支持 `urllib.request.urlopen` 和已安装 `requests` 时的 `requests.Session.request`。
- sandbox 是 workspace 复制，不是 Docker/overlayfs。
