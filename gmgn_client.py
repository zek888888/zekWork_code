#!/usr/bin/env python3
"""
GMGN API Python 客户端
直接调用 GMGN API，无需 gmgn-cli
"""

import os
import json
import base64
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 加载环境变量
def load_env():
    """加载 ~/.config/gmgn/.env"""
    env_path = Path.home() / ".config/gmgn/.env"
    if not env_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {env_path}")
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                # 处理多行值
                if '\\n' in value:
                    value = value.replace('\\n', '\n')
                os.environ[key] = value

class GMGNClient:
    """GMGN API 客户端"""
    
    BASE_URL = "https://api.gmgn.ai/v1"
    
    def __init__(self, use_proxy: bool = True):
        load_env()
        self.api_key = os.getenv("GMGN_API_KEY")
        self.private_key = os.getenv("GMGN_PRIVATE_KEY")
        
        if not self.api_key:
            raise ValueError("GMGN_API_KEY not found in .env")
            
        self.session = requests.Session()
        self.session.headers.update({
            "X-APIKEY": self.api_key,
            "Content-Type": "application/json"
        })
        
        # 配置代理
        if use_proxy:
            http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
            https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
            if http_proxy or https_proxy:
                self.session.proxies = {
                    "http": http_proxy,
                    "https": https_proxy or http_proxy
                }
                print(f"   🔄 使用代理: {http_proxy}")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """发送请求"""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": "Request timeout", "status": "timeout"}
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "error"}
    
    # ==================== Market API ====================
    
    def get_kline(self, chain: str, address: str, resolution: str = "1h", 
                  from_time: int = None, to_time: int = None) -> Dict:
        """
        获取K线数据
        
        Args:
            chain: sol / bsc / base
            address: 代币合约地址
            resolution: 1m / 5m / 15m / 1h / 4h / 1d
            from_time: 开始时间戳 (秒)
            to_time: 结束时间戳 (秒)
        """
        params = {
            "resolution": resolution,
        }
        if from_time:
            params["from"] = from_time * 1000  # 转换为毫秒
        if to_time:
            params["to"] = to_time * 1000
            
        return self._request("GET", f"/token/{chain}/{address}/kline", params=params)
    
    def get_trending(self, chain: str, interval: str = "1h", 
                     limit: int = 100, order_by: str = "volume") -> Dict:
        """
        获取热门代币
        
        Args:
            chain: sol / bsc / base
            interval: 1h / 3h / 6h / 24h
            limit: 数量 (最大100)
            order_by: 排序字段
        """
        params = {
            "interval": interval,
            "limit": min(limit, 100),
            "orderby": order_by,
            "direction": "desc"
        }
        return self._request("GET", f"/token/{chain}/trending", params=params)
    
    # ==================== Token API ====================
    
    def get_token_info(self, chain: str, address: str) -> Dict:
        """获取代币基础信息"""
        return self._request("GET", f"/token/{chain}/{address}")
    
    def get_token_security(self, chain: str, address: str) -> Dict:
        """获取代币安全信息"""
        return self._request("GET", f"/token/{chain}/{address}/security")
    
    def get_token_pool(self, chain: str, address: str) -> Dict:
        """获取代币流动性池信息"""
        return self._request("GET", f"/token/{chain}/{address}/pools")
    
    def get_token_holders(self, chain: str, address: str, limit: int = 20) -> Dict:
        """获取代币持仓地址列表"""
        return self._request("GET", f"/token/{chain}/{address}/holders", 
                           params={"limit": limit})
    
    def get_token_traders(self, chain: str, address: str, limit: int = 20) -> Dict:
        """获取代币交易者列表"""
        return self._request("GET", f"/token/{chain}/{address}/traders",
                           params={"limit": limit})
    
    # ==================== Portfolio API ====================
    
    def get_user_info(self) -> Dict:
        """获取API Key绑定的用户信息"""
        return self._request("GET", "/user/info")
    
    def get_wallet_holdings(self, chain: str, wallet: str, limit: int = 20) -> Dict:
        """获取钱包持仓"""
        return self._request("GET", f"/wallet/{chain}/{wallet}/holdings",
                           params={"limit": limit})
    
    def get_wallet_activity(self, chain: str, wallet: str, limit: int = 20) -> Dict:
        """获取钱包交易活动"""
        return self._request("GET", f"/wallet/{chain}/{wallet}/activity",
                           params={"limit": limit})
    
    def get_wallet_stats(self, chain: str, wallet: str, period: str = "7d") -> Dict:
        """获取钱包交易统计"""
        return self._request("GET", f"/wallet/{chain}/{wallet}/stats",
                           params={"period": period})


# ==================== 便捷函数 ====================

def quick_trending(chain: str = "sol", interval: str = "1h", limit: int = 10):
    """快速获取热门代币"""
    client = GMGNClient()
    return client.get_trending(chain, interval, limit)

def quick_token_info(address: str, chain: str = "sol"):
    """快速查询代币信息"""
    client = GMGNClient()
    return client.get_token_info(chain, address)

def quick_user_info():
    """快速查询用户信息"""
    client = GMGNClient()
    return client.get_user_info()


if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("GMGN API Python 客户端")
    print("="*60)
    
    # 测试连接
    try:
        client = GMGNClient()
        print(f"\n✅ API Key: {client.api_key[:8]}...{client.api_key[-8:]}")
        print(f"✅ Private Key: {'已配置' if client.private_key else '未配置'}")
        
        print("\n📡 测试 API 连接...")
        
        # 测试获取热门代币
        print("\n1. 获取 SOL 链热门代币 (1小时)...")
        result = client.get_trending("sol", "1h", 5)
        
        if "error" in result:
            print(f"❌ 请求失败: {result['error']}")
        else:
            print(f"✅ 请求成功")
            if "data" in result and result["data"]:
                print(f"\n热门代币列表:")
                for i, token in enumerate(result["data"][:3], 1):
                    symbol = token.get("symbol", "Unknown")
                    address = token.get("address", "")[:12] + "..."
                    print(f"  {i}. {symbol} ({address})")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("使用示例:")
    print("="*60)
    print("""
from gmgn_client import GMGNClient

client = GMGNClient()

# 获取热门代币
trending = client.get_trending("sol", "1h", 10)

# 查询代币信息
info = client.get_token_info("sol", "<token_address>")

# 查看持仓
holdings = client.get_wallet_holdings("sol", "<wallet_address>")
""")
