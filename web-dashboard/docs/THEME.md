# 主题定制指南

本文档介绍如何自定义量化交易仪表板的主题样式，包括 CSS 变量、深色/浅色主题切换等。

---

## 目录

- [快速开始](#快速开始)
- [CSS 变量列表](#css-变量列表)
- [深色/浅色主题](#深色浅色主题)
- [自定义主题](#自定义主题)
- [金融配色](#金融配色)

---

## 快速开始

主题样式通过 CSS 变量定义，位于 `static/css/style.css` 文件的开头部分。

```css
:root {
  /* 主题色 */
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  
  /* 背景色 */
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  
  /* 圆角 */
  --radius: 0.5rem;
}
```

---

## CSS 变量列表

### 颜色变量

#### 主题色

| 变量 | HSL 值 | 用途 |
|------|--------|------|
| `--primary` | 221.2 83.2% 53.3% | 主要操作色（蓝色） |
| `--primary-foreground` | 210 40% 98% | 主要色上的文字 |
| `--secondary` | 210 40% 96.1% | 次要操作色 |
| `--secondary-foreground` | 222.2 47.4% 11.2% | 次要色上的文字 |
| `--accent` | 210 40% 96.1% | 强调色 |
| `--accent-foreground` | 222.2 47.4% 11.2% | 强调色上的文字 |

#### 语义色

| 变量 | HSL 值 | 用途 |
|------|--------|------|
| `--destructive` | 0 84.2% 60.2% | 危险/删除操作（红色） |
| `--destructive-foreground` | 210 40% 98% | 危险色上的文字 |
| `--success` | 142.1 76.2% 36.3% | 成功/盈利（绿色） |
| `--success-foreground` | 355.7 100% 97.3% | 成功色上的文字 |
| `--warning` | 38 92% 50% | 警告/注意（黄色） |
| `--warning-foreground` | 48 96% 89% | 警告色上的文字 |
| `--info` | 200 100% 45% | 信息提示（蓝色） |
| `--info-foreground` | 210 40% 98% | 信息色上的文字 |

#### 中性色

| 变量 | HSL 值 | 用途 |
|------|--------|------|
| `--background` | 0 0% 100% | 页面背景 |
| `--foreground` | 222.2 84% 4.9% | 主要文字 |
| `--card` | 0 0% 100% | 卡片背景 |
| `--card-foreground` | 222.2 84% 4.9% | 卡片文字 |
| `--popover` | 0 0% 100% | 弹出层背景 |
| `--popover-foreground` | 222.2 84% 4.9% | 弹出层文字 |
| `--muted` | 210 40% 96.1% | 次要背景 |
| `--muted-foreground` | 215.4 16.3% 46.9% | 次要文字 |
| `--border` | 214.3 31.8% 91.4% | 边框 |
| `--input` | 214.3 31.8% 91.4% | 输入框边框 |
| `--ring` | 221.2 83.2% 53.3% | 聚焦光环 |

### 布局变量

| 变量 | 值 | 用途 |
|------|-----|------|
| `--radius` | 0.5rem | 基础圆角 |
| `--radius-sm` | calc(var(--radius) - 4px) | 小圆角 |
| `--radius-md` | calc(var(--radius) - 2px) | 中圆角 |
| `--radius-lg` | var(--radius) | 大圆角 |
| `--radius-xl` | calc(var(--radius) + 4px) | 超大圆角 |

### 间距变量

| 变量 | 值 | 用途 |
|------|-----|------|
| `--spacing-1` | 0.25rem (4px) | 超小间距 |
| `--spacing-2` | 0.5rem (8px) | 小间距 |
| `--spacing-3` | 0.75rem (12px) | 中间距 |
| `--spacing-4` | 1rem (16px) | 默认间距 |
| `--spacing-5` | 1.25rem (20px) | 大间距 |
| `--spacing-6` | 1.5rem (24px) | 超大间距 |
| `--spacing-8` | 2rem (32px) | 特大间距 |
| `--spacing-10` | 2.5rem (40px) | 超特大间距 |
| `--spacing-12` | 3rem (48px) | 巨大间距 |

### 字体变量

| 变量 | 值 | 用途 |
|------|-----|------|
| `--font-sans` | system-ui, -apple-system, ... | 无衬线字体 |
| `--font-mono` | ui-monospace, SFMono-Regular, ... | 等宽字体 |
| `--font-size-xs` | 0.75rem (12px) | 超小字 |
| `--font-size-sm` | 0.875rem (14px) | 小字 |
| `--font-size-base` | 1rem (16px) | 默认字 |
| `--font-size-lg` | 1.125rem (18px) | 大字 |
| `--font-size-xl` | 1.25rem (20px) | 超大字 |
| `--font-size-2xl` | 1.5rem (24px) | 特大字 |

### 阴影变量

| 变量 | 值 | 用途 |
|------|-----|------|
| `--shadow-sm` | 0 1px 2px 0 rgb(0 0 0 / 0.05) | 小阴影 |
| `--shadow` | 0 1px 3px 0 rgb(0 0 0 / 0.1) | 默认阴影 |
| `--shadow-md` | 0 4px 6px -1px rgb(0 0 0 / 0.1) | 中阴影 |
| `--shadow-lg` | 0 10px 15px -3px rgb(0 0 0 / 0.1) | 大阴影 |
| `--shadow-xl` | 0 20px 25px -5px rgb(0 0 0 / 0.1) | 超大阴影 |

---

## 深色/浅色主题

### 主题切换实现

系统支持深色和浅色两种主题，通过 `data-theme` 属性切换。

```html
<!-- 浅色主题（默认） -->
<html data-theme="light">

<!-- 深色主题 -->
<html data-theme="dark">
```

### CSS 定义

```css
:root {
  /* 浅色主题变量 */
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;
  --popover: 0 0% 100%;
  --popover-foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96.1%;
  --accent-foreground: 222.2 47.4% 11.2%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 221.2 83.2% 53.3%;
  --radius: 0.5rem;
}

[data-theme="dark"] {
  /* 深色主题变量 */
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --card: 222.2 84% 4.9%;
  --card-foreground: 210 40% 98%;
  --popover: 222.2 84% 4.9%;
  --popover-foreground: 210 40% 98%;
  --primary: 217.2 91.2% 59.8%;
  --primary-foreground: 222.2 47.4% 11.2%;
  --secondary: 217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;
  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;
  --accent: 217.2 32.6% 17.5%;
  --accent-foreground: 210 40% 98%;
  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;
  --border: 217.2 32.6% 17.5%;
  --input: 217.2 32.6% 17.5%;
  --ring: 224.3 76.3% 48%;
}
```

### JavaScript 切换

```javascript
// 切换主题
function toggleTheme() {
  const html = document.documentElement;
  const currentTheme = html.getAttribute('data-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', newTheme);
  
  // 保存到本地存储
  localStorage.setItem('theme', newTheme);
}

// 初始化主题
function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = savedTheme || (prefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', theme);
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', initTheme);
```

### 主题切换按钮

```html
<button class="btn btn-ghost btn-icon" onclick="toggleTheme()">
  <i class="ti ti-sun" data-theme-icon="light"></i>
  <i class="ti ti-moon" data-theme-icon="dark" style="display: none;"></i>
</button>
```

---

## 自定义主题

### 创建自定义主题

在 `:root` 或 `[data-theme="custom"]` 中定义自定义变量：

```css
[data-theme="custom"] {
  /* 主色调：紫色 */
  --primary: 270 60% 50%;
  --primary-foreground: 0 0% 100%;
  
  /* 背景：深蓝灰 */
  --background: 220 20% 10%;
  --foreground: 220 10% 90%;
  
  /* 卡片：稍浅的蓝灰 */
  --card: 220 15% 15%;
  --card-foreground: 220 10% 90%;
  
  /* 强调色：青色 */
  --accent: 180 70% 45%;
  --accent-foreground: 220 20% 10%;
  
  /* 圆角：更大 */
  --radius: 0.75rem;
}
```

### 动态主题切换

```javascript
// 应用自定义主题
function applyCustomTheme(primaryHue) {
  const root = document.documentElement;
  root.style.setProperty('--primary', `${primaryHue} 80% 50%`);
}

// 使用：设置主色调为绿色
applyCustomTheme(142);
```

---

## 金融配色

针对金融交易场景，提供专门的配色方案。

### A股配色（红涨绿跌）

```css
:root {
  /* 上涨 - 红色 */
  --rise: 0 80% 55%;
  --rise-foreground: 0 0% 100%;
  
  /* 下跌 - 绿色 */
  --fall: 142 70% 40%;
  --fall-foreground: 0 0% 100%;
  
  /* 持平 - 灰色 */
  --flat: 220 10% 60%;
  --flat-foreground: 220 10% 20%;
}

/* 使用示例 */
.price-rise {
  color: hsl(var(--rise));
}

.price-fall {
  color: hsl(var(--fall));
}

.price-flat {
  color: hsl(var(--flat));
}
```

### 港股/美股配色（绿涨红跌）

```css
:root {
  /* 上涨 - 绿色 */
  --rise: 142 70% 40%;
  --rise-foreground: 0 0% 100%;
  
  /* 下跌 - 红色 */
  --fall: 0 80% 55%;
  --fall-foreground: 0 0% 100%;
}
```

### 完整金融配色方案

```css
:root {
  /* ===== 基础色 ===== */
  --bg-primary: 0 0% 100%;
  --bg-secondary: 210 40% 96.1%;
  --bg-tertiary: 210 30% 93%;
  
  /* ===== 文字色 ===== */
  --text-primary: 222.2 84% 4.9%;
  --text-secondary: 215.4 16.3% 46.9%;
  --text-tertiary: 215 20% 55%;
  
  /* ===== 涨跌色（A股） ===== */
  --stock-up: 0 80% 55%;           /* 红色 */
  --stock-down: 142 70% 40%;       /* 绿色 */
  --stock-neutral: 220 10% 60%;    /* 灰色 */
  
  /* ===== 信号强度 ===== */
  --signal-strong-buy: 0 80% 55%;   /* 强买入 - 红 */
  --signal-buy: 0 60% 65%;          /* 买入 - 浅红 */
  --signal-neutral: 220 10% 60%;    /* 中性 - 灰 */
  --signal-sell: 142 60% 45%;       /* 卖出 - 浅绿 */
  --signal-strong-sell: 142 70% 40%; /* 强卖出 - 绿 */
  
  /* ===== 状态色 ===== */
  --status-success: 142 76% 36%;
  --status-warning: 38 92% 50%;
  --status-error: 0 84% 60%;
  --status-info: 200 100% 45%;
  
  /* ===== 图表色 ===== */
  --chart-line: 221.2 83.2% 53.3%;
  --chart-area: 221.2 83.2% 53.3% / 0.2;
  --chart-grid: 214.3 31.8% 91.4%;
  --chart-tooltip-bg: 222.2 84% 4.9%;
  --chart-tooltip-text: 210 40% 98%;
}

[data-theme="dark"] {
  /* ===== 基础色 ===== */
  --bg-primary: 222.2 84% 4.9%;
  --bg-secondary: 217.2 32.6% 17.5%;
  --bg-tertiary: 217.2 25% 22%;
  
  /* ===== 文字色 ===== */
  --text-primary: 210 40% 98%;
  --text-secondary: 215 20% 65%;
  --text-tertiary: 215 15% 55%;
  
  /* ===== 涨跌色（A股） ===== */
  --stock-up: 0 70% 60%;           /* 红色 */
  --stock-down: 142 60% 50%;       /* 绿色 */
  --stock-neutral: 215 15% 50%;    /* 灰色 */
  
  /* ===== 图表色 ===== */
  --chart-grid: 217.2 32.6% 25%;
}
```

### 使用示例

```html
<!-- 股票价格 -->
<span class="stock-price" data-change="up">
  ¥12.50
  <i class="ti ti-arrow-up"></i>
  +2.5%
</span>

<style>
.stock-price[data-change="up"] {
  color: hsl(var(--stock-up));
}
.stock-price[data-change="down"] {
  color: hsl(var(--stock-down));
}
.stock-price[data-change="neutral"] {
  color: hsl(var(--stock-neutral));
}
</style>
```

---

## 主题调试

### 查看当前主题变量

在浏览器控制台运行：

```javascript
// 获取所有 CSS 变量
function getCSSVariables() {
  const styles = getComputedStyle(document.documentElement);
  const variables = {};
  
  for (let i = 0; i < styles.length; i++) {
    const prop = styles[i];
    if (prop.startsWith('--')) {
      variables[prop] = styles.getPropertyValue(prop).trim();
    }
  }
  
  return variables;
}

console.table(getCSSVariables());
```

### 实时预览主题

```javascript
// 实时修改主题变量
function setThemeVariable(name, value) {
  document.documentElement.style.setProperty(name, value);
}

// 示例：修改主色调
setThemeVariable('--primary', '200 80% 50%');
```

---

## 最佳实践

1. **使用 HSL 格式**：便于调整饱和度和亮度
2. **保持对比度**：文字和背景对比度至少 4.5:1
3. **一致性**：整个应用使用相同的配色逻辑
4. **可访问性**：考虑色盲用户，不要仅用颜色传达信息
5. **性能**：避免在动画中频繁修改 CSS 变量
