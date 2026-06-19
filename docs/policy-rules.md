# TraceSeal Policy 规则设计

> 当前实现：工作区 `policy.yaml` / `policy.yml` DSL，缺失或无效时兼容 `policy/default_policy.json` + `policy/rules.py`
> 当前模式：默认 warn/mark；设置 `TRACESEAL_POLICY_MODE=block` 后，高危操作会被阻断或模拟阻断。

## 1. 当前规则总览

| rule_id | event_type | 触发条件 | risk_level | 默认 action | 对应案例 |
|---|---|---|---|---|---|
| `dangerous_delete` | `shell` | `rm -rf` / `rmdir /s /q` | critical | warn | `bad_agent_delete.py` |
| `env_write` | `file.write` | 写入 `.env` / `.env.*` | high | warn | `bad_agent_env.py` |
| `sensitive_file_read` | `file.read` | 读取 `.env`、SSH key、PEM/key 或 credential/secret/token/password 路径 | high | warn | `bad_agent_file_read.py` |
| `git_push` | `shell` | `git push ...` | high | warn | `bad_agent_git.py` |
| `git_force_push` | `shell` | `git push --force` / `-f` | critical | warn | `bad_agent_git_push_classification.py` |
| `git_force_with_lease` | `shell` | `git push --force-with-lease` | high | warn | `bad_agent_git_push_classification.py` |
| `git_mirror_push` | `shell` | `git push --mirror` | critical | warn | `bad_agent_git_push_classification.py` |
| `git_delete_remote_branch` | `shell` | `--delete` / `:branch` refspec | critical | warn | `bad_agent_git_push_classification.py` |
| `git_force_refspec_push` | `shell` | `+ref` / `+src:dst` | critical | warn | `bad_agent_git_push_classification.py` |
| `git_bulk_push` | `shell` | `git push --all` / `--tags` | high | warn | `bad_agent_git_push_classification.py` |
| `domain_denylist_match` | `network.http` | host 命中 deny_domains | critical | warn | `bad_agent_domain_policy.py` |
| `domain_warnlist_match` | `network.http` | host 命中 warn_domains | high | warn | `bad_agent_domain_policy.py` |
| `domain_unknown_external` | `network.http` | external/ip host 未命中 allowlist | medium | warn | `bad_agent_domain_policy.py` |
| `domain_allowlist_match` | `network.http` | host 命中 allow_domains | low | allow | `bad_agent_domain_policy.py` |
| `domain_localhost_allowed` | `network.http` | localhost/loopback 且允许本地流量 | low | allow | `bad_agent_domain_policy.py` |
| `suspicious_http_post` | `http` | HTTP `POST` 到外部 URL 或携带敏感字段 | high | warn | `bad_agent_http.py` |
| `sensitive_http_request` | `network.http` | `httpx` 请求含敏感 query/header/cookie/auth | high | warn | `bad_agent_httpx.py` |
| `insecure_http_request` | `network.http` | 明文 `http://` 请求 | medium | warn | `bad_agent_httpx.py` |

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
  "suggested_policy": "deny file_write \".env*\""
}
```

## 3. 规则细节

### 3.1 dangerous_delete

| 字段 | 值 |
|---|---|
| 触发 | `rm -rf`、`rm -fr`、`rmdir /s /q` |
| 当前实现 | `policy.rules.is_rm_rf()` + `rm_targets()` |
| 风险说明 | 递归强制删除会不可逆地销毁目录树，Agent 可能误删数据目录或源码目录。 |
| warn 模式 | 执行/模拟执行并记录 critical 事件。 |
| block 模式 | 返回 126 / 抛出 `CalledProcessError`，不执行删除。 |

Explain 示例：

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

演示话术：Agent 本来只是整理文件，却删掉了整个 `data/`，TraceSeal 能精确指出第一步有害调用，并给出下一次可阻断的规则。

### 3.2 env_write

| 字段 | 值 |
|---|---|
| 触发 | 写入 `.env`、`.env.*` |
| 当前实现 | `policy.rules.evaluate_file_write()` |
| 风险说明 | `.env` 通常包含 API Key、数据库密码、Token；被 Agent 创建、覆盖或打印都需要审计。 |
| warn 模式 | 记录 `file.write`，标记 high。 |
| block 模式 | 在写入前阻断，避免敏感配置被创建/覆盖。 |

Explain 示例：

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

演示话术：这个案例使用 `sk-demo-secret` 等演示占位符，不包含真实密钥；重点是证明 TraceSeal 能发现敏感配置文件写入。

### 3.3 sensitive_file_read

| 字段 | 值 |
|---|---|
| 触发 | `.env` / `.env.*`、`id_rsa`、`id_ed25519`、`*.pem`、`*.key`、`.ssh` 及 credential/secret/token/password 类路径 |
| 当前实现 | `policy.rules.evaluate_file_read()` |
| 风险说明 | 读取敏感路径可能暴露凭据或密钥。 |
| warn 模式 | 执行读取并记录元数据，不记录文件全文。 |
| block 模式 | 在读取前阻断并记录 `status=blocked`。 |

该能力是 Python-level instrumentation，覆盖 `builtins.open` 和常见 `Path` API，不是 OS-level EDR，不承诺捕获 C 扩展或外部进程的读取。

### 3.4 git_push

| 字段 | 值 |
|---|---|
| 触发 | `git push ...` |
| 当前实现 | `policy.rules.classify_git_push()` + `is_git_push()`；subprocess 与 os.system 均离线模拟 |
| 风险说明 | `git push` 会把本地状态发布到远端；即使不是 `--force`，也应要求人工确认。 |
| warn 模式 | SDK 离线模拟，不执行真实 push，不接触远端。 |
| block 模式 | 模拟阻断并记录 `status=blocked`。 |

Explain 示例：

```text
首次有害工具调用:
[evt_0002] Shell 命令: git push origin main

