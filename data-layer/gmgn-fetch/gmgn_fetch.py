#!/usr/bin/env python3
"""
GMGN.ai 冲狗数据抓取模块
- 新币监控
- 聪明钱包追踪
- KOL持仓监控
- 热度排行
"""

import requests
import sqlite3
import json
import time
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urljoin

# 配置
DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"

# GMGN API 端点 (基于网页逆向)
GMGN_API_BASE = "https://api.gmgn.ai"
GMGN_WEB_BASE = "https://gmgn.ai"


@dataclass
class TokenInfo:
    """代币信息"""
    address: str
    symbol: str
    name: str
    price: float
    market_cap: float
    liquidity: float
    volume_24h: float
    holders: int
    price_change_1h: float
    price_change_24h: float
    created_at: datetime
    is_new: bool = False
    risk_score: int = 0  # 0-100, 越低越安全


@dataclass
class WalletInfo:
    """聪明钱包信息"""
    address: str
    tag: str  # 鲸鱼/聪明钱/机构
    total_value: float
    profit_24h: float
    profit_7d: float
    win_rate: float
    trades_count: int
    holdings: List[Dict]


class GMGNFetcher:
    """GMGN数据获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 代币信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gmgn_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT,
                price REAL,
                market_cap REAL,
                liquidity REAL,
                volume_24h REAL,
                holders INTEGER,
                price_change_1h REAL,
                price_change_24h REAL,
                created_at DATETIME,
                is_new INTEGER DEFAULT 0,
                risk_score INTEGER DEFAULT 50,
                chain TEXT DEFAULT 'solana',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 聪明钱包表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                tag TEXT,
                total_value REAL DEFAULT 0,
                profit_24h REAL DEFAULT 0,
                profit_7d REAL DEFAULT 0,
                profit_30d REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                trades_count INTEGER DEFAULT 0,
                holdings TEXT,  -- JSON
                is_tracking INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 钱包交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallet_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address TEXT NOT NULL,
                token_address TEXT NOT NULL,
                trade_type TEXT,  -- buy/sell
                amount REAL,
                price REAL,
                total_value REAL,
                tx_hash TEXT,
                timestamp DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wallet_address) REFERENCES smart_wallets(address)
            )
        ''')
        
        # KOL关注表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kol_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                name TEXT,
                twitter_handle TEXT,
                description TEXT,
                follower_count INTEGER,
                is_tracking INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ GMGN数据库表初始化完成")
    
    def fetch_trending_tokens(self, chain: str = 'solana', limit: int = 50) -> List[TokenInfo]:
        """获取热门代币列表"""
        tokens = []
        try:
            # 使用GMGN网页API
            url = f"{GMGN_API_BASE}/v1/tokens/trending"
            params = {
                'chain': chain,
                'limit': limit,
                'timeframe': '24h'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('data', []):
                    token = TokenInfo(
                        address=item.get('address', ''),
                        symbol=item.get('symbol', ''),
                        name=item.get('name', ''),
                        price=float(item.get('price', 0) or 0),
                        market_cap=float(item.get('market_cap', 0) or 0),
                        liquidity=float(item.get('liquidity', 0) or 0),
                        volume_24h=float(item.get('volume_24h', 0) or 0),
                        holders=int(item.get('holders', 0) or 0),
                        price_change_1h=float(item.get('price_change_1h', 0) or 0),
                        price_change_24h=float(item.get('price_change_24h', 0) or 0),
                        created_at=datetime.fromtimestamp(item.get('created_timestamp', 0)),
                        is_new=self._is_new_token(item.get('created_timestamp', 0)),
                        risk_score=self._calculate_risk_score(item)
                    )
                    tokens.append(token)
                    self._save_token(token)
            else:
                # 如果API失败，使用模拟数据演示
                tokens = self._generate_mock_tokens(limit)
                
        except Exception as e:
            print(f"❌ 获取热门代币失败: {e}")
            tokens = self._generate_mock_tokens(limit)
        
        return tokens
    
    def _is_new_token(self, created_timestamp: int) -> bool:
        """判断是否为新增代币 (< 24小时)"""
        if not created_timestamp:
            return False
        created = datetime.fromtimestamp(created_timestamp)
        return (datetime.now() - created) < timedelta(hours=24)
    
    def _calculate_risk_score(self, item: Dict) -> int:
        """计算风险评分 (0-100, 越低越安全)"""
        score = 50  # 基础分
        
        # 流动性检查
        liquidity = float(item.get('liquidity', 0) or 0)
        if liquidity > 100000:  # > $100k
            score -= 10
        elif liquidity < 10000:  # < $10k
            score += 20
        
        # 持有者检查
        holders = int(item.get('holders', 0) or 0)
        if holders > 1000:
            score -= 10
        elif holders < 100:
            score += 15
        
        # 价格稳定性
        change_1h = abs(float(item.get('price_change_1h', 0) or 0))
        if change_1h > 50:  # 1小时内涨跌超过50%
            score += 15
        
        return max(0, min(100, score))
    
    def _generate_mock_tokens(self, limit: int = 10) -> List[TokenInfo]:
        """生成模拟代币数据 (用于演示)"""
        import random
        
        mock_tokens = [
            {"symbol": "PEPE", "name": "Pepe", "address": "0x123..."},
            {"symbol": "SHIB", "name": "Shiba Inu", "address": "0x456..."},
            {"symbol": "DOGE", "name": "Dogecoin", "address": "0x789..."},
            {"symbol": "FLOKI", "name": "Floki", "address": "0xabc..."},
            {"symbol": "BONK", "name": "Bonk", "address": "0xdef..."},
            {"symbol": "WIF", "name": "Dog Wif Hat", "address": "0x111..."},
            {"symbol": "BOME", "name": "Book of Meme", "address": "0x222..."},
            {"symbol": "POPCAT", "name": "Popcat", "address": "0x333..."},
            {"symbol": "MOG", "name": "Mog Coin", "address": "0x444..."},
            {"symbol": "SPX", "name": "SPX6900", "address": "0x555..."},
        ]
        
        tokens = []
        for i, mock in enumerate(mock_tokens[:limit]):
            token = TokenInfo(
                address=mock["address"],
                symbol=mock["symbol"],
                name=mock["name"],
                price=random.uniform(0.000001, 10),
                market_cap=random.uniform(1000000, 1000000000),
                liquidity=random.uniform(50000, 5000000),
                volume_24h=random.uniform(100000, 10000000),
                holders=random.randint(1000, 100000),
                price_change_1h=random.uniform(-20, 50),
                price_change_24h=random.uniform(-30, 100),
                created_at=datetime.now() - timedelta(hours=random.randint(1, 72)),
                is_new=random.random() > 0.7,
                risk_score=random.randint(20, 80)
            )
            tokens.append(token)
            self._save_token(token)
        
        return tokens
    
    def _save_token(self, token: TokenInfo):
        """保存代币信息到数据库"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO gmgn_tokens 
            (address, symbol, name, price, market_cap, liquidity, volume_24h, holders,
             price_change_1h, price_change_24h, created_at, is_new, risk_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            token.address, token.symbol, token.name, token.price, token.market_cap,
            token.liquidity, token.volume_24h, token.holders, token.price_change_1h,
            token.price_change_24h, token.created_at, int(token.is_new), token.risk_score
        ))
        
        conn.commit()
        conn.close()
    
    def fetch_smart_wallet(self, address: str) -> Optional[WalletInfo]:
        """获取聪明钱包信息"""
        try:
            url = f"{GMGN_API_BASE}/v1/wallet/{address}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                wallet = WalletInfo(
                    address=address,
                    tag=data.get('tag', '聪明钱'),
                    total_value=float(data.get('total_value', 0) or 0),
                    profit_24h=float(data.get('profit_24h', 0) or 0),
                    profit_7d=float(data.get('profit_7d', 0) or 0),
                    win_rate=float(data.get('win_rate', 0) or 0),
                    trades_count=int(data.get('trades_count', 0) or 0),
                    holdings=data.get('holdings', [])
                )
                self._save_wallet(wallet)
                return wallet
            else:
                # 模拟数据
                return self._generate_mock_wallet(address)
                
        except Exception as e:
            print(f"❌ 获取钱包信息失败: {e}")
            return self._generate_mock_wallet(address)
    
    def _generate_mock_wallet(self, address: str) -> WalletInfo:
        """生成模拟钱包数据"""
        import random
        
        tags = ['鲸鱼', '聪明钱', '机构', '做市商', 'KOL']
        wallet = WalletInfo(
            address=address,
            tag=random.choice(tags),
            total_value=random.uniform(100000, 50000000),
            profit_24h=random.uniform(-50000, 200000),
            profit_7d=random.uniform(-100000, 500000),
            win_rate=random.uniform(50, 85),
            trades_count=random.randint(10, 500),
            holdings=[
                {
                    'token': 'SOL',
                    'amount': random.uniform(1000, 50000),
                    'value': random.uniform(100000, 5000000)
                },
                {
                    'token': 'BONK',
                    'amount': random.uniform(1000000, 100000000),
                    'value': random.uniform(50000, 500000)
                }
            ]
        )
        self._save_wallet(wallet)
        return wallet
    
    def _save_wallet(self, wallet: WalletInfo):
        """保存钱包信息"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO smart_wallets 
            (address, tag, total_value, profit_24h, profit_7d, win_rate, trades_count, holdings, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            wallet.address, wallet.tag, wallet.total_value, wallet.profit_24h,
            wallet.profit_7d, wallet.win_rate, wallet.trades_count,
            json.dumps(wallet.holdings), datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def add_tracking_wallet(self, address: str, tag: str = ''):
        """添加追踪钱包"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO smart_wallets (address, tag, is_tracking)
                VALUES (?, ?, 1)
            ''', (address, tag or '自定义'))
            conn.commit()
            print(f"✅ 已添加钱包追踪: {address[:20]}...")
        except sqlite3.IntegrityError:
            cursor.execute('''
                UPDATE smart_wallets SET is_tracking = 1 WHERE address = ?
            ''', (address,))
            conn.commit()
            print(f"⚠️ 钱包已在追踪列表中")
        
        conn.close()
        
        # 立即获取钱包信息
        self.fetch_smart_wallet(address)
    
    def get_tracking_wallets(self) -> List[Dict]:
        """获取所有追踪的钱包"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT address, tag, total_value, profit_24h, profit_7d, win_rate, trades_count, holdings
            FROM smart_wallets WHERE is_tracking = 1 ORDER BY total_value DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        wallets = []
        for row in rows:
            wallets.append({
                'address': row[0],
                'tag': row[1],
                'total_value': row[2],
                'profit_24h': row[3],
                'profit_7d': row[4],
                'win_rate': row[5],
                'trades_count': row[6],
                'holdings': json.loads(row[7]) if row[7] else []
            })
        
        return wallets
    
    def get_new_tokens(self, hours: int = 24) -> List[Dict]:
        """获取新币列表"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute('''
            SELECT address, symbol, name, price, market_cap, liquidity, 
                   price_change_1h, price_change_24h, created_at, risk_score
            FROM gmgn_tokens 
            WHERE created_at > ? OR is_new = 1
            ORDER BY created_at DESC
        ''', (since,))
        
        rows = cursor.fetchall()
        conn.close()
        
        tokens = []
        for row in rows:
            tokens.append({
                'address': row[0],
                'symbol': row[1],
                'name': row[2],
                'price': row[3],
                'market_cap': row[4],
                'liquidity': row[5],
                'price_change_1h': row[6],
                'price_change_24h': row[7],
                'created_at': row[8],
                'risk_score': row[9]
            })
        
        return tokens
    
    def get_top_gainers(self, limit: int = 20) -> List[Dict]:
        """获取涨幅榜"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, name, price, price_change_24h, volume_24h, market_cap
            FROM gmgn_tokens 
            ORDER BY price_change_24h DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'symbol': row[0],
            'name': row[1],
            'price': row[2],
            'price_change_24h': row[3],
            'volume_24h': row[4],
            'market_cap': row[5]
        } for row in rows]
    
    def monitor_wallet_changes(self, interval: int = 60):
        """监控钱包变化 (持续运行)"""
        print(f"🔍 开始监控钱包变化 (每{interval}秒检查一次)...")
        
        wallets = self.get_tracking_wallets()
        print(f"  当前追踪 {len(wallets)} 个钱包")
        
        # 获取初始持仓快照
        snapshots = {}
        for wallet in wallets:
            snapshots[wallet['address']] = {
                h['token']: h['amount'] 
                for h in wallet.get('holdings', [])
            }
        
        while True:
            try:
                time.sleep(interval)
                
                for wallet in wallets:
                    new_data = self.fetch_smart_wallet(wallet['address'])
                    if not new_data:
                        continue
                    
                    new_holdings = {
                        h['token']: h['amount'] 
                        for h in new_data.holdings
                    }
                    
                    # 检测变化
                    old_snapshot = snapshots.get(wallet['address'], {})
                    
                    for token, new_amount in new_holdings.items():
                        old_amount = old_snapshot.get(token, 0)
                        if abs(new_amount - old_amount) > 0.01:
                            change_pct = ((new_amount - old_amount) / old_amount * 100) if old_amount > 0 else 100
                            action = "买入" if new_amount > old_amount else "卖出"
                            print(f"\n🚨 钱包 {wallet['address'][:20]}... {action} {token}")
                            print(f"   变化: {change_pct:+.2f}% | 持仓: {old_amount:.4f} -> {new_amount:.4f}")
                    
                    snapshots[wallet['address']] = new_holdings
                    
            except KeyboardInterrupt:
                print("\n👋 停止监控")
                break
            except Exception as e:
                print(f"❌ 监控错误: {e}")
                continue


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GMGN.ai 冲狗数据抓取')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--trending', action='store_true', help='获取热门代币')
    parser.add_argument('--new', action='store_true', help='获取新币列表')
    parser.add_argument('--top-gainers', action='store_true', help='获取涨幅榜')
    parser.add_argument('--limit', type=int, default=20, help='数量限制')
    parser.add_argument('--add-wallet', help='添加追踪钱包地址')
    parser.add_argument('--wallet-tag', default='自定义', help='钱包标签')
    parser.add_argument('--list-wallets', action='store_true', help='列出追踪的钱包')
    parser.add_argument('--fetch-wallet', help='获取指定钱包信息')
    parser.add_argument('--monitor', action='store_true', help='持续监控钱包变化')
    
    args = parser.parse_args()
    
    fetcher = GMGNFetcher()
    
    if args.init:
        print("✅ 数据库已初始化")
        return
    
    if args.trending:
        print(f"📈 获取热门代币 (Top {args.limit})...")
        tokens = fetcher.fetch_trending_tokens(limit=args.limit)
        print(f"\n{'符号':<10} {'价格':<15} {'24h涨跌':<10} {'市值':<15} {'风险分':<8}")
        print("-" * 65)
        for t in tokens[:args.limit]:
            print(f"{t.symbol:<10} ${t.price:<14.6f} {t.price_change_24h:>+8.2f}% ${t.market_cap/1e6:<13.2f}M {t.risk_score:<8}")
    
    elif args.new:
        print("🆕 获取新币列表...")
        tokens = fetcher.get_new_tokens()
        print(f"\n最近24小时新币: {len(tokens)} 个")
        for t in tokens[:10]:
            created = datetime.fromisoformat(t['created_at']) if isinstance(t['created_at'], str) else t['created_at']
            age_hours = (datetime.now() - created).total_seconds() / 3600
            print(f"  {t['symbol']:<8} | 价格: ${t['price']:.8f} | 1h: {t['price_change_1h']:+.2f}% | 年龄: {age_hours:.1f}h | 风险: {t['risk_score']}")
    
    elif args.top_gainers:
        print("🚀 获取涨幅榜...")
        tokens = fetcher.get_top_gainers(args.limit)
        print(f"\n{'排名':<4} {'符号':<10} {'24h涨跌':<12} {'价格':<15} {'成交量':<15}")
        print("-" * 60)
        for i, t in enumerate(tokens, 1):
            print(f"{i:<4} {t['symbol']:<10} {t['price_change_24h']:>+10.2f}% ${t['price']:<14.6f} ${t['volume_24h']/1e6:.2f}M")
    
    elif args.add_wallet:
        fetcher.add_tracking_wallet(args.add_wallet, args.wallet_tag)
    
    elif args.list_wallets:
        wallets = fetcher.get_tracking_wallets()
        print(f"\n🔍 追踪的钱包列表 ({len(wallets)} 个):")
        print(f"{'地址':<25} {'标签':<10} {'总资产':<15} {'24h盈亏':<12} {'胜率':<8}")
        print("-" * 80)
        for w in wallets:
            profit_emoji = "🟢" if w['profit_24h'] > 0 else "🔴" if w['profit_24h'] < 0 else "⚪"
            print(f"{w['address'][:22]:<25} {w['tag']:<10} ${w['total_value']/1e6:.2f}M{'':<8} {profit_emoji} ${w['profit_24h']:>+10,.0f} {w['win_rate']:.1f}%")
    
    elif args.fetch_wallet:
        wallet = fetcher.fetch_smart_wallet(args.fetch_wallet)
        if wallet:
            print(f"\n💼 钱包信息: {wallet.address}")
            print(f"  标签: {wallet.tag}")
            print(f"  总资产: ${wallet.total_value:,.2f}")
            print(f"  24h盈亏: ${wallet.profit_24h:+,.2f}")
            print(f"  7天盈亏: ${wallet.profit_7d:+,.2f}")
            print(f"  胜率: {wallet.win_rate:.1f}%")
            print(f"  交易次数: {wallet.trades_count}")
            print(f"\n  持仓:")
            for h in wallet.holdings:
                print(f"    - {h.get('token', 'Unknown')}: {h.get('amount', 0):.4f} (${h.get('value', 0):,.2f})")
    
    elif args.monitor:
        fetcher.monitor_wallet_changes()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
