# Dashboard-data contract

## Status

The Python Core `dashboard-data` output is the shared read-only contract for desktop dashboard consumers. This document records the stable fields and compatibility expectations used by tests and docs.

Electron remains the default desktop implementation. Slint remains experimental-only.

## Consumers

Electron and the experimental Slint desktop path both consume Python Core `dashboard-data` JSON.

Electron uses the contract for the default desktop dashboard. The Slint path uses the same contract for experimental read-only dashboard views and parser tests.

## Commands

The shared read-only commands are:

- `python -m traceseal dashboard-data latest`
- `python -m traceseal dashboard-data list`
- `python -m traceseal dashboard-data policy`

These commands return JSON only. Consumers should treat the data as evidence for display, not as permission to mutate TraceSeal state.

## latest contract

`dashboard-data latest` describes the latest available run.

Required core fields:

- `schema_version`: contract schema version.
- `run_id`: stable run identifier for display and correlation.
- `status`: run status string.
- `event_count`: number of recorded events.
- `risk_count`: number of dashboard risks.

Optional representative fields include `started_at`, `finished_at`, `summary`, and `risks`.

## list contract

`dashboard-data list` returns a read-only run index.

Required core fields:

- `schema_version`: contract schema version.
- `runs`: ordered run summaries.

Each run summary should keep `run_id`, `status`, `started_at`, `event_count`, and `risk_count` stable when available.

## policy contract

`dashboard-data policy` returns read-only policy metadata for display.

Required core fields:

- `schema_version`: contract schema version.
- `policy`: policy summary metadata.
- `rules`: policy rule summaries.

Rule summaries should expose stable display identifiers and decisions without granting desktop consumers edit rights.

## Compatibility rules

Consumers must tolerate missing optional fields and use conservative display fallbacks. New optional fields may be added without breaking the contract. Existing core fields should remain stable in name and JSON type unless a future schema version documents the migration.

Fixtures under `tests/fixtures/dashboard-data/` are minimal, sanitized examples for Electron and Slint contract tests. They do not need to mirror every runtime field.

## Non-goals

This contract does not require either desktop path to call `traceseal run`, execute target commands, write workspace state, edit policy, or modify release / packaging behavior.

This contract does not replace Python Core behavior, change Electron runtime behavior, change Slint runtime behavior, change `app.slint`, create a release, or modify tags.

---

# dashboard-data 契约

## 状态

Python Core 的 `dashboard-data` 输出是桌面 dashboard 消费方共享的只读契约。本文记录测试和文档依赖的稳定字段与兼容预期。

Electron 仍是默认桌面实现。Slint 仍是实验用途。

## 消费方

Electron 和实验性的 Slint 桌面路径都消费 Python Core 的 `dashboard-data` JSON。

Electron 将该契约用于默认桌面 dashboard。Slint 路径将同一契约用于实验性的只读 dashboard 视图和 parser 测试。

## 命令

共享的只读命令是：

- `python -m traceseal dashboard-data latest`
- `python -m traceseal dashboard-data list`
- `python -m traceseal dashboard-data policy`

这些命令只返回 JSON。消费方应将数据视为展示用证据，而不是修改 TraceSeal 状态的授权。

## latest 契约

`dashboard-data latest` 描述最新可用 run。

必需核心字段：

- `schema_version`：契约 schema 版本。
- `run_id`：用于展示和关联的稳定 run 标识。
- `status`：run 状态字符串。
- `event_count`：记录事件数量。
- `risk_count`：dashboard 风险数量。

可选代表字段包括 `started_at`、`finished_at`、`summary` 和 `risks`。

## list 契约

`dashboard-data list` 返回只读 run 索引。

必需核心字段：

- `schema_version`：契约 schema 版本。
- `runs`：有序 run 摘要列表。

每个 run 摘要在可用时应保持 `run_id`、`status`、`started_at`、`event_count` 和 `risk_count` 稳定。

## policy 契约

`dashboard-data policy` 返回展示用只读 policy metadata。

必需核心字段：

- `schema_version`：契约 schema 版本。
- `policy`：policy 摘要 metadata。
- `rules`：policy rule 摘要列表。

Rule 摘要应暴露稳定的展示标识和 decision，但不授予桌面消费方编辑权限。

## 兼容规则

消费方必须容忍可选字段缺失，并使用保守展示 fallback。新增可选字段不应破坏契约。除非未来 schema version 记录迁移方式，现有核心字段应保持字段名和 JSON 类型稳定。

`tests/fixtures/dashboard-data/` 下的 fixture 是用于 Electron 和 Slint 契约测试的最小脱敏示例，不需要完整复刻 runtime 的所有字段。

## 非目标

该契约不要求任何桌面路径调用 `traceseal run`、执行目标命令、写入 workspace、编辑 policy，或修改 release / packaging 行为。

该契约不替代 Python Core 行为，不改变 Electron runtime 行为，不改变 Slint runtime 行为，不修改 `app.slint`，不创建 release，也不修改 tag。
