# TraceSeal 项目规格说明书

## 文档状态

本文是 TraceSeal 的目标规格说明，并同步标注当前代码仓库已经落地的 MVP 范围。

当前可运行实现以仓库根目录的 `README.md`、`python -m traceseal --help` 和 `policy/default_policy.json` 为准；尚未落地的能力在下方标为“后续”。


## 1. 项目背景

### 1.1 问题定义

AI Agent 正在接管越来越多的开发工作，但 Agent 的操作对开发者来说是一个**黑匣子**。当 Agent 把项目搞坏时，我们面临三个无法回答的问题：

1. **Agent 到底做了哪些操作？**
2. **哪一次工具调用第一次造成了错误？**
3. **下次能不能提前拦住类似危险操作？**

### 1.2 解决方案

TraceSeal 是 AI Agent 的**操作黑匣子 + 执行前安全防火墙 + 失败回放系统**。

它通过拦截 Agent 的工具调用，实现：

- **记录**：完整记录 Agent 的每一步操作
- **拦截**：在执行前检查操作风险，阻止危险行为
- **回放**：能够重现 Agent 的执行轨迹
- **定位**：精确定位首次造成错误的工具调用

### 1.3 第一版目标

把一次 Agent 事故完整记录下来，能够再次重现，并指出哪一次工具调用首次造成错误。

### 1.4 典型场景

**场景示例**：

Agent 本来应该修改 `src/main.py`，但它错误执行了 `rm -rf data/`。

TraceSeal 应该能记录：

- 第 1 步：读取 `src/main.py`
- 第 2 步：运行 `pytest`
- 第 3 步：执行 `rm -rf data/`
- 第 4 步：测试失败

然后输出：

```
首次造成错误的是第 3 步：
shell 命令 rm -rf data/
```

## 2. 第一版 MVP 功能边界

### 2.1 当前已实现（MVP）

| 功能 | 当前状态 |
|------|----------|
| 文件写入拦截 | 已拦截 `Path.write_text()`、`open()` 写模式，并记录写入前后状态。文件读取仅作为后续增强。 |
| 删除 API 拦截 | 已拦截 `shutil.rmtree()`、`os.remove()` / `os.unlink()`；Windows demo 中会模拟 `rm -rf data/` 删除效果。 |
| Shell 命令拦截 | 已拦截 Python 进程内的 `subprocess.run()`，记录命令、返回码、stdout/stderr 摘要和风险。 |
| HTTP 请求拦截 | 已拦截 `urllib.request.urlopen()`；如安装 `requests`，同时拦截 `requests.Session.request()`。`httpx` 后续实现。 |
| Git 风险识别 | 当前通过 shell 命令识别 `git push` 等风险；完整 Git diff / staged / HEAD 状态后续实现。 |
| 事件记录 | 已写入 `runs/<run_id>/events.jsonl`，包含事件编号、时间、cwd、env 摘要、输入/输出、风险和文件变更。 |
| Run 产物 | 已生成 `manifest.json`、`workspace_before.json`、`workspace_after.json`、sandbox workspace 和 `runs/latest`。 |
| 风险规则 | 当前使用 `policy/default_policy.json`，支持 `dangerous_delete`、`env_write`、`git_push`。 |
| CLI 工具 | 当前命令为 `python -m traceseal run/replay/explain`；安装后可使用 `traceseal run/replay/explain`。 |
| 回放 | 当前为 transcript replay：重建时间线，不重新执行副作用。 |
| 首次有害定位 | `traceseal explain` 会基于事件风险和文件影响找出首次高风险/有害事件并输出建议规则。 |

### 2.2 后续增强（Target / Nice to Have）

| 功能 | 说明 |
|------|------|
| 文件读取拦截 | 完整记录 `open().read()`、`Path.read_text()` 等读取行为。 |
| 完整 Git 记录 | 记录 Git diff、HEAD、staged 状态、远程分支信息和危险 Git 操作上下文。 |
| 完整 HTTP cassette | 记录请求/响应摘要、body 脱敏、重放所需的最小 cassette。 |
| `policy.yaml` DSL | 支持 allow / warn / deny / require_approval、路径匹配、命令 pattern、环境规则。 |
| 确定性回放 | 在隔离环境中按事件序列重新执行或模拟副作用。 |
| Dashboard | 可视化运行总览、事件时间线、高风险操作、文件 diff、首次错误。 |
| Attestation | 为运行日志、manifest、策略版本生成签名证明。 |
| 多 Agent 支持 | 支持同时监控多个 Agent 或多语言 Agent。 |

### 2.3 暂时不做（Won't Do）

| 功能 | 说明 | 原因 |
|------|------|------|
| 万能 Agent 平台 | 支持所有语言和框架 | 第一版只支持 Python Agent |
| 数据库操作拦截 | 拦截 SQL 执行 | 超出第一版范围 |
| 浏览器自动化拦截 | 拦截 Selenium/Playwright | 超出第一版范围 |
| 云端审计服务 | 将审计日志上传到云端 | 第一版只支持本地存储 |
| 实时协作 | 多人同时查看 Agent 操作 | 超出第一版范围 |
| AI 风险预测 | 用 AI 预测操作风险 | 先基于规则，后续再考虑 AI |

## 3. 用户画像

### 3.1 主要用户

| 用户类型 | 需求 | 使用场景 |
|----------|------|----------|
| AI Agent 开发者 | 调试 Agent 行为 | Agent 执行出错时，查看操作轨迹 |
| 技术团队负责人 | 审计 Agent 操作 | 审查 Agent 是否有违规操作 |
| DevOps 工程师 | 保障环境安全 | 防止 Agent 破坏生产环境 |
| 安全工程师 | 风险管控 | 定义和执行安全策略 |

### 3.2 典型使用场景

**场景 1：Agent 调试**

开发者使用 Codex/Cursor 等工具让 Agent 自动修改代码。Agent 执行后，开发者发现项目无法运行。使用 TraceSeal 查看 Agent 的操作轨迹，发现 Agent 在第 5 步误删了一个配置文件。

**场景 2：安全审计**

安全团队需要审查 AI Agent 是否有违规操作。使用 TraceSeal 查看 Agent 的操作记录，发现 Agent 尝试访问外部 API 并发送了敏感数据。

**场景 3：事故回放**

测试环境被 Agent 破坏，需要重现事故过程。使用 TraceSeal 的回放功能，在隔离环境中重现 Agent 的操作，定位问题根源。
