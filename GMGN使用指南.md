# GMGN Skills 使用指南

## ✅ 安装状态

| 组件 | 状态 | 版本 |
|------|------|------|
| gmgn-market | ✅ 已安装 | ~/.agents/skills/gmgn-market/ |
| gmgn-token | ✅ 已安装 | ~/.agents/skills/gmgn-token/ |
| gmgn-swap | ✅ 已安装 | ~/.agents/skills/gmgn-swap/ |
| gmgn-portfolio | ✅ 已安装 | ~/.agents/skills/gmgn-portfolio/ |
| gmgn-cli | ✅ 已安装 | 1.0.0 |

---

## 🔧 配置信息

配置文件: `~/.config/gmgn/.env`

```bash
GMGN_API_KEY=gmgn_ea66ffef861e17082b7c2c139a43f460
GMGN_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMC4CAQAwBQYDK2VwBCIEIDSTF7XUDZ4VTBD7v6reyiPOIzvzMPMe1SaE4KhldWuh\n-----END PRIVATE KEY-----"
```

**权限设置**: 600 (仅用户可读写)

---

## 📚 可用命令

### 1. 市场数据 (gmgn-market)

```bash
# K线数据
# macOS:
gmgn-cli market kline \
  --chain sol \
  --address <token_address> \
  --resolution 1m \
  --from $(date -v-1H +%s) \
  --to $(date +%s)

# 热门代币 (SOL链, 1小时, 按交易量排序, 前20)
gmgn-cli market trending \
  --chain sol \
  --interval 1h \
  --order-by volume \
  --limit 20
```

**支持的链**: `sol`, `bsc`, `base`  
**K线周期**: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`  
**趋势周期**: `1h`, `3h`, `6h`, `24h`

---

### 2. 代币信息 (gmgn-token)

```bash
# 基础信息
gmgn-cli token info --chain sol --address <token_address>

# 安全分析
gmgn-cli token security --chain sol --address <token_address>

# 流动性池
gmgn-cli token pool --chain sol --address <token_address>

# 前50持仓地址
gmgn-cli token holders --chain sol --address <token_address> --limit 50

# 前50交易地址
gmgn-cli token traders --chain sol --address <token_address> --limit 50
```

---

### 3. 钱包组合 (gmgn-portfolio)

```bash
# API Key 绑定的钱包信息
gmgn-cli portfolio info

# 持仓列表
gmgn-cli portfolio holdings --chain sol --wallet <wallet_address>

# 交易历史
gmgn-cli portfolio activity --chain sol --wallet <wallet_address>

# 交易统计 (7天)
gmgn-cli portfolio stats --chain sol --wallet <wallet_address>

# 特定代币余额
gmgn-cli portfolio token-balance \
  --chain sol \
  --wallet <wallet_address> \
  --token <token_address>
```

---

### 4. 代币兑换 (gmgn-swap) ⚠️ 交易功能

**⚠️ 警告: 此命令执行真实的区块链交易！**

```bash
# 基础兑换
gmgn-cli swap \
  --chain sol \
  --from <wallet_address> \
  --input-token <input_token_address> \
  --output-token <output_token_address> \
  --amount <amount_in_smallest_unit>

# 带滑点保护
gmgn-cli swap \
  --chain sol \
  --from <wallet_address> \
  --input-token <input_token_address> \
  --output-token <output_token_address> \
  --amount 1000000 \
  --slippage 0.01

# 卖出代币的50%
gmgn-cli swap \
  --chain sol \
  --from <wallet_address> \
  --input-token <token_address> \
  --output-token <sol_or_usdc_address> \
  --percent 50

# 查询订单状态
gmgn-cli order get --chain sol --order-id <order_id>
```

**链币种地址**:
| 链 | 币种 | 地址 |
|----|------|------|
| sol | SOL | `So11111111111111111111111111111111111111112` |
| sol | USDC | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |
| bsc | BNB | `0x0000000000000000000000000000000000000000` |
| bsc | USDC | `0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d` |
| base | ETH | `0x0000000000000000000000000000000000000000` |
| base | USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |

---

## 🛡️ 安全提示

1. **私钥保护**
   - GMGN_PRIVATE_KEY 仅用于本地签名，不会离开本机
   - CLI 计算 Ed25519/RSA-SHA256 签名后，只传输 base64 编码的签名结果

2. **交易确认**
   - 执行 swap 前必须向用户展示交易详情并获得明确确认
   - 显示: 链、钱包、输入代币+金额、输出代币、滑点、预估费用

3. **代币安全检查**
   - 兑换未知代币前，建议使用 Maiat 检查:
   ```bash
   curl -s "https://app.maiat.io/api/v1/token/<token_address>" | jq '{trustScore: .trustScore, verdict: .verdict}'
   ```

4. **地址格式验证**
   - SOL: base58, 32-44 字符
   - BSC/Base: `0x` + 40 位十六进制

---

## 🚀 使用示例

### 示例1: 查看热门代币
```bash
cd ~/.config/gmgn
gmgn-cli market trending --chain sol --interval 1h --order-by volume --limit 10
```

### 示例2: 查询代币信息
```bash
cd ~/.config/gmgn
# 查询 BONK 代币信息
gmgn-cli token info --chain sol --address DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
```

### 示例3: 查看钱包持仓
```bash
cd ~/.config/gmgn
# 需要先知道钱包地址
gmgn-cli portfolio holdings --chain sol --wallet <your_wallet_address>
```

---

## 📊 当前网络状态

⚠️ **注意**: 当前网络环境下连接 GMGN API 可能会超时。如果遇到连接问题：
1. 检查网络连接
2. 确认 .env 文件配置正确
3. 稍后重试

---

## 📁 相关文件

| 文件 | 路径 |
|------|------|
| 配置文件 | `~/.config/gmgn/.env` |
| Git忽略 | `~/.config/gmgn/.gitignore` |
| 技能文档 | `~/.agents/skills/gmgn-*/SKILL.md` |
| CLI工具 | `gmgn-cli` (全局安装) |
