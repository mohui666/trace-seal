# TraceSeal 剩余案例与 Roadmap 验收报告

## 1. 结论

**通过。**

本次完成剩余关键任务：

- 新增/确认 `.env` 风险案例：`examples/bad_agent_env.py`
- 新增/确认 Git push 风险案例：`examples/bad_agent_git.py`
- 完善 policy 的 `dangerous_delete`、`env_write`、`git_push`、`suspicious_http_post`
- 调整 explain 输出：中文说明 + 针对 env/git 的建议策略
- 收敛 unittest 到 5 个目标测试
- 新增/更新 `docs/roadmap.md`
- 更新 README 的案例、explain 示例、roadmap 和架构说明

## 2. 验证时间

2026-06-17 17:34（Asia/Shanghai）

## 3. 最终验证命令

```powershell
cd C:\Users\mohui666\Documents\projectA\trace-seal

python -m traceseal run python examples/bad_agent_delete.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_env.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_git.py
python -m traceseal explain runs/latest

python -m traceseal replay runs/latest

python -m unittest discover -s tests -v
```

## 4. 关键输出

### dangerous_delete

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

### env_write

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

### git_push

```text
首次有害工具调用:
[evt_0002] Shell 命令: git push origin main

原因:
- 请求远程 git push
- 命中策略规则: git_push

建议策略:
require_approval git "push"
```

## 5. 自动测试结果

```text
test_bad_agent_delete_detected ... ok
test_env_write_detected ... ok
test_explain_latest ... ok
test_git_push_detected ... ok
test_replay_latest ... ok

----------------------------------------------------------------------
Ran 5 tests in 2.413s

OK
```

## 6. 注意事项

- `.env` 中只写入 demo 假密钥：`OPENAI_API_KEY=sk-demo-secret`。
- `bad_agent_git.py` 中的 `git push origin main` 由 TraceSeal SDK 离线模拟，不会真实推送远端。
- 当前继续保持 Python Core 路线；Rust Guard 是远期阶段。
- Electron + React + TypeScript + TailwindCSS 只作为后续 Dashboard 展示层。

## 7. 2026-06-19 Git 状态记录验收

- 新增 `recorder/git_state.py`，覆盖非 Git 目录、branch/HEAD、unstaged、staged、untracked、Git 缺失和失败降级。
- run 新增 `git_state_before.json` / `git_state_after.json`，manifest 新增 `git.before` / `git.after` / `git.summary`。
- `dashboard-data run <run_id>` 新增兼容性字段 `git_state`，包含 before、after 和 summary。
- `examples/bad_agent_git_state.py` 在 sandbox 内制造三类 Git 变更，不 commit、不 push、不访问网络。
- Python 全量测试：35 个，全部通过。

## 8. 2026-06-19 HTTP cassette 脱敏记录验收

- run 新增 `http_cassette.jsonl`，每条 entry 通过 `event_id` 关联 HTTP / `network.http` 事件。
- manifest 新增 `http_cassette.present/entry_count/high_risk_count/external_host_count/redacted/path` 摘要与失败 metadata。
- dashboard-data 新增 `http_cassette.summary` 和最多 50 条脱敏 entries。
- header/query 敏感字段统一替换为 `<redacted>`；请求/响应 body 仅保存 content type、size 和 SHA-256 摘要。
- `examples/bad_agent_http_cassette.py` 仅访问本地临时 HTTP server，使用合成假 secret。
- 新增 8 个 cassette 专项测试；Python 全量测试共 43 个。

## 9. 2026-06-19 policy.yaml DSL 验收

- 新增 `policy/dsl.py` 与 `policy/yaml_loader.py`，覆盖 schema 校验、规则匹配和 `policy.yaml` → `policy.yml` → 默认 JSON 加载顺序。
- YAML 解析/schema/regex 错误不会终止 run；记录 `yaml_error_fallback`、路径和错误后回退 `policy/default_policy.json`。
- match 支持 `event_type/path/command/method/host/url/risk_level/sensitive`，以及 exact 简写、`exact/contains/contains_any/glob/any_of/regex`。
- action 支持 `allow/warn/deny/require_approval`；`TRACESEAL_POLICY_MODE` 环境变量继续具有最高优先级。
- dashboard-data policy/run 与 explain 已暴露 `policy_source`、`rule_id`、`action`、`reason`、`suggested_policy`。
- `examples/bad_agent_policy_yaml.py` 仅使用 sandbox、本地 MockTransport 和合成 demo secret；危险删除被 YAML deny 稳定阻断，HTTP query/header 仍脱敏。
- 新增 13 个 YAML policy 专项测试；Python 全量测试共 56 个，全部通过。

