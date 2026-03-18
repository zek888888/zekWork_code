# Clash + GMGN 配置指南

## 🔍 问题原因

Clash 默认使用 **分流规则** (Rule Mode)，导致：
- `curl` 命令 → 可能走直连
- Python `requests` → 可能走代理
- 结果：**SSL 握手环境不一致**，GMGN 服务器拒绝连接

---

## ✅ 解决方案

### 方案 1: 临时关闭 Clash (推荐测试)

```bash
# 1. 在 Clash 菜单中选择 "Direct" (直连模式)
# 或完全退出 Clash

# 2. 检测真实 IP
curl https://v4.ident.me/
# 预期输出: 113.132.239.118

# 3. 将此 IP 添加到 GMGN 白名单
# 4. 测试 GMGN API
cd ~/.config/gmgn
gmgn-cli portfolio info
```

---

### 方案 2: 强制所有流量走 Clash 代理

#### 步骤 1: 切换 Clash 为 Global 模式
```
Clash 菜单 → Mode → Global
```

#### 步骤 2: 检测代理出口 IP
```bash
# 确认所有流量都走代理
curl -x http://127.0.0.1:7890 https://v4.ident.me/
# 或
https_proxy=http://127.0.0.1:7890 curl https://v4.ident.me/
```

#### 步骤 3: 将代理出口 IP 加入 GMGN 白名单

#### 步骤 4: 配置工具使用代理

**gmgn-cli 使用代理：**
```bash
export https_proxy=http://127.0.0.1:7890
cd ~/.config/gmgn
gmgn-cli portfolio info
```

**Python 客户端使用代理：**
```python
import os
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from gmgn_client import GMGNClient
client = GMGNClient()
```

---

### 方案 3: 配置 Clash 规则 (推荐长期使用)

在 Clash 配置文件中添加规则，让 `api.gmgn.ai` 走指定路径：

#### 方法 A: 让 GMGN 走代理
```yaml
# 编辑 Clash 配置文件 (通常是 ~/.config/clash/config.yaml)
# 在 rules 部分添加：

rules:
  # GMGN API 走代理
  - DOMAIN,api.gmgn.ai,PROXY
  
  # 其他规则...
  - GEOIP,CN,DIRECT
  - MATCH,PROXY
```

#### 方法 B: 让 GMGN 走直连
```yaml
rules:
  # GMGN API 走直连
  - DOMAIN,api.gmgn.ai,DIRECT
  
  # 其他规则...
  - GEOIP,CN,DIRECT
  - MATCH,PROXY
```

**重启 Clash 后生效**

---

## 🛠️ 快速诊断脚本

创建脚本检测当前网络配置：

```bash
# 保存为 check_network.sh
#!/bin/bash

echo "===== 网络诊断 ====="
echo ""

echo "1. 直连 IP (无代理):"
curl -s https://v4.ident.me/ | xargs echo "   "

echo ""
echo "2. Clash 代理 IP (7890端口):"
curl -x http://127.0.0.1:7890 -s https://v4.ident.me/ 2>/dev/null | xargs echo "   " || echo "   无法连接"

echo ""
echo "3. 环境变量:"
echo "   HTTP_PROXY: $HTTP_PROXY"
echo "   HTTPS_PROXY: $HTTPS_PROXY"

echo ""
echo "4. 测试 GMGN API (直连):"
cd ~/.config/gmgn 2>/dev/null && timeout 5 gmgn-cli portfolio info 2>&1 | head -3 || echo "   失败"

echo ""
echo "===== 建议 ====="
echo "如果 IP 不一致，请统一使用其中一种方式"
```

运行：
```bash
chmod +x check_network.sh
./check_network.sh
```

---

## 📋 推荐配置总结

| 场景 | 推荐方案 | 操作 |
|------|----------|------|
| 测试/开发 | 方案 1: 关闭 Clash | 切换 Direct 模式 |
| 长期使用 + 代理 | 方案 2: Global 模式 | 代理 IP 加入白名单 |
| 精细控制 | 方案 3: 自定义规则 | 配置 DOMAIN 规则 |

---

## ⚠️ 注意事项

1. **Clash 默认端口**: `7890` (HTTP) / `7891` (SOCKS5)
2. **白名单更新**: 每次 IP 变化后需要在 GMGN 后台更新
3. **测试顺序**: 建议先用方案 1 测试，确认是网络问题后再配置代理

---

## 🚀 立即测试

请执行以下命令，我来帮您判断最佳方案：

```bash
# 检测直连 IP
curl https://v4.ident.me/

# 检测代理 IP (如果 Clash 在运行)
curl -x http://127.0.0.1:7890 https://v4.ident.me/
```

告诉我两个命令的输出结果，我帮您选择最佳配置方案！
