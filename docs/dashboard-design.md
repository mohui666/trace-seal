# TraceSeal Dashboard 原型设计

> 当前状态：已完成 Dashboard 数据接口、Electron main/preload/IPC 运行层、Renderer 真实数据接入和 Windows 打包链路。
> 技术栈决策：Electron + React + TypeScript + TailwindCSS。
> 数据来源：开发环境为 `python -m traceseal dashboard-data ...`；打包环境为 bundled `resources/traceseal-core/traceseal-core.exe dashboard-data ...`。

## 1. 分层架构

```text
Electron Desktop UI
  React + TypeScript + TailwindCSS
  只负责展示 runs / events / explain / policy
        │
        │ 调用或读取
        ▼
Python Core CLI
  python -m traceseal run/replay/explain/dashboard-data
        │
        ▼
runs/<run_id>/events.jsonl + manifest.json + snapshots
```

当前阶段不要把拦截逻辑搬到 Electron，也不要重构成 Rust。

## 2. 已实现数据接口

命令：

```powershell
# 兼容旧命令
python -m traceseal dashboard-data runs/latest

# 阶段 2 Electron runtime 使用
python -m traceseal dashboard-data latest
python -m traceseal dashboard-data list
python -m traceseal dashboard-data run <run_id>
python -m traceseal dashboard-data policy
```

输出 JSON：

```json
{
  "schema_version": 1,
  "run_id": "run_...",
  "command": "python examples/bad_agent_http.py",
  "started_at": "2026-06-17T08:37:33Z",
  "finished_at": "2026-06-17T08:37:34Z",
  "status": "completed",
  "exit_code": 0,
  "event_count": 2,
  "high_risk_count": 1,
  "first_harmful_event": { "id": "evt_0002" },
  "events": [],
  "affected_files": [],
  "suggested_policy": "deny http \"POST https://...\""
}
```


## 2.1 Electron runtime IPC API

`desktop/electron/` 已实现 main/preload/IPC/Python runner 数据运行层。Renderer 只能通过 `window.traceSeal` 使用以下固定 API：

```typescript
window.traceSeal.getLatestRun()
window.traceSeal.listRuns()
window.traceSeal.getRun(runId)
window.traceSeal.getPolicy()
window.traceSeal.getRuntimeInfo()
```

安全边界：

- Electron main 通过 `spawn(command, args, { shell: false })` 调用 Python CLI。
- IPC 只暴露固定操作，不支持任意命令或任意文件路径。
- preload 只暴露 `traceSeal` 对象。
- BrowserWindow 必须设置 `contextIsolation: true` 和 `nodeIntegration: false`。

## 3. 页面信息架构

```text
Dashboard
├── /                    # 首页
├── /runs                # 运行列表
├── /runs/:id            # 运行详情
├── /runs/:id/explain    # 事故分析
├── /policy              # 策略管理（后续）
└── /settings            # 设置（后续）
```

## 4. 首页 `/`

### 统计卡片

| 字段 | 来源 |
|---|---|
| 总事件数 | `event_count` |
| 高风险事件数 | `high_risk_count` |
| 最近运行状态 | `status` / `exit_code` |
| First harmful | `first_harmful_event` |
| 当前 policy 模式 | manifest / 环境配置，后续补充 |

### 最近事故卡片

展示：

- Run ID
- 命令
- 首个有害事件摘要
- 风险等级
- 建议规则

### 最近运行列表（后续聚合多个 run）

| 列 | 说明 |
|---|---|
| Run ID | 运行标识 |
| 命令 | 执行命令 |
| 开始时间 | ISO 时间 |
| 退出码 | 0 或非 0 |
| 事件数 | `event_count` |
| 高风险 | `high_risk_count` |
| 操作 | 查看 / replay / explain |

## 5. Run Detail `/runs/:id`

### 运行概要

| 字段 | JSON 字段 |
|---|---|
| Run ID | `run_id` |
| 命令 | `command` |
| 开始时间 | `started_at` |
| 结束时间 | `finished_at` |
| 事件总数 | `event_count` |
| 高风险数 | `high_risk_count` |

### 事件时间线

每条事件展示：

- `id` / `seq`
- `ts`
- `type`
- `operation`
- `input.command` 或 `input.path` / `input.url`
- `risk.level`
- `risk.policy_rule`
- `output.status`
- `file_changes`

### 详情面板

| 面板 | 展示内容 |
|---|---|
| File Diff | created / modified / deleted，以及后续可视化 diff |
| Shell Output | 命令、返回码、stdout/stderr 摘要 |
| HTTP Detail | method、url、status/异常摘要 |
| Policy Hit | rule_id、risk_level、action、reason |
| Raw JSON | 完整事件 JSON，便于调试 |

