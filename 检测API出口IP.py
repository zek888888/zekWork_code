#!/usr/bin/env python3
"""
API出口IP检测工具
用于确定调用DeepSeek/MiniMAX API时使用的实际IP，帮助配置白名单

使用方法:
    python3 检测API出口IP.py              # 基础检测
    python3 检测API出口IP.py --deepseek   # 测试DeepSeek API
    python3 检测API出口IP.py --minimax    # 测试MiniMAX API
    python3 检测API出口IP.py --all        # 完整测试(推荐)
"""

import os
import sys
import json
import time
import socket
import requests
import subprocess
from datetime import datetime
from urllib.parse import urlparse

# 项目路径
PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
LOG_DIR = f"{PROJECT_ROOT}/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-612745625de4483586baaf1397799cc6")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "sk-api-Am5r_op-rdb6NXE47LaF5fO9TdTyaDTHFVWJRrdp8pJcBdnuXILfxkQ7QKx9ZJmEEagMpl6y5GtNyQV31gAbRXyrtR_1wGCXLp6AY6-hfPmK0DQ3723I41A")

# API端点
IP_CHECK_SERVERS = [
    ("ident.me", "https://v4.ident.me/"),
    ("ipify", "https://api.ipify.org"),
    ("ip.sb", "https://api.ip.sb/ip"),
    ("icanhazip", "https://icanhazip.com"),
]

