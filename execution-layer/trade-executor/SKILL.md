---
name: trade-executor
description: "Trade execution engine for crypto trading. Supports both paper trading simulation and real trading via exchange APIs."
metadata:
  {
    "openclaw":
      {
        "emoji": "⚡",
        "requires": { "bins": ["python3", "curl"] },
      },
  }
---

# Trade Executor

交易执行引擎 - 模拟交易和真实交易执行

## When to Use

✅ **USE this skill when:**
- Executing buy/sell orders
- Managing positions
- Paper trading simulation
- Real trading via APIs

## 功能

1. **模拟交易** - 虚拟资金练习
2. **真实交易** - 币安API接入
3. **订单管理** - 下单/撤单/查询
4. **持仓管理** - 仓位追踪
5. **风险控制** - 止损止盈

## Usage Examples

### 模拟交易

```bash
# 模拟买入
trade-executor --paper --buy BTCUSDT --amount 1000

# 模拟卖出
trade-executor --paper --sell BTCUSDT --amount 0.5

# 查看模拟持仓
trade-executor --paper --positions
```

### 真实交易

```bash
# 买入 (需要API Key)
trade-executor --buy BTCUSDT --amount 1000 --type market

# 限价单
trade-executor --buy BTCUSDT --amount 1000 --price 70000 --type limit

# 设置止损
trade-executor --stop-loss BTCUSDT --price 65000
```

### 订单管理

```bash
# 查看订单
trade-executor --orders --status open

# 撤单
trade-executor --cancel <order_id>

# 交易历史
trade-executor --history --limit 20
```

## 配置

```bash
# 设置币安API Key
export BINANCE_API_KEY="your-api-key"
export BINANCE_SECRET_KEY="your-secret-key"

# 测试网模式
export BINANCE_TESTNET=true
```

## 输出格式

```json
{
  "order": {
    "id": "123456",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "MARKET",
    "amount": 1000,
    "price": 71234.56,
    "status": "FILLED",
    "timestamp": "2026-03-11T01:00:00Z"
  },
  "position": {
    "symbol": "BTCUSDT",
    "quantity": 0.014,
    "avg_price": 71234.56,
    "unrealized_pnl": 0
  }
}
```
