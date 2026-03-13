# 量化交易系统 (Quant Trading System) v1.0.0

🚀 **全自动、多市场、AI驱动的量化交易系统**

> 目标：打造一个真正能帮助赚钱的量化交易系统

---

## 📋 功能特性

### ✅ 已实现功能

| 模块 | 功能 | 状态 |
|------|------|------|
| **数据层** | 虚拟货币行情 (Binance) | ✅ |
| **数据层** | 股票行情 (Yahoo Finance) | ✅ |
| **数据层** | 冲狗数据 (GMGN.ai) | ✅ |
| **研究层** | 多因子评分引擎 | ✅ |
| **研究层** | 聪明钱包追踪 | ✅ |
| **决策层** | 策略推荐系统 | ✅ |
| **决策层** | 风控管理 | ✅ |
| **执行层** | 模拟交易 | ✅ |
| **执行层** | 币安API接入 | ✅ |
| **回测** | 策略回测引擎 | ✅ |
| **AI** | 知识库管理 | ✅ |
| **通知** | 飞书推送 | ✅ |
| **展示** | Web Dashboard | ✅ |

### 🚧 开发中功能

| 功能 | 描述 | 预计完成 |
|------|------|----------|
| 港股/A股数据 | 接入富途/通达信 | v1.1 |
| Polymarket预测 | 预测市场交易 | v1.2 |
| 移动端APP | iOS/Android | v1.3 |

---

## 🏗️ 系统架构

```
quant-trading/
├── data-layer/                    # 数据层
│   ├── market-data-fetch/         # 行情数据
│   │   └── fetch.py               # Binance/Yahoo数据获取
│   ├── gmgn-fetch/                # 冲狗数据
│   │   └── gmgn_fetch.py          # GMGN.ai集成
│   └── fundamentals-parser/       # 基本面数据
│
├── research-layer/                # 研究层
│   ├── factor-score-engine/       # 因子评分
│   │   └── score.py               # 多因子评分引擎
│   ├── news-sentiment-scan/       # 新闻情绪
│   ├── twitter-kol-monitor/       # KOL监控
│   └── event-impact-analyzer/     # 事件分析
│
├── decision-layer/                # 决策层
│   ├── risk-guardrail/            # 风控系统
│   └── portfolio-suggestion/      # 组合建议
│
├── execution-layer/               # 执行层
│   └── trade-executor/            # 交易执行
│       ├── trade_executor.py      # 模拟交易
│       └── exchange_api.py        # 交易所API
│
├── ai_models/                     # AI模块
│   └── knowledge_base/            # 知识库
│       └── knowledge_manager.py   # 策略知识管理
│
├── backtest/                      # 回测系统
│   └── backtest_engine.py         # 回测引擎
│
├── web-dashboard/                 # Web界面
│   └── app.py                     # Flask应用
│
├── utils/                         # 工具模块
│   └── notification.py            # 通知推送
│
├── main.py                        # 主控程序 ⭐
├── scheduler.py                   # 定时任务
└── feishu_reporter.py             # 飞书报告
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pandas numpy matplotlib schedule flask ccxt
```

### 2. 初始化系统

```bash
cd ~/.openclaw/workspace/quant-trading
python main.py --init
```

### 3. 添加监控标的

```bash
# 添加虚拟货币
python main.py --add BTCUSDT crypto
python main.py --add ETHUSDT crypto
python main.py --add SOLUSDT crypto

# 添加美股
python main.py --add AAPL stock
python main.py --add TSLA stock
```

### 4. 启动自动交易（模拟模式）

```bash
python main.py --daemon
```

### 5. 查看系统状态

```bash
python main.py --status
```

---

## 📊 核心功能使用

### 市场扫描
```bash
# 手动扫描市场
python main.py --scan
```

### 冲狗监控
```bash
# 扫描GMGN热门代币
python data-layer/gmgn-fetch/gmgn_fetch.py --trending --limit 20

# 查看新币
python data-layer/gmgn-fetch/gmgn_fetch.py --new

# 添加聪明钱包追踪
python data-layer/gmgn-fetch/gmgn_fetch.py --add-wallet <地址> --wallet-tag 鲸鱼
```

### 策略回测
```bash
# 趋势跟踪策略回测
python main.py --backtest trend --days 90

# 均值回归策略回测
python main.py --backtest mean_reversion --days 90

# 冲狗策略回测
python main.py --backtest meme --days 90
```

### 交易执行
```bash
# 模拟交易
python execution-layer/trade-executor/trade_executor.py --account
python execution-layer/trade-executor/trade_executor.py --buy BTCUSDT --amount 0.1

# 查看持仓
python execution-layer/trade-executor/trade_executor.py --positions
```

