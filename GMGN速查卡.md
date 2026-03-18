# GMGN 速查卡

## 常用命令

### 🔥 热门代币
```bash
cd ~/.config/gmgn
gmgn-cli market trending --chain sol --interval 1h --limit 10
```

### 📊 K线数据
```bash
gmgn-cli market kline \
  --chain sol \
  --address <token_address> \
  --resolution 1h \
  --from $(date -v-24H +%s) \
  --to $(date +%s)
```

### 🔍 代币信息
```bash
gmgn-cli token info --chain sol --address <token_address>
gmgn-cli token security --chain sol --address <token_address>
gmgn-cli token pool --chain sol --address <token_address>
```

### 💼 钱包信息
```bash
gmgn-cli portfolio info
gmgn-cli portfolio holdings --chain sol --wallet <wallet>
gmgn-cli portfolio activity --chain sol --wallet <wallet>
```

### 💰 兑换代币 ⚠️
```bash
gmgn-cli swap \
  --chain sol \
  --from <wallet> \
  --input-token <input> \
  --output-token <output> \
  --amount <amount> \
  --slippage 0.01
```

---

## 常用代币地址

| 链 | 代币 | 地址 |
|----|------|------|
| SOL | SOL | `So11111111111111111111111111111111111111112` |
| SOL | USDC | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |
| BSC | BNB | `0x0000000000000000000000000000000000000000` |
| BSC | USDC | `0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d` |
| Base | ETH | `0x0000000000000000000000000000000000000000` |
| Base | USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |

---

## 参数速查

| 参数 | 可选值 |
|------|--------|
| `--chain` | sol, bsc, base |
| `--resolution` | 1m, 5m, 15m, 1h, 4h, 1d |
| `--interval` | 1h, 3h, 6h, 24h |
| `--order-by` | volume, swaps, marketcap, holder_count, change1h |
| `--period` | 7d, 30d |
| `--slippage` | 0.01 (1%), 0.005 (0.5%) |

---

## Python 快速开始

```python
from gmgn_client import GMGNClient

client = GMGNClient()

# 热门代币
trending = client.get_trending("sol", "1h", 10)

# 代币信息
info = client.get_token_info("sol", "<address>")

# 安全分析
security = client.get_token_security("sol", "<address>")

# 钱包持仓
holdings = client.get_wallet_holdings("sol", "<wallet>")
```

---

## 配置文件

位置: `~/.config/gmgn/.env`

```bash
GMGN_API_KEY=your_api_key
GMGN_PRIVATE_KEY=your_private_key
```

---

## 故障排除

### SSL 错误
- 检查网络连接
- 尝试更换网络
- 稍后重试

### 超时错误
- API 服务可能暂时不可用
- 稍后重试

### 认证错误
- 检查 API Key 是否正确
- 确认 .env 文件位置

---

## 安全提示 ⚠️

- `swap` 命令执行真实交易
- 交易前必须确认详情
- 私钥仅本地存储
- 小额测试后再大额交易
