# TraceSeal 5 分钟演示脚本

> 适合答辩、项目展示、Demo Day。  
> 推荐命令统一使用 `python -m traceseal ...`，避免未安装 console script 时失败。

## 0. 舞台布置与演示前准备

舞台布置建议：

- 左侧：终端窗口，字体调大，深色背景。
- 右侧：GitHub 仓库、README 或 Dashboard 原型设计文档。
- 终端提前进入项目目录。

```powershell
cd C:\Users\mohui666\Documents\projectA\trace-seal
python -m unittest discover -s tests -v
```

确认测试通过后开始演示。

---

## 1. 开场：为什么 Agent 需要黑匣子（30 秒）

演讲词：

> AI Agent 写代码越来越强，但它也会犯错。它可能误删目录、改坏 `.env`、执行 `git push`，或者把敏感数据 POST 到外部服务。  
> 问题是：事故发生后，我们往往不知道 Agent 到底做了哪些副作用操作，也不知道第一步有害操作是哪一次。  
> TraceSeal 要做的就是给 AI Agent 加上黑匣子、安全防火墙和失败回放。

一句话介绍：**TraceSeal 记录 Agent 做了什么，回放事故过程，并指出第一次造成错误的工具调用。**

---

## 2. 演示误删目录（60 秒）

```powershell
python -m traceseal run python examples/bad_agent_delete.py
python -m traceseal replay runs/latest
python -m traceseal explain runs/latest
```

讲解点：

- Agent 创建了 `data/important.txt`。
- Agent 执行了 `rm -rf data/`。
- TraceSeal 在 sandbox 中跨平台模拟删除，不破坏真实工作区。
- replay 重建时间线。
- explain 定位 `dangerous_delete`。

关键输出：

```text
首次有害工具调用:
[evt_0003] Shell 命令: rm -rf data/

建议策略:
deny shell "rm -rf data/**"
```

演讲词：

> 这个 Agent 本来只是写测试数据，却误删了整个 `data/` 目录。  
> TraceSeal 不只告诉我们“测试失败了”，还告诉我们是哪一次工具调用第一次造成了事故。

---

## 3. 演示 block 模式（30 秒）

```powershell
$env:TRACESEAL_POLICY_MODE = "block"
python -m traceseal run python examples/bad_agent_delete.py
$env:TRACESEAL_POLICY_MODE = "warn"
```

讲解点：

- 默认 warn 模式用于记录事故，便于 replay/explain。
- block 模式用于执行前阻断高危操作。
- 这体现 TraceSeal 的“执行前安全防火墙”定位。

---

## 4. 演示 .env 风险（45 秒）

```powershell
python -m traceseal run python examples/bad_agent_env.py
python -m traceseal explain runs/latest
```

讲解点：

- Agent 写入 `.env`，内容类似 `OPENAI_API_KEY=sk-demo-secret` 和 `DATABASE_URL=postgres://demo:demo@localhost/demo`。
- 这些都是 demo 假密钥，不包含真实凭据。
- TraceSeal 记录 `file.write`。
- 命中 `env_write`。
- 如果开启 block 模式，写入前会被阻断。

---

## 5. 演示 Git push 风险（45 秒）

```powershell
python -m traceseal run python examples/bad_agent_git.py
python -m traceseal explain runs/latest
```

讲解点：

- Agent 尝试执行 `git push origin main`。
- SDK 离线模拟，不真实推送远端。
- 事件仍被记录为 shell 风险。
- 命中 `git_push`。
- 普通 `git push` 也应该至少要求人工确认，不只是 `--force` 才危险。

---

## 6. 演示 HTTP POST 风险（45 秒）

```powershell
python -m traceseal run python examples/bad_agent_http.py
python -m traceseal explain runs/latest
```

讲解点：

- Agent 模拟向 `https://exfil.example.invalid/collect` POST 敏感 payload。
- demo 默认启用 `TRACESEAL_OFFLINE_HTTP=1`，不访问真实外网。
- TraceSeal 记录 method、url、状态和风险。
- 命中 `suspicious_http_post`。

---

## 7. 展示 Dashboard 数据接口（45 秒）

```powershell
python -m traceseal dashboard-data runs/latest
```

讲解点：

- Electron Dashboard 不直接做拦截。
- Python Core 负责 run / replay / explain / policy / recorder / sandbox。
- Electron + React + TypeScript + TailwindCSS 只读取这个 JSON 做展示。

JSON 重点字段：

- `run_id`
- `event_count`
- `high_risk_count`
- `first_harmful_event`
- `events`
- `affected_files`
- `suggested_policy`

---

## 8. 结尾（30 秒）

TraceSeal 当前已经具备：

1. **可记录**：记录文件写入、Shell、Git push、HTTP POST 等核心副作用。
2. **可回放**：replay 重建事件时间线。
3. **可定位**：explain 找出首次有害工具调用。
4. **可阻断**：block 模式阻断高危行为。
5. **可展示**：dashboard-data JSON 可供 Electron 原型读取。

演讲词：

> TraceSeal 让 AI Agent 不再是一个黑匣子。当前我们已经完成 Python CLI MVP，下一步是把这些数据接到最小 Electron Dashboard。

## 9. 演示环境检查清单

- [ ] 已进入 `C:\Users\mohui666\Documents\projectA\trace-seal`
- [ ] `python -m unittest discover -s tests -v` 通过
- [ ] 终端字体调大，方便投屏
- [ ] `runs/latest` 可被新 demo 覆盖
- [ ] 不使用真实密钥
- [ ] 不真实 git push
- [ ] 不真实访问危险 URL
