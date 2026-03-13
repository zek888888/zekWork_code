---
name: factor-score-engine
description: "Multi-factor scoring engine for stock and crypto selection. Evaluates technical indicators, on-chain metrics, and market data to generate trading signals."
metadata:
  {
    "openclaw":
      {
        "emoji": "🎯",
        "requires": { "bins": ["python3", "sqlite3"] },
      },
  }
---

# Factor Score Engine

多因子评分引擎 - 选股/选币量化评分系统

## 因子分类

### 技术面因子 (Technical)

| 因子 | 说明 | 权重 |
|------|------|------|
| RSI | 相对强弱指标 | 15% |
| MACD | 趋势指标 | 15% |
| MA | 均线系统 | 10% |
| Volume | 成交量变化 | 10% |
| Bollinger | 布林带 | 10% |

### 资金面因子 (Capital Flow)

| 因子 | 说明 | 权重 |
|------|------|------|
| Net Inflow | 资金净流入 | 15% |
| Large Orders | 大单动向 | 10% |
| OI Change | 持仓量变化 | 10% |

### 情绪面因子 (Sentiment)

| 因子 | 说明 | 权重 |
|------|------|------|
| News Sentiment | 新闻情绪 | 5% |

## Usage Examples

### 单标的评分

```bash
# 对BTC进行综合评分
factor-score-engine --symbol BTCUSDT --market crypto

# 对AAPL进行综合评分
factor-score-engine --symbol AAPL --market stock
```

### 批量评分

```bash
# 对监控列表所有标的评分
factor-score-engine --watchlist

# 对指定列表评分
factor-score-engine --symbols "BTCUSDT,ETHUSDT,SOLUSDT"
```

### 筛选标的

```bash
# 筛选评分大于70的标的
factor-score-engine --filter --min-score 70

# 按市场筛选
factor-score-engine --filter --market crypto --min-score 60 --limit 10
```

## 评分标准

| 总分 | 评级 | 建议 |
|------|------|------|
| 90-100 | S | 强烈买入 |
| 80-89 | A | 买入 |
| 70-79 | B | 观望/轻仓 |
| 60-69 | C | 观望 |
| <60 | D | 回避 |

## 输出格式

```json
{
  "symbol": "BTCUSDT",
  "timestamp": "2026-03-11T01:00:00Z",
  "total_score": 78.5,
  "rating": "B",
  "factors": {
    "technical": {
      "score": 82,
      "rsi": 65,
      "macd": "bullish",
      "ma_trend": "up"
    },
    "capital_flow": {
      "score": 75,
      "net_inflow": 1500000,
      "large_order_ratio": 0.65
    },
    "sentiment": {
      "score": 70,
      "news_sentiment": 0.42
    }
  },
  "signal": "观望/轻仓",
  "confidence": 0.75
}
```
