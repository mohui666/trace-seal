# TraceSeal Dashboard 原型设计

> 当前状态：已完成 Dashboard 数据接口，Electron UI 待实现。  
> 技术栈决策：Electron + React + TypeScript + TailwindCSS。  
> 数据来源：`python -m traceseal dashboard-data runs/latest`。

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
python -m traceseal dashboard-data runs/latest
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

### 最近事故卡片

展示：

- Run ID
- 命令
- 首个有害事件摘要
- 风险等级
- 建议规则

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

## 6. Explain 页面

重点展示：

- `first_harmful_event`
- `affected_files`
- `suggested_policy`
- 一键复制策略按钮

## 7. 最小 Electron 实现建议

第一版 UI 只需要：

1. 调用 `python -m traceseal dashboard-data runs/latest`。
2. 解析 JSON。
3. 渲染运行概要卡片。
4. 渲染事件时间线。
5. 渲染 first harmful 和 suggested policy。

不要先做复杂图表、用户系统、云同步或 policy 编辑器。

## 8. 后续增强

- runs 列表聚合多个 run
- 文件 diff 可视化
- shell stdout/stderr 面板
- HTTP 请求列表
- policy 规则编辑与测试
- 导出事故报告
