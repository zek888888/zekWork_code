#!/usr/bin/env python3
"""
千手财童 - Solana主网链上数据查询
使用Solana RPC API
"""

import os
import sys
import requests
import json
import base64
from typing import List, Dict
from datetime import datetime
import time

# Solana RPC 配置
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

# 常用SPL代币合约地址 (Mint Address)
POPULAR_SPL_TOKENS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
    "SRM": "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",
    "COPE": "8HGyAAB1yoM1ttS7pXjHMa3dukTFGQggnFFH3hJZgzQh",
    "STEP": "StepAscQoEioFxxWGnh2sLBDFp9d8rvKz2Yp39iDpyT",
    "MEDIA": "ETAtLmCmsoiEEKfNrHKJ2kYy3MoABhS6NLQE92fqgdr",
    "MER": "MERtDfcL9weHy5uF7w6thhFyjiC13r6jYQpX4xrwNi",
    "SLRS": "SLRSSpSLUTP7okMGCAjTV4Z3CjsKrxfTpjTaNbD8YXp",
    "ATLAS": "ATLASXmbPQxBUYbxPsV97usA3fPQXEq7QdBvusdFX4Xj",
    "POLIS": "poLisWXnNRwC6oBu1vKiuTfvmjq6NaLL98jb9VwBCv5",
    "BOP": "BopXqtWCbkKYALCkp92SDx4NGiQ3TNozfPPD39uqJMX",
    "LIKE": "3bRTivrVsitbmCTGtqwp7hxXPsybkjn4XLNtPsHqa3zR",
    "MSOL": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",
    "STSOL": "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj",
}

