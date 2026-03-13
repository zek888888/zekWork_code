---
name: risk-guardrail
description: "Risk management and guardrail system for quant trading. Controls position sizing, stop-loss, take-profit, and portfolio risk limits."
metadata:
  {
    "openclaw":
      {
        "emoji": "🛡️",
        "requires": { "bins": ["python3"] },
      },
  }
---

# Risk Guardrail

风控护栏系统 - 量化交易风险管理

## 风控规则

### 仓位管理

| 规则 | 说明 | 默认值 |
|------|------|--------|
| 单标的上限 | 单个标的最大仓位 | 20% |
| 板块上限 | 单个板块最大仓位 | 40% |
| 总仓位上限 | 最大总仓位 | 80% |
| 单笔下限 | 最小交易金额 | $100 |

### 止损止盈

| 规则 | 说明 | 默认值 |
|------|------|--------|
| 止损比例 | 亏损达到即止损 | -5% |
| 止盈比例 | 盈利达到即止盈 | +15% |
| 移动止损 | 盈利后跟踪止损 | -3% |
| 时间止损 | 持仓超期强制平仓 | 7天 |

### 风险限额

| 规则 | 说明 | 默认值 |
|------|------|--------|
| 日最大亏损 | 单日最大亏损限额 | -3% |
| 周最大亏损 | 单周最大亏损限额 | -10% |
| 月最大亏损 | 单月最大亏损限额 | -20% |
| 最大回撤 | 账户最大回撤限额 | -30% |

## Usage Examples

### 检查交易合规性

```bash
# 检查是否可以买入
risk-guardrail --check-buy --symbol BTCUSDT --amount 1000

# 检查仓位限制
risk-guardrail --check-position --symbol ETHUSDT --position 0.5
```

### 计算建议仓位

```bash
# 根据风险评分计算建议仓位
risk-guardrail --calc-position --symbol BTCUSDT --risk-score 75

# 计算组合仓位
risk-guardrail --calc-portfolio --symbols "BTCUSDT:0.3,ETHUSDT:0.2"
```

### 监控风险状态

```bash
# 查看当前风险状态
risk-guardrail --status

# 检查是否需要止损
risk-guardrail --check-stoploss
```

## 风险等级

| 等级 | 分数 | 说明 | 建议仓位 |
|------|------|------|----------|
| 低风险 | 0-30 | 市场稳定 | 70-80% |
| 中低风险 | 30-50 | 轻微波动 | 50-70% |
| 中风险 | 50-70 | 明显波动 | 30-50% |
| 高风险 | 70-85 | 剧烈波动 | 10-30% |
| 极高风险 | 85-100 | 极端行情 | 0-10% |

## 输出格式

```json
{
  "timestamp": "2026-03-11T01:00:00Z",
  "account_status": {
    "total_equity": 100000,
    "available": 30000,
    "used_margin": 70000,
    "margin_ratio": 0.7
  },
  "risk_metrics": {
    "daily_pnl": -0.015,
    "weekly_pnl": 0.032,
    "max_drawdown": 0.08,
    "risk_level": "中风险",
    "risk_score": 55
  },
  "checks": {
    "can_trade": true,
    "position_limit_ok": true,
    "stoploss_triggered": [],
    "warnings": ["BTCUSDT 接近止损线 -4.2%"]
  }
}
```
