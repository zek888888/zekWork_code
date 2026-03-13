# UI 设计规范

本文档定义了量化交易仪表板的 UI 设计系统，包括颜色方案、CSS 变量和组件规范。

## 目录

- [颜色方案](#颜色方案)
- [CSS 变量](#css-变量)
- [排版规范](#排版规范)
- [组件规范](#组件规范)
- [布局规范](#布局规范)

---

## 颜色方案

### 主色调

| 颜色名称 | 色值 | 用途 |
|---------|------|------|
| 主色蓝 | `#3B82F6` | 主要按钮、链接、强调 |
| 主色深蓝 | `#1E40AF` | 悬停状态、激活状态 |
| 主色浅蓝 | `#60A5FA` | 高亮、选中状态 |

### 功能色

| 颜色名称 | 色值 | 用途 |
|---------|------|------|
| 上涨红 | `#EF4444` | 价格上涨、盈利 |
| 下跌绿 | `#10B981` | 价格下跌、亏损 |
| 警告黄 | `#F59E0B` | 警告提示、注意 |
| 危险红 | `#DC2626` | 错误、删除操作 |
| 成功绿 | `#059669` | 成功提示、买入 |

### 中性色

| 颜色名称 | 色值 | 用途 |
|---------|------|------|
| 背景色 | `#0F172A` | 页面背景 |
| 卡片背景 | `#1E293B` | 卡片、面板背景 |
| 边框色 | `#334155` | 边框、分割线 |
| 主文字 | `#F1F5F9` | 主要文字 |
| 次文字 | `#94A3B8` | 次要文字、标签 |
| 禁用色 | `#475569` | 禁用状态 |

### 图表配色

```css
--chart-primary: #3B82F6;    /* 主要数据线 */
--chart-secondary: #8B5CF6;  /* 辅助线 */
--chart-tertiary: #10B981;   /* 第三色 */
--chart-volume: #64748B;     /* 成交量 */
--chart-grid: #334155;       /* 网格线 */
```

---

## CSS 变量

### 基础变量

```css
:root {
  /* 颜色系统 */
  --color-primary: #3B82F6;
  --color-primary-dark: #1E40AF;
  --color-primary-light: #60A5FA;
  
  --color-up: #EF4444;
  --color-down: #10B981;
  --color-warning: #F59E0B;
  --color-danger: #DC2626;
  --color-success: #059669;
  
  --color-bg: #0F172A;
  --color-card: #1E293B;
  --color-border: #334155;
  --color-text: #F1F5F9;
  --color-text-secondary: #94A3B8;
  --color-disabled: #475569;
  
  /* 间距系统 */
  --space-xs: 0.25rem;   /* 4px */
  --space-sm: 0.5rem;    /* 8px */
  --space-md: 1rem;      /* 16px */
  --space-lg: 1.5rem;    /* 24px */
  --space-xl: 2rem;      /* 32px */
  --space-2xl: 3rem;     /* 48px */
  
  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
  
  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);
  --shadow-glow: 0 0 20px rgba(59, 130, 246, 0.3);
  
  /* 过渡 */
  --transition-fast: 150ms ease;
  --transition-base: 250ms ease;
  --transition-slow: 350ms ease;
}
```

### 使用示例

```css
/* 卡片样式 */
.card {
  background-color: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  box-shadow: var(--shadow-md);
  transition: box-shadow var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-lg);
}

/* 价格显示 */
.price-up {
  color: var(--color-up);
  font-weight: 600;
}

.price-down {
  color: var(--color-down);
  font-weight: 600;
}

/* 按钮样式 */
.btn-primary {
  background-color: var(--color-primary);
  color: white;
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
  transition: background-color var(--transition-fast);
}

.btn-primary:hover {
  background-color: var(--color-primary-dark);
}
```

---

## 排版规范

### 字体栈

```css
--font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--font-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
```

### 字体大小

| 级别 | 大小 | 行高 | 用途 |
|-----|------|------|------|
| H1 | 2rem (32px) | 1.2 | 页面标题 |
| H2 | 1.5rem (24px) | 1.3 | 区块标题 |
| H3 | 1.25rem (20px) | 1.4 | 卡片标题 |
| H4 | 1.125rem (18px) | 1.4 | 小标题 |
| Body | 1rem (16px) | 1.5 | 正文 |
| Small | 0.875rem (14px) | 1.5 | 辅助文字 |
| XSmall | 0.75rem (12px) | 1.5 | 标签、时间 |

### 字重

```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

---

## 组件规范

### 卡片 (Card)

```css
.card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 1.125rem;
  font-weight: var(--font-semibold);
  color: var(--color-text);
}
```

### 按钮 (Button)

| 类型 | 背景 | 文字 | 悬停 |
|-----|------|------|------|
| Primary | `--color-primary` | white | `--color-primary-dark` |
| Secondary | transparent | `--color-primary` | `--color-card` |
| Danger | `--color-danger` | white | `#B91C1C` |
| Ghost | transparent | `--color-text` | `--color-card` |

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  font-weight: var(--font-medium);
  transition: all var(--transition-fast);
  cursor: pointer;
  border: none;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background: var(--color-primary-dark);
}
```

### 表单输入 (Input)

```css
.input {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: 1rem;
  transition: border-color var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input::placeholder {
  color: var(--color-text-secondary);
}
```

### 表格 (Table)

```css
.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: var(--space-md);
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.table th {
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.table tbody tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.table .cell-up {
  color: var(--color-up);
}

.table .cell-down {
  color: var(--color-down);
}
```

### 标签 (Badge)

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: var(--font-medium);
}

.badge-success {
  background: rgba(5, 150, 105, 0.2);
  color: var(--color-success);
}

.badge-warning {
  background: rgba(245, 158, 11, 0.2);
  color: var(--color-warning);
}

.badge-danger {
  background: rgba(220, 38, 38, 0.2);
  color: var(--color-danger);
}
```

### 数据指标 (Metric)

```css
.metric {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.metric-label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.metric-value {
  font-size: 1.5rem;
  font-weight: var(--font-bold);
  color: var(--color-text);
}

.metric-change {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.875rem;
}

.metric-change.up {
  color: var(--color-up);
}

.metric-change.down {
  color: var(--color-down);
}
```

---

## 布局规范

### 页面结构

```
┌─────────────────────────────────────┐
│  Sidebar    │  Header               │
│  (200px)    ├───────────────────────┤
│             │                       │
│             │  Main Content         │
│             │  (flex: 1)            │
│             │                       │
│             │                       │
└─────────────┴───────────────────────┘
```

### 网格系统

```css
/* 12列网格 */
.grid {
  display: grid;
  gap: var(--space-lg);
}

.grid-cols-1 { grid-template-columns: repeat(1, 1fr); }
.grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
.grid-cols-4 { grid-template-columns: repeat(4, 1fr); }

/* 响应式 */
@media (max-width: 1024px) {
  .grid-cols-4 { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .grid-cols-3,
  .grid-cols-4 { grid-template-columns: 1fr; }
}
```

### 间距规范

- 页面内边距: `var(--space-lg)` (24px)
- 卡片间距: `var(--space-lg)` (24px)
- 组件内部间距: `var(--space-md)` (16px)
- 文字间距: `var(--space-sm)` (8px)

---

## 动画规范

### 过渡效果

```css
/* 悬停效果 */
.hover-lift {
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* 脉冲效果 - 用于实时数据指示 */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* 闪烁效果 - 用于价格更新 */
@keyframes flash {
  0% { background-color: rgba(59, 130, 246, 0.3); }
  100% { background-color: transparent; }
}

.flash-update {
  animation: flash 0.5s ease-out;
}
```

---

## 响应式断点

| 断点 | 宽度 | 说明 |
|-----|------|------|
| sm | 640px | 小屏手机 |
| md | 768px | 大屏手机/小平板 |
| lg | 1024px | 平板/小笔记本 |
| xl | 1280px | 桌面显示器 |
| 2xl | 1536px | 大屏显示器 |

```css
/* 使用示例 */
@media (min-width: 768px) {
  .sidebar {
    display: block;
  }
}

@media (max-width: 767px) {
  .sidebar {
    display: none;
  }
}
```

---

## 最佳实践

1. **始终使用 CSS 变量** - 便于主题切换和统一维护
2. **保持对比度** - 文字与背景对比度至少 4.5:1
3. **限制颜色使用** - 同一页面不超过 3 种主色
4. **统一间距** - 使用变量系统中的间距值
5. **添加过渡动画** - 所有交互元素都应有过渡效果
6. **测试响应式** - 在多个断点测试布局

---

## 相关资源

- [CHANGELOG.md](../CHANGELOG.md) - 更新日志
- [README.md](../README.md) - 项目说明
