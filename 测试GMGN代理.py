#!/usr/bin/env python3
"""
测试 GMGN API 通过 Clash 代理连接
"""

import os
import sys

# 加载环境变量
env_path = os.path.expanduser("~/.config/gmgn/.env")
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"\'')
            if '\\n' in value:
                value = value.replace('\\n', '\n')
            os.environ[key] = value

print("="*60)
print("🧪 GMGN API 代理连接测试")
print("="*60)

# 显示代理配置
http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")

print(f"\n📡 代理配置:")
print(f"   HTTP_PROXY: {http_proxy}")
print(f"   HTTPS_PROXY: {https_proxy}")

# 测试代理出口 IP
print(f"\n🌍 测试代理出口 IP...")
import requests

try:
    proxies = {
        "http": http_proxy,
        "https": https_proxy or http_proxy
    }
    r = requests.get("https://v4.ident.me/", proxies=proxies, timeout=10)
    proxy_ip = r.text.strip()
    print(f"   ✅ 代理出口 IP: {proxy_ip}")
except Exception as e:
    print(f"   ❌ 获取代理 IP 失败: {e}")
    proxy_ip = None

# 测试 GMGN API
print(f"\n🔗 测试 GMGN API 连接...")
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')

from gmgn_client import GMGNClient

try:
    client = GMGNClient(use_proxy=True)
    
    print(f"   API Key: {client.api_key[:8]}...{client.api_key[-8:]}")
    print(f"   Private Key: {'已配置' if client.private_key else '未配置'}")
    
    # 测试获取热门代币
    print(f"\n📊 测试获取热门代币...")
    result = client.get_trending("sol", "1h", 5)
    
    if "error" in result:
        print(f"   ❌ 请求失败: {result['error']}")
        print(f"\n   💡 可能原因:")
        print(f"      1. 代理配置不正确")
        print(f"      2. 需要将代理出口 IP 加入 GMGN 白名单")
        if proxy_ip:
            print(f"      3. 白名单 IP 应为: {proxy_ip}")
    else:
        print(f"   ✅ API 连接成功!")
        if "data" in result and result["data"]:
            print(f"\n   热门代币 (SOL/1h):")
            for i, token in enumerate(result["data"][:5], 1):
                symbol = token.get("symbol", "Unknown")
                price = token.get("price", 0)
                print(f"      {i}. {symbol} - ${price:.6f}")
        
        # 测试用户信息
        print(f"\n👤 测试获取用户信息...")
        user_info = client.get_user_info()
        if "error" not in user_info:
            print(f"   ✅ 用户信息获取成功")
            if "data" in user_info:
                print(f"   用户: {user_info['data'].get('name', 'Unknown')}")
        
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("📋 总结")
print("="*60)

if proxy_ip:
    print(f"""
代理配置:
   代理地址: {http_proxy}
   出口 IP: {proxy_ip}

下一步操作:
   1. 访问 https://gmgn.ai/ 登录账号
   2. 进入 API 设置页面
   3. 将 IP {proxy_ip} 添加到白名单
   4. 等待审核通过 (通常几分钟)
   5. 重新运行本脚本测试

如果已添加白名单但仍失败:
   - 检查 IP 是否输入正确
   - 确认 Clash 代理稳定运行
   - 尝试重启 Clash
""")
