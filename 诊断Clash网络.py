#!/usr/bin/env python3
"""
Clash 网络诊断工具
检测直连和代理的出口 IP，帮助配置 GMGN 白名单
"""

import os
import sys
import subprocess
import requests

def test_direct():
    """测试直连 IP"""
    print("\n" + "="*60)
    print("1️⃣  直连网络 (无代理)")
    print("="*60)
    
    # 清除代理环境变量
    env = os.environ.copy()
    env.pop('HTTP_PROXY', None)
    env.pop('HTTPS_PROXY', None)
    env.pop('http_proxy', None)
    env.pop('https_proxy', None)
    
    try:
        result = subprocess.run(
            ['curl', '-s', 'https://v4.ident.me/'],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        if result.returncode == 0:
            ip = result.stdout.strip()
            print(f"   ✅ 直连 IP: {ip}")
            return ip
        else:
            print(f"   ❌ 获取失败: {result.stderr}")
            return None
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return None

def test_proxy():
    """测试代理 IP"""
    print("\n" + "="*60)
    print("2️⃣  Clash 代理 (127.0.0.1:7890)")
    print("="*60)
    
    proxy = "http://127.0.0.1:7890"
    
    try:
        result = subprocess.run(
            ['curl', '-x', proxy, '-s', 'https://v4.ident.me/', '--max-time', '5'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            ip = result.stdout.strip()
            print(f"   ✅ 代理 IP: {ip}")
            return ip
        else:
            print(f"   ❌ Clash 可能未运行或端口不对")
            print(f"      错误: {result.stderr[:100]}")
            return None
    except subprocess.TimeoutExpired:
        print("   ⏱️  超时 - Clash 可能未响应")
        return None
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return None

def test_python_requests():
    """测试 Python requests 使用的 IP"""
    print("\n" + "="*60)
    print("3️⃣  Python requests 库")
    print("="*60)
    
    # 清除代理
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        os.environ.pop(key, None)
    
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)
    except:
        pass
    
    try:
        r = requests.get('https://v4.ident.me/', timeout=10)
        ip = r.text.strip()
        print(f"   ✅ Python 直连 IP: {ip}")
        return ip
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return None

def test_gmgn_api():
    """测试 GMGN API 连接"""
    print("\n" + "="*60)
    print("4️⃣  GMGN API 连接测试")
    print("="*60)
    
    sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')
    
    try:
        from gmgn_client import GMGNClient
        client = GMGNClient()
        
        print(f"   API Key: {client.api_key[:8]}...{client.api_key[-8:]}")
        
        result = client.get_user_info()
        
        if 'error' in result:
            print(f"   ❌ API 请求失败: {result['error']}")
            return False
        else:
            print(f"   ✅ API 连接成功!")
            if 'data' in result:
                print(f"   用户: {result['data'].get('name', 'Unknown')}")
            return True
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

def main():
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "Clash + GMGN 网络诊断" + " "*22 + "║")
    print("╚" + "="*58 + "╝")
    
    # 检测各种方式的 IP
    direct_ip = test_direct()
    proxy_ip = test_proxy()
    python_ip = test_python_requests()
    
    # 分析结果
    print("\n" + "="*60)
    print("📊 诊断结果")
    print("="*60)
    
    ips = {
        'curl 直连': direct_ip,
        'Clash 代理': proxy_ip,
        'Python 直连': python_ip,
    }
    
    print("\n检测到的 IP:")
    for name, ip in ips.items():
        if ip:
            print(f"   {name}: {ip}")
        else:
            print(f"   {name}: 未检测到")
    
    # 判断是否一致
    unique_ips = set([ip for ip in ips.values() if ip])
    
    print(f"\n🔍 分析:")
    if len(unique_ips) == 0:
        print("   ❌ 无法获取任何 IP，请检查网络连接")
    elif len(unique_ips) == 1:
        print(f"   ✅ 所有工具使用相同 IP: {list(unique_ips)[0]}")
        print("   这是理想状态，将此 IP 加入 GMGN 白名单即可")
    else:
        print(f"   ⚠️  检测到 {len(unique_ips)} 个不同 IP!")
        print("   这会导致 SSL 握手不一致")
        print("\n   建议解决方案:")
        print("   1. 方案A: 关闭 Clash，使用直连 IP")
        print("   2. 方案B: Clash 设为 Global 模式，统一走代理")
        print("   3. 方案C: 配置 Clash 规则，统一 GMGN 流量路径")
    
    # 测试 GMGN API
    print()
    gmgn_ok = test_gmgn_api()
    
    # 最终建议
    print("\n" + "="*60)
    print("💡 建议操作")
    print("="*60)
    
    if gmgn_ok:
        print("   ✅ GMGN API 可以正常连接!")
        print("   当前配置正确，无需修改")
    else:
        print("   根据诊断结果，推荐以下操作:")
        print()
        
        if len(unique_ips) > 1:
            print("   【方案A - 简单快速】关闭 Clash:")
            print("      1. Clash 菜单 → Mode → Direct")
            print("      2. 使用 IP " + (direct_ip or python_ip or "[检测失败]") + " 加入 GMGN 白名单")
            print()
            print("   【方案B - 使用代理】统一走 Clash:")
            print("      1. Clash 菜单 → Mode → Global")
            if proxy_ip:
                print(f"      2. 使用 IP {proxy_ip} 加入 GMGN 白名单")
            print()
            print("   【方案C - 精细控制】配置 Clash 规则:")
            print("      编辑 ~/.config/clash/config.yaml")
            print("      添加: - DOMAIN,api.gmgn.ai,DIRECT (走直连)")
            print("         或: - DOMAIN,api.gmgn.ai,PROXY (走代理)")
        else:
            print("   IP 一致但 API 连接失败，可能是:")
            print("   - 白名单配置不正确")
            print("   - 需要在 GMGN 后台更新白名单")
            if direct_ip:
                print(f"   - 将 IP {direct_ip} 加入白名单")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
