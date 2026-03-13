---
name: market-data-fetch
description: "Quant trading market data fetcher. Fetches real-time and historical price data for stocks (US/HK/CN) and cryptocurrencies (BTC/ETH/SOL). Stores data locally for analysis."
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
        "requires": { "bins": ["curl", "jq", "python3"] },
      },
  }
---

# Market Data Fetch Skill

行情数据抓取技能 - 支持股票和虚拟货币

## 支持的市场

| 市场 | 代码示例 | 数据源 |
|------|----------|--------|
| 美股 | AAPL, TSLA, NVDA | Yahoo Finance |
| 港股 | 0700.HK, 3690.HK | Yahoo Finance |
| A股 | 000001.SZ, 600000.SS | Yahoo Finance |
| BTC | BTCUSDT | Binance |
| ETH | ETHUSDT | Binance |
| SOL | SOLUSDT | Binance |

## 数据存储

本地 SQLite 数据库: `~/.openclaw/workspace/quant-trading/data/market_data.db`

表结构:
- `price_data` - 价格数据 (OHLCV)
- `symbols` - 交易对/股票列表
- `data_sources` - 数据源配置

## Usage Examples

### 获取实时价格

```bash
# 获取 BTC 实时价格
market-data-fetch --symbol BTCUSDT --market crypto --type realtime

# 获取 AAPL 实时价格
market-data-fetch --symbol AAPL --market stock --type realtime

# 获取多个币种
market-data-fetch --symbols "BTCUSDT,ETHUSDT,SOLUSDT" --market crypto
```

### 获取历史K线

```bash
# 获取 BTC 1小时K线，最近100根
market-data-fetch --symbol BTCUSDT --market crypto --interval 1h --limit 100

# 获取 AAPL 日线，最近30天
market-data-fetch --symbol AAPL --market stock --interval 1d --limit 30
```

### 批量获取

```bash
# 获取监控列表中的所有数据
market-data-fetch --watchlist --market crypto
```

## API 数据源

### Binance (虚拟货币)
- 实时价格: `https://api.binance.com/api/v3/ticker/price`
- K线数据: `https://api.binance.com/api/v3/klines`
- 24h统计: `https://api.binance.com/api/v3/ticker/24hr`

### Yahoo Finance (股票)
- 实时价格: `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}`

## 配置

配置文件: `~/.openclaw/workspace/quant-trading/config/market-data.yaml`

```yaml
sources:
  binance:
    base_url: "https://api.binance.com"
    rate_limit: 1200  # requests per minute
  yahoo:
    base_url: "https://query1.finance.yahoo.com"
    
watchlist:
  crypto:
    - BTCUSDT
    - ETHUSDT
    - SOLUSDT
  stocks:
    - AAPL
    - TSLA
    - NVDA
```

## 输出格式

### 实时价格 (JSON)

```json
{
  "symbol": "BTCUSDT",
  "price": 67234.56,
  "timestamp": "2026-03-11T00:54:00Z",
  "source": "binance",
  "change_24h": 2.34,
  "volume_24h": 1523456789
}
```

### K线数据 (JSON)

```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "data": [
    {
      "timestamp": "2026-03-11T00:00:00Z",
      "open": 67000.00,
      "high": 67300.00,
      "low": 66800.00,
      "close": 67234.56,
      "volume": 1234567
    }
  ]
}
```
