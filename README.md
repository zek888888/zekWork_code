# 量化交易系统 (Quant Trading System) v0.3.0

## 📁 项目结构

```
quant-trading/
├── data-layer/                    # 数据层
│   ├── market-data-fetch/         # 行情数据抓取 ✅
│   │   ├── SKILL.md
│   │   └── fetch.py
│   ├── fundamentals-parser/       # 基本面分析 ✅
│   │   └── SKILL.md
│   └── gmgn-fetch/                # 冲狗数据抓取 ✅
│       ├── SKILL.md
│       └── gmgn_fetch.py
├── research-layer/                # 研究层
│   ├── news-sentiment-scan/       # 新闻情绪扫描 ✅
│   │   ├── SKILL.md
│   │   └── scan.py
│   ├── twitter-kol-monitor/       # Twitter KOL监控 ✅
│   │   ├── SKILL.md
│   │   └── twitter_monitor.py
│   ├── factor-score-engine/       # 因子评估引擎 ✅
│   │   ├── SKILL.md
│   │   └── score.py
│   └── event-impact-analyzer/     # 事件冲击分析 ✅
│       └── SKILL.md
├── decision-layer/                # 决策层
│   ├── risk-guardrail/            # 风控护栏 ✅
│   │   └── SKILL.md
│   └── portfolio-suggestion/      # 组合建议 ✅
│       └── SKILL.md
├── execution-layer/               # 执行层
│   └── trade-executor/            # 交易执行器 ✅
│       ├── SKILL.md
│       └── trade_executor.py
├── web-dashboard/                 # 展示层
│   └── report-generator/          # 报告生成 ✅
│       └── SKILL.md
├── data/
│   └── market_data.db             # SQLite数据库
├── tasks/                         # 任务分发配置
│   └── quant_trading_v0.2.json
├── scheduler.py                   # 定时任务
├── feishu_reporter.py             # 飞书报告
└── README.md
```

## ✅ 技能清单

| 层级 | 技能名称 | 状态 | 描述 |
|------|----------|------|------|
| **数据层** | market-data-fetch | ✅ 代码+文档 | 股票/虚拟货币行情数据抓取 |
| **数据层** | fundamentals-parser | ✅ 文档 | 基本面数据解析 |
| **数据层** | gmgn-fetch | ✅ 代码+文档 | gmgn.ai冲狗数据抓取 |
| **研究层** | news-sentiment-scan | ✅ 代码+文档 | 新闻情绪扫描分析 |
| **研究层** | twitter-kol-monitor | ✅ 代码+文档 | Twitter KOL监控 |
| **研究层** | factor-score-engine | ✅ 代码+文档 | 多因子评分引擎 |
| **研究层** | event-impact-analyzer | ✅ 文档 | 事件冲击分析 |
| **决策层** | risk-guardrail | ✅ 文档 | 风控护栏系统 |
| **决策层** | portfolio-suggestion | ✅ 文档 | 投资组合建议 |
| **执行层** | trade-executor | ✅ 代码+文档 | 交易执行器 |
| **展示层** | report-generator | ✅ 文档 | 报告生成与展示 |

**完成度: 11/11 技能 (100%)**

## 🚀 快速开始

### 初始化系统
```bash
cd ~/.openclaw/workspace/quant-trading

# 初始化数据库
python3 data-layer/market-data-fetch/fetch.py --init
python3 research-layer/news-sentiment-scan/scan.py --init
python3 research-layer/factor-score-engine/score.py --init
```

### 添加监控标的
```bash
# 添加虚拟货币
python3 data-layer/market-data-fetch/fetch.py --symbol BTCUSDT --market crypto --add
python3 data-layer/market-data-fetch/fetch.py --symbol ETHUSDT --market crypto --add

# 添加股票
python3 data-layer/market-data-fetch/fetch.py --symbol AAPL --market stock --add
```

### 获取数据
```bash
# 获取实时价格
python3 data-layer/market-data-fetch/fetch.py --symbol BTCUSDT --market crypto

# 获取K线数据
python3 data-layer/market-data-fetch/fetch.py --symbol BTCUSDT --market crypto --type klines --interval 1h --limit 100

# 批量获取监控列表
python3 data-layer/market-data-fetch/fetch.py --watchlist
```

### 因子评分
```bash
# 单标的评分
python3 research-layer/factor-score-engine/score.py --symbol BTCUSDT --market crypto

# 批量评分
python3 research-layer/factor-score-engine/score.py --watchlist
```

### 模拟交易
```bash
# 查看模拟账户
python3 execution-layer/trade-executor/trade_executor.py --account

# 买入
python3 execution-layer/trade-executor/trade_executor.py --buy BTCUSDT --amount 0.1

# 查看持仓
python3 execution-layer/trade-executor/trade_executor.py --positions

# 查看交易历史
python3 execution-layer/trade-executor/trade_executor.py --history
```

### 生成报告
```bash
# 生成飞书报告
python3 feishu_reporter.py
```

### 启动定时任务
```bash
python3 scheduler.py
```

## 📊 评分系统

### 因子权重
| 因子 | 权重 | 说明 |
|------|------|------|
| 技术面 | 40% | RSI、均线、成交量、波动率 |
| 资金面 | 35% | 涨跌幅、资金流向 |
| 情绪面 | 25% | 新闻情绪分析 |

### 评级标准
| 分数 | 评级 | 建议 |
|------|------|------|
| 80-100 | A | 买入 |
| 65-79 | B | 观望/轻仓 |
| 50-64 | C | 观望 |
| <50 | D | 回避 |

## 📈 当前监控标的

| 标的 | 市场 | 当前价格 | 24h涨跌 | 评分 | 信号 |
|------|------|----------|---------|------|------|
| BTCUSDT | crypto | $71,216 | +3.27% | 74.46 | 观望/轻仓 |
| ETHUSDT | crypto | $2,081 | +2.60% | 62.32 | 观望 |
| SOLUSDT | crypto | $88.40 | +3.82% | 63.17 | 观望 |

## 🛠️ 技术栈

- **语言**: Python 3
- **数据库**: SQLite
- **数据源**: Binance API, Yahoo Finance, gmgn.ai
- **定时任务**: schedule库
- **消息推送**: 飞书
- **任务分发**: subagent并行开发

## 📝 版本记录

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-03-11 | v0.1.0 | 项目初始化，数据层+研究层基础功能 |
| 2026-03-11 | v0.2.0 | 完善技能架构，启动子Agent并行开发 |
| 2026-03-11 | v0.3.0 | 所有技能完成，模拟交易功能上线 |
