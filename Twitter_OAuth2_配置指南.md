# Twitter OAuth 2.0 配置与使用指南

> 本指南帮助您配置 Twitter OAuth 2.0，实现程序化发推。

---

## 📋 前置条件

1. 已申请 Twitter Developer 账号
2. 已创建 Twitter App
3. 已启用 OAuth 2.0 权限

---

## 🔧 第一步：获取 OAuth 2.0 凭证

### 1.1 进入开发者控制台

访问: https://developer.twitter.com/en/portal/dashboard

### 1.2 获取 Client ID 和 Client Secret

1. 进入您的 Project → Apps
2. 点击您的应用名称
3. 选择 **"Keys and Tokens"** 标签
4. 在 **"OAuth 2.0 Client ID and Client Secret"** 区域:
   - 复制 `Client ID`
   - 点击 **"Regenerate"** 生成 `Client Secret`（只显示一次，务必保存！）

### 1.3 配置回调 URL

在同一页面，找到 **"User authentication settings"**:

1. 开启 **"OAuth 2.0"**
2. **App permissions**: 选择 `Read and Write`
3. **Type of App**: 选择 `Web App, Automated App or Bot`
4. **Callback URI / Redirect URL**: 添加
   ```
   http://127.0.0.1:5000/callback
   ```
5. **Website URL**: 填写任意有效URL（如您的GitHub主页）
6. 保存设置

---

## 📝 第二步：填写配置文件

编辑文件 `.env.twitter.oauth2`:

```bash
# 填写您从 Developer Portal 获取的凭证
TWITTER_CLIENT_ID=your_actual_client_id_here
TWITTER_CLIENT_SECRET=your_actual_client_secret_here
TWITTER_REDIRECT_URI=http://127.0.0.1:5000/callback
```

---

## 🚀 第三步：运行授权流程

执行授权脚本获取 Access Token:

```bash
python3 twitter_oauth2_authorize.py
```

### 授权流程:

1. **启动本地服务器** (端口5000)
2. **自动打开浏览器** 跳转到 Twitter 授权页面
3. **登录 Twitter** 并点击 **"Authorize App"**
4. **授权成功后**，浏览器显示 "授权成功"
5. **终端自动保存** Access Token 和 Refresh Token

成功后会显示:
```
✅ OAuth 2.0 授权完成！
✅ 授权用户: @your_username
```

---

## 🐦 第四步：发布推文

### 基本用法

```bash
# 直接发推
python3 post_tweet_oauth2.py "Hello, World! 这是OAuth 2.0发的第一条推文🚀"

# 从文件发推
python3 post_tweet_oauth2.py --file tweet.txt

# 回复推文
python3 post_tweet_oauth2.py --reply 1234567890 "这是一条回复"
```

### 示例输出

```
============================================================
  Twitter OAuth 2.0 发推工具
============================================================

推文内容: Hello, World! 这是OAuth 2.0发的第一条推文🚀

【发布推文】...
✅ 推文发布成功！
   Tweet ID: 1234567890123456789
   链接: https://twitter.com/i/web/status/1234567890123456789
```

---

## 📁 文件说明

| 文件 | 用途 |
|------|------|
| `.env.twitter.oauth2` | OAuth 2.0 配置和令牌存储 |
| `twitter_oauth2_authorize.py` | 授权流程脚本 |
| `post_tweet_oauth2.py` | 发推工具 |
| `.tweet_history.json` | 发推历史记录 |

---

## ⚠️ 注意事项

### 1. 令牌有效期

- **Access Token**: 默认2小时有效
- **Refresh Token**: 长期有效（除非用户撤销授权）
- 脚本会自动刷新过期的 Access Token

### 2. 权限范围

OAuth 2.0 当前权限:
- ✅ 读取推文
- ✅ 发布推文
- ✅ 读取用户信息
- ❌ 上传媒体（需要 OAuth 1.0a）

如需发图片，请使用 OAuth 1.0a 版本。

### 3. 重新授权

如果出现以下情况，需要重新运行授权流程:
- Refresh Token 失效
- 用户撤销了应用授权
- 需要更改权限范围

---

## 🔍 故障排除

### 问题1: "无效的 Client ID"

**原因**: Client ID 填写错误

**解决**: 
1. 确认从 Developer Portal 复制的 Client ID 正确
2. 检查 `.env.twitter.oauth2` 文件是否有空格或特殊字符

### 问题2: "回调 URL 不匹配"

**原因**: Twitter Developer Portal 中配置的回调URL与脚本使用的不一致

**解决**:
1. 确保 Portal 中配置的回调URL是 `http://127.0.0.1:5000/callback`
2. 如果端口5000被占用，修改脚本和Portal配置使用其他端口

### 问题3: "授权页面打不开"

**原因**: 浏览器或网络问题

**解决**:
1. 手动复制终端显示的授权URL
2. 在浏览器中粘贴访问
3. 授权完成后，浏览器会跳转到 `http://127.0.0.1:5000/callback?code=xxx`

### 问题4: "发推失败 403"

**原因**: 权限不足或令牌过期

**解决**:
1. 检查 Access Token 是否过期（会自动刷新）
2. 确认 Twitter App 的权限设置为 "Read and Write"
3. 重新运行授权流程

---

## 📚 相关文档

- [Twitter OAuth 2.0 官方文档](https://developer.twitter.com/en/docs/authentication/oauth-2-0)
- [Twitter API v2 参考](https://developer.twitter.com/en/docs/twitter-api)

---

**配置完成后，您就可以程序化发布推文了！** 🎉
