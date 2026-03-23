# 🤖 自动化推文生成系统

> 每日自动获取BTC、黄金、原油、特斯拉、微软价格，自动生成推文
> 无需人工干预，一键生成，三种风格可选

---

## 📋 系统功能

### 自动获取数据
- ✅ BTC价格（币安API）
- ✅ 黄金价格（Yahoo Finance）
- ✅ 原油价格（WTI，Yahoo Finance）
- ✅ 特斯拉股价（Yahoo Finance）
- ✅ 微软股价（Yahoo Finance）

### 自动生成推文（三种风格）
- **版本A**：硬核痞气版（推荐）
- **版本B**：街头江湖版
- **版本C**：冷静分析版

---

## 🚀 使用方法

### 方法一：手动运行

```bash
# 运行推文生成器
python3 auto_tweet_generator.py
```

输出示例：
```
============================================================
  自动化推文生成系统
  日期: 2026-03-23 14:30
============================================================

【获取实时价格】...
  BTC: $69,500.00
  黄金: $2,180.50
  石油: $81.30
  特斯拉: $175.40
  微软: $425.80

【生成推文】...
  版本A已保存: tweets_generated/tweet_0323_A.txt
  版本B已保存: tweets_generated/tweet_0323_B.txt
  版本C已保存: tweets_generated/tweet_0323_C.txt
```

### 方法二：定时自动运行（推荐）

添加定时任务（每天自动生成）：

```bash
# 编辑crontab
crontab -e

# 添加以下行（每天北京时间20:00运行）
0 20 * * * /Users/mac/.openclaw/workspace/quant-trading/run_daily_tweet.sh
```

或手动运行定时脚本：

```bash
bash run_daily_tweet.sh
```

---

## 📁 输出文件

生成的推文保存在：
```
tweets_generated/
├── tweet_0323_A.txt  # 硬核痞气版
├── tweet_0323_B.txt  # 街头江湖版
└── tweet_0323_C.txt  # 冷静分析版
```

---

## 📝 发布流程

### 步骤1：生成推文
```bash
python3 auto_tweet_generator.py
```

### 步骤2：查看并选择版本
```bash
# 查看最新生成的推文
cat tweets_generated/tweet_0323_A.txt
```

### 步骤3：发布推文
```bash
# 方法1：直接发布
python3 post_tweet.py --file tweets_generated/tweet_0323_A.txt

# 方法2：复制内容手动发布
# 复制生成的内容到Twitter
```

---

## 🔄 完全自动化（可选）

如需完全自动化（生成+自动发布），修改 `run_daily_tweet.sh`：

取消注释以下行：
```bash
# 自动发送推文
LATEST_A=$(ls -t "$TWEET_DIR"/tweet_*_A.txt 2>/dev/null | head -1)
if [ -n "$LATEST_A" ]; then
    python3 post_tweet.py --file "$LATEST_A"
fi
```

⚠️ **警告**：完全自动化前，请确保推文内容符合您的要求，建议先手动审核几次。

---

## 🛠️ 故障排除

### 问题1：价格获取失败
**原因**：网络问题或API限制
**解决**：
- 检查网络连接
- 检查代理设置（`http_proxy`）
- 稍后重试

### 问题2：推文生成失败
**原因**：Python环境问题
**解决**：
```bash
# 检查Python版本
python3 --version

# 确保urllib可用
python3 -c "import urllib.request; print('OK')"
```

### 问题3：推文太长
**解决**：系统已自动优化，如仍超长，使用Thread形式发布

---

## 📊 日志查看

```bash
# 查看生成日志
tail -f logs/tweet_generator.log

# 查看所有历史推文
ls -la tweets_generated/
```

---

## 🎯 使用建议

### 每日工作流程
1. **定时生成**（自动）：每天20:00自动生成
2. **人工审核**（推荐）：查看生成的推文，确认无误
3. **选择发布**：选择A/B/C版本，或组合修改
4. **一键发布**：使用post_tweet.py发布

### 三种版本使用场景
- **版本A（硬核痞气）**：适合表达强烈观点，吸引眼球
- **版本B（街头江湖）**：适合口语化表达，接地气
- **版本C（冷静分析）**：适合专业分析，建立权威形象

---

## ⚠️ 免责声明

1. 系统自动获取的价格可能存在延迟
2. 生成的推文仅供参考，发布前请人工审核
3. 投资有风险，推文内容不构成投资建议
4. 建议先手动运行几次，确认无误后再开启全自动模式

---

## 🔧 自定义配置

如需修改推文风格，编辑 `auto_tweet_generator.py`：

- 修改 `generate_template_a()` 函数 → 修改版本A风格
- 修改 `generate_template_b()` 函数 → 修改版本B风格
- 修改 `generate_template_c()` 函数 → 修改版本C风格

---

**系统已就绪！运行 `python3 auto_tweet_generator.py` 开始生成推文！** 🚀
