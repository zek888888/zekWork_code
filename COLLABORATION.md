# 协作开发指南 (Collaboration Guide)

> 本文档用于指导 AI Agent (Kimi Code CLI 和 OpenClaw) 协同开发本项目

---

## 🎯 协作原则

1. **模块化开发** - 每个Agent负责不同模块，避免冲突
2. **版本控制** - 所有修改通过Git管理，确保可追溯
3. **文档同步** - 每次迭代更新README和CHANGELOG
4. **代码审查** - 关键改动需要说明原因和影响

---

## 📁 项目架构速览

```
quant-trading/
│
├── 📊 数据层 (data-layer/)
│   ├── market-data-fetch/       # 行情数据获取
│   │   └── fetch.py             # Binance/Yahoo接口
│   ├── gmgn-fetch/              # 冲狗数据
│   │   └── gmgn_fetch.py        # GMGN.ai API集成
│   └── fundamentals-parser/     # 基本面分析
│
├── 🔬 研究层 (research-layer/)
│   ├── factor-score-engine/     # 多因子评分
│   │   └── score.py             # 技术面/资金面/情绪面评分
│   ├── news-sentiment-scan/     # 新闻情绪扫描
│   ├── twitter-kol-monitor/     # Twitter KOL监控
│   └── event-impact-analyzer/   # 事件冲击分析
│
├── 🧠 决策层 (decision-layer/)
│   ├── risk-guardrail/          # 风控系统
│   └── portfolio-suggestion/    # 组合建议
│
├── ⚡ 执行层 (execution-layer/)
│   └── trade-executor/          # 交易执行
│       ├── trade_executor.py    # 模拟交易
│       └── exchange_api.py      # 币安API
│
├── 🤖 AI模块 (ai_models/)
│   └── knowledge_base/          # AI知识库
│       └── knowledge_manager.py # 策略知识管理
│
├── 📈 回测系统 (backtest/)
│   └── backtest_engine.py       # 策略回测引擎
│
├── 🎨 Web界面 (web-dashboard/)
│   ├── app.py                   # Flask主应用
│   └── templates/               # HTML模板
│
├── 🔔 工具模块 (utils/)
│   └── notification.py          # 通知推送系统
│
├── 🎯 主控程序
│   ├── main.py                  # 系统主入口 ⭐ 核心文件
│   └── scheduler.py             # 定时任务
│
└── 📄 文档
    ├── README.md                # 项目说明 (每次迭代更新)
    ├── ARCHITECTURE_v1.0.md     # 架构设计文档
    ├── CHANGELOG.md             # 更新日志 (每次迭代更新)
    └── COLLABORATION.md         # 本文件
```

---

## 🔧 核心模块详解

### 1. main.py - 系统主控 ⭐⭐⭐

**作用**: 统一入口，协调所有模块工作

**关键功能**:
```python
- init_system()        # 初始化数据库
- scan_market()        # 扫描市场，生成交易信号
- scan_gmgn()          # 扫描冲狗市场
- execute_signals()    # 执行交易信号
- run_backtest()       # 策略回测
- start_scheduler()    # 启动定时任务
```

**使用方式**:
```bash
python main.py --init          # 初始化
python main.py --daemon        # 启动自动交易
python main.py --status        # 查看状态
python main.py --backtest trend --days 90
```

---

### 2. GMGN冲狗模块 (gmgn_fetch.py)

**作用**: 获取Meme币市场数据，追踪聪明钱包

**关键类**:
```python
class GMGNFetcher:
    - fetch_trending_tokens()   # 获取热门代币
    - fetch_smart_wallet()      # 获取钱包信息
    - add_tracking_wallet()     # 添加追踪钱包
    - monitor_wallet_changes()  # 监控钱包变化
```

**数据表**:
- `gmgn_tokens` - 代币信息
- `smart_wallets` - 聪明钱包
- `wallet_trades` - 钱包交易记录

---

### 3. 回测引擎 (backtest_engine.py)

**作用**: 验证策略效果，计算绩效指标

**内置策略**:
```python
- trend_following_strategy()    # 均线趋势跟踪
- mean_reversion_strategy()     # RSI均值回归
- breakout_strategy()           # 波动率突破
- meme_coin_strategy()          # 冲狗动量策略
```

**绩效指标**:
- 总收益率
- 夏普比率
- 最大回撤
- 胜率
- 盈亏比

---

### 4. AI知识库 (knowledge_manager.py)

**作用**: 管理交易策略，智能推荐

**关键功能**:
```python
- get_strategies()          # 获取策略列表
- recommend_strategy()      # 根据市场推荐策略
- learn_from_backtest()     # 从回测学习
- generate_trading_plan()   # 生成交易计划
```

**内置策略**:
1. `trend_following_ma` - 均线趋势跟踪
2. `mean_reversion_rsi` - RSI均值回归
3. `breakout_volatility` - 波动率突破
4. `meme_coin_momentum` - 冲狗动量策略
5. `event_driven_earnings` - 财报事件驱动

---

### 5. 币安API (exchange_api.py)

**作用**: 接入真实交易所，执行交易

