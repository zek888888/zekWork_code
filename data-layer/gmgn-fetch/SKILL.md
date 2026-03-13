# GMGN.ai 冲狗数据抓取技能

## 简介

本技能用于抓取 gmgn.ai 网站的加密货币数据，包括新币列表、聪明钱包追踪和代币热度指标。适用于Solana链上的meme币分析和冲狗策略研究。

## 功能特性

- **新币列表抓取**: 获取最新上线的代币信息，包括价格、市值、流动性等
- **聪明钱包追踪**: 监控聪明钱包（Smart Money）的买卖活动
- **热度指标计算**: 分析代币的社交热度、聪明钱流向、买卖压力等
- **数据持久化**: 自动保存到SQLite数据库，支持历史数据查询
- **双模式抓取**: 支持Playwright浏览器模拟和直接API请求

## 安装依赖

```bash
pip install playwright requests
playwright install chromium
```

## 文件结构

```
gmgn-fetch/
├── gmgn_fetch.py    # 主数据抓取脚本
└── SKILL.md         # 本说明文档
```

## 数据库结构

数据存储在: `~/.openclaw/workspace/quant-trading/data/market_data.db`

### 表结构

1. **gmgn_new_tokens** - 新币列表
   - token_address: 代币合约地址
   - symbol: 代币符号
   - name: 代币名称
   - created_at: 创建时间
   - market_cap: 市值
   - liquidity: 流动性
   - volume_24h: 24小时交易量
   - price: 当前价格
   - price_change_24h: 24小时价格变化
   - holder_count: 持有者数量

2. **gmgn_smart_wallets** - 聪明钱包活动
   - wallet_address: 钱包地址
   - token_address: 代币地址
   - action: 操作类型 (buy/sell)
   - amount: 交易数量
   - value_usd: 交易金额(USD)
   - tx_hash: 交易哈希
   - timestamp: 交易时间
   - pnl_24h: 24小时盈亏
   - win_rate: 胜率

3. **gmgn_token_heat** - 代币热度指标
   - token_address: 代币地址
   - heat_score: 热度分数 (0-100)
   - social_mentions: 社交提及次数
   - twitter_sentiment: 推特情绪分数
   - smart_money_inflow: 聪明钱流入
   - buy_pressure: 买入压力
   - sell_pressure: 卖出压力
   - trending_rank:  trending排名

## 使用示例

### 1. 基础使用

```python
import asyncio
from gmgn_fetch import GmgnFetcher

async def main():
    # 创建抓取器 (使用Playwright模式)
    async with GmgnFetcher(use_playwright=True, headless=True) as fetcher:
        # 获取新币列表
        new_tokens = await fetcher.fetch_new_tokens(limit=50)
        
        # 获取聪明钱包数据
        smart_wallets = await fetcher.fetch_smart_wallets(limit=100)
        
        # 获取代币热度
        token_heats = await fetcher.fetch_token_heat(limit=50)

asyncio.run(main())
```

### 2. 使用Requests模式 (更轻量)

```python
async with GmgnFetcher(use_playwright=False) as fetcher:
    tokens = await fetcher.fetch_new_tokens(limit=20)
```

### 3. 查询数据库

```python
from gmgn_fetch import DatabaseManager

db = DatabaseManager()

# 获取热门代币
hot_tokens = db.get_hot_tokens(limit=20, min_heat_score=70.0)

# 获取聪明钱包活动
wallet_activity = db.get_smart_wallet_activity(
    wallet_address="xxx...",
    limit=50
)
```

### 4. 计算代币热度指标

```python
# 计算特定代币的综合指标
metrics = fetcher.calculate_heat_metrics("token_address_here")
print(f"价格变化: {metrics['price_change_24h']}%")
print(f"聪明钱包交易: {metrics['smart_wallet_tx_count']}次")
print(f"净流入: ${metrics['net_flow']}")
```

### 5. 命令行运行

```bash
# 直接运行脚本
python gmgn_fetch.py
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| GMGN_DB_PATH | 数据库路径 | ~/.openclaw/workspace/quant-trading/data/market_data.db |
| GMGN_HEADLESS | 是否无头模式 | true |
| GMGN_TIMEOUT | 请求超时(秒) | 30 |

### 参数说明

**GmgnFetcher 初始化参数:**

- `use_playwright`: 是否使用Playwright浏览器模式
  - `True`: 使用浏览器模拟，适合反爬严格的场景
  - `False`: 使用requests直接请求API，速度更快
- `headless`: 是否无头模式 (不显示浏览器窗口)

## 数据抓取方法

### fetch_new_tokens(limit=50)

获取新币列表

**参数:**
- `limit`: 获取数量，默认50

**返回:** `List[NewToken]`

### fetch_smart_wallets(token_address=None, limit=100)

获取聪明钱包交易数据

**参数:**
- `token_address`: 特定代币地址，None则获取所有
- `limit`: 获取数量，默认100

**返回:** `List[SmartWallet]`

### fetch_token_heat(limit=50)

获取代币热度指标

**参数:**
- `limit`: 获取数量，默认50

**返回:** `List[TokenHeat]`

### calculate_heat_metrics(token_address)

计算特定代币的综合热度指标

**参数:**
- `token_address`: 代币合约地址

**返回:** `Dict` 包含价格变化、聪明钱包活动、资金流向等

## 注意事项

1. **反爬处理**: gmgn.ai可能有反爬机制，建议使用Playwright模式并控制请求频率
2. **数据更新**: 建议每5-15分钟抓取一次，避免过于频繁
3. **存储空间**: 长期运行会产生较多数据，定期清理旧数据
4. **网络要求**: 需要能访问 gmgn.ai，可能需要科学上网

## 故障排查

### Playwright启动失败

```bash
# 重新安装浏览器
playwright install chromium
```

### 数据抓取为空

- 检查网络连接
- 确认网站可访问
- 查看日志输出排查问题
- 尝试切换use_playwright模式

### 数据库锁定

- 确保只有一个进程访问数据库
- 检查是否有僵尸进程占用

## 扩展开发

可以根据需要扩展以下功能:

1. 添加更多数据源 (DexScreener, Birdeye等)
2. 实现实时WebSocket数据流
3. 添加 alerting 功能 (价格异动、聪明钱包大额交易等)
4. 集成Telegram/Discord机器人推送

## 更新日志

- v1.0.0: 初始版本，实现基础数据抓取功能

## 许可证

MIT License
