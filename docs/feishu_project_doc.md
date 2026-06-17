# TraceSeal 项目文档

## 1. 项目一句话介绍

TraceSeal 是面向 AI Agent 的 **操作黑匣子、安全防火墙和事故回放系统**。

它专门记录 AI Agent 在执行任务时发生的文件读写、Shell 命令、HTTP 请求、Git 操作等工具调用，并在事故发生后帮助开发者复现过程、定位首次造成错误的工具调用。

---

## 2. 项目背景

随着 AI Agent 开始参与真实工程开发，它不再只是回答问题，而是会直接操作项目：

- 读取和修改代码文件；
- 执行 Shell 命令；
- 访问 HTTP API；
- 执行 Git 操作；
- 自动运行测试、生成文件、清理目录。

这带来了一个新问题：

> 当 Agent 把项目搞坏时，我们很难知道它到底做了什么，以及是哪一步最先造成了错误。

传统日志通常只能看到最终结果，无法完整还原 Agent 的工具调用过程；传统防火墙也不理解 Agent 的开发行为，例如 `rm -rf data/`、修改 `.env`、`git push main` 这类操作在普通系统里只是命令，但在 Agent 场景下可能就是事故源头。

因此 TraceSeal 的目标是为 Agent 执行过程增加三种能力：

1. **记录**：像黑匣子一样记录每次工具调用；
2. **回放**：事故发生后可以重建执行时间线；
3. **定位**：指出第一次造成错误或高风险影响的工具调用。

---

## 3. 核心问题

TraceSeal 第一阶段重点回答三个问题：

| 问题 | TraceSeal 的回答 |
|---|---|
| Agent 到底做了什么？ | 通过 `events.jsonl` 记录工具调用时间线 |
| 哪一步第一次出错？ | 通过 `traceseal explain` 定位 first harmful event |
| 下次能不能拦住？ | 通过 policy 规则标记或阻断高危操作 |

---

## 4. 第一版 MVP 范围

第一版不做万能 Agent 平台，只支持 Python Agent 的核心副作用边界。

### 必须支持

- Python Agent 执行包装：`traceseal run`
- 文件写入和删除记录
- Shell 命令记录
- HTTP 请求记录基础能力
- Git 高风险操作识别
- 运行事件记录：`events.jsonl`
- 工作区快照：`workspace_before.json` / `workspace_after.json`
- 事故回放：`traceseal replay`
- 事故解释：`traceseal explain`
- 最小自动测试

### 可以后续支持

- 更完整的 HTTP 请求响应 cassette
- Docker / overlayfs 沙箱
- Dashboard 可视化页面
- 签名审计证明 attestation
- 多个事故案例库
- 更完善的 policy DSL

### 暂时不做

- 不做万能 Agent 平台
- 不做多语言 Agent 支持
- 不做浏览器自动化审计
- 不做 Kubernetes / 云资源审计
- 不做完全系统调用级别录制
- 不承诺 100% 确定性复现外部世界

---

## 5. 当前工程实现状态

项目路径：

```text
C:\Users\mohui666\Documents\projectA\trace-seal
```

当前已经完成 MVP 工程闭环：

```text
traceseal run → events.jsonl → replay → explain → 自动测试
```

### 已实现核心模块

| 模块 | 文件路径 | 当前状态 |
|---|---|---|
| CLI | `traceseal/cli.py` | 已实现 `run/replay/explain` |
| SDK hooks | `sdk/hooks.py` | 已实现 Python 进程内 hook |
| Recorder | `recorder/core.py` | 已实现事件 JSONL 记录 |
| Workspace snapshot/diff | `recorder/workspace.py` | 已实现运行前后工作区快照 |
| Replay | `replay/renderer.py` | 已实现 transcript replay |
| Explain / minimizer | `minimizer/explain.py` | 已实现首次高风险调用定位 |
| Policy | `policy/default_policy.json` | 已实现 MVP 规则 |
| Demo agent | `examples/bad_agent_delete.py` | 已实现误删数据案例 |
| Tests | `tests/test_mvp.py` | 已通过自动测试 |

---

## 6. 项目目录结构

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
├── attestation/        # 后续：签名审计证明
└── dashboard/          # 后续：可视化界面
```

---

## 7. Demo 使用方式

进入项目目录：

```powershell
cd C:\Users\mohui666\Documents\projectA\trace-seal
```

### 7.1 运行 Agent 并记录

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
runs/latest
```

### 7.2 回放事故

```powershell
python -m traceseal replay runs/latest
```

Replay 当前是 transcript replay，不重新执行副作用，只根据日志重建事件时间线。