**关键类**:
```python
class BinanceAPI:
    - get_account_info()      # 账户信息
    - place_order()           # 下单
    - cancel_order()          # 撤单
    - get_order_status()      # 查询订单

class RiskManager:
    - check_order_risk()      # 检查订单风险
    - calculate_position_size() # 计算仓位
```

**风控规则**:
- 单标的最大仓位: 20%
- 单日最大亏损: 5%
- 总最大回撤: 15%

---

### 6. 通知系统 (notification.py)

**作用**: 飞书推送交易信号和提醒

**通知类型**:
```python
- notify_trade_signal()     # 交易信号
- notify_order()            # 订单执行
- notify_risk()             # 风险警告
- notify_daily_report()     # 日报
```

---

## 🔄 协作工作流程

### 1. 功能开发流程

```
1. 读取 COLLABORATION.md 和 README.md 了解当前状态
2. 分析需要修改的模块
3. 编写/修改代码
4. 更新 README.md 和 CHANGELOG.md
5. 提交到Git: git add . && git commit -m "描述"
6. 推送到GitHub: git push origin main
```

### 2. Git 提交规范

```bash
# 格式: [类型] 描述

git commit -m "[feat] 添加GMGN聪明钱包监控功能"
git commit -m "[fix] 修复回测结果保存失败问题"
git commit -m "[docs] 更新README使用说明"
git commit -m "[refactor] 优化因子评分算法"
git commit -m "[test] 添加策略回测单元测试"
```

**类型说明**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具

### 3. 版本发布流程

```bash
# 1. 更新版本号 (在 main.py 和 CHANGELOG.md)
# 2. 提交更改
git add .
git commit -m "[release] v1.1.0"

# 3. 打标签
git tag -a v1.1.0 -m "版本1.1.0发布"

# 4. 推送
git push origin main --tags
```

---

## 📝 文档更新规范

### README.md 更新要求

每次迭代必须更新:
1. **功能列表** - 新增/修改的功能
2. **使用示例** - 新的命令行用法
3. **配置说明** - 新增的配置项
4. **版本信息** - 当前版本号

### CHANGELOG.md 更新要求

按照格式添加:
```markdown
## [版本号] - 日期

### 新增
- 功能1描述
- 功能2描述

### 改进
- 改进1描述

### 修复
- Bug修复描述
```

---

## 🐛 调试和测试

### 本地测试命令

```bash
# 测试数据获取
python data-layer/market-data-fetch/fetch.py --symbol BTCUSDT --market crypto

# 测试GMGN模块
python data-layer/gmgn-fetch/gmgn_fetch.py --trending --limit 10

# 测试回测
python backtest/backtest_engine.py --symbol BTCUSDT --strategy trend --days 30

# 测试主控
python main.py --scan
python main.py --status

# 测试通知
python utils/notification.py --test-trade
```

### 日志查看

```bash
# 查看Web服务日志
tail -f ~/.openclaw/workspace/quant-trading/web-dashboard/server.log

# 查看数据库内容
sqlite3 ~/.openclaw/workspace/quant-trading/data/market_data.db ".tables"
```

---

## 🚀 常用开发任务

### 添加新策略

1. 在 `ai_models/knowledge_base/knowledge_manager.py` 添加策略配置
2. 在 `backtest/backtest_engine.py` 实现策略逻辑
3. 更新 `README.md` 策略列表
4. 提交: `git commit -m "[feat] 添加新策略XXX"`

### 添加新数据源

1. 在 `data-layer/` 创建新目录
2. 实现数据获取函数
3. 在 `main.py` 添加调用
4. 更新文档

### 修复Bug

1. 定位问题模块
2. 修复代码
3. 测试验证
4. 提交: `git commit -m "[fix] 修复XXX问题"`

---

## ⚠️ 注意事项

### 1. 敏感信息处理
- API密钥不要硬编码，使用环境变量
- 数据库文件不要提交到Git (.gitignore已配置)
- 日志文件不要提交

### 2. 数据库变更
- 新增表需要在对应模块的 `init_database()` 中添加
- 表结构变更需要版本化管理

### 3. 依赖管理
- 新增Python包需要记录在 `requirements.txt`
- 测试是否向后兼容

### 4. 性能优化
- 数据库查询使用索引
- 批量操作代替循环单条
- 缓存热点数据

---

## 📞 协作沟通

### 代码注释规范

```python
def function_name(param: str) -> Dict:
    """
    函数功能简述
    
    Args:
        param: 参数说明
    
    Returns:
        返回值说明
    
    Example:
        >>> function_name("test")
        {"result": "ok"}
    """
    pass
```

### TODO标记

```python
# TODO: [Agent-name] 需要实现的功能说明
# FIXME: [Agent-name] 已知问题，需要修复
# HACK: [Agent-name] 临时方案，需要优化
```

---

## 📚 参考文档

- [项目README](./README.md) - 项目整体说明
- [架构设计](./ARCHITECTURE_v1.0.md) - 系统设计文档
- [更新日志](./CHANGELOG.md) - 版本历史

---

**最后更新**: 2026-03-14  
**版本**: v1.0.0  
**协作者**: Kimi Code CLI + OpenClaw
