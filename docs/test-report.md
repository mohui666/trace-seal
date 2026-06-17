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