原因:
- 请求远程 git push
- 命中策略规则: git_push

建议策略:
require_approval git "push"
```

演示话术：前置的修改、测试、提交可能都是正常操作，但直接 `git push origin main` 跨越了本地工作区边界，需要至少 `require_approval`。

分类 metadata：

```json
{
  "kind": "push",
  "push_type": "force_refspec",
  "remote": "origin",
  "refs": ["+main:main"],
  "protected_branch": true
}
```

`push_type` 支持 `normal`、`force`、`force_with_lease`、`mirror`、`delete_remote_branch`、`force_refspec`、`all`、`tags`。默认仍为 warn，以保持旧 demo 兼容；`TRACESEAL_POLICY_MODE=block/deny/enforce` 时沿用现有 high/critical enforcement 语义。无论 warn 或 block，检测到的 Git push 都不会调用真实 Git 远端。

### 3.5 suspicious_http_post

| 字段 | 值 |
|---|---|
| 触发 | HTTP `POST` / `PUT` 请求，尤其是外部 URL 或携带 secret-like 字段。 |
| 当前实现 | `policy.rules.evaluate_http_request()` |
| 风险说明 | HTTP POST 可能把源码、`.env` 或 token 外传。 |
| warn 模式 | 记录 method、url、status 或异常摘要。 |
| block 模式 | 写入 `status=blocked` 并抛出 `PermissionError`。 |

Explain 示例：

```text
首次有害工具调用:
[evt_0002] HTTP 请求: POST https://exfil.example.invalid/collect

原因:
- 可疑的出站 HTTP POST: POST https://exfil.example.invalid/collect
- 命中策略规则: suspicious_http_post

