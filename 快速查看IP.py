#!/usr/bin/env python3
"""
快速查看当前公网IP
用于API白名单配置
"""
import requests

def get_ip():
    services = [
        ("https://v4.ident.me/", "ident.me"),
        ("https://api.ipify.org", "ipify"),
        ("https://icanhazip.com", "icanhazip"),
    ]
    
    print("🌍 正在检测公网IP...\n")
    ips = []
    
    for url, name in services:
        try:
            ip = requests.get(url, timeout=5).text.strip()
            if ip not in ips:
                ips.append(ip)
            print(f"  {name}: {ip}")
        except:
            pass
    
    if ips:
        print(f"\n📌 推荐添加到白名单的IP:")
        for ip in ips:
            print(f"   {ip}")
        print("\n⚠️  提示: 如果使用了翻墙软件，实际API调用IP可能不同")
        print("   建议运行: python3 检测API出口IP.py --all")
    else:
        print("❌ 无法获取IP，请检查网络连接")

if __name__ == "__main__":
    get_ip()