## 10. 2026-06-19 Git push 风险细分验收

- 新增 `classify_git_push()`，区分 normal、force、force-with-lease、mirror、delete remote branch、force refspec、`--all` 和 `--tags`。
- 默认 JSON policy 与示例 YAML policy 新增精确 rule_id、risk、reason 和 suggested policy；普通 `git_push` 保持 high/warn 兼容。
- Shell 事件增加 `git_operation.push_type/remote/refs/protected_branch`，dashboard-data、replay 和 explain 可见。
- `subprocess.run()` 与 `os.system()` 的 Git push 均离线模拟，不调用真实 Git 或远端网络。
- 新增 `examples/bad_agent_git_push_classification.py` 和 6 个测试方法（含 16 组分类 subtests）。
- Python 全量测试共 62 个，全部通过。

## 11. 2026-06-19 HTTP 域名白名单 / 黑名单验收

- policy YAML 新增可选 `domain_policy`：allow/deny/warn domains、localhost/private 开关、unknown external 告警与 deny 阻断开关。
- host 分类覆盖 localhost、loopback、private、external、公网 IP 和 unknown；不进行 DNS 查询。
- 默认 JSON policy 和示例 YAML 同步新增 denylist、warnlist、unknown external、allowlist 和 localhost rule metadata。
- HTTP event、cassette、dashboard-data、replay、explain 均展示 domain decision 与 matched domain rule。
- `examples/bad_agent_domain_policy.py` 使用 `httpx.MockTransport`，不会访问真实外网；敏感 query/header 继续脱敏，body 仍只记录摘要。
- 新增 9 个域名策略专项测试；Python 全量测试共 71 个，全部通过。

## 12. 2026-06-19 级联错误案例验收

- 新增 `traceseal/cascade.py`，按 event `seq`、timestamp 或输入 index 排序，并从同一 run 中提取 sensitive read、HTTP exfiltration attempt、configuration corruption、destructive shell、dangerous Git push 五类 stage。
- 3 类 stage 标记 high cascade，4 类或更多标记 critical；1-2 类事件只保留普通风险说明，不产生 cascade。
- `dashboard-data` 新增 `cascade` object；replay / explain 展示是否命中、severity、有序 stages、first harmful event 和 human-readable summary。
- 新增 `cascade_config_corruption` 与 `cascade_failure_detected` policy metadata，不改变 YAML 缺失/无效时的 JSON fallback。
- `examples/bad_agent_cascade_failure.py` 使用 `httpx.MockTransport`、sandbox-only 删除与 Git push simulation，不访问真实外网、不执行真实 push。
- HTTP query/header 保持 `<redacted>`，request/response body 仍仅保存摘要；events、cassette、dashboard、replay、explain 均未发现完整合成 secret。
- 新增 19 个 cascade 专项测试；Python 全量测试共 90 个。

## 13. 2026-06-19 v0.3.0 release prep 全量验收

### 13.1 基线与结论

- 基线 commit：`520276d42c90d6c528a250cb51ade473c560c08b`
- 验证分支：`chore/v0.3-release-prep`
- 结论：**PASS FOR RELEASE CANDIDATE PREP**
- 发布状态：Stage 3 Core complete；v0.3.0 未创建 tag、未创建 GitHub Release。

### 13.2 自动化与 demo