## 6. Explain 页面 `/runs/:id/explain`

重点展示：

- `first_harmful_event`
- reason 列表
- `affected_files`
- `suggested_policy`
- 一键复制策略按钮

## 7. Policy 页面 `/policy`（后续）

第一版可只读展示 `policy/default_policy.json`：

| 列 | 说明 |
|---|---|
| 规则 ID | `rule_id` |
| 触发条件 | `pattern` |
| 类型 | `event_type` |
| 风险等级 | `risk_level` |
| 动作 | `action` |
| 建议规则 | `suggested_policy` |

后续再做编辑、启用/禁用、规则测试器。

## 8. 关键组件列表

| 组件名 | 用途 | 所在页面 |
|---|---|---|
| `StatCard` | 统计卡片 | 首页 |
| `RunsTable` | 运行列表表格 | 首页 / Runs |
| `EventTimeline` | 事件时间线 | Run Detail |
| `EventDetail` | 事件详情展开 | Run Detail |
| `FileDiff` | 文件对比 | Run Detail |
| `ShellOutput` | Shell 输出 | Run Detail |
| `HttpDetail` | HTTP 请求详情 | Run Detail |
| `ExplainPanel` | 事故分析面板 | Explain |
| `PolicyList` | 策略列表 | Policy |
| `RiskBadge` | 风险等级标签 | 多处 |
| `RunStatusBadge` | 运行状态标签 | 多处 |
| `FilterBar` | 筛选栏 | Runs |

## 9. TypeScript 类型定义草案

```typescript
type RiskLevel = "low" | "medium" | "high" | "critical";
type PolicyAction = "warn" | "deny" | "block";
type EventType = "file.write" | "file.delete" | "shell" | "http" | "sdk";
type RunStatus = "completed" | "failed" | "blocked";

interface DashboardRunExport {
  schema_version: number;
  run_id: string;
  command: string;
  started_at?: string;
  finished_at?: string;
  status?: RunStatus;
  exit_code?: number;
  event_count: number;
  high_risk_count: number;
  first_harmful_event?: TraceEvent | null;
  events: TraceEvent[];
  affected_files: string[];
  suggested_policy?: string | null;
}

interface TraceEvent {
  id: string;
  seq?: number;
  ts?: string;
  type: EventType;
  operation?: string;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  risk?: {
    level?: RiskLevel;
    reasons?: string[];
    policy_rule?: string;
    action?: PolicyAction;
  };
  file_changes?: FileChange[];
}

interface FileChange {
  path: string;
  change_type: "created" | "modified" | "deleted";
  before_sha256?: string;
  after_sha256?: string;
}
```

## 10. Tailwind 风格建议

| 用途 | Tailwind Class |
|---|---|
| 主背景 | `bg-gray-950` |
| 卡片背景 | `bg-gray-900` |
| 边框 | `border-gray-800` |
| 主文字 | `text-gray-100` |
| 次要文字 | `text-gray-400` |
| 强调色 | `text-emerald-400` |
| 风险 low | `bg-green-900/30 text-green-400` |
| 风险 medium | `bg-yellow-900/30 text-yellow-400` |
| 风险 high | `bg-orange-900/30 text-orange-400` |
| 风险 critical | `bg-red-900/30 text-red-400` |
| 按钮主色 | `bg-emerald-600 hover:bg-emerald-500` |
| 按钮危险 | `bg-red-600 hover:bg-red-500` |

风格要点：暗色主题、卡片式布局、事件时间线竖线连接、代码块使用等宽字体、风险 Badge 用圆角标签。

## 11. 最小 Electron 实现状态

第一版 UI/运行层已经按以下方式落地：

1. Renderer 只调用 `window.traceSeal.*`，不直接访问 Node.js。
2. Electron main 通过固定 IPC 调用 Python Core。
3. 开发环境调用 `python -m traceseal dashboard-data ...`。
4. 打包环境调用 bundled `traceseal-core.exe dashboard-data ...`。
5. Renderer 渲染运行概要、事件时间线、first harmful 和 suggested policy。

不要先做复杂图表、用户系统、云同步或 policy 编辑器。

## 12. Demo 展示顺序

1. 首页：展示统计卡片和最近事故。
2. Runs 列表：展示多次运行记录。
3. Run Detail：展示事件时间线，高亮高危事件。
4. Explain：展示 first harmful tool call 和一键复制规则。
5. Policy：展示规则列表，演示规则测试思路。

## 13. 后续增强

- runs 列表聚合多个 run
- 文件 diff 可视化
- shell stdout/stderr 面板
- HTTP 请求列表
- policy 规则编辑与测试
- 导出事故报告
