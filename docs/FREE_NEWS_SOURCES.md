# 免费多源新闻获取方案

## 📡 已配置数据源

### 1. RSS订阅源 (稳定可用)
| 来源 | 类型 | 状态 | 语言 |
|------|------|------|------|
| IT之家 RSS | 科技/AI | ✅ 正常 | 中文 |
| BBC Business | 国际财经 | ✅ 正常 | 英文 |
| Reuters Business | 国际财经 | ✅ 正常 | 英文 |

### 2. 计划添加的源 (需要适配)
| 来源 | 类型 | 费用 | 备注 |
|------|------|------|------|
| 新浪财经 | 财经 | 免费 | RSS不稳定 |
| 金色财经 | 加密货币 | 免费 | API需适配 |
| 币世界 | 加密货币 | 免费 | API需适配 |
| NewsAPI | 综合 | 免费100次/天 | 国际新闻 |

## 📊 当前数据

```
总计: 17 条新闻
├── RSS_IT: 5 条 (科技)
├── RSS_财经: 5 条 (国际财经)
└── jin10: 7 条 (演示数据)
```

## 🔄 自动获取

### 定时任务设置
```bash
# 每小时获取一次免费新闻
crontab -e

# 添加:
0 * * * * cd ~/.openclaw/workspace/quant-trading && python3 cron/fetch_free_news.py >> logs/free_news.log 2>&1
```

### 手动获取
```bash
# 命令行
python3 research-layer/news-sentiment-scan/free_news_fetcher.py

# 或API调用
POST /api/news/fetch_free
```

## 📰 新闻分类覆盖

- ✅ **科技/AI**: IT之家、TechWeb
- ✅ **国际财经**: BBC、Reuters
- 🔄 **加密货币**: 金色财经、币世界 (待修复)
- 🔄 **国内财经**: 新浪财经 (待修复)
- 🔄 **政治**: NewsAPI (待配置)

## 🛠️ 使用方式

### 前端集成
```javascript
// 获取免费新闻
fetch('/api/news/fetch_free', {method: 'POST'})
  .then(r => r.json())
  .then(data => {
    console.log(`获取 ${data.saved} 条新闻`);
  });
```

### 后端调用
```python
from free_news_fetcher import FreeNewsFetcher

fetcher = FreeNewsFetcher()
result = fetcher.fetch_all()
# result: {'total': 10, 'saved': 10, 'stats': {...}}
```

## 📝 数据源详情

### RSS源配置
```python
rss_sources = [
    ('https://www.ithome.com/rss/', '科技', 'IT'),
    ('https://feeds.bbci.co.uk/news/business/rss.xml', '国际', '财经'),
    ('https://feeds.reuters.com/reuters/businessNews', '国际', '财经'),
]
```

### 关键词提取
- 金融: 股票、基金、债券、外汇、黄金
- 加密货币: BTC、ETH、比特币、区块链、DeFi
- AI: AI、人工智能、ChatGPT、大模型
- 政治: 政策、监管、法规、政府

### 情绪分析
- 🚀 强烈看涨: +1.0
- 🟢 看涨: +0.3 ~ +0.9
- ⚪ 中性: -0.2 ~ +0.2
- 🔴 看跌: -0.9 ~ -0.3
- 🔻 强烈看跌: -1.0

## 🔧 故障排除

### SSL错误
部分API可能出现SSL错误，已添加异常处理自动降级。

### 获取为空
- 检查RSS源是否可用
- 检查网络连接
- 查看日志: `logs/free_news.log`

### 重复数据
系统会自动基于标题前20字符去重。

## 📈 扩展计划

1. **添加更多RSS源**
   - 华尔街见闻
   - 财新网
   - 界面新闻

2. **接入NewsAPI**
   - 注册免费账户
   - 配置API密钥
   - 支持多语言新闻

3. **自定义爬虫**
   - 新浪财经
   - 东方财富
   - 雪球

---

**当前状态**: ✅ 基础RSS源正常工作，可获取科技和国际财经新闻
