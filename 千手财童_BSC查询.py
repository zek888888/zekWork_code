#!/usr/bin/env python3
"""
千手财童 - BSC主网链上数据查询
使用BscScan API
"""

import os
import sys
import requests
import json
from typing import List, Dict
from datetime import datetime
import time

# BscScan API 配置
BSCSCAN_API_KEY = "YourApiKeyToken"  # 公共key，如需高频查询请替换
BSCSCAN_API_URL = "https://api.bscscan.com/api"

# 常用BSC代币合约地址
POPULAR_BSC_TOKENS = {
    "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    "BUSD": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
    "USDT": "0x55d398326f99059fF775485246999027B3197955",
    "USDC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
    "CAKE": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
    "ETH": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
    "BTCB": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",
    "XRP": "0x1D2F0da169ceB9fC7B3144628dB156f3F6c60dBE",
    "ADA": "0x3EE2200Efb3400fAbB9AacF31297cBdD1d435D47",
    "DOGE": "0xbA2aE424d960c26247Dd6c32edC70B295c744C43",
    "DOT": "0x7083609fCE4d1d8Dc0C979AAb8c869Ea2C873402",
    "LINK": "0xF8A0BF9cF54Bb92F17374d9e9A321E6a111a51bD",
    "LTC": "0x4338665CBB7B2485A8855A139b75D5e34AB0DB94",
    "MATIC": "0xCC42724C6683B7E57334c4E856f4c9965ED682bD",
    "SHIB": "0x2859e4544C4bB03966803b044A93563Bd2D0DD4D",
}

