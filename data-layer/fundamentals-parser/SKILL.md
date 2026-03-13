---
name: fundamentals-parser
description: "Fundamental data parser for stocks and cryptocurrencies. Analyzes financial statements, on-chain metrics, and project fundamentals."
metadata:
  {
    "openclaw":
      {
        "emoji": "📊",
        "requires": { "bins": ["python3", "curl", "jq"] },
      },
  }
---

# Fundamentals Parser

基本面分析技能 - 股票和虚拟货币基本面数据解析

## When to Use

✅ **USE this skill when:**
- Analyzing stock financial statements
- Evaluating crypto project fundamentals
- Parsing on-chain metrics
- Researching company/ project background

## 支持的数据类型

### 股票基本面
- 财务报表 (营收、利润、现金流)
- 估值指标 (PE、PB、PS)
- 股东结构
- 行业对比

### 虚拟货币基本面
- 链上数据 (活跃地址、交易量)
- 代币经济学 (流通量、通胀率)
- 项目背景 (团队、融资、路线图)
- 生态指标 (TVL、DApp数量)

## Usage Examples

### 股票基本面

```bash
# 获取股票基本面数据
fundamentals-parser --symbol AAPL --type stock

# 获取财务报表
fundamentals-parser --symbol TSLA --report financial

# 对比分析
fundamentals-parser --compare AAPL,MSFT,GOOGL --metric pe_ratio
```

### 虚拟货币基本面

```bash
# 获取代币基本面
fundamentals-parser --symbol BTC --type crypto

# 链上数据分析
fundamentals-parser --symbol ETH --metric onchain

# 项目背景研究
fundamentals-parser --symbol SOL --research project
```

## 数据源

- Yahoo Finance (股票)
- CoinGecko (虚拟货币)
- DeFiLlama (DeFi数据)
- Token Terminal (链上数据)

## 输出格式

```json
{
  "symbol": "AAPL",
  "type": "stock",
  "timestamp": "2026-03-11T01:00:00Z",
  "fundamentals": {
    "valuation": {
      "pe_ratio": 28.5,
      "pb_ratio": 45.2,
      "market_cap": 2800000000000
    },
    "financials": {
      "revenue": 380000000000,
      "profit": 97000000000,
      "cash_flow": 110000000000
    },
    "growth": {
      "revenue_growth": 0.08,
      "profit_growth": 0.12
    }
  },
  "score": 75,
  "rating": "B"
}
```
