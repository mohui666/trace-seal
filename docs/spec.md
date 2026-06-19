# TraceSeal 项目规格说明书

> 最后更新：2026-06-19
> 当前版本：v0.3.0 Core 增强已完成（未发布）+ Desktop Dashboard 数据层

## 1. TraceSeal 解决的问题

AI Agent 自动读写文件、执行 Shell、发 HTTP 请求、操作 Git 时，一旦把项目搞坏，开发者需要回答：

| 问题 | TraceSeal 的回答 |
|---|---|
| Agent 做了哪些操作？ | 记录核心副作用事件到 `events.jsonl`。 |
| 哪次调用第一次造成错误？ | `traceseal explain` 定位首次有害工具调用。 |
| 能否回放事故？ | `traceseal replay` 做 transcript replay，重建事件时间线。 |
| 下次如何提前阻断？ | 工作区 `policy.yaml` DSL，缺失/无效时回退 `policy/default_policy.json`。 |
| 桌面端如何展示？ | `traceseal dashboard-data` 导出 JSON，供 Electron 读取。 |
| Agent 改动了哪些 Git 文件？ | run 前后记录 branch、HEAD、staged、unstaged、untracked 元数据。 |
| 多个风险是否形成事故链？ | deterministic cascade detector 按顺序聚合 stage、severity 和 first harmful event。 |

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
| sdk | 文件读取拦截 | `open(r/rb)`、`Path.open/read_text/read_bytes`，只保存路径、模式、API 和大小等元数据 |
| sdk | 文件写入拦截 | `open(w/a/x/+)`、`Path.write_text/write_bytes` |
| sdk | 删除拦截 | `shutil.rmtree`、`os.remove/unlink`，并跨平台模拟 `rm -rf` |
| sdk | Shell 拦截 | `subprocess.run()` 与 `os.system()`，记录命令、返回码、stdout/stderr 摘要 |
| sdk | Git push 风险 | 离线分类 normal/force/force-with-lease/mirror/delete/refspec/all/tags，不访问真实远端 |
| policy | HTTP 域名策略 | allow/deny/warn 名单、unknown external 告警与 localhost/loopback/private/external/ip/unknown 分类，不做 DNS 查询 |
| sdk | HTTP 拦截 | `urllib.request.urlopen`、可选 `requests.Session.request`、`httpx` 函数/Client/AsyncClient；敏感 query/header 脱敏 |
| recorder | 事件记录 | `events.jsonl`，包含 cwd、env 摘要、输入/输出、风险、文件变更 |
| recorder | Run 产物 | `manifest.json`、workspace/Git 快照与 `http_cassette.jsonl` |
| recorder | Git 状态 | `git_state_before.json`、`git_state_after.json`，只保存路径、状态、branch、HEAD 等元数据 |
| recorder | HTTP cassette | `http_cassette.jsonl`，保存脱敏 URL/header、状态码、风险规则及非正文 body 摘要 |
| sandbox | 最小隔离 | 复制 workspace 到 `runs/<run_id>/workspace` |
| replay | transcript replay | 重建时间线，不重新执行副作用 |
| minimizer | explain | 定位首次高风险/有害事件，输出原因和建议规则 |
| core | cascade analysis | 同一 run 的 3 类有序风险标记 high cascade，4 类或更多标记 critical |
| policy | YAML DSL + 默认规则 | 工作区 YAML schema/校验/匹配，支持 allow/warn/deny/require_approval，并兼容默认 JSON matcher |
| cli | 命令行 | `run`、`replay`、`explain`、`dashboard-data` |
| dashboard | 数据层 | `dashboard/export.py` 输出 Electron 可读 JSON |
| tests | 自动化测试 | 90 个 unittest 覆盖 recorder、cascade、policy YAML/JSON fallback、Git push/域名策略、replay、Git 与 HTTP 链路 |

## 6. 已落地事故案例

| 案例 | 风险规则 | 说明 |
|---|---|---|
| `examples/bad_agent_delete.py` | `dangerous_delete` | 创建 `data/important.txt` 后执行 `rm -rf data/`。 |
| `examples/bad_agent_env.py` | `env_write` | 写入 `.env`，模拟敏感配置污染。 |
| `examples/bad_agent_git.py` | `git_push` | 模拟 `git push origin main`，不会真实推送。 |
| `examples/bad_agent_http.py` | `suspicious_http_post` | 离线模拟向外部 URL POST 敏感数据。 |
| `examples/bad_agent_git_state.py` | Git 状态审计 | 制造 unstaged、staged、untracked 三类状态，不 commit、不访问远端。 |
| `examples/bad_agent_http_cassette.py` | HTTP cassette | 使用本地 server 生成 GET/POST 脱敏 cassette，不依赖外网。 |
| `examples/bad_agent_policy_yaml.py` | policy YAML DSL | 在 sandbox 中安装示例 YAML 并触发文件、Shell 与本地 HTTP 规则。 |
| `examples/bad_agent_git_push_classification.py` | Git push 分类 | 离线触发 normal/force/lease/mirror/delete/refspec/all/tags，不连接远端。 |
| `examples/bad_agent_domain_policy.py` | HTTP 域名策略 | 通过 MockTransport 离线触发 local、deny/warn/unknown/insecure 类别，不访问外网。 |
| `examples/bad_agent_cascade_failure.py` | `cascade_failure_detected` | 串联敏感读取、脱敏 HTTP、配置破坏、危险删除和离线 mirror push，输出有序 cascade summary。 |

## 7. 第一版仍不做什么

| 不做 | 原因 |
|---|---|
| 非 Python Agent 支持 | 先聚焦 Python 生态。 |
| 完整源码 Git diff 内容 | 默认只保存文件路径与状态，避免复制源码内容。 |
| 完整 HTTP 请求/响应正文 | cassette 默认只保存 size/hash/content-type 摘要，隐私优先。 |
| 真正确定性副作用重放 | 当前是 transcript replay。 |
| Docker/overlayfs sandbox | 当前 workspace 复制足够演示。 |
| policy UI / 云端 policy | v0.3.0 只实现本地 YAML DSL，不做编辑器、账号或云端同步。 |
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

Stage 3 Core 已完成并通过 2026-06-19 release-prep 验证。v0.3.0 当前仍是未发布、未打 tag 状态；Rust Guard 是阶段 4 远期规划。