### 7.3 定位首次错误调用

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

### 7.4 运行自动测试

```powershell
python -m unittest discover -s tests -v
```

当前测试结果：

```text
Ran 1 test in 0.658s

OK
```

---

## 8. 当前事故案例：误删 data 目录

### 案例名称

`bad_agent_delete.py`

### 错误行为

Agent 本来应该处理项目文件，但错误执行了递归强制删除命令：

```bash
rm -rf data/
```

### TraceSeal 应记录

- Agent 执行的 Shell 命令；
- 命令所在工作目录；
- 命令退出码；
- 删除前后的工作区差异；
- 被影响的文件路径；
- 命中的 policy 规则。

### 风险等级

高风险。

### explain 期望输出

TraceSeal 应指出：

```text
首次造成错误的工具调用是 evt_0003：shell rm -rf data/
原因：递归强制删除，命中 dangerous_delete 规则，删除了 protected path data/
建议规则：deny shell "rm -rf data/**"
```

---

## 9. MVP Policy 规则

默认策略文件：

```text
policy/default_policy.json
```

当前策略采取 `warn/mark` 模式：默认先记录风险，不强制阻断，便于演示事故回放。

### 当前规则

| 规则名 | 触发条件 | 风险说明 |
|---|---|---|
| `dangerous_delete` | `rm -rf` / `rmdir /s /q` | 递归强制删除可能破坏项目数据 |
| `env_write` | 写入 `.env` / `.env.*` | 可能修改或泄露敏感配置 |
| `git_push` | 执行 `git push` | 可能把错误代码推送到远端 |

### 阻断模式

如需把高危操作从“标记”改为“阻断”，可以设置：

```powershell
$env:TRACESEAL_POLICY_MODE = "block"
python -m traceseal run python examples/bad_agent_delete.py
```

---

## 10. 双人协作分工

| 成员 | 工具 | 主要职责 |
|---|---|---|
| 你 | Codex | 工程实现、CLI、SDK hooks、Recorder、Replay、Explain、测试 |
| 朋友 | v4pro / GLM | 需求文档、Policy 规则、事故案例、Dashboard 原型、README 和演示脚本 |
| 共同 | 任意 AI | 接口对齐、最终演示、验收、答辩材料 |

---

## 11. 当前已完成内容

### 工程侧已完成

- CLI 命令：`run/replay/explain`
- SDK hooks 基础实现
- Shell 危险命令记录
- 文件变更记录
- workspace snapshot/diff
- policy 规则加载
- bad agent demo
- transcript replay
- first harmful event explain
- unittest 自动测试

### 文档/产品侧待补充

- 更完整的 `docs/spec.md`
- 更完整的 `docs/policy-rules.md`
- 更多事故案例设计
- Dashboard 页面结构设计
- 3 到 5 分钟演示脚本
- 项目答辩材料

---

## 12. 下一阶段计划

### 短期目标

1. 增加更多事故案例：
   - 修改 `.env`
   - `git push main`
   - `curl | sh`
   - HTTP 数据外传
   - 改坏配置导致测试失败

2. 扩展自动测试：
   - `test_bad_agent_delete`
   - `test_env_write_detected`
   - `test_git_push_detected`
   - `test_replay_latest`
   - `test_explain_outputs_first_harmful_call`

3. 完善 policy：
   - 支持 `allow/warn/deny/require_approval`
   - 支持路径匹配
   - 支持命令 pattern 匹配

4. 设计 Dashboard 原型：
   - 运行总览
   - 事件时间线
   - 高风险操作
   - 文件 diff
   - Shell 输出
   - HTTP 请求记录
   - Git diff
   - 首次错误调用

### 中期目标

- Docker / overlayfs 沙箱
- HTTP cassette 回放
- 签名审计证明
- Web Dashboard
- Agent 框架适配：LangChain / OpenAI Agents SDK

---

## 13. 项目价值总结

TraceSeal 的核心价值不是“再造一个 Agent 平台”，而是为 Agent 落地补齐基础设施能力：

> 当 Agent 出事故时，TraceSeal 能告诉我们它做了什么、哪一步先出错、能否复现、下次如何拦住。

对于企业或团队使用 AI Agent 来说，这类能力会越来越重要，因为 Agent 的执行权限越大，对审计、回放、归责和防护的要求就越高。

---

## 14. 当前一句话结论

TraceSeal MVP 已经跑通核心闭环：

```text
运行 Agent → 记录工具调用 → 回放事故 → 定位首次有害调用 → 给出防护规则建议
```

下一步重点不是继续扩大范围，而是补充更多事故案例、完善测试、做好演示和文档。
