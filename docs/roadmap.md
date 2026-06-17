# TraceSeal 路线图

## 阶段 1：Python CLI MVP — 已完成

**时间**：2026 Q2

目标：把一次 Agent 事故完整记录下来，能够回放时间线，并指出首次有害调用。

### 已交付

| 模块 | 内容 |
|---|---|
| sdk | 文件写入、Shell、删除 API、HTTP 请求、Git push 风险拦截/模拟 |
| sandbox | workspace 复制隔离 |
| recorder | `events.jsonl` + `manifest.json` + workspace 快照 |
| replay | Transcript 回放 |
| policy | `dangerous_delete`、`env_write`、`git_push`、`suspicious_http_post` |
| minimizer | 首次有害工具调用 定位 |
| cli | `run/replay/explain/dashboard-data` |
| examples | delete/env/git/http 四个 bad agent demo |
| tests | 6 个 unittest 覆盖核心链路 |

### 当前指标

- 规则数：4 条
- Demo 数：4 个
- 测试数：6 个
- Dashboard 数据接口：1 个 JSON export

---

## 阶段 2：最小 Electron Desktop Dashboard — 下一步

**时间**：2026 Q3

目标：把 CLI MVP 升级为可展示的桌面原型。

### 技术栈

- Electron
- React
- TypeScript
- TailwindCSS
- Python Core CLI 作为数据来源

### 计划交付

| 模块 | 内容 |
|---|---|
| Electron 壳 | 本地桌面窗口 |
| 数据桥接 | 调用 `python -m traceseal dashboard-data runs/latest` |
| 首页 | run 概览、事件数、高风险数 |
| 事件时间线 | 展示 `events` 列表 |
| Explain 卡片 | 展示 `first_harmful_event` 和 `suggested_policy` |
| 案例切换 | 选择 delete/env/git/http demo 结果 |

### 不做

- 不做云同步
- 不做用户登录
- 不做复杂图表
- 不做 policy 编辑器完整闭环
- 不把拦截逻辑搬进 Electron

---

## 阶段 3：Core 增强

目标：补齐当前 Python Core 的工程缺口。

| 能力 | 状态 |
|---|---|
| 文件读取拦截 | 待做 |
| `os.system()` 拦截 | 待做 |
| `httpx` 拦截 | 待做 |
| Git diff / HEAD / staged 记录 | 待做 |
| HTTP cassette 脱敏记录 | 待做 |
| policy.yaml DSL | 待做 |
| 级联错误案例 | 待做 |
| GitHub Actions CI | 待做 |

---

## 阶段 4：Rust Guard 产品化 — 远期规划

当前阶段明确不做 Rust 重构。Rust Guard 作为远期产品化方向：

- OS 级进程监控
- 跨语言 Agent 支持
- 防篡改审计日志
- 更强 sandbox / policy enforcement

```text
阶段 1：Python Agent → Python hooks
阶段 2：Python hooks → dashboard-data → Electron Dashboard
阶段 3：增强 Python Core
阶段 4：Any Agent → Rust Guard（OS 级）
```

---

## 版本历史

| 版本 | 日期 | 内容 |
|---|---|---|
| v0.1.0 | 2026-06 | Python CLI MVP：run/replay/explain |
| v0.1.1 | 2026-06 | 补 env/git/http 案例与 dashboard-data JSON |
| v0.2.0 | 计划 | 最小 Electron Dashboard |
| v0.3.0 | 计划 | Core 增强：读取、os.system、httpx、Git diff |
| v1.0.0 | 远期 | 产品化 Guard + Dashboard |
