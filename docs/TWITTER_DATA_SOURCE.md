# Twitter 数据源接入方案

## 当前状态

已配置 Twitter API 凭证，但免费层级（Essential Access）有以下限制：
- 每月 1,500 条读取限制
- 无法访问某些端点
- 实际使用需要付费订阅（Basic $100/月 或 Pro $5000/月）

## 可选方案

### 方案1：Twitter API 付费订阅（推荐正式环境）

**Basic 订阅** ($100/月)
- 每月 10,000 条读取
- 支持所有读取端点
- 适合小型项目

**Pro 订阅** ($5000/月)
- 每月 1,000,000 条读取
- 完整功能支持

**配置步骤：**
1. 访问 https://developer.twitter.com/en/portal/products
2. 订阅 Basic ($100/月)
3. 使用现有凭证即可访问

### 方案2：Nitter 镜像（免费但不稳定）

Nitter 是 Twitter 的镜像站点，无需登录即可查看公开推文。

**优点：**
- 完全免费
- 无需 API 密钥

**缺点：**
- 不稳定，经常被封锁
- 需要维护可用实例列表

**当前配置的 Nitter 实例：**
- https://nitter.net
- https://nitter.cz
- https://nitter.it

### 方案3：第三方数据服务

**推荐服务：**
- **RapidAPI Twitter API** - 按量付费，$0.001/请求
- **SocialSearch.io** - 加密货币KOL专用数据
- **LunarCrush** - 社交媒体情绪分析专业平台

### 方案4：手动采集 + 数据库维护

适用于监控少量KOL（<20人）的场景：
- 定期手动复制推文内容
- 或使用浏览器插件采集

## 当前演示数据

由于 API 限制，当前使用 5 条高质量模拟数据演示功能：

| 用户 | 内容 | 分析结果 |
|------|------|---------|
| @cz_binance | 币安Launchpool新消息 | 🟢 利好BNB |
| @xiaomustock | BTC突破阻力位 | 🟢 利好BTC |
| @thankUcrypto | 交易所风险提示 | 🔴 利空市场 |
| @dotyyds1234 | DOT生态发展 | 🟢 利好DOT |
| @monkeyjiang | 市场风险提醒 | ⚪ 中性提醒 |

## 接入正式数据步骤

1. **选择数据源**
   - 预算充足：Twitter API Basic ($100/月)
   - 预算有限：Nitter + 备用方案
   - 专业需求：第三方数据服务

2. **配置凭证**
   ```bash
   # 编辑 .env.twitter 文件
   TWITTER_BEARER_TOKEN=your_token_here
   ```

3. **测试连接**
   ```python
   python config-layer/twitter_api_client.py
   ```

4. **启动定时任务**
   ```bash
   python cron/twitter_cron.py
   ```

## 成本对比

| 方案 | 月成本 | 可靠性 | 适用场景 |
|------|--------|--------|---------|
| Twitter API Basic | $100 | ⭐⭐⭐⭐⭐ | 生产环境 |
| Twitter API Pro | $5000 | ⭐⭐⭐⭐⭐ | 大规模应用 |
| Nitter | $0 | ⭐⭐ | 个人/测试 |
| RapidAPI | ~$50 | ⭐⭐⭐⭐ | 中等规模 |
| 第三方服务 | $200-500 | ⭐⭐⭐⭐ | 专业分析 |

## 建议

**当前阶段（演示/测试）：**
- 使用模拟数据展示功能
- 考虑申请 Twitter API Basic 试用

**生产环境：**
- 建议订阅 Twitter API Basic ($100/月)
- 或选择 RapidAPI 按量付费
- 预算充足可直接使用专业数据服务
