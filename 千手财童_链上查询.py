#!/usr/bin/env python3
"""
千手财童 - 链上数据查询 (使用Ethplorer API)
查询以太坊地址持币信息
"""

import os
import sys
import requests
import json
from typing import List, Dict
from datetime import datetime
import time

# Ethplorer API 配置
ETHPLORER_API_KEY = "freekey"  # 免费版API Key
ETHPLORER_API_URL = "https://api.ethplorer.io"

class 千手财童链上查询:
    """千手财童 - 链上数据查询模块"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.session = requests.Session()
        
    def _setup_logger(self):
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - 千手财童 - %(levelname)s - %(message)s'
        )
        return logging.getLogger('千手财童链上')
    
    def 查询地址信息(self, address: str) -> Dict:
        """查询地址完整信息"""
        try:
            url = f"{ETHPLORER_API_URL}/getAddressInfo/{address}"
            params = {
                'apiKey': ETHPLORER_API_KEY
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"查询失败: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            self.logger.error(f"查询异常: {e}")
            return {}
    
    def 查询地址持仓(self, address: str) -> Dict:
        """查询地址完整持仓信息"""
        self.logger.info(f"🔍 查询地址: {address}")
        
        result = {
            'address': address,
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'eth_balance': 0,
            'tokens': []
        }
        
        data = self.查询地址信息(address)
        
        if not data:
            return result
        
        # ETH余额
        eth_info = data.get('ETH', {})
        if eth_info:
            result['eth_balance'] = float(eth_info.get('balance', 0))
            result['eth_price'] = eth_info.get('price', {}).get('rate', 0)
        
        # 代币余额
        tokens_data = data.get('tokens', [])
        for token_info in tokens_data:
            token_data = token_info.get('tokenInfo', {})
            balance_raw = float(token_info.get('balance', 0))
            decimals = int(token_data.get('decimals', 18))
            balance = balance_raw / (10 ** decimals)
            
            if balance > 0:
                token = {
                    'symbol': token_data.get('symbol', 'UNKNOWN'),
                    'name': token_data.get('name', ''),
                    'balance': balance,
                    'contract': token_data.get('address', ''),
                    'decimals': decimals,
                    'price_usd': token_data.get('price', {}).get('rate', 0) if token_data.get('price') else 0
                }
                result['tokens'].append(token)
        
        # 按价值排序
        result['tokens'].sort(
            key=lambda x: x['balance'] * x.get('price_usd', 0), 
            reverse=True
        )
        
        return result
    
    def 批量查询(self, addresses: List[str]) -> List[Dict]:
        """批量查询多个地址"""
        results = []
        
        print("=" * 70)
        print("🙏 千手财童 - 链上持仓查询")
        print("=" * 70)
        print(f"查询地址数: {len(addresses)}")
        print(f"数据来源: Ethplorer (以太坊主网)")
        print(f"API Key: {ETHPLORER_API_KEY}")
        print("=" * 70)
        
        for i, addr in enumerate(addresses, 1):
            print(f"\n[{i}/{len(addresses)}] 查询地址: {addr}")
            result = self.查询地址持仓(addr)
            results.append(result)
            self._打印持仓结果(result)
            time.sleep(0.5)  # 免费版限速
        
        return results
    
    def _打印持仓结果(self, result: Dict):
        """打印持仓结果"""
        addr = result['address']
        eth_balance = result['eth_balance']
        eth_price = result.get('eth_price', 0)
        tokens = result['tokens']
        
        print(f"\n{'='*70}")
        print(f"📍 地址: {addr}")
        print(f"⏱️  查询时间: {result['query_time']}")
        print(f"{'='*70}")
        
        # ETH
        eth_value_usd = eth_balance * eth_price
        print(f"\n💎 ETH (以太坊)")
        print(f"   余额: {eth_balance:.6f} ETH")
        if eth_price > 0:
            print(f"   单价: ${eth_price:,.2f}")
            print(f"   价值: ${eth_value_usd:,.2f}")
        
        # 代币
        if tokens:
            total_token_value = 0
            print(f"\n🪙 ERC-20 代币 ({len(tokens)} 种):")
            print(f"\n{'代币':<12} {'余额':>20} {'单价':>15} {'价值(USD)':>15}")
            print("-" * 70)
            
            for token in tokens:
                symbol = token['symbol']
                name = token['name']
                balance = token['balance']
                price = token.get('price_usd', 0)
                value = balance * price
                total_token_value += value
                
                print(f"{symbol:<12} {balance:>20.6f}", end="")
                if price > 0:
                    print(f" ${price:>14.4f} ${value:>14.2f}")
                else:
                    print(f" {'N/A':>14} {'N/A':>14}")
                
                if name and name != symbol:
                    print(f"   ({name})")
            
            print("-" * 70)
            if total_token_value > 0:
                print(f"{'代币总价值:':<12} {'':>20} {'':>15} ${total_token_value:>14.2f}")
        else:
            print("\n🪙 ERC-20 代币: 未持有")
        
        total_value = eth_value_usd + sum(t['balance'] * t.get('price_usd', 0) for t in tokens)
        print(f"\n💰 总资产价值: ${total_value:,.2f} USD")
        print(f"{'='*70}")


if __name__ == "__main__":
    # 要查询的地址列表
    addresses = [
        "0x7852346c77b3a622fa73607ee35cc784e53f326b",
        "0x97a1c2efb9cafb6ef1f149bf2b8f3285871e342b",
        "0x95701259b045f972b06089e5ba498d463f627aa2"
    ]
    
    # 创建查询实例
    财童 = 千手财童链上查询()
    
    # 执行查询
    results = 财童.批量查询(addresses)
    
    print("\n" + "=" * 70)
    print("✅ 查询完成!")
    print("=" * 70)