### AI知识库
```bash
# 查看策略列表
python ai_models/knowledge_base/knowledge_manager.py --list-strategies

# 查看策略详情
python ai_models/knowledge_base/knowledge_manager.py --strategy-id trend_following_ma

# 获取策略推荐
python ai_models/knowledge_base/knowledge_manager.py --recommend --market crypto --condition bull
```

---

## ⚙️ 配置真实交易

### 1. 设置币安API密钥

```bash
export BINANCE_API_KEY="your_api_key"
export BINANCE_SECRET_KEY="your_secret_key"
export ENABLE_REAL_TRADING="true"
```

### 2. 测试API连接

```bash
python execution-layer/trade-executor/exchange_api.py --test
```

### 3. 启用真实交易

```bash
python main.py --daemon --real
```

⚠️ **警告**: 真实交易有风险，建议先用模拟盘验证策略！

---

## 📈 交易策略

### 内置策略

| 策略 | 类型 | 风险等级 | 适用市场 |
|------|------|----------|----------|
| 均线趋势跟踪 | 趋势 | 3/5 | 全部 |
| RSI均值回归 | 反转 | 2/5 | 股票/币圈 |
| 波动率突破 | 趋势 | 4/5 | 全部 |
| 冲狗动量 | 动量 | 5/5 | Meme币 |
| 财报事件驱动 | 事件 | 3/5 | 美股 |

### 策略参数

```python
# 趋势跟踪策略参数
{
    "fast_ma": 5,           # 快速均线
    "slow_ma": 20,          # 慢速均线
    "position_size": 0.2,   # 仓位比例
    "stop_loss": 0.05,      # 止损5%
    "take_profit": 0.10     # 止盈10%
}

# 冲狗策略参数
{
    "volume_threshold": 3.0,    # 成交量倍数
    "momentum_period": 3,       # 动量周期(小时)
    "position_size": 0.10,      # 仓位10%
    "stop_loss": 0.08,          # 止损8%
    "take_profit": 0.20,        # 止盈20%
    "max_holding_hours": 72     # 最大持仓72小时
}
```

---

## 🛡️ 风控系统

### 风控规则

```python
# 单笔限制
max_position_pct = 0.2      # 单标的最大仓位20%
max_daily_loss_pct = 0.05   # 单日最大亏损5%
max_total_loss_pct = 0.15   # 总最大亏损15%

# 止损止盈
stop_loss = 0.05            # 止损5%
take_profit = 0.10          # 止盈10%

# 持仓限制
max_positions = 10          # 最大持仓10个标的
```

---

## 📊 绩效指标

回测结果包含以下指标：

- **总收益率**: 策略整体收益
- **夏普比率**: 风险调整后收益
- **最大回撤**: 资金曲线最大回落
- **胜率**: 盈利交易占比
- **盈亏比**: 平均盈利/平均亏损
- **交易次数**: 总交易次数

---

## 🔔 通知推送

### 飞书配置

```bash
export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
export FEISHU_CHAT_ID="oc_4db6083a476458269556aa3ff77a6fbd"
```

### 通知类型

- 🎯 **交易信号**: 高置信度买卖信号
- 💰 **订单执行**: 成交通知
- 🚨 **风险警告**: 回撤/亏损超限
- 📈 **日报**: 每日交易总结

---

## 🗓️ 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2026-03-14 | 首个可用版本，整合所有模块 |
| v0.3.0 | 2026-03-11 | 模拟交易、Web界面 |
| v0.2.0 | 2026-03-11 | 多Agent并行开发 |
| v0.1.0 | 2026-03-11 | 项目初始化 |

详见 [CHANGELOG.md](CHANGELOG.md)

---

## 🛠️ 技术栈

- **语言**: Python 3.12
- **数据库**: SQLite
- **Web框架**: Flask
- **数据源**: Binance API, Yahoo Finance, GMGN.ai
- **AI**: Kimi API
- **图表**: ECharts, Matplotlib
- **消息**: 飞书Bot

---

## ⚠️ 风险提示

1. **市场风险**: 所有交易都有亏损风险，过往表现不代表未来收益
2. **技术风险**: 系统故障可能导致意外损失
3. **合规风险**: 请遵守当地法律法规
4. **建议**: 
   - 先用模拟盘充分验证策略
   - 从小资金开始实盘
   - 设置严格的风控规则
   - 定期检查和优化策略

---

## 📞 支持与反馈

如有问题或建议，欢迎通过以下方式联系：

- 飞书群: [量化交易讨论群](https://www.feishu.cn)
- GitHub Issues: 提交Bug或Feature Request

---

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

**免责声明**: 本系统仅供学习研究使用，不构成任何投资建议。使用本系统进行交易的风险由用户自行承担。