- Python `compileall`：通过。
- Python unittest：90/90 通过（39.863 秒）。
- Renderer：typecheck 通过，96/96 tests 通过，production build 通过。
- Electron：typecheck 通过，45/45 tests 通过。
- 以下 7 个 demo 均生成独立 run，且每个 run 的 dashboard-data、replay、explain 均退出码 0：
  - delete：`run_20260619_215621_305434`
  - Git state：`run_20260619_215623_868575`
  - HTTP cassette：`run_20260619_215626_518762`
  - policy YAML：`run_20260619_215631_132158`
  - Git push classification：`run_20260619_215634_109263`
  - domain policy：`run_20260619_215636_714266`
  - cascade failure：`run_20260619_215639_826813`

### 13.3 隐私与安全

- 对 63 份 run artifact / dashboard-data / replay / explain 输出扫描 12 类完整敏感值，结果为 0 命中。
- 扫描覆盖 `demo-cascade-secret-123`、`sk-demo-secret`、`demo-token`、Authorization bearer、Cookie 和 HTTP cassette demo 的完整 token/header/body marker。
- 10 条 cassette entry 均无 `request_body`、`response_body` 或 raw body 字段，仅保留 content type、size、SHA-256 与 redaction metadata。
- domain/cascade HTTP 使用 MockTransport 或本地 server；Git push 全部模拟；删除只发生在 run 的 sandbox workspace。

### 13.4 Windows 构建与打包

- `scripts/build-windows.ps1 -SkipInstall`：通过。
- PyInstaller bundled core 构建与 `dashboard-data policy` smoke test：通过。
- Electron Forge package/make：通过。
- `TraceSeal-Setup.exe`：已生成，151,891,968 bytes（144.86 MiB）。
- Installer SHA-256：`fa08a63b2cc8f5062a6e37c73390853d6ccd753ffd18d09cfd27400c0ff48319`，与本地 `SHA256SUMS.txt` 一致。
- Packaged renderer `index.html` 与 bundled `traceseal-core.exe`：存在且 core smoke test 通过。
- GitHub Actions Windows build：main baseline `520276d` 的 [run 27829438486](https://github.com/mohui666/trace-seal/actions/runs/27829438486) 成功。
- `scripts/verify-release.ps1 -Mode Source`：PASS；当前 prep 分支产生预期的 non-standard branch warning。

### 13.5 已知限制

- package version metadata 仍一致地保持为已发布的 0.2.0；升级到 0.3.0 留给明确的 release/tag 步骤。
- 本次验证完成本地 installer 生成、资源和 hash 校验，但未把该 v0.3.0 release candidate 安装到干净 Windows VM 后重启验证。
- installer 未代码签名；仅验证 Windows x64。
- Python monkey-patch、目录复制 sandbox、transcript replay 和 metadata-only cassette 的既有边界保持不变。
- Rust Guard 不在本次范围。

## 14. 2026-06-21 v0.3.0 最终发布验证

### 14.1 发布状态

- Release：**TraceSeal v0.3.0 — RELEASED**
- Tag：`v0.3.0`
- Tag commit：`59ae99d6db495276963e2f4b47b137f4de846d35`
- GitHub Release：<https://github.com/mohui666/trace-seal/releases/tag/v0.3.0>
- Release workflow：[run 27901748342](https://github.com/mohui666/trace-seal/actions/runs/27901748342) — **success**

### 14.2 最终验证证据

- Python unittest：90/90 通过。
- 7 个核心 demo：全部通过，且 dashboard-data、replay、explain 验证成功。
- Renderer：96/96 tests 通过。
- Electron：45/45 tests 通过。
- Windows x64 installer build：通过。
- SHA-256 三重核验：本地 installer、`SHA256SUMS.txt` 与发布资产 digest 一致。
- 发布 installer SHA-256：`9a5e11083377c96b5d41b97fef81875120a66debce731ff23e4ed76ca08eefac`。
- Privacy scan：63 份输出、12 类敏感值、0 泄露。

### 14.3 发布边界

- Windows x64 是主要且已验证的桌面安装目标；installer 未代码签名。
- macOS/Linux desktop packaging 未做本次 release 验证。
- Rust Guard 不包含在 v0.3.0 中，Stage 4 当前仅为设计阶段。
- 完整发布证据见 [`artifacts/v0.3-release-report.md`](../artifacts/v0.3-release-report.md)。
