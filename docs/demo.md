# TraceSeal 5 分钟演示脚本

> 适合答辩、项目展示、Demo Day。  
> 推荐命令统一使用 `python -m traceseal ...`，避免未安装 console script 时失败。

## 0. 演示前准备

```powershell
cd C:\Users\mohui666\Documents\projectA\trace-seal
python -m unittest discover -s tests -v
```

确认测试通过后开始演示。

---

## 1. 开场：问题引入（30 秒）

AI Agent 写代码越来越强，但它也会犯错。它可能误删目录、改坏 `.env`、执行 `git push`、或者把敏感数据 POST 到外部服务。

问题是：事故发生后，我们往往不知道 Agent 到底做了哪些副作用操作，也不知道第一步有害操作是哪一次。

TraceSeal 要做的就是给 AI Agent 加上黑匣子、安全防火墙和失败回放。

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
[evt_0003] shell: rm -rf data/

建议策略:
deny shell "rm -rf data/**"
```

---

## 3. 演示 .env 风险（45 秒）

```powershell
python -m traceseal run python examples/bad_agent_env.py
python -m traceseal explain runs/latest
```

讲解点：

- Agent 写入 `.env`，内容类似 `OPENAI_API_KEY=sk-demo-secret` 和 `DATABASE_URL=postgres://demo:demo@localhost/demo`。
- TraceSeal 记录 `file.write`。
- 命中 `env_write`。
- 如果开启 block 模式，写入前会被阻断。

---

## 4. 演示 Git push 风险（45 秒）

```powershell
python -m traceseal run python examples/bad_agent_git.py
python -m traceseal explain runs/latest
```

讲解点：

- Agent 尝试执行 `git push origin main`。
- SDK 离线模拟，不真实推送远端。
- 事件仍被记录为 shell 风险。
- 命中 `git_push`。

---

## 5. 演示 HTTP POST 风险（45 秒）

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

## 6. 展示 Dashboard 数据接口（45 秒）

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

## 7. 结尾（30 秒）

TraceSeal 当前已经具备：

1. 可记录：记录文件写入、Shell、Git push、HTTP POST 等核心副作用。
2. 可回放：replay 重建事件时间线。
3. 可定位：explain 找出 首次有害工具调用。
4. 可阻断：block 模式阻断高危行为。
5. 可展示：dashboard-data JSON 可供 Electron 原型读取。

下一步是把这个 JSON 接到最小 Electron Dashboard。