建议策略:
deny http "POST https://exfil.example.invalid/collect"
```

演示话术：当前 demo 默认 `TRACESEAL_OFFLINE_HTTP=1`，因此不会真实访问危险 URL，但事件、风险和建议规则都会完整产生。

### 3.6 sensitive_http_request

| 字段 | 值 |
|---|---|
| 触发 | `httpx` URL 含 token/api_key/secret/password 等 query，或请求含 Authorization/Cookie/X-API-Key 等敏感认证元数据 |
| 当前实现 | `sdk.httpx_hooks` + `policy.rules.evaluate_httpx_request()` |
| warn 模式 | 请求正常执行，敏感值替换为 `<redacted>`，不记录请求/响应全文。 |
| block 模式 | 请求前阻断 high-risk 请求并记录 `status=blocked`。 |

### 3.7 insecure_http_request

明文 `http://` 请求标记为 medium/warn；本地 HTTP demo 也保留该标记，敏感 query/header 规则优先级更高。该能力是 Python-level instrumentation，不是系统级网络防火墙或完整 DLP/WAF。

### 3.8 HTTP 域名策略

`policy.yaml` 可选顶层配置：

```yaml
domain_policy:
  allow_domains: ["api.example.com", "*.trusted.test", "localhost"]
  deny_domains: ["*.malware.test", "evil.example.com"]
  warn_domains: ["*.unknown.test"]
  allow_localhost: true
  allow_private_networks: false
  warn_on_unknown_external: true
  block_on_deny: false
```

现有 host `glob` 即域名通配匹配：`*.example.com` 匹配其子域名；无需额外 `domain_glob` 运算符。域名策略与普通 rules 共用 `rule_id/risk_level/action/reason/suggested_policy`，并遵守 `TRACESEAL_POLICY_MODE`。`block_on_deny=false` 保持默认 warn 兼容，设为 true 时复用现有 HTTP deny enforcement。

事件 metadata 输出 normalized host、host class、matched domain rule、decision 及 allow/deny/warnlist flags。HTTP cassette 只复制这组非敏感 metadata，URL query、header 和 body 仍沿用原脱敏/摘要边界。分类仅使用字符串和 `ipaddress`，不进行 DNS 查询。

## 4. 规则验证命令

```powershell
python -m traceseal run python examples/bad_agent_delete.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_env.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_git.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_http.py
python -m traceseal explain runs/latest

python -m traceseal run -- python examples/bad_agent_file_read.py
python -m traceseal explain runs/latest

python -m traceseal run -- python examples/bad_agent_httpx.py
python -m traceseal explain runs/latest
```

## 5. Policy 模式

| 模式 | 配置 | 行为 |
|---|---|---|
| warn | 默认或 `TRACESEAL_POLICY_MODE=warn` | 执行并记录风险。 |
| block | `TRACESEAL_POLICY_MODE=block` | high/critical 事件在执行前阻断或模拟阻断。 |

```powershell
$env:TRACESEAL_POLICY_MODE = "block"
python -m traceseal run python examples/bad_agent_env.py
```

## 6. policy.yaml DSL（v0.3.0）

工作区策略按 `policy.yaml`、`policy.yml`、内置 `policy/default_policy.json` 顺序加载。YAML 解析或 schema 校验失败时不终止 run，而是通过 `policy_source.type=yaml_error_fallback` 暴露错误并回退默认 JSON。示例：

```yaml
version: 1
mode: warn
rules:
  - id: dangerous-delete
    match:
      event_type: shell
      command:
        contains: "rm -rf"
    risk_level: critical
    action: deny
    reason: Recursive force delete can remove protected workspace data
    suggested_policy: 'deny shell "rm -rf <path>/**"'
```

字段：`version/mode/rules`；rule 支持 `id/description/match/risk_level/action/reason/suggested_policy`。match 字段支持 `event_type/path/command/method/host/url/risk_level/sensitive`，操作符支持 exact 标量简写、`exact/contains/contains_any/glob/any_of/regex`。无效 regex 在加载期报错并安全 fallback。

action 支持 `allow/warn/deny/require_approval`。第一版 `require_approval` 只记录 metadata；`deny` 仅在现有 Shell/HTTP enforcement 路径生效，不引入审批 UI。阶段 3 后续增强只剩级联错误案例。
