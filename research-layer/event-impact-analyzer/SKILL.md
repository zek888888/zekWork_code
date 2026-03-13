---
name: event-impact-analyzer
description: "Event impact analyzer for financial markets. Tracks and analyzes the impact of news events, economic data, and market-moving announcements."
metadata:
  {
    "openclaw":
      {
        "emoji": "⚡",
        "requires": { "bins": ["python3"] },
      },
  }
---

# Event Impact Analyzer

事件冲击分析技能 - 追踪和分析金融市场事件影响

## When to Use

✅ **USE this skill when:**
- Tracking major news events
- Analyzing market reactions to events
- Predicting price impact of announcements
- Building event-driven trading strategies

## 事件类型

### 宏观经济事件
- 利率决议 (FED, ECB, PBOC)
- 通胀数据 (CPI, PPI)
- 就业数据 (非农就业, 失业率)
- GDP数据

### 行业/公司事件
- 财报发布
- 并购消息
- 产品发布
- 监管政策

### 加密货币事件
- 代币解锁
- 协议升级
- 交易所上市/下架
- 监管新闻

## Usage Examples

### 监控事件

```bash
# 获取今日重要事件
event-impact-analyzer --today

# 监控特定事件类型
event-impact-analyzer --type fed_rate --impact high

# 查看历史事件影响
event-impact-analyzer --history --symbol BTC --days 30
```

### 分析事件影响

```bash
# 分析特定事件的市场反应
event-impact-analyzer --event "FOMC Meeting" --analyze

# 预测事件影响
event-impact-analyzer --event "CPI Release" --predict --symbol BTC
```

### 事件日历

```bash
# 查看本周事件日历
event-impact-analyzer --calendar --week

# 设置事件提醒
event-impact-analyzer --alert --event "Fed Meeting" --before 1h
```

## 影响评分

| 等级 | 分数 | 说明 |
|------|------|------|
| 极高 | 90-100 | 市场剧烈波动，>5%价格变动 |
| 高 | 70-89 | 明显波动，2-5%价格变动 |
| 中 | 40-69 | 一定影响，1-2%价格变动 |
| 低 | 10-39 | 轻微影响，<1%价格变动 |
| 无 | 0-9 | 几乎无影响 |

## 输出格式

```json
{
  "event": {
    "name": "FOMC Interest Rate Decision",
    "type": "macro",
    "datetime": "2026-03-11T14:00:00Z",
    "expected": "5.50%",
    "actual": "5.25%"
  },
  "impact": {
    "score": 85,
    "level": "高",
    "affected_assets": ["BTC", "ETH", "SPY", "QQQ"],
    "price_changes": {
      "BTC": 0.035,
      "ETH": 0.042,
      "SPY": -0.012
    }
  },
  "analysis": {
    "market_sentiment": "risk_on",
    "duration": "short_term",
    "recommendation": "考虑减仓避险资产"
  }
}
```
