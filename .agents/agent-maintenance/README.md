# Agent-maintenance: GitHub 自动同步

## 📝 功能说明

每天上海时间凌晨6:00自动执行GitHub同步：
- 检查本地更改
- 自动提交并推送
- 记录执行日志

## ⏰ 定时配置

| 项目 | 值 |
|------|---|
| 执行时间 | 每天凌晨 6:00 (上海时间 CST) |
| Cron表达式 | `0 6 * * *` |
| 时区 | CST (China Standard Time, UTC+8) |

## 🛠️ 手动执行

```bash
# 执行同步
python3 .agents/agent-maintenance/maintenance.py

# 查看日志
tail -f .agents/agent-maintenance/maintenance.log
```

## 📊 执行状态

### 查看定时任务
```bash
crontab -l | grep agent-maintenance
```

### 查看最近日志
```bash
tail -20 .agents/agent-maintenance/maintenance.log
```

## 🔧 故障排除

### 任务未执行
1. 检查cron服务: `ps aux | grep cron`
2. 检查日志权限: `ls -la .agents/agent-maintenance/`
3. 手动测试: `python3 .agents/agent-maintenance/maintenance.py`

### 推送失败
1. 检查网络连接
2. 检查Git凭证: `git remote -v`
3. 查看详细日志

## 📁 文件结构

```
.agents/agent-maintenance/
├── maintenance.py      # 主脚本
├── maintenance.log     # 执行日志
└── README.md          # 说明文档
```

## 🔄 修改定时时间

```bash
# 编辑crontab
crontab -e

# 修改时间 (例如改为每天8:00)
0 8 * * * cd /Users/mac/.openclaw/workspace/quant-trading && python3 .agents/agent-maintenance/maintenance.py >> .agents/agent-maintenance/maintenance.log 2>&1
```

## ✅ 验证状态

- [x] 测试执行成功
- [x] 定时任务已配置
- [x] 日志系统正常
- [x] GitHub推送成功

---

**最后更新**: 2026-03-14
**状态**: ✅ 运行中
