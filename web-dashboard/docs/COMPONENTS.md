# 组件使用指南

本文档介绍量化交易仪表板中使用的 shadcn-ui 风格组件及其用法。

---

## 目录

- [Button 按钮](#button-按钮)
- [Card 卡片](#card-卡片)
- [Badge 徽章](#badge-徽章)
- [Table 表格](#table-表格)

---

## Button 按钮

多功能按钮组件，支持多种变体和尺寸。

### 基础用法

```html
<!-- 默认按钮 -->
<button class="btn">默认按钮</button>

<!-- 主要按钮 -->
<button class="btn btn-primary">主要按钮</button>

<!-- 次要按钮 -->
<button class="btn btn-secondary">次要按钮</button>

<!-- 幽灵按钮 -->
<button class="btn btn-ghost">幽灵按钮</button>

<!-- 链接按钮 -->
<button class="btn btn-link">链接按钮</button>
```

### 变体

| 变体 | 类名 | 用途 |
|------|------|------|
| 默认 | `.btn` | 一般操作 |
| 主要 | `.btn-primary` | 主要操作，如保存、提交 |
| 次要 | `.btn-secondary` | 次要操作，如取消、返回 |
| 幽灵 | `.btn-ghost` | 低优先级操作，背景透明 |
| 链接 | `.btn-link` | 文字链接样式 |
| 危险 | `.btn-destructive` | 删除、危险操作 |

### 尺寸

```html
<!-- 小尺寸 -->
<button class="btn btn-sm">小按钮</button>

<!-- 默认尺寸 -->
<button class="btn">默认按钮</button>

<!-- 大尺寸 -->
<button class="btn btn-lg">大按钮</button>

<!-- 图标按钮 -->
<button class="btn btn-icon">
  <i class="ti ti-plus"></i>
</button>
```

### 带图标的按钮

```html
<!-- 左侧图标 -->
<button class="btn btn-primary">
  <i class="ti ti-refresh"></i>
  刷新数据
</button>

<!-- 右侧图标 -->
<button class="btn btn-secondary">
  查看详情
  <i class="ti ti-chevron-right"></i>
</button>
```

### 状态

```html
<!-- 加载状态 -->
<button class="btn btn-primary btn-loading" disabled>
  <i class="ti ti-loader-2 ti-spin"></i>
  加载中...
</button>

<!-- 禁用状态 -->
<button class="btn btn-primary" disabled>禁用按钮</button>
```

### 完整示例

```html
<div class="btn-group">
  <button class="btn btn-primary">
    <i class="ti ti-device-floppy"></i>
    保存
  </button>
  <button class="btn btn-secondary">取消</button>
  <button class="btn btn-ghost btn-sm">
    <i class="ti ti-trash"></i>
    删除
  </button>
</div>
```

---

## Card 卡片

用于内容分组的容器组件，支持头部、内容区和底部。

### 基础用法

```html
<div class="card">
  <div class="card-content">
    <h3>卡片标题</h3>
    <p>卡片内容区域...</p>
  </div>
</div>
```

### 带头部的卡片

```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">持仓概览</h3>
    <p class="card-description">实时持仓数据统计</p>
  </div>
  <div class="card-content">
    <!-- 内容 -->
  </div>
</div>
```

### 带底部的卡片

```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">交易信号</h3>
  </div>
  <div class="card-content">
    <!-- 内容 -->
  </div>
  <div class="card-footer">
    <button class="btn btn-secondary btn-sm">查看全部</button>
    <button class="btn btn-primary btn-sm">刷新</button>
  </div>
</div>
```

### 变体

| 变体 | 类名 | 用途 |
|------|------|------|
| 默认 | `.card` | 标准卡片 |
| 可悬停 | `.card-hover` | 带悬停效果 |
| 统计卡片 | `.stat-card` | 数据展示 |
| 指标卡片 | `.metric-card` | 关键指标 |

### 统计卡片示例

```html
<div class="stat-card">
  <div class="stat-header">
    <span class="stat-label">总资产</span>
    <span class="stat-trend up">
      <i class="ti ti-trending-up"></i>
      +2.5%
    </span>
  </div>
  <div class="stat-value">¥1,234,567.89</div>
  <div class="stat-footer">
    <span class="text-muted">较昨日</span>
    <span class="text-success">+¥30,000</span>
  </div>
</div>
```

### 指标卡片示例

```html
<div class="metric-card">
  <div class="metric-icon bg-primary">
    <i class="ti ti-chart-line"></i>
  </div>
  <div class="metric-content">
    <div class="metric-label">今日收益</div>
    <div class="metric-value text-success">+5.67%</div>
  </div>
</div>
```

### 卡片组

```html
<div class="card-grid">
  <div class="card">
    <div class="card-content">卡片 1</div>
  </div>
  <div class="card">
    <div class="card-content">卡片 2</div>
  </div>
  <div class="card">
    <div class="card-content">卡片 3</div>
  </div>
</div>
```

---

## Badge 徽章

用于标记状态、分类或标签的小型组件。

### 基础用法

```html
<!-- 默认徽章 -->
<span class="badge">默认</span>

<!-- 主要徽章 -->
<span class="badge badge-primary">主要</span>

<!-- 次要徽章 -->
<span class="badge badge-secondary">次要</span>
```

### 变体

| 变体 | 类名 | 用途 |
|------|------|------|
| 默认 | `.badge` | 一般标签 |
| 主要 | `.badge-primary` | 主要状态 |
| 次要 | `.badge-secondary` | 次要状态 |
| 成功 | `.badge-success` | 成功、盈利 |
| 警告 | `.badge-warning` | 警告、注意 |
| 危险 | `.badge-danger` | 错误、亏损 |
| 信息 | `.badge-info` | 提示信息 |
| 轮廓 | `.badge-outline` | 边框样式 |

### 交易场景示例

```html
<!-- 信号强度 -->
<span class="badge badge-danger">强买入</span>
<span class="badge badge-success">强卖出</span>
<span class="badge badge-warning">观望</span>

<!-- 持仓状态 -->
<span class="badge badge-success">盈利</span>
<span class="badge badge-danger">亏损</span>
<span class="badge badge-secondary">持平</span>

<!-- 订单状态 -->
<span class="badge badge-primary">已成交</span>
<span class="badge badge-warning">待成交</span>
<span class="badge badge-secondary">已撤销</span>
```

### 尺寸

```html
<!-- 小尺寸 -->
<span class="badge badge-sm">小标签</span>

<!-- 默认尺寸 -->
<span class="badge">默认</span>

<!-- 大尺寸 -->
<span class="badge badge-lg">大标签</span>
```

### 带图标的徽章

```html
<span class="badge badge-success">
  <i class="ti ti-trending-up"></i>
  上涨
</span>

<span class="badge badge-danger">
  <i class="ti ti-trending-down"></i>
  下跌
</span>
```

---

## Table 表格

用于展示结构化数据的表格组件。

### 基础用法

```html
<div class="table-container">
  <table class="table">
    <thead>
      <tr>
        <th>代码</th>
        <th>名称</th>
        <th>价格</th>
        <th>涨跌幅</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>000001</td>
        <td>平安银行</td>
        <td>12.50</td>
        <td class="text-success">+2.5%</td>
      </tr>
    </tbody>
  </table>
</div>
```

### 变体

| 变体 | 类名 | 用途 |
|------|------|------|
| 默认 | `.table` | 标准表格 |
| 条纹 | `.table-striped` | 斑马纹行 |
| 悬停 | `.table-hover` | 行悬停效果 |
| 边框 | `.table-bordered` | 全边框 |
| 紧凑 | `.table-compact` | 紧凑行高 |

### 完整示例

```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">持仓列表</h3>
    <div class="card-actions">
      <button class="btn btn-ghost btn-sm">
        <i class="ti ti-download"></i>
        导出
      </button>
    </div>
  </div>
  <div class="card-content">
    <div class="table-container">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>股票代码</th>
            <th>股票名称</th>
            <th class="text-right">持仓数量</th>
            <th class="text-right">成本价</th>
            <th class="text-right">现价</th>
            <th class="text-right">盈亏</th>
            <th class="text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <span class="font-mono">000001</span>
            </td>
            <td>平安银行</td>
            <td class="text-right">1000</td>
            <td class="text-right">¥12.00</td>
            <td class="text-right">¥12.50</td>
            <td class="text-right text-success">+¥500</td>
            <td class="text-center">
              <button class="btn btn-ghost btn-sm">
                <i class="ti ti-edit"></i>
              </button>
              <button class="btn btn-ghost btn-sm text-danger">
                <i class="ti ti-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
```

### 排序表头

```html
<thead>
  <tr>
    <th class="sortable" data-sort="code">
      代码
      <i class="ti ti-chevron-down sort-icon"></i>
    </th>
    <th class="sortable active" data-sort="name">
      名称
      <i class="ti ti-chevron-up sort-icon"></i>
    </th>
  </tr>
</thead>
```

### 空状态

```html
<div class="table-empty">
  <i class="ti ti-inbox"></i>
  <p>暂无数据</p>
  <button class="btn btn-primary btn-sm">添加数据</button>
</div>
```

### 分页

```html
<div class="table-pagination">
  <div class="pagination-info">
    显示 1-10 条，共 100 条
  </div>
  <div class="pagination-controls">
    <button class="btn btn-ghost btn-sm" disabled>
      <i class="ti ti-chevron-left"></i>
    </button>
    <button class="btn btn-primary btn-sm">1</button>
    <button class="btn btn-ghost btn-sm">2</button>
    <button class="btn btn-ghost btn-sm">3</button>
    <span class="pagination-ellipsis">...</span>
    <button class="btn btn-ghost btn-sm">10</button>
    <button class="btn btn-ghost btn-sm">
      <i class="ti ti-chevron-right"></i>
    </button>
  </div>
</div>
```

---

## 组合示例

### 交易信号卡片

```html
<div class="card">
  <div class="card-header">
    <div class="flex items-center gap-2">
      <span class="badge badge-danger">强买入</span>
      <h3 class="card-title">贵州茅台 (600519)</h3>
    </div>
    <span class="text-muted text-sm">2分钟前</span>
  </div>
  <div class="card-content">
    <div class="grid grid-cols-3 gap-4">
      <div>
        <div class="text-muted text-sm">信号强度</div>
        <div class="text-lg font-semibold">92/100</div>
      </div>
      <div>
        <div class="text-muted text-sm">建议价格</div>
        <div class="text-lg font-semibold">¥1,680.00</div>
      </div>
      <div>
        <div class="text-muted text-sm">预期收益</div>
        <div class="text-lg font-semibold text-success">+8.5%</div>
      </div>
    </div>
  </div>
  <div class="card-footer">
    <button class="btn btn-ghost btn-sm">查看详情</button>
    <div class="flex gap-2">
      <button class="btn btn-secondary btn-sm">忽略</button>
      <button class="btn btn-primary btn-sm">
        <i class="ti ti-check"></i>
        确认交易
      </button>
    </div>
  </div>
</div>
```

### 仪表板指标卡片组

```html
<div class="card-grid grid-cols-4">
  <div class="metric-card">
    <div class="metric-icon bg-primary">
      <i class="ti ti-wallet"></i>
    </div>
    <div class="metric-content">
      <div class="metric-label">总资产</div>
      <div class="metric-value">¥1.2M</div>
    </div>
  </div>
  
  <div class="metric-card">
    <div class="metric-icon bg-success">
      <i class="ti ti-trending-up"></i>
    </div>
    <div class="metric-content">
      <div class="metric-label">今日收益</div>
      <div class="metric-value text-success">+2.5%</div>
    </div>
  </div>
  
  <div class="metric-card">
    <div class="metric-icon bg-warning">
      <i class="ti ti-bell"></i>
    </div>
    <div class="metric-content">
      <div class="metric-label">待处理信号</div>
      <div class="metric-value">5</div>
    </div>
  </div>
  
  <div class="metric-card">
    <div class="metric-icon bg-info">
      <i class="ti ti-chart-pie"></i>
    </div>
    <div class="metric-content">
      <div class="metric-label">持仓数量</div>
      <div class="metric-value">12</div>
    </div>
  </div>
</div>
```

---

## CSS 变量

组件样式基于以下 CSS 变量：

```css
/* 颜色 */
--primary: 221.2 83.2% 53.3%;
--primary-foreground: 210 40% 98%;
--secondary: 210 40% 96.1%;
--secondary-foreground: 222.2 47.4% 11.2%;
--destructive: 0 84.2% 60.2%;
--destructive-foreground: 210 40% 98%;

/* 圆角 */
--radius: 0.5rem;

/* 间距 */
--spacing-1: 0.25rem;
--spacing-2: 0.5rem;
--spacing-3: 0.75rem;
--spacing-4: 1rem;
```

更多主题变量请参考 [THEME.md](./THEME.md)。
