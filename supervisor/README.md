# 🎖️ 隔壁老王 (Task Supervisor)

与 Openclaw 集成的全链路任务监控平台，自动发现漏执行的定时任务，及时告警并修复。

---

## ✨ 核心功能

### 1. 心跳监控 (Heartbeat Monitor)
- 实时检测所有定时任务是否按时执行
- 基于 Cron 表达式计算预期执行时间
- 5分钟宽限期后自动标记为"漏执行"

### 2. 自动修复 (Auto Repair)
- **路径错误**: 自动转换为绝对路径
- **权限错误**: 自动修复文件权限
- **超时错误**: 延迟重试
- **未知错误**: 通知人工介入

### 3. 飞书告警 (Feishu Alerts)
- 漏执行立即告警（关键任务）
- 失败任务汇总告警
- 每日执行报告（早8点）
- 需要人工修复时@负责人

### 4. 修复指挥室 (Command Room)
- Web 界面查看所有任务状态
- 一键查看修复选项
- 手动执行修复命令
- 修复历史记录

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Task Supervisor                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Registry  │  │  Heartbeat  │  │   Repair Engine     │ │
│  │  任务注册表  │  │   心跳监控   │  │     修复引擎         │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                    │            │
│         └────────────────┼────────────────────┘            │
│                          ▼                                 │
│                   ┌─────────────┐                          │
│                   │  Scheduler  │                          │
│                   │  中央调度器  │                          │
│                   └──────┬──────┘                          │
│                          │                                 │
│         ┌────────────────┼────────────────┐               │
│         ▼                ▼                ▼               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Alert     │  │    Web      │  │   Openclaw  │       │
│  │  飞书告警    │  │  Dashboard  │  │ Integration │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 安装

```bash
cd ~/.openclaw/workspace/quant-trading
python3 supervisor/install.py
```

### 2. 配置飞书 Webhook

编辑 `config.yaml`:
```yaml
feishu_webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
```

### 3. 启动监工系统

```bash
# 启动后台监控
./start_supervisor.sh

# 启动Web控制台 (另一个终端)
./start_supervisor_web.sh
```

### 4. 访问控制台

打开浏览器: http://localhost:5001/supervisor

---

## 📊 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 漏执行 | 未在预期时间执行的任务 | 立即告警 |
| 执行失败 | 返回非0退出码 | 立即告警 |
| 执行超时 | 超过设置的超时时间 | 立即告警 |
| 成功率 | 成功执行/计划执行 | <80%告警 |

---

## 🔧 修复策略

### 自动修复场景

| 错误类型 | 自动修复动作 | 成功率 |
|----------|-------------|--------|
| `getcwd` 错误 | 使用绝对路径执行 | 95% |
| `Permission denied` | chmod +x 后重试 | 90% |
| `Timeout` | 30秒后延迟重试 | 70% |
| `Connection refused` | 延迟重试 | 60% |

### 需人工介入场景

- 代码语法错误 (SyntaxError)
- 依赖缺失 (ModuleNotFoundError)
- 自动修复3次仍失败

---

## 📝 任务注册

### 新增监控任务

```python
from supervisor.core.registry import TaskRegistry, TaskDefinition

registry = TaskRegistry()

task = TaskDefinition(
    task_id="my_task",                    # 唯一ID
    name="我的任务",                       # 显示名称
    type="cron",                          # 类型: cron/interval/once
    schedule="0 */6 * * *",               # Cron表达式
    command="python3 /path/to/script.py", # 执行命令
    working_dir="/path/to/workdir",       # 工作目录
    timeout_seconds=300,                  # 超时时间
    retries=3,                            # 重试次数
    critical=True,                        # 是否关键任务
    owner="your-name",                    # 负责人
    description="任务描述"                 # 描述
)

registry.register_task(task)
```

---

## 🔔 告警消息格式

### 漏执行告警
```
🚨 任务漏执行 - 神算子（AI预测）
━━━━━━━━━━━━━━━━━━━━━
任务: 神算子（AI预测）
计划时间: 2024-03-17 14:29:00
原因: 未检测到执行记录
级别: 🔴 关键任务
```

### 每日报告
```
📊 任务执行日报 (2024-03-17)
━━━━━━━━━━━━━━━━━━━━━
总执行: 96 | 成功: 94 | 失败: 2 | 超时: 0
成功率: 97.9%
```

### 修复请求
```
🔧 需要人工修复 - 神算子（AI预测）
━━━━━━━━━━━━━━━━━━━━━
任务: 神算子（AI预测）
执行ID: prediction_agent_20240317142900
失败时间: 2024-03-17 14:30:15
错误: ModuleNotFoundError: No module named 'requests'

可选修复方案:
1. 立即重试
2. 人工修复

回复: supervisor repair <execution_id> <option>
```

---

## 📁 项目结构

```
supervisor/
├── core/
│   ├── registry.py          # 任务注册表
│   ├── heartbeat.py         # 心跳监控
│   ├── scheduler.py         # 中央调度器
│   └── reporter.py          # 报告生成
├── alerts/
│   └── feishu_notifier.py   # 飞书通知
├── commands/
│   └── repair_engine.py     # 修复引擎
├── web/
│   ├── app.py               # Web服务
│   └── templates/
│       └── supervisor.html  # 控制台页面
├── install.py               # 安装脚本
└── README.md                # 本文档
```

---

## 🔄 与 Prediction Agent 集成

监工系统已预配置监控以下任务:

| 任务ID | 名称 | 计划 | 关键 |
|--------|------|------|------|
| shen_suan_zi | 神算子（AI预测） | 每15分钟 | ✅ |
| shen_suan_zi_verify | 神算子验算 | 每2小时 | ⚪ |

当 Prediction Agent 漏执行时:
1. 监工系统 5分钟内检测到
2. 发送飞书告警
3. 尝试自动修复（路径/权限问题）
4. 修复失败则通知人工介入

---

## 🛠️ 故障排查

### 查看日志
```bash
# 监工系统日志
tail -f logs/supervisor.log

# 任务执行日志
tail -f logs/神算子.log
```

### 检查状态
```bash
# 查看进程
ps aux | grep supervisor

# 检查数据库
sqlite3 data/supervisor.db "SELECT * FROM task_executions ORDER BY created_at DESC LIMIT 10;"
```

### 手动修复任务
```bash
# 进入Python交互模式
python3

from supervisor.commands.repair_engine import RepairEngine
engine = RepairEngine()

# 查看修复选项
options = engine.get_repair_options({'execution_id': 'xxx', ...})

# 执行修复
result = engine.manual_repair('execution_id', '修复命令')
```

---

## 📝 License

MIT License - Quant Trading System v1.0
