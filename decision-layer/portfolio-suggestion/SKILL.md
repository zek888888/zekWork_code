---
name: portfolio-suggestion
description: "Portfolio suggestion and optimization engine. Provides asset allocation recommendations based on risk profile, market conditions, and factor scores."
metadata:
  {
    "openclaw":
      {
        "emoji": "💼",
        "requires": { "bins": ["python3"] },
      },
  }
---

# Portfolio Suggestion

投资组合建议技能 - 资产配置优化引擎

## When to Use

✅ **USE this skill when:**
- Building investment portfolios
- Optimizing asset allocation
- Rebalancing positions
- Managing risk exposure

## 功能

1. **资产配置建议** - 基于风险偏好的配置方案
2. **组合优化** - 马科维茨均值-方差优化
3. **再平衡建议** - 定期调整建议
4. **风险分析** - 组合风险度量

## Usage Examples

### 获取配置建议

```bash
# 基于风险偏好的配置
portfolio-suggestion --risk medium --capital 100000

# 特定市场配置
portfolio-suggestion --market crypto --risk high --capital 50000

# 多资产配置
portfolio-suggestion --assets "BTC,ETH,AAPL,TSLA" --ratio "40,30,20,10"
```

### 组合优化

```bash
# 优化现有组合
portfolio-suggestion --optimize --current "BTC:0.5,ETH:0.3,SOL:0.2"

# 目标收益优化
portfolio-suggestion --optimize --target-return 0.15

# 风险最小化
portfolio-suggestion --optimize --min-risk
```

### 再平衡建议

```bash
# 检查再平衡需求
portfolio-suggestion --rebalance-check

# 生成再平衡方案
portfolio-suggestion --rebalance --threshold 0.05
```

## 风险等级配置

### 保守型 (Conservative)
| 资产 | 配置比例 |
|------|----------|
| BTC | 20% |
| ETH | 15% |
| 稳定币 | 50% |
| 股票 | 15% |

### 平衡型 (Balanced)
| 资产 | 配置比例 |
|------|----------|
| BTC | 35% |
| ETH | 25% |
| 山寨币 | 15% |
| 稳定币 | 15% |
| 股票 | 10% |

### 激进型 (Aggressive)
| 资产 | 配置比例 |
|------|----------|
| BTC | 40% |
| ETH | 30% |
| 山寨币 | 25% |
| 稳定币 | 5% |

## 输出格式

```json
{
  "risk_profile": "balanced",
  "capital": 100000,
  "suggestion": {
    "allocation": [
      {"asset": "BTC", "weight": 0.35, "amount": 35000},
      {"asset": "ETH", "weight": 0.25, "amount": 25000},
      {"asset": "SOL", "weight": 0.15, "amount": 15000},
      {"asset": "USDT", "weight": 0.15, "amount": 15000},
      {"asset": "AAPL", "weight": 0.10, "amount": 10000}
    ],
    "expected_return": 0.25,
    "expected_risk": 0.35,
    "sharpe_ratio": 0.71
  },
  "rebalancing": {
    "needed": false,
    "threshold": 0.05,
    "actions": []
  }
}
```
