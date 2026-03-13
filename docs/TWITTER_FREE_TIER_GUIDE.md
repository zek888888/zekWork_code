# Twitter API 免费额度使用指南

## 📊 当前额度状态

| 项目 | 值 | 说明 |
|------|---|------|
| 当前额度 | 已用完 | Essential层级限制 |
| 次月额度 | 1,500条 | 每月1号重置 |
| 下次重置 | 2026-04-01 | 约18天后 |
| 当前状态 | 使用演示数据 | 功能正常展示 |

## 🔄 自动监控机制

### 1. 定时任务设置

添加以下cron任务，每小时检查一次额度状态：

```bash
# 编辑crontab
crontab -e

# 添加以下行（每小时执行一次监控）
0 * * * * cd ~/.openclaw/workspace/quant-trading && python3 cron/twitter_free_tier_monitor.py >> logs/twitter_monitor.log 2>&1

# 或每天执行一次（推荐）
0 0 * * * cd ~/.openclaw/workspace/quant-trading && python3 cron/twitter_free_tier_monitor.py >> logs/twitter_monitor.log 2>&1
```

### 2. 监控脚本功能

**`cron/twitter_free_tier_monitor.py`** 会自动：

1. 检查Twitter API剩余额度
2. 如果有额度，获取真实推文数据
3. 如果额度用完，记录日志并等待
4. 次月1号自动切换回真实数据

### 3. 手动检查额度

```bash
cd ~/.openclaw/workspace/quant-trading
python3 cron/twitter_free_tier_monitor.py
```

## 📅 额度重置时间表

| 重置日期 | 额度 | 状态 |
|---------|------|------|
| 每月1号 00:00 UTC | 1,500条 | 自动恢复 |

**注意：**
- 重置时间是UTC时间（北京时间上午8点）
- 不需要手动操作，系统会自动检测

## 💡 使用建议

### 短期（当前-次月1号）
- ✅ 使用演示数据展示功能
- ✅ 配置观察人列表
- ✅ 测试AI分析功能

### 中期（次月1号后）
- ✅ 自动获取真实数据（1,500条/月）
- ✅ 约可监控 6人 × 每天8条 = 1,440条/月
- ✅ 满足基础监控需求

### 长期（如需求增加）
- 💰 订阅Basic ($100/月) - 10,000条/月
- 💰 订阅Pro ($5000/月) - 1,000,000条/月
- 🔌 接入第三方数据服务

## 🔍 额度查询命令

```bash
# 查看当前额度状态
cd ~/.openclaw/workspace/quant-trading
python3 -c "
from datetime import datetime
today = datetime.now()
reset_day = 1
if today.day >= reset_day:
    if today.month == 12:
        next_reset = datetime(today.year + 1, 1, reset_day)
    else:
        next_reset = datetime(today.year, today.month + 1, reset_day)
else:
    next_reset = datetime(today.year, today.month, reset_day)
days = (next_reset - today).days + 1
print(f'下次重置: {next_reset.strftime(\"%Y-%m-%d\")} ({days}天后)')
print(f'次月额度: 1,500条')
"
```

## 📝 日志查看

```bash
# 查看监控日志
tail -f ~/.openclaw/workspace/quant-trading/logs/twitter_monitor.log

# 查看额度历史
cd ~/.openclaw/workspace/quant-trading
sqlite3 data-layer/market_data.db "SELECT * FROM twitter_api_quota_log ORDER BY check_time DESC LIMIT 10;"
```

## ⚠️ 注意事项

1. **免费额度**仅限 Essential 访问级别
2. **重置时间**为UTC时间每月1号
3. **系统会自动检测**，无需手动切换
4. **演示数据**会一直保留用于展示

---

**现在只需等待次月1号，系统会自动切换到真实数据！**
