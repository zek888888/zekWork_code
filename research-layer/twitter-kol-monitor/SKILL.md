---
name: twitter-kol-monitor
description: "Twitter KOL monitor for crypto trading signals. Tracks key opinion leaders, analyzes sentiment, and extracts trading signals."
metadata:
  {
    "openclaw":
      {
        "emoji": "🐦",
        "requires": { "bins": ["python3", "curl", "jq"] },
      },
  }
---

# Twitter KOL Monitor

Twitter KOL监控 - 推文分析和交易信号提取

## When to Use

✅ **USE this skill when:**
- Monitoring crypto KOLs
- Extracting trading signals from tweets
- Analyzing market sentiment
- Tracking alpha leaks

## 监控KOL列表

- cz_binance (CZ)
- VitalikButerin (V神)
- elonmusk (马斯克)
- Pentosh1
- Ansem
- ...

## Usage Examples

### 监控推文

```bash
# 获取KOL最新推文
twitter-kol-monitor --fetch --limit 50

# 监控特定KOL
twitter-kol-monitor --user cz_binance --limit 10
```

### 情绪分析

```bash
# 分析推文情绪
twitter-kol-monitor --analyze --timeframe 1h

# 特定代币情绪
twitter-kol-monitor --analyze --token BTC
```

### 交易信号

```bash
# 提取交易信号
twitter-kol-monitor --signals --timeframe 24h

# 信号过滤
twitter-kol-monitor --signals --min-confidence 0.7
```

## 信号类型

| 类型 | 关键词 | 权重 |
|------|--------|------|
| 买入信号 | buy, long, bullish, pump | 高 |
| 卖出信号 | sell, short, bearish, dump | 高 |
| 中性 | hold, wait, neutral | 中 |

## 输出格式

```json
{
  "timestamp": "2026-03-11T01:00:00Z",
  "signals": [
    {
      "user": "cz_binance",
      "tweet_id": "...",
      "content": "...",
      "sentiment": "bullish",
      "signal": "buy",
      "target": "BTC",
      "confidence": 0.85,
      "timestamp": "2026-03-11T00:45:00Z"
    }
  ]
}
```