class 千手财童BSC查询:
    """千手财童 - BSC链上数据查询模块"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def _setup_logger(self):
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - 千手财童 - %(levelname)s - %(message)s'
        )
        return logging.getLogger('千手财童BSC')
    
    def 查询BNB余额(self, address: str) -> Dict:
        """查询地址BNB余额"""
        try:
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest',
                'apikey': BSCSCAN_API_KEY
            }
            
            response = self.session.get(BSCSCAN_API_URL, params=params, timeout=30)
            data = response.json()
            
            if data['status'] == '1':
                balance_wei = int(data['result'])
                balance_bnb = balance_wei / 10**18
                return {
                    'symbol': 'BNB',
                    'name': 'Binance Coin',
                    'balance': balance_bnb,
                    'contract': '0x0000000000000000000000000000000000000000',
                    'decimals': 18
                }
            else:
                self.logger.debug(f"查询BNB余额: {data.get('message', '')}")
                return None
                
        except Exception as e:
            self.logger.debug(f"查询BNB余额异常: {e}")
            return None
    
    def 查询代币余额(self, address: str, token_contract: str, symbol: str, decimals: int = 18) -> Dict:
        """查询单个代币余额"""
        try:
            params = {
                'module': 'account',
                'action': 'tokenbalance',
                'contractaddress': token_contract,
                'address': address,
                'tag': 'latest',
                'apikey': BSCSCAN_API_KEY
            }
            
            response = self.session.get(BSCSCAN_API_URL, params=params, timeout=10)
            data = response.json()
            
            if data['status'] == '1':
                balance_raw = int(data['result'])
                balance = balance_raw / 10**decimals
                
                if balance > 0:
                    return {
                        'symbol': symbol,
                        'name': symbol,
                        'balance': balance,
                        'contract': token_contract,
                        'decimals': decimals
                    }
            
        except Exception as e:
            self.logger.debug(f"查询代币 {symbol} 余额失败: {e}")
        
        return None
    
    def 查询代币交易记录(self, address: str) -> List[str]:
        """查询代币交易记录来发现持有的代币"""
        try:
            params = {
                'module': 'account',
                'action': 'tokentx',
                'address': address,
                'startblock': 0,
                'endblock': 999999999,
                'sort': 'desc',
                'apikey': BSCSCAN_API_KEY
            }
            
            response = self.session.get(BSCSCAN_API_URL, params=params, timeout=30)
            data = response.json()
            
            if data['status'] == '1':
                # 收集所有涉及过的代币合约
                token_contracts = set()
                for tx in data['result'][:50]:  # 只检查最近的50条
                    token_contracts.add(tx['contractAddress'].lower())
                return list(token_contracts)
            
        except Exception as e:
            self.logger.debug(f"查询代币交易记录失败: {e}")
        
        return []
    
    def 查询地址持仓(self, address: str) -> Dict:
        """查询地址完整持仓信息"""
        self.logger.info(f"🔍 查询BSC地址: {address}")
        
        result = {
            'address': address,
            'chain': 'BSC',
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'bnb_balance': 0,
            'tokens': []
        }
        
        # 查询BNB
        bnb_balance = self.查询BNB余额(address)
        if bnb_balance:
            result['bnb_balance'] = bnb_balance['balance']
            if bnb_balance['balance'] > 0:
                result['tokens'].append(bnb_balance)
        
        # 查询常用代币
        for symbol, contract in POPULAR_BSC_TOKENS.items():
            token_balance = self.查询代币余额(address, contract, symbol)
            if token_balance:
                result['tokens'].append(token_balance)
            time.sleep(0.2)  # 避免请求过快
        
        # 按余额排序
        result['tokens'].sort(key=lambda x: x['balance'], reverse=True)
        
        return result
    
    def 批量查询(self, addresses: List[str]) -> List[Dict]:
        """批量查询多个地址"""
        results = []
        
        print("=" * 70)
        print("🙏 千手财童 - BSC主网持仓查询")
        print("=" * 70)
        print(f"查询地址数: {len(addresses)}")
        print(f"数据来源: BscScan (BSC主网)")
        print("=" * 70)
        
        for i, addr in enumerate(addresses, 1):
            print(f"\n[{i}/{len(addresses)}] 查询地址: {addr}")
            result = self.查询地址持仓(addr)
            results.append(result)
            self._打印持仓结果(result)
            time.sleep(1)  # 避免请求过快
        
        return results
    
    def _打印持仓结果(self, result: Dict):
        """打印持仓结果"""
        addr = result['address']
        bnb_balance = result['bnb_balance']
        tokens = result['tokens']
        
        print(f"\n{'='*70}")
        print(f"📍 地址: {addr}")
        print(f"⛓️  链: BSC (Binance Smart Chain)")
        print(f"⏱️  查询时间: {result['query_time']}")
        print(f"{'='*70}")
        
        # BNB
        print(f"\n💎 BNB (币安币)")
        print(f"   余额: {bnb_balance:.6f} BNB")
        
        # 代币
        erc20_tokens = [t for t in tokens if t['symbol'] != 'BNB']
        if erc20_tokens:
            print(f"\n🪙 BEP-20 代币 ({len(erc20_tokens)} 种):")
            print(f"\n{'代币':<12} {'余额':>25} {'合约地址':>30}")
            print("-" * 70)
            
            for token in erc20_tokens:
                symbol = token['symbol']
                balance = token['balance']
                contract = token['contract']
                
                print(f"{symbol:<12} {balance:>25.6f} {contract[:30]:>30}")
        else:
            print("\n🪙 BEP-20 代币: 未持有常用代币")
        
        print(f"\n{'='*70}")


if __name__ == "__main__":
    # 要查询的地址列表
    addresses = [
        "0x7852346c77b3a622fa73607ee35cc784e53f326b",
        "0x97a1c2efb9cafb6ef1f149bf2b8f3285871e342b",
        "0x95701259b045f972b06089e5ba498d463f627aa2"
    ]
    
    # 创建查询实例
    财童 = 千手财童BSC查询()
    
    # 执行查询
    results = 财童.批量查询(addresses)
    
    print("\n" + "=" * 70)
    print("✅ BSC查询完成!")
    print("=" * 70)
