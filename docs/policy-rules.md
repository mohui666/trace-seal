# TraceSeal Policy 规则设计

## 文档状态

本文是下一阶段 `policy.yaml` DSL 的设计草案，不代表当前 MVP 已全部实现。

当前仓库实际使用的策略文件是 `policy/default_policy.json`，已落地规则包括：

- `dangerous_delete`：标记/阻断 `rm -rf`、`rmdir /s /q` 等递归强制删除。
- `env_write`：标记写入 `.env` / `.env.*`。
- `git_push`：标记 `git push`。

当前默认是 warn/mark 模式；设置 `TRACESEAL_POLICY_MODE=block` 后可阻断高危规则。


## 1. 设计原则

- **默认拒绝**：未明确允许的操作视为风险
- **分级管控**：allow / warn / deny / require_approval
- **最小权限**：只授予 Agent 完成任务所需的最小权限
- **可扩展**：规则格式支持后续扩展新的操作类型和条件

## 2. 规则格式

### 2.1 文件结构

```yaml
# policy.yaml
version: "1.0"
description: "TraceSeal 安全策略配置"

# 默认策略
default_action: deny

# 全局规则（按优先级排序，先匹配的先执行）
global_rules:
  - name: "禁止删除关键目录"
    action: deny
    operations:
      - type: shell
        patterns:
          - "rm -rf /*"
          - "rm -rf /"
          - "rm -rf ~/*"
    description: "禁止删除系统根目录或用户主目录"

  - name: "禁止访问敏感文件"
    action: deny
    operations:
      - type: file_read
        paths:
          - ".env"
          - ".env.*"
          - "*.pem"
          - "*.key"
          - "id_rsa"
          - "id_rsa.pub"
          - "config.json"  # 包含敏感配置的文件
    description: "禁止读取包含敏感信息的文件"

  - name: "禁止修改敏感文件"
    action: deny
    operations:
      - type: file_write
        paths:
          - ".env"
          - "*.pem"
          - "*.key"
          - "id_rsa"
          - "id_rsa.pub"
    description: "禁止修改密钥和敏感配置文件"

  - name: "禁止执行危险命令"
    action: deny
    operations:
      - type: shell
        patterns:
          - "*:(){ :|:& };:*"  # fork bomb
          - "dd if=*"
          - "mkfs.*"
          - "fdisk*"
          - "format*"
    description: "禁止执行系统破坏性命令"

  - name: "禁止访问外部网络"
    action: deny
    operations:
      - type: http
        url_patterns:
          - "*://*.*"
    description: "禁止所有外部 HTTP 请求"
    condition:
      env:
        - name: "TRACESEAL_ALLOW_EXTERNAL_HTTP"
          value: "false"

  - name: "Git 危险操作需要审批"
    action: require_approval
    operations:
      - type: git
        commands:
          - "push --force"
          - "push -f"
          - "reset --hard"
          - "clean -fd"
          - "branch -D"
          - "branch -d"
    description: "Git 强制推送、硬重置等操作需要人工确认"

  - name: "警告：删除操作"
    action: warn
    operations:
      - type: shell
        patterns:
          - "rm *"
          - "rmdir *"
          - "del *"
    description: "删除文件/目录时发出警告"

  - name: "允许项目目录内的文件操作"
    action: allow
    operations:
      - type: file_read
        paths:
          - "src/**"
          - "tests/**"
          - "docs/**"
          - "*.py"
          - "*.md"
          - "*.json"
          - "*.yaml"
          - "*.yml"
          - "*.txt"
      - type: file_write
        paths:
          - "src/**"
          - "tests/**"
          - "docs/**"
          - "*.py"
          - "*.md"
          - "*.json"
          - "*.yaml"
          - "*.yml"
          - "*.txt"
    description: "允许在项目目录内进行常规文件读写"

  - name: "允许运行测试命令"
    action: allow
    operations:
      - type: shell
        patterns:
          - "pytest*"
          - "python -m pytest*"
          - "python -m unittest*"
          - "python test_*.py"
    description: "允许运行测试相关命令"

  - name: "允许常规 Git 操作"
    action: allow
    operations:
      - type: git
        commands:
          - "status"
          - "log"
          - "diff"
          - "add"
          - "commit"
          - "pull"
          - "fetch"
          - "clone"
    description: "允许常规 Git 查询和提交操作"

  - name: "允许访问白名单域名"
    action: allow
    operations:
      - type: http
        url_patterns:
          - "https://api.github.com/*"
          - "https://pypi.org/*"
          - "https://registry.npmjs.org/*"
    description: "允许访问开发常用的 API"

# 环境特定规则
environments:
  production:
    default_action: deny
    rules:
      - name: "生产环境禁止写入"
        action: deny
        operations:
          - type: file_write
            paths:
              - "**/*"
        description: "生产环境禁止任何文件写入"

  development:
    default_action: warn
    rules:
      - name: "开发环境允许更多操作"
        action: allow
        operations:
          - type: shell
            patterns:
              - "pip install*"
              - "npm install*"
              - "cargo build*"
        description: "开发环境允许安装依赖"
```

