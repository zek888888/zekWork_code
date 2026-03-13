---
name: report-generator
description: "Trading report generator and web dashboard. Displays market data, trading signals, portfolio status, and performance analytics."
metadata:
  {
    "openclaw":
      {
        "emoji": "📊",
        "requires": { "bins": ["python3"] },
      },
  }
---

# Report Generator

报告生成与展示系统 - 量化交易数据可视化

## 功能模块

### 1. 市场概览
- 主要指数行情
- 热门板块/币种
- 市场情绪指标

### 2. 交易信号
- 买入/卖出信号列表
- 信号强度评分
- 历史信号回测

### 3. 持仓管理
- 当前持仓列表
- 盈亏统计
- 风险敞口

### 4. 绩效分析
- 收益率曲线
- 夏普比率
- 最大回撤
- 胜率统计

## Usage Examples

### 生成日报

```bash
# 生成每日交易报告
report-generator --daily

# 生成特定日期报告
report-generator --date 2026-03-10
```

### 生成周报/月报

```bash
# 生成周报
report-generator --weekly

# 生成月报
report-generator --monthly
```

### 启动Web界面

```bash
# 启动本地Web服务器
report-generator --web --port 8080

# 生成静态报告
report-generator --export --format html --output ./reports/
```

### 实时数据推送

```bash
# 启动实时推送服务
report-generator --stream --channel feishu
```

## 报告类型

| 类型 | 频率 | 内容 |
|------|------|------|
| 简报 | 实时 | 重要信号、价格异动 |
| 日报 | 每日 | 市场回顾、持仓状态、交易记录 |
| 周报 | 每周 | 周度收益、策略表现、市场分析 |
| 月报 | 每月 | 月度总结、绩效归因、策略优化 |

## 飞书推送

```bash
# 推送报告到飞书
report-generator --push --target feishu --type daily

# 推送紧急信号
report-generator --push --target feishu --type alert --urgent
```

## Web界面

访问地址: `http://localhost:8080`

### 页面结构

```
/
├── /dashboard      # 总览面板
├── /market         # 市场行情
├── /signals        # 交易信号
├── /portfolio      # 持仓管理
├── /performance    # 绩效分析
├── /backtest       # 回测结果
└── /settings       # 系统设置
```
