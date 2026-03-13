# 量化交易系统 Web 仪表板

一个基于 Flask 的量化交易系统 Web 界面，支持实时市场数据、交易信号、持仓管理和绩效报告。

## ✨ UI 升级 v3.0

我们完成了基于 **shadcn-ui** 和 **Tabler Icons** 的全新 UI 升级，带来更现代、更专业的交易界面体验。

### 新设计亮点

- **shadcn-ui 组件库** - 基于 Radix UI 的无头组件，完全可定制
- **Tabler Icons** - 简洁现代的开源图标库，2000+ 专业图标
- **深色主题** - 专为长时间盯盘设计的深色模式，减少眼部疲劳
- **数据可视化** - 全新图表设计，信息层次更清晰
- **响应式布局** - 完美适配桌面、平板和手机
- **专业配色** - 金融级专业配色方案，涨跌一目了然
- **流畅动效** - 微妙的过渡动画，提升交互体验

### 设计参考

- [shadcn-ui](https://ui.shadcn.com/) - 现代 React 组件库设计规范
- [Tabler Icons](https://tabler-icons.io/) - 开源图标库
- [Tabler Dashboard](https://tabler.io/) - 仪表板设计灵感

### 组件列表

| 组件 | 描述 | 状态 |
|------|------|------|
| `Button` | 多变体按钮（默认、次要、幽灵、链接） | ✅ 已集成 |
| `Card` | 卡片容器，支持头部、内容、底部区域 | ✅ 已集成 |
| `Badge` | 标签徽章，支持多种颜色变体 | ✅ 已集成 |
| `Table` | 数据表格，支持排序、筛选、分页 | ✅ 已集成 |
| `Dialog` | 模态对话框，支持 alert/confirm/prompt | ✅ 已集成 |
| `Dropdown` | 下拉菜单，支持键盘导航 | ✅ 已集成 |
| `Tabs` | 标签页切换，支持多种样式 | ✅ 已集成 |
| `Toast` | 消息提示，支持6种位置 | ✅ 已集成 |

### 设计预览

> 📸 截图占位符 - 仪表板总览 v3.0
> ![Dashboard Overview v3.0](./docs/screenshots/dashboard-v3-overview.png)

> 📸 截图占位符 - 市场数据页面 v3.0
> ![Market Data v3.0](./docs/screenshots/market-v3-data.png)

> 📸 截图占位符 - 交易信号页面 v3.0
> ![Trading Signals v3.0](./docs/screenshots/signals-v3.png)

> 📸 截图占位符 - 持仓管理页面 v3.0
> ![Portfolio v3.0](./docs/screenshots/portfolio-v3.png)

> 📸 截图占位符 - 组件展示
> ![Components Showcase](./docs/screenshots/components-showcase.png)

更多截图请查看 [docs/screenshots/](./docs/screenshots/) 目录。

---

## 📚 文档

- [组件使用指南](./docs/COMPONENTS.md) - Button, Card, Badge, Table 等组件详细用法
- [主题定制指南](./docs/THEME.md) - CSS 变量、深色/浅色主题切换
- [UI 设计规范 v2.0](./docs/UI_GUIDE.md) - 旧版设计规范（参考）
- [更新日志](./CHANGELOG.md) - 版本变更记录

---

## 功能特性

- 📊 实时市场数据展示
- 📈 交易信号监控
- 💼 持仓管理
- 🔄 交易执行
- 📋 绩效报告生成
- 📱 响应式设计（支持移动端）
- 🎨 全新深色主题 UI

## 技术栈

- **后端**: Python Flask
- **前端**: HTML5 + Vanilla JS
- **UI 框架**: shadcn-ui 设计系统 + 自定义 CSS 变量
- **图标**: Tabler Icons
- **数据库**: SQLite
- **图表**: Chart.js / ECharts

## 快速启动

### 1. 安装依赖

```bash
cd ~/.openclaw/workspace/quant-trading/web-dashboard
pip install -r requirements.txt
```

### 2. 启动应用

```bash
python app.py
```

### 3. 访问系统

打开浏览器访问: http://localhost:5000

默认登录账号:
- 用户名: `admin`
- 密码: `admin123`

## 页面说明

| 页面 | 路径 | 功能 |
|------|------|------|
| 登录 | /login | 用户认证 |
| 仪表板 | / | 资产总览、今日盈亏、快速操作 |
| 市场数据 | /market | 实时价格、K线图、涨跌幅排行 |
| 交易信号 | /signals | 信号列表、强度评分、回测结果 |
| 持仓管理 | /portfolio | 持仓列表、盈亏分析、资产配置 |
| 交易执行 | /trade | 买卖下单、订单管理 |
| 报告 | /reports | 收益曲线、绩效指标、导出功能 |

## 开发文档

- [组件使用指南](./docs/COMPONENTS.md) - shadcn-ui 组件使用说明
- [主题定制指南](./docs/THEME.md) - CSS 变量和主题切换
- [UI 设计规范 v2.0](./docs/UI_GUIDE.md) - 旧版设计规范（参考）
- [更新日志](./CHANGELOG.md) - 版本变更记录

## 数据库配置

系统使用 SQLite 数据库，默认路径:
```
~/.openclaw/workspace/quant-trading/data/market_data.db
```

相关数据表:
- `realtime_price` - 实时价格数据
- `price_data` - K线历史数据
- `factor_scores` - 因子评分
- `positions` - 持仓数据
- `orders` - 订单数据
- `trade_history` - 交易历史

## 开发说明

### 目录结构

```
web-dashboard/
├── app.py              # Flask 主应用
├── requirements.txt    # Python 依赖
├── README.md          # 说明文档
├── CHANGELOG.md       # 更新日志
├── docs/              # 文档目录
│   ├── UI_GUIDE.md    # UI设计规范
│   └── screenshots/   # 截图目录
├── templates/         # HTML 模板
│   ├── base.html      # 基础模板
│   ├── login.html     # 登录页
│   ├── dashboard.html # 仪表板
│   ├── market.html    # 市场数据
│   ├── signals.html   # 交易信号
│   ├── portfolio.html # 持仓管理
│   ├── trade.html     # 交易执行
│   └── reports.html   # 报告页面
└── static/            # 静态资源
    ├── css/
    │   └── style.css  # 自定义样式
    └── js/
        └── app.js     # 前端交互
```

### 自定义配置

可以在 `app.py` 中修改以下配置:

```python
# 数据库路径
DATABASE_PATH = os.path.expanduser('~/.openclaw/workspace/quant-trading/data/market_data.db')

# 会话密钥 (生产环境请修改)
app.secret_key = 'your-secret-key-here'

# 调试模式
app.config['DEBUG'] = True
```

## 安全提示

⚠️ 默认账号密码仅用于演示，生产环境请:
1. 修改默认密码
2. 使用环境变量存储密钥
3. 启用 HTTPS
4. 添加验证码防止暴力破解

## 许可证

MIT License