## 3. 规则字段说明

### 3.1 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| version | string | 是 | 策略版本号 |
| description | string | 否 | 策略描述 |
| default_action | string | 是 | 默认策略：allow / warn / deny / require_approval |
| global_rules | array | 是 | 全局规则列表 |
| environments | object | 否 | 环境特定规则 |

### 3.2 规则字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 规则名称 |
| action | string | 是 | 动作：allow / warn / deny / require_approval |
| operations | array | 是 | 操作匹配条件 |
| description | string | 否 | 规则描述 |
| condition | object | 否 | 附加条件 |

### 3.3 操作类型

| 类型 | 说明 | 匹配字段 |
|------|------|----------|
| file_read | 文件读取 | paths: 文件路径模式 |
| file_write | 文件写入 | paths: 文件路径模式 |
| shell | Shell 命令 | patterns: 命令模式 |
| http | HTTP 请求 | url_patterns: URL 模式 |
| git | Git 操作 | commands: Git 子命令 |

### 3.4 动作说明

| 动作 | 说明 | 行为 |
|------|------|------|
| allow | 允许 | 直接执行，不记录风险 |
| warn | 警告 | 执行但记录警告，可在 Dashboard 查看 |
| deny | 拒绝 | 阻止执行，抛出异常 |
| require_approval | 需要审批 | 暂停执行，等待用户确认 |

### 3.5 匹配模式

支持 glob 模式匹配：

- `*` - 匹配任意字符（不含 `/`）
- `**` - 匹配任意路径
- `?` - 匹配单个字符
- `[abc]` - 匹配括号内的任意字符

## 4. 规则优先级

1. 规则按数组顺序匹配，**第一个匹配的规则生效**
2. 环境规则优先于全局规则
3. 未匹配任何规则时，使用 `default_action`

## 5. 危险操作清单

### 5.1 高危操作（目标 DSL 默认 deny；当前 MVP 以 `default_policy.json` 为准）

| 类别 | 操作 | 风险 |
|------|------|------|
| 文件系统 | `rm -rf /` | 删除整个系统 |
| 文件系统 | `rm -rf ~/*` | 删除用户所有文件 |
| 文件系统 | 写入 `.env`, `*.pem` | 泄露或破坏敏感信息 |
| Shell | `dd if=/dev/zero of=/dev/sda` | 破坏磁盘 |
| Shell | `mkfs.ext4 /dev/sda1` | 格式化分区 |
| Shell | `:(){ :|:& };:` | fork bomb |
| Git | `git push --force` | 覆盖远程历史 |
| Git | `git reset --hard` | 丢失未提交更改 |
| HTTP | 访问未授权的外部 API | 数据泄露 |

### 5.2 中危操作（目标 DSL 默认 warn）

| 类别 | 操作 | 风险 |
|------|------|------|
| 文件系统 | `rm file.txt` | 误删文件 |
| 文件系统 | `rmdir dir/` | 误删目录 |
| Shell | `pip install unknown-package` | 安装恶意包 |
| Git | `git clean -fd` | 删除未跟踪文件 |
| HTTP | 访问非白名单域名 | 潜在安全风险 |

### 5.3 低危操作（目标 DSL 默认 allow）

| 类别 | 操作 | 说明 |
|------|------|------|
| 文件系统 | 读取 `src/**` | 正常开发操作 |
| 文件系统 | 写入 `*.py`, `*.md` | 正常开发操作 |
| Shell | `pytest` | 运行测试 |
| Shell | `python script.py` | 运行脚本 |
| Git | `git status` | 查询状态 |
| Git | `git add`, `git commit` | 常规提交 |
| HTTP | 访问 `api.github.com` | 常用开发 API |
