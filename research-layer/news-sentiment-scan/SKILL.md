---
name: news-sentiment-scan
description: "News sentiment analysis for quant trading. Scans financial news from Jin10, Twitter KOLs, and RSS feeds. Analyzes sentiment impact on markets."
metadata:
  {
    "openclaw":
      {
        "emoji": "📰",
        "requires": { "bins": ["curl", "jq"] },
      },
  }
---

# News Sentiment Scan Skill

新闻情绪扫描技能 - 监控并分析金融市场情绪

## 功能

1. **金十数据监控** - 实时快讯抓取
2. **Twitter KOL监控** - 关注列表推文分析
3. **RSS订阅** - 财经媒体聚合
4. **情绪评分** - AI情绪分析
5. **事件标记** - 重要事件自动标记

## 数据源

| 来源 | 类型 | 更新频率 |
|------|------|----------|
| 金十数据 | 快讯 | 实时 |
| Twitter/X | KOL动态 | 5分钟 |
| RSS订阅 | 新闻 | 15分钟 |

## Usage Examples

### 扫描金十数据

```bash
# 获取最新快讯
news-sentiment-scan --source jin10 --limit 20

# 搜索特定关键词
news-sentiment-scan --source jin10 --keyword "比特币" --limit 10

# 获取带情绪评分的快讯
news-sentiment-scan --source jin10 --sentiment --limit 20
```

### 监控Twitter KOL

```bash
# 获取KOL最新推文
news-sentiment-scan --source twitter --kol-list

# 分析特定KOL
news-sentiment-scan --source twitter --username "cz_binance" --limit 10
```

### 情绪分析

```bash
# 分析市场情绪
news-sentiment-scan --sentiment-analysis --market crypto

# 生成情绪报告
news-sentiment-scan --report --output sentiment_report.json
```

## 情绪评分标准

| 分数 | 情绪 | 说明 |
|------|------|------|
| +1.0 ~ +0.6 | 极度看涨 | 重大利好 |
| +0.6 ~ +0.3 | 看涨 | 利好消息 |
| +0.3 ~ -0.3 | 中性 | 无明显影响 |
| -0.3 ~ -0.6 | 看跌 | 利空消息 |
| -0.6 ~ -1.0 | 极度看跌 | 重大利空 |

## 关键词库

### 虚拟货币
- 看涨词: 暴涨, 突破, 创新高, 利好,  adoption, 机构入场
- 看跌词: 暴跌, 崩盘, 监管, 利空, 黑客, 抛售

### 股票
- 看涨词: 财报超预期, 分红, 回购, 并购, 新产品
- 看跌词: 财报不及预期, 裁员, 诉讼, 召回, 亏损

## 输出格式

```json
{
  "timestamp": "2026-03-11T01:00:00Z",
  "source": "jin10",
  "items": [
    {
      "id": "12345",
      "title": "比特币突破7万美元",
      "content": "...",
      "sentiment_score": 0.85,
      "sentiment_label": "看涨",
      "keywords": ["比特币", "突破"],
      "impact_market": ["BTC", "ETH"],
      "published_at": "2026-03-11T00:55:00Z"
    }
  ],
  "summary": {
    "total": 20,
    "bullish": 12,
    "bearish": 3,
    "neutral": 5,
    "avg_sentiment": 0.42
  }
}
```
