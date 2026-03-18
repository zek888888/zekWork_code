# GMGN + Clash 代理配置完成

## ✅ 配置状态

| 项目 | 配置值 |
|------|--------|
| Clash HTTP 代理端口 | `7897` |
| 代理出口 IP | `188.253.121.184` |
| API Key | `gmgn_ea6...9a43f460` |
| Private Key | 已配置 |

---

## 🔧 已完成配置

### 1. 环境变量配置 (`~/.config/gmgn/.env`)

```bash
# API 配置
GMGN_API_KEY=gmgn_ea66ffef861e17082b7c2c139a43f460
GMGN_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"

# Clash 代理配置
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
http_proxy=http://127.0.0.1:7897
https_proxy=http://127.0.0.1:7897
```

### 2. Python 客户端已更新

`gmgn_client.py` 已更新支持自动读取代理配置

---

## ⚠️ 关键步骤: 添加白名单

### 必须完成

将代理出口 IP **`188.253.121.184`** 添加到 GMGN 白名单：

1. 访问 https://gmgn.ai/
2. 登录您的账号
3. 进入 **设置** → **API 管理**
4. 找到 **IP 白名单** 设置
5. 添加 IP: `188.253.121.184`
6. 保存并等待审核 (通常几分钟)

---

## 🚀 使用方法

### 方法 1: 命令行 (gmgn-cli)

```bash
# 进入配置目录
cd ~/.config/gmgn

# 设置代理环境变量
export https_proxy=http://127.0.0.1:7897

# 查询热门代币
gmgn-cli market trending --chain sol --interval 1h --limit 10

# 查询代币信息
gmgn-cli token info --chain sol --address <token_address>

# 查看钱包信息
gmgn-cli portfolio info
```

### 方法 2: Python 脚本

```python
from gmgn_client import GMGNClient

# 自动使用代理配置
client = GMGNClient(use_proxy=True)

# 获取热门代币
trending = client.get_trending("sol", "1h", 10)

# 查询代币信息
info = client.get_token_info("sol", "<token_address>")

# 查看持仓
holdings = client.get_wallet_holdings("sol", "<wallet_address>")
```

---

## 🧪 测试命令

```bash
# 测试代理连接
cd ~/.openclaw/workspace/quant-trading
python3 测试GMGN代理.py

# 或使用诊断工具
python3 诊断Clash网络.py
```

---

## 📋 常见问题

### Q: 为什么需要添加白名单？
**A**: GMGN 为了安全，只允许特定 IP 访问 API。Clash 代理的出口 IP 是 `188.253.121.184`，需要添加到白名单才能连接。

### Q: Clash 重启后 IP 会变吗？
**A**: 
- 如果使用的是 **固定节点** → IP 不会变
- 如果使用的是 **自动选择/负载均衡** → IP 可能变化
- 建议：在 Clash 中固定选择一个节点，避免 IP 变动

### Q: 如何固定 Clash 节点？
**A**: 
1. 打开 Clash 客户端
2. 选择 **Proxies** 标签
3. 手动选择一个节点（不要选 Auto 或 Load Balance）
4. 确认 `curl -x http://127.0.0.1:7897 https://v4.ident.me/` 返回的 IP 固定

### Q: IP 变化了怎么办？
**A**: 
1. 运行 `python3 测试GMGN代理.py` 获取新 IP
2. 在 GMGN 后台更新白名单
3. 或使用 Clash 固定节点避免 IP 变化

---

## 🛡️ 安全提示

1. **白名单 IP**: `188.253.121.184` 是代理服务器出口 IP，不是您的真实 IP
2. **Private Key**: 仅本地存储，通过代理加密传输
3. **API Key**: 通过 HTTPS 传输，代理服务器无法解密内容

---

## ✅ 配置检查清单

- [x] Clash 运行中
- [x] 代理端口 7897 正常工作
- [x] `.env` 文件配置正确
- [x] Python 客户端更新完成
- [ ] **GMGN 白名单添加** `188.253.121.184`
- [ ] **测试 API 连接**

---

## 📞 下一步

1. **立即操作**: 访问 https://gmgn.ai/ 添加白名单 IP `188.253.121.184`
2. **等待**: 几分钟让白名单生效
3. **测试**: 运行 `python3 测试GMGN代理.py` 验证连接
4. **使用**: 开始使用 GMGN API 进行链上数据分析

---

**配置完成！等待白名单生效后即可正常使用。**