class IPDetector:
    """IP检测器"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "local_ips": [],
            "public_ips": {},
            "api_tests": {},
            "recommendations": []
        }
        
    def get_local_ips(self):
        """获取本机IP地址"""
        print("\n" + "="*70)
        print("🔍 检测本机网络信息")
        print("="*70)
        
        # 获取主机名
        hostname = socket.gethostname()
        print(f"\n📱 主机名: {hostname}")
        
        # 获取本地IP
        try:
            # 方法1: 通过UDP连接获取
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            self.results["local_ips"].append({"type": "IPv4", "address": local_ip, "method": "UDP"})
            print(f"🌐 本地IPv4: {local_ip}")
        except Exception as e:
            print(f"⚠️  获取本地IPv4失败: {e}")
            
        # 方法2: 通过socket.getaddrinfo
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            ips = set()
            for info in addr_info:
                ip = info[4][0]
                if ip not in ips and ip != '127.0.0.1' and not ip.startswith('::'):
                    ips.add(ip)
                    print(f"🌐 网络接口IP: {ip}")
        except Exception as e:
            print(f"⚠️  获取接口IP失败: {e}")
            
    def get_public_ips(self):
        """获取公网IP"""
        print("\n" + "="*70)
        print("🌍 检测公网IP (多源验证)")
        print("="*70)
        
        ipv4_list = []
        ipv6_list = []
        
        for name, url in IP_CHECK_SERVERS:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    ip = response.text.strip()
                    # 判断IPv4还是IPv6
                    if ':' in ip:
                        ipv6_list.append((name, ip))
                        print(f"✅ {name}: {ip} (IPv6)")
                    else:
                        ipv4_list.append((name, ip))
                        print(f"✅ {name}: {ip} (IPv4)")
                else:
                    print(f"❌ {name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: 请求失败 ({str(e)[:30]})")
                
        # 统计结果
        if ipv4_list:
            # 找出最常见的IPv4
            from collections import Counter
            ip_counts = Counter([ip for _, ip in ipv4_list])
            most_common = ip_counts.most_common(1)[0]
            self.results["public_ips"]["ipv4"] = {
                "primary": most_common[0],
                "all": list(dict.fromkeys([ip for _, ip in ipv4_list])),
                "sources": ipv4_list,
                "agreement": f"{most_common[1]}/{len(ipv4_list)} 源一致"
            }
            print(f"\n📌 主要公网IPv4: {most_common[0]} ({most_common[1]}个源一致)")
            
        if ipv6_list:
            self.results["public_ips"]["ipv6"] = {
                "all": list(dict.fromkeys([ip for _, ip in ipv6_list])),
                "sources": ipv6_list
            }
            print(f"📌 公网IPv6: {ipv6_list[0][1]}")
            
    def test_deepseek_api(self):
        """测试DeepSeek API并检测出口IP"""
        print("\n" + "="*70)
        print("🧠 测试 DeepSeek API")
        print("="*70)
        
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your_key_here":
            print("❌ 未配置DEEPSEEK_API_KEY")
            return
            
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 简单的测试请求
        data = {
            "model": "deepseek-reasoner",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10
        }
        
        try:
            print("\n📡 发送测试请求...")
            start_time = time.time()
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            elapsed = time.time() - start_time
            
            result = {
                "status_code": response.status_code,
                "response_time": f"{elapsed:.2f}s",
                "headers": dict(response.headers),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if response.status_code == 200:
                print(f"✅ API连接成功 (耗时{elapsed:.2f}s)")
                result["status"] = "success"
                
                # 尝试解析响应
                try:
                    resp_json = response.json()
                    result["model"] = resp_json.get("model", "unknown")
                    result["usage"] = resp_json.get("usage", {})
                    print(f"📊 使用模型: {result['model']}")
                except:
                    pass
                    
            elif response.status_code == 403:
                print(f"❌ API返回403 - IP可能被拒绝")
                print(f"   响应: {response.text[:200]}")
                result["status"] = "forbidden"
                result["error"] = response.text[:500]
                
            elif response.status_code == 401:
                print(f"❌ API返回401 - API Key无效")
                result["status"] = "unauthorized"
                
            else:
                print(f"⚠️  API返回: {response.status_code}")
                print(f"   响应: {response.text[:200]}")
                result["status"] = "error"
                result["error"] = f"HTTP {response.status_code}"
                
            self.results["api_tests"]["deepseek"] = result
            
            # 分析响应头
            print("\n📋 响应头信息:")
            for key, value in response.headers.items():
                if any(x in key.lower() for x in ['ip', 'client', 'remote', 'x-forwarded', 'cf-', 'x-real']):
                    print(f"   {key}: {value}")
                    
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
            self.results["api_tests"]["deepseek"] = {"status": "timeout", "error": "Request timeout"}
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            self.results["api_tests"]["deepseek"] = {"status": "error", "error": str(e)}
            
    def test_minimax_api(self):
        """测试MiniMAX API"""
        print("\n" + "="*70)
        print("🎭 测试 MiniMAX API")
        print("="*70)
        
        if not MINIMAX_API_KEY or MINIMAX_API_KEY == "your_key_here":
            print("❌ 未配置MINIMAX_API_KEY")
            return
            
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "MiniMax-Text-01",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10
        }
        
        try:
            print("\n📡 发送测试请求...")
            start_time = time.time()
            response = requests.post(
                "https://api.minimaxi.chat/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            elapsed = time.time() - start_time
            
            result = {
                "status_code": response.status_code,
                "response_time": f"{elapsed:.2f}s",
                "headers": dict(response.headers),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if response.status_code == 200:
                print(f"✅ API连接成功 (耗时{elapsed:.2f}s)")
                result["status"] = "success"
                try:
                    resp_json = response.json()
                    result["model"] = resp_json.get("model", "unknown")
                    print(f"📊 使用模型: {result['model']}")
                except:
                    pass
            elif response.status_code == 403:
                print(f"❌ API返回403 - IP可能被拒绝")
                result["status"] = "forbidden"
                result["error"] = response.text[:500]
            else:
                print(f"⚠️  API返回: {response.status_code}")
                result["status"] = "error"
                result["error"] = f"HTTP {response.status_code}"
                
            self.results["api_tests"]["minimax"] = result
            
            print("\n📋 响应头信息:")
            for key, value in response.headers.items():
                if any(x in key.lower() for x in ['ip', 'client', 'remote', 'x-forwarded', 'cf-', 'x-real']):
                    print(f"   {key}: {value}")
                    
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
            self.results["api_tests"]["minimax"] = {"status": "timeout"}
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            self.results["api_tests"]["minimax"] = {"status": "error", "error": str(e)}
            
    def generate_report(self):
        """生成检测报告"""
        print("\n" + "="*70)
        print("📊 生成检测报告")
        print("="*70)
        
        # 生成推荐IP列表
        recommended_ips = []
        
        if "ipv4" in self.results["public_ips"]:
            primary_ip = self.results["public_ips"]["ipv4"]["primary"]
            recommended_ips.append(primary_ip)
            self.results["recommendations"].append({
                "priority": "high",
                "ip": primary_ip,
                "type": "IPv4",
                "reason": "主要公网IP，多个检测源一致"
            })
            
        # 检查API测试结果
        for api_name, test_result in self.results["api_tests"].items():
            if test_result.get("status") == "forbidden":
                self.results["recommendations"].append({
                    "priority": "urgent",
                    "api": api_name,
                    "issue": "IP被API服务商拒绝(403)",
                    "solution": "需要将当前公网IP加入API白名单"
                })
                
        # 检查翻墙影响
        if len(self.results["public_ips"].get("ipv4", {}).get("all", [])) > 1:
            self.results["recommendations"].append({
                "priority": "medium",
                "issue": "检测到多个公网IP，可能使用了代理/翻墙",
                "solution": "建议固定使用一种网络环境，或在白名单中添加所有可能的IP"
            })
            
        # 显示推荐配置
        print("\n📋 API白名单配置建议:")
        print("-" * 70)
        
        if recommended_ips:
            print("\n✅ 推荐的IPv4白名单:")
            for ip in recommended_ips:
                print(f"   • {ip}")
                
        # 显示详细报告
        print("\n📄 详细报告:")
        print("-" * 70)
        
        # 保存报告到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{LOG_DIR}/ip_detection_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 详细报告已保存: {report_file}")
        
        # 生成便于复制粘贴的格式
        txt_report = f"{LOG_DIR}/ip_whitelist_{timestamp}.txt"
        with open(txt_report, 'w', encoding='utf-8') as f:
            f.write("# API白名单IP配置\n")
            f.write(f"# 生成时间: {self.results['timestamp']}\n")
            f.write("#\n\n")
            
            if "ipv4" in self.results["public_ips"]:
                f.write("# IPv4地址 (推荐)\n")
                for ip in self.results["public_ips"]["ipv4"]["all"]:
                    f.write(f"{ip}\n")
                    
            if "ipv6" in self.results["public_ips"]:
                f.write("\n# IPv6地址\n")
                for ip in self.results["public_ips"]["ipv6"]["all"]:
                    f.write(f"{ip}\n")
                    
            f.write("\n# API测试结果\n")
            for api, result in self.results["api_tests"].items():
                f.write(f"# {api}: {result.get('status', 'unknown')}\n")
                
        print(f"💾 IP列表已保存: {txt_report}")
        
        return report_file, txt_report
        
    def run(self, test_deepseek=False, test_minimax=False):
        """运行完整检测"""
        print("╔" + "="*68 + "╗")
        print("║" + " "*20 + "API出口IP检测工具" + " "*25 + "║")
        print("║" + " "*15 + "用于配置API服务商白名单" + " "*22 + "║")
        print("╚" + "="*68 + "╝")
        
        # 基础检测
        self.get_local_ips()
        self.get_public_ips()
        
        # API测试
        if test_deepseek or test_minimax:
            if test_deepseek:
                self.test_deepseek_api()
            if test_minimax:
                self.test_minimax_api()
        else:
            # 默认都测试
            self.test_deepseek_api()
            self.test_minimax_api()
            
        # 生成报告
        report_files = self.generate_report()
        
        # 最终提示
        print("\n" + "="*70)
        print("✅ 检测完成!")
        print("="*70)
        print("\n下一步操作:")
        print("1. 查看上方的推荐IP地址")
        print("2. 将推荐IP添加到API服务商的白名单")
        print("3. 再次运行本脚本验证配置是否生效")
        print("\n提示: 如果使用了翻墙软件，建议:")
        print("  • 方案A: 临时关闭翻墙，使用直连IP配置")
        print("  • 方案B: 保持翻墙开启，将代理IP也加入白名单")
        print("="*70)
        
        return report_files


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='API出口IP检测工具')
    parser.add_argument('--deepseek', action='store_true', help='仅测试DeepSeek API')
    parser.add_argument('--minimax', action='store_true', help='仅测试MiniMAX API')
    parser.add_argument('--all', action='store_true', help='完整测试(默认)')
    parser.add_argument('--ip-only', action='store_true', help='仅检测IP，不测试API')
    
    args = parser.parse_args()
    
    detector = IPDetector()
    
    if args.ip_only:
        detector.get_local_ips()
        detector.get_public_ips()
        detector.generate_report()
    elif args.deepseek:
        detector.run(test_deepseek=True, test_minimax=False)
    elif args.minimax:
        detector.run(test_deepseek=False, test_minimax=True)
    else:
        detector.run(test_deepseek=True, test_minimax=True)


if __name__ == "__main__":
    main()
