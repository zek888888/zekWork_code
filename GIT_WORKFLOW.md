# Git 工作流建议 - 量化交易系统

> 建议的工作流程：本地开发 → 日终统一提交 → GitHub

---

## 📋 推荐工作流

### 日常开发流程

```bash
# 1. 开始工作前 - 拉取最新代码（仅每天第一次）
git pull origin main

# 2. 开发过程中 - 频繁本地提交
git add -A
git commit -m "[feat/fix/docs] 描述修改内容"

# 3. 开发过程中 - 不需要推送到GitHub，继续本地开发...
# ... 修改代码 ...
git add -A
git commit -m "[feat] 添加XXX功能"

# ... 继续开发 ...
git add -A
git commit -m "[fix] 修复XXX问题"

# 4. 日终/阶段性完成 - 统一推送GitHub
git push origin main
```

---

## 🎯 提交信息规范

```
[类型] 简短描述

详细说明（可选）
```

**类型说明**:
- `[feat]` - 新功能
- `[fix]` - Bug修复
- `[docs]` - 文档更新
- `[refactor]` - 代码重构
- `[test]` - 测试相关
- `[chore]` - 构建/配置

**示例**:
```bash
git commit -m "[feat] 新闻聚焦板块添加人工获取按钮"
git commit -m "[fix] 修复新闻去重逻辑问题"
git commit -m "[docs] 更新README使用说明"
```

---

## 🔄 本地开发常用命令

```bash
# 查看当前修改状态
git status

# 查看提交历史（最近10条）
git log --oneline -10

# 对比修改内容
git diff

# 撤销未提交的修改（慎用）
git checkout -- 文件名

# 查看哪些文件被修改
git diff --stat
```

---

## 📤 日终提交流程

### 步骤1: 确认所有修改
```bash
git status
```

### 步骤2: 添加所有修改到暂存区
```bash
git add -A
# 或只添加特定文件
git add 文件名
```

### 步骤3: 提交到本地仓库
```bash
# 单条提交
git commit -m "[类型] 描述"

# 或查看所有修改后提交
git commit -m "[feat] 今日开发内容总结

- 功能1：XXX
- 功能2：XXX
- 修复：XXX"
```

### 步骤4: 推送到GitHub
```bash
# 先拉取远程最新（防止冲突）
git pull origin main

# 推送到GitHub
git push origin main
```

---

## ⚠️ 注意事项

### 不要提交的文件
以下文件只保留在本地，**不要提交**到GitHub：

```
data/*.db              # 数据库文件（包含敏感数据）
*.log                  # 日志文件
.env                   # 环境变量（包含API密钥）
*.pem, *.key           # 密钥文件
```

已在 `.gitignore` 中配置，通常会自动忽略。

### 提交前检查
```bash
# 检查要提交的内容
git diff --cached --stat

# 确认无误后再提交
```

---

## 🆘 常见问题

### Q: 如何撤销上次提交（未推送）？
```bash
# 撤销提交，保留修改
git reset --soft HEAD~1

# 撤销提交，丢弃修改（慎用）
git reset --hard HEAD~1
```

### Q: 如何修改上次提交信息？
```bash
git commit --amend -m "新的提交信息"
```

### Q: 推送时遇到冲突怎么办？
```bash
# 1. 先拉取远程代码
git pull origin main

# 2. 解决冲突（如果有）
# 编辑冲突文件，保留需要的代码

# 3. 添加解决后的文件
git add -A

# 4. 提交合并
git commit -m "[merge] 解决冲突"

# 5. 推送
git push origin main
```

### Q: 如何查看某个文件的修改历史？
```bash
git log -p -- 文件名
```

---

## 💡 最佳实践

1. **频繁本地提交** - 小步快跑，每次完成一个小功能就提交
2. **写好提交信息** - 方便日后追溯和回滚
3. **日终统一推送** - 每天工作结束前推送一次到GitHub
4. **重要节点打标签** - 版本发布时打标签
5. **不要提交敏感数据** - API密钥、数据库等不要提交

---

## 📊 示例工作日

```bash
# 09:00 - 开始工作，拉取最新代码
git pull origin main

# 10:30 - 完成新闻模块功能1
git add -A
git commit -m "[feat] 新闻模块添加时间筛选功能"

# 12:00 - 完成新闻模块功能2
git add -A
git commit -m "[feat] 新闻模块添加情绪筛选功能"

# 14:00 - 修复发现的Bug
git add -A
git commit -m "[fix] 修复新闻去重逻辑错误"

# 16:00 - 更新文档
git add -A
git commit -m "[docs] 更新新闻模块使用说明"

# 18:00 - 日终，统一推送
git pull origin main
git push origin main

# 查看今日提交
git log --oneline -10
```

---

**建议**: 按照这个工作流，每天只需要推送1次到GitHub即可，既可以保留开发历史，又不会频繁触发CI/CD。
