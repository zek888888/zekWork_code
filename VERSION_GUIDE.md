# 版本管理速查指南

> 快速了解如何管理和追溯项目版本

---

## 📌 当前版本信息

| 项目 | 信息 |
|------|------|
| **当前版本** | v1.0.0 |
| **发布日期** | 2026-03-14 |
| **Git提交** | 3bf1c1c |
| **GitHub仓库** | https://github.com/zek888888/zekWork_code |

---

## 🚀 Git 常用命令速查

### 查看状态
```bash
# 查看当前状态
git status

# 查看提交历史
git log --oneline -10

# 查看所有标签
git tag

# 查看某文件的修改历史
git log -p -- filename.py
```

### 提交更改
```bash
# 添加所有修改
git add -A

# 提交并添加描述
git commit -m "[类型] 描述"

# 推送到GitHub
git push origin main
```

### 版本回退
```bash
# 查看所有操作记录
git reflog

# 回退到某个提交 (保留修改)
git reset --soft HEAD~1

# 回退到某个提交 (丢弃修改)
git reset --hard 提交哈希

# 回退到标签版本
git checkout v1.0.0

# 创建回退分支
git checkout -b rollback-branch v1.0.0
```

### 分支管理
```bash
# 创建新分支
git checkout -b feature/xxx

# 切换分支
git checkout main

# 合并分支
git merge feature/xxx

# 删除分支
git branch -d feature/xxx
```

---

## 📝 版本号规范 (SemVer)

格式: `主版本号.次版本号.修订号` (如 v1.2.3)

| 版本类型 | 说明 | 示例 |
|----------|------|------|
| **主版本 (Major)** | 不兼容的API修改 | v1.0.0 → v2.0.0 |
| **次版本 (Minor)** | 向下兼容的功能新增 | v1.0.0 → v1.1.0 |
| **修订号 (Patch)** | 向下兼容的问题修复 | v1.0.0 → v1.0.1 |

### 本项目版本规划

```
v1.0.0 - 当前版本 (完整可用版本)
v1.1.0 - 计划: 港股/A股数据接入
v1.2.0 - 计划: Polymarket预测市场
v1.3.0 - 计划: 移动端支持
v2.0.0 - 计划: AI全自动交易
```

---

## 🏷️ 标签管理

### 创建标签
```bash
# 创建附注标签
git tag -a v1.0.0 -m "版本1.0.0发布"

# 推送标签到GitHub
git push origin v1.0.0

# 推送所有标签
git push origin --tags
```

### 删除标签
```bash
# 本地删除
git tag -d v1.0.0

# 远程删除
git push origin :refs/tags/v1.0.0
```

---

## 🔄 与OpenClaw协作流程

### 1. 开始新迭代
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 创建新分支 (可选)
git checkout -b feature/xxx
```

### 2. 开发过程中
```bash
# 经常提交小改动
git add -A
git commit -m "[feat] 实现XXX功能"

# 推送到GitHub
git push origin main  # 或 git push origin feature/xxx
```

### 3. 完成迭代
```bash
# 1. 更新版本号 (在main.py中)
# VERSION = "1.1.0"

# 2. 更新CHANGELOG.md

# 3. 提交所有更改
git add -A
git commit -m "[release] v1.1.0 - XXX功能"

# 4. 打标签
git tag -a v1.1.0 -m "版本1.1.0"

# 5. 推送
git push origin main --tags
```

---

## 📊 版本对比

### 查看两个版本差异
```bash
# 对比工作区和最新提交
git diff

# 对比两个提交
git diff v0.3.0 v1.0.0

# 对比某个文件的变化
git diff v0.3.0 v1.0.0 -- main.py

# 统计代码行数变化
git diff --stat v0.3.0 v1.0.0
```

---

## 🆘 常见问题

### Q: 误删了文件如何恢复？
```bash
# 从Git历史中恢复
git checkout HEAD -- 文件名

# 从暂存区恢复
git checkout -- 文件名
```

### Q: 提交信息写错了怎么办？
```bash
# 修改最后一次提交
git commit --amend -m "新的提交信息"

# 修改后再推送 (如果已推送)
git push origin main --force-with-lease
```

### Q: 如何忽略已跟踪的文件？
```bash
# 停止跟踪但不删除
git rm --cached 文件名

# 然后添加到.gitignore
echo "文件名" >> .gitignore
```

### Q: 如何查看某个版本的完整代码？
```bash
# 方式1: 切换到标签
git checkout v1.0.0

# 方式2: 在GitHub上查看
# https://github.com/zek888888/zekWork_code/releases/tag/v1.0.0

# 方式3: 下载ZIP
# https://github.com/zek888888/zekWork_code/archive/refs/tags/v1.0.0.zip
```

---

## 📁 重要文件清单

每次发布必须更新的文件：

| 文件 | 用途 | 必须更新 |
|------|------|----------|
| `main.py` | 版本号 | ✅ |
| `README.md` | 项目说明 | ✅ |
| `CHANGELOG.md` | 更新日志 | ✅ |
| `COLLABORATION.md` | 协作指南 | 需要时 |
| `requirements.txt` | 依赖包 | 有新依赖时 |

---

## 🔗 GitHub链接

- **仓库主页**: https://github.com/zek888888/zekWork_code
- **Release页面**: https://github.com/zek888888/zekWork_code/releases
- **v1.0.0标签**: https://github.com/zek888888/zekWork_code/releases/tag/v1.0.0
- **提交历史**: https://github.com/zek888888/zekWork_code/commits/main

---

## 💡 最佳实践

1. **频繁提交** - 小步快跑，每次提交一个完整功能点
2. **写清楚提交信息** - 方便后续追溯
3. **定期推送到GitHub** - 防止本地数据丢失
4. **打标签记录重要版本** - 方便回退
5. **保持主分支稳定** - 新功能在分支开发

---

**最后更新**: 2026-03-14  
**适用于版本**: v1.0.0+