class 千手财童SOL查询:
    """千手财童 - Solana链上数据查询模块"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def _setup_logger(self):
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - 千手财童 - %(levelname)s - %(message)s'
        )
        return logging.getLogger('千手财童SOL')
    
    def _rpc调用(self, method: str, params: list) -> Dict:
        """调用Solana RPC"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params
            }
            
            response = self.session.post(SOLANA_RPC_URL, json=payload, timeout=30)
            data = response.json()
            
            if 'result' in data:
                return data['result']
            else:
                self.logger.debug(f"RPC错误: {data.get('error', {})}")
                return {}
                
        except Exception as e:
            self.logger.debug(f"RPC调用异常: {e}")
            return {}
    
    def 查询SOL余额(self, address: str) -> float:
        """查询地址SOL余额"""
        try:
            result = self._rpc调用("getBalance", [address])
            if result and 'value' in result:
                lamports = result['value']
                sol = lamports / 10**9
                return sol
            return 0.0
        except Exception as e:
            self.logger.debug(f"查询SOL余额失败: {e}")
            return 0.0
    
    def 查询代币账户(self, address: str) -> List[Dict]:
        """查询地址所有代币账户"""
        try:
            # 使用getTokenAccountsByOwner
            params = [
                address,
                {
                    "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
                },
                {
                    "encoding": "jsonParsed"
                }
            ]
            
            result = self._rpc调用("getTokenAccountsByOwner", params)
            
            if result and 'value' in result:
                return result['value']
            return []
            
        except Exception as e:
            self.logger.debug(f"查询代币账户失败: {e}")
            return []
    
    def 查询代币余额(self, address: str) -> List[Dict]:
        """查询地址所有代币余额"""
        tokens = []
        
        try:
            accounts = self.查询代币账户(address)
            
            for account in accounts:
                try:
                    parsed = account.get('account', {}).get('data', {}).get('parsed', {})
                    info = parsed.get('info', {})
                    
                    mint = info.get('mint', '')
                    token_amount = info.get('tokenAmount', {})
                    amount = float(token_amount.get('uiAmount', 0))
                    decimals = token_amount.get('decimals', 0)
                    
                    if amount > 0:
                        # 查找代币符号
                        symbol = self._查找代币符号(mint)
                        
                        tokens.append({
                            'symbol': symbol,
                            'mint': mint,
                            'balance': amount,
                            'decimals': decimals
                        })
                except:
                    continue
            
            # 按余额排序
            tokens.sort(key=lambda x: x['balance'], reverse=True)
            
        except Exception as e:
            self.logger.debug(f"查询代币余额异常: {e}")
        
        return tokens
    
    def _查找代币符号(self, mint: str) -> str:
        """根据Mint地址查找代币符号"""
        for symbol, address in POPULAR_SPL_TOKENS.items():
            if address.lower() == mint.lower():
                return symbol
        return mint[:8] + "..."
    
    def 查询地址持仓(self, address: str) -> Dict:
        """查询地址完整持仓信息"""
        self.logger.info(f"🔍 查询Solana地址: {address}")
        
        result = {
            'address': address,
            'chain': 'Solana',
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sol_balance': 0,
            'tokens': []
        }
        
        # 查询SOL
        result['sol_balance'] = self.查询SOL余额(address)
        
        # 查询代币
        result['tokens'] = self.查询代币余额(address)
        
        return result
    
    def 批量查询(self, addresses: List[str]) -> List[Dict]:
        """批量查询多个地址"""
        results = []
        
        print("=" * 70)
        print("🙏 千手财童 - Solana主网持仓查询")
        print("=" * 70)
        print(f"查询地址数: {len(addresses)}")
        print(f"数据来源: Solana Mainnet RPC")
        print("=" * 70)
        
        for i, addr in enumerate(addresses, 1):
            print(f"\n[{i}/{len(addresses)}] 查询地址: {addr}")
            result = self.查询地址持仓(addr)
            results.append(result)
            self._打印持仓结果(result)
            time.sleep(0.5)  # 避免请求过快
        
        return results
    
    def _打印持仓结果(self, result: Dict):
        """打印持仓结果"""
        addr = result['address']
        sol_balance = result['sol_balance']
        tokens = result['tokens']
        
        print(f"\n{'='*70}")
        print(f"📍 地址: {addr}")
        print(f"⛓️  链: Solana (主网)")
        print(f"⏱️  查询时间: {result['query_time']}")
        print(f"{'='*70}")
        
        # SOL
        print(f"\n💎 SOL (Solana原生代币)")
        print(f"   余额: {sol_balance:.9f} SOL")
        
        # 代币
        if tokens:
            print(f"\n🪙 SPL 代币 ({len(tokens)} 种):")
            print(f"\n{'代币':<12} {'余额':>25} {'Mint地址':>30}")
            print("-" * 70)
            
            for token in tokens:
                symbol = token['symbol']
                balance = token['balance']
                mint = token['mint']
                
                print(f"{symbol:<12} {balance:>25.6f} {mint[:30]:>30}")
        else:
            print("\n🪙 SPL 代币: 未持有")
        
        print(f"\n{'='*70}")


if __name__ == "__main__":
    # 要查询的地址列表 (以太坊地址格式，需要检查是否是有效的Solana地址)
    # 注意：以太坊地址格式不适用于Solana，Solana地址是Base58编码的
    # 这里提供几个常见的Solana地址格式示例
    
    # 由于用户给的是以太坊地址格式，这些地址在Solana上可能不存在
    # 我将尝试查询，但预期结果可能是空
    
    addresses = [
        "0x7852346c77b3a622fa73607ee35cc784e53f326b",
        "0x97a1c2efb9cafb6ef1f149bf2b8f3285871e342b",
        "0x95701259b045f972b06089e5ba498d463f627aa2"
    ]
    
    print("⚠️  注意：您提供的地址是以太坊格式 (0x...)")
    print("   Solana地址格式不同 (例如: 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU)")
    print("   将尝试查询这些地址在Solana上的状态...\n")
    
    # 创建查询实例
    财童 = 千手财童SOL查询()
    
    # 执行查询
    results = 财童.批量查询(addresses)
    
    print("\n" + "=" * 70)
    print("✅ Solana查询完成!")
    print("=" * 70)
    print("\n📌 说明:")
    print("   如果查询结果为0，可能是因为:")
    print("   1. 这些是以太坊地址，不是Solana地址")
    print("   2. 地址在Solana上确实没有持仓")
    print("\n   如需查询正确的Solana地址，请提供Base58格式的地址")
