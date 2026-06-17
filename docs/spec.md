# TraceSeal 项目规格说明书

> 最后更新：2026-06-17  
> 当前版本：MVP v1 + Desktop Dashboard 数据层

## 1. TraceSeal 解决的问题

AI Agent 自动读写文件、执行 Shell、发 HTTP 请求、操作 Git 时，一旦把项目搞坏，开发者需要回答：

| 问题 | TraceSeal 的回答 |
|---|---|
| Agent 做了哪些操作？ | 记录核心副作用事件到 `events.jsonl`。 |
| 哪次调用第一次造成错误？ | `traceseal explain` 定位首次有害工具调用。 |
| 能否回放事故？ | `traceseal replay` 做 transcript replay，重建事件时间线。 |
| 下次如何提前阻断？ | `policy/default_policy.json` + warn/block 模式。 |
| 桌面端如何展示？ | `traceseal dashboard-data` 导出 JSON，供 Electron 读取。 |

一句话：TraceSeal 是 AI Agent 的操作黑匣子 + 执行前安全防火墙 + 失败回放系统。

## 2. 当前架构决策

当前不重构成 Rust，继续采用：

```text
Electron Dashboard
React + TypeScript + TailwindCSS
只负责展示 runs / explain / policy
        │
        │ 读取 dashboard-data JSON / 调用 Python CLI
        ▼
Python Core
traceseal run / replay / explain / dashboard-data
        │
        ├── sdk hooks
        ├── recorder events
        ├── policy rules
        ├── sandbox workspace copy
        └── replay / minimizer
```

原因：第一版只支持 Python Agent，`sitecustomize` + monkey patch 能最快覆盖 `open/pathlib/subprocess/urllib/requests` 等核心副作用边界。Rust Guard 适合作为后续 OS 级产品化方向，不是当前阶段重点。

## 3. 目标用户

| 用户类型 | 核心需求 | 使用方式 |
|---|---|---|
| AI Agent 开发者 | 调试 Agent 行为，定位事故根因 | CLI: `python -m traceseal run/explain` |
| 技术团队负责人 | 审计 Agent 操作 | Dashboard: 查看 runs 和风险报告 |
| DevOps 工程师 | 防止 Agent 破坏环境 | sandbox + policy block |
| 安全工程师 | 定义和执行安全策略 | policy 规则 + explain 建议 |

## 4. 典型使用场景

### 场景 A：Agent 误删数据目录

Agent 本应整理项目文件，但错误执行 `rm -rf data/`，导致测试数据丢失。

TraceSeal 记录文件写入、shell 删除和后续测试失败，并在 explain 中输出：

```text
首次有害工具调用:
[evt_0003] Shell 命令: rm -rf data/

建议策略:
deny shell "rm -rf data/**"
```

### 场景 B：Agent 修改敏感环境配置

Agent 自动创建或覆盖 `.env`，写入类似 `OPENAI_API_KEY=sk-demo-secret`、`DATABASE_URL=...` 的配置。TraceSeal 标记 `env_write`，并建议阻断 `.env*` 写入。

### 场景 C：Agent 未经确认推送 Git

Agent 执行 `git push origin main`。当前 demo 中 SDK 会离线模拟，不真实访问远端，但事件仍被记录并命中 `git_push`。

### 场景 D：Agent 发起可疑 HTTP POST

Agent 将敏感 payload POST 到外部 URL。demo 使用 `TRACESEAL_OFFLINE_HTTP=1` 离线模拟，命中 `suspicious_http_post`。

### 场景 E：安全审计与演示

团队可以通过 `events.jsonl`、`replay`、`explain` 和 `dashboard-data` JSON 审计一次 Agent 运行，定位风险事件并生成下一步 policy。

## 5. 当前已实现能力

| 模块 | 能力 | 当前状态 |
|---|---|---|
| sdk | 文件写入拦截 | `open(w/a/x/+)`、`Path.write_text/write_bytes` |
| sdk | 删除拦截 | `shutil.rmtree`、`os.remove/unlink`，并跨平台模拟 `rm -rf` |
| sdk | Shell 拦截 | `subprocess.run()`，记录命令、返回码、stdout/stderr 摘要 |
| sdk | Git push 风险 | 识别并模拟 `git push`，不访问真实远端 |
| sdk | HTTP 拦截 | `urllib.request.urlopen`、可选 `requests.Session.request`；demo 支持离线模拟 |
| recorder | 事件记录 | `events.jsonl`，包含 cwd、env 摘要、输入/输出、风险、文件变更 |
| recorder | Run 产物 | `manifest.json`、`workspace_before.json`、`workspace_after.json` |
| sandbox | 最小隔离 | 复制 workspace 到 `runs/<run_id>/workspace` |
| replay | transcript replay | 重建时间线，不重新执行副作用 |
| minimizer | explain | 定位首次高风险/有害事件，输出原因和建议规则 |
| policy | MVP 规则 | `dangerous_delete`、`env_write`、`git_push`、`suspicious_http_post` |
| cli | 命令行 | `run`、`replay`、`explain`、`dashboard-data` |
| dashboard | 数据层 | `dashboard/export.py` 输出 Electron 可读 JSON |
| tests | 自动化测试 | 5 个 unittest 覆盖 delete/env/git/replay/explain |

## 6. 已落地事故案例

| 案例 | 风险规则 | 说明 |
|---|---|---|
| `examples/bad_agent_delete.py` | `dangerous_delete` | 创建 `data/important.txt` 后执行 `rm -rf data/`。 |
| `examples/bad_agent_env.py` | `env_write` | 写入 `.env`，模拟敏感配置污染。 |
| `examples/bad_agent_git.py` | `git_push` | 模拟 `git push origin main`，不会真实推送。 |
| `examples/bad_agent_http.py` | `suspicious_http_post` | 离线模拟向外部 URL POST 敏感数据。 |

## 7. 第一版仍不做什么

| 不做 | 原因 |
|---|---|
| 非 Python Agent 支持 | 先聚焦 Python 生态。 |
| `os.system()` 完整拦截 | 当前重点是 `subprocess.run()`，后续补。 |
| `httpx` 拦截 | 当前已有 urllib/requests，后续补。 |
| 完整 Git diff/HEAD/staged 记录 | 当前只做 git push 风险识别。 |
| 真正确定性副作用重放 | 当前是 transcript replay。 |
| Docker/overlayfs sandbox | 当前 workspace 复制足够演示。 |
| `policy.yaml` DSL | 当前使用 JSON + Python matcher，后续升级。 |
| 完整 Electron UI | 当前先做 `dashboard-data` JSON 数据接口。 |

## 8. 为什么不是万能 Agent 平台

TraceSeal 有明确边界：

1. **只优先记录副作用**：重点是写文件、执行命令、HTTP 请求、Git 操作，不做完整 IDE 行为追踪。
2. **先做 Python Agent**：先把一个语言生态做深，再考虑跨语言守卫。
3. **不替代 Agent 编排框架**：不替代 LangChain、AutoGPT、Codex 等上层系统，而是在更底层做审计和防护。
4. **不一开始做云平台**：第一阶段是本地 CLI + 后续桌面 Dashboard，避免过早引入账号、云同步、权限系统。

## 9. CLI 验证命令

```powershell
python -m traceseal run python examples/bad_agent_delete.py
python -m traceseal replay runs/latest
python -m traceseal explain runs/latest
python -m traceseal dashboard-data runs/latest
python -m unittest discover -s tests -v
```

## 10. 路线图

详见 [roadmap.md](roadmap.md)。
