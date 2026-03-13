#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gmgn.ai 冲狗数据抓取模块
用于抓取gmgn.ai网站的新币列表、聪明钱包追踪和热度指标数据
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import requests
from playwright.async_api import async_playwright, Page, Browser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = Path("~/.openclaw/workspace/quant-trading/data/market_data.db").expanduser()


@dataclass
class NewToken:
    """新币数据结构"""
    token_address: str
    symbol: str
    name: str
    created_at: datetime
    market_cap: float
    liquidity: float
    volume_24h: float
    price: float
    price_change_24h: float
    holder_count: int
    twitter_url: Optional[str] = None
    website_url: Optional[str] = None
    fetched_at: datetime = None
    
    def __post_init__(self):
        if self.fetched_at is None:
            self.fetched_at = datetime.now()


@dataclass
class SmartWallet:
    """聪明钱包数据结构"""
    wallet_address: str
    token_address: str
    token_symbol: str
    action: str  # 'buy' or 'sell'
    amount: float
    price: float
    value_usd: float
    tx_hash: str
    timestamp: datetime
    pnl_24h: Optional[float] = None
    win_rate: Optional[float] = None
    fetched_at: datetime = None
    
    def __post_init__(self):
        if self.fetched_at is None:
            self.fetched_at = datetime.now()


@dataclass
class TokenHeat:
    """代币热度数据结构"""
    token_address: str
    symbol: str
    heat_score: float  # 热度分数 0-100
    social_mentions: int  # 社交提及次数
    twitter_sentiment: float  # 推特情绪分数 -1到1
    smart_money_inflow: float  # 聪明钱流入
    buy_pressure: float  # 买入压力
    sell_pressure: float  # 卖出压力
    trending_rank: int  #  trending排名
    fetched_at: datetime = None
    
    def __post_init__(self):
        if self.fetched_at is None:
            self.fetched_at = datetime.now()


class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_tables()
    
    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _init_tables(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 新币列表表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gmgn_new_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    created_at TIMESTAMP,
                    market_cap REAL,
                    liquidity REAL,
                    volume_24h REAL,
                    price REAL,
                    price_change_24h REAL,
                    holder_count INTEGER,
                    twitter_url TEXT,
                    website_url TEXT,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(token_address, fetched_at)
                )
            """)
            
            # 聪明钱包追踪表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gmgn_smart_wallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_address TEXT NOT NULL,
                    token_address TEXT NOT NULL,
                    token_symbol TEXT,
                    action TEXT,
                    amount REAL,
                    price REAL,
                    value_usd REAL,
                    tx_hash TEXT,
                    timestamp TIMESTAMP,
                    pnl_24h REAL,
                    win_rate REAL,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tx_hash, wallet_address)
                )
            """)
            
            # 代币热度表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gmgn_token_heat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT NOT NULL,
                    symbol TEXT,
                    heat_score REAL,
                    social_mentions INTEGER,
                    twitter_sentiment REAL,
                    smart_money_inflow REAL,
                    buy_pressure REAL,
                    sell_pressure REAL,
                    trending_rank INTEGER,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(token_address, fetched_at)
                )
            """)
            
            # 创建索引优化查询
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_new_tokens_address 
                ON gmgn_new_tokens(token_address)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_smart_wallets_address 
                ON gmgn_smart_wallets(wallet_address)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_token_heat_address 
                ON gmgn_token_heat(token_address)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_token_heat_score 
                ON gmgn_token_heat(heat_score DESC)
            """)
            
            conn.commit()
            logger.info("数据库表初始化完成")
    
    def save_new_tokens(self, tokens: List[NewToken]):
        """保存新币列表到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for token in tokens:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO gmgn_new_tokens 
                        (token_address, symbol, name, created_at, market_cap, liquidity,
                         volume_24h, price, price_change_24h, holder_count,
                         twitter_url, website_url, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        token.token_address, token.symbol, token.name,
                        token.created_at, token.market_cap, token.liquidity,
                        token.volume_24h, token.price, token.price_change_24h,
                        token.holder_count, token.twitter_url, token.website_url,
                        token.fetched_at
                    ))
                except sqlite3.Error as e:
                    logger.error(f"保存新币数据失败 {token.symbol}: {e}")
            conn.commit()
            logger.info(f"成功保存 {len(tokens)} 条新币数据")
    
    def save_smart_wallets(self, wallets: List[SmartWallet]):
        """保存聪明钱包数据到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for wallet in wallets:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO gmgn_smart_wallets 
                        (wallet_address, token_address, token_symbol, action, amount,
                         price, value_usd, tx_hash, timestamp, pnl_24h, win_rate, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        wallet.wallet_address, wallet.token_address, wallet.token_symbol,
                        wallet.action, wallet.amount, wallet.price, wallet.value_usd,
                        wallet.tx_hash, wallet.timestamp, wallet.pnl_24h, wallet.win_rate,
                        wallet.fetched_at
                    ))
                except sqlite3.Error as e:
                    logger.error(f"保存聪明钱包数据失败 {wallet.wallet_address}: {e}")
            conn.commit()
            logger.info(f"成功保存 {len(wallets)} 条聪明钱包数据")
    
    def save_token_heat(self, heats: List[TokenHeat]):
        """保存代币热度数据到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for heat in heats:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO gmgn_token_heat 
                        (token_address, symbol, heat_score, social_mentions,
                         twitter_sentiment, smart_money_inflow, buy_pressure,
                         sell_pressure, trending_rank, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        heat.token_address, heat.symbol, heat.heat_score,
                        heat.social_mentions, heat.twitter_sentiment,
                        heat.smart_money_inflow, heat.buy_pressure,
                        heat.sell_pressure, heat.trending_rank, heat.fetched_at
                    ))
                except sqlite3.Error as e:
                    logger.error(f"保存热度数据失败 {heat.symbol}: {e}")
            conn.commit()
            logger.info(f"成功保存 {len(heats)} 条热度数据")
    
    def get_hot_tokens(self, limit: int = 20, min_heat_score: float = 50.0) -> List[Dict]:
        """获取热门代币列表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM gmgn_token_heat 
                WHERE heat_score >= ? 
                ORDER BY heat_score DESC 
                LIMIT ?
            """, (min_heat_score, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_smart_wallet_activity(self, wallet_address: Optional[str] = None, 
                                   limit: int = 100) -> List[Dict]:
        """获取聪明钱包活动"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if wallet_address:
                cursor.execute("""
                    SELECT * FROM gmgn_smart_wallets 
                    WHERE wallet_address = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (wallet_address, limit))
            else:
                cursor.execute("""
                    SELECT * FROM gmgn_smart_wallets 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]


class GmgnFetcher:
    """gmgn.ai 数据抓取器"""
    
    BASE_URL = "https://gmgn.ai"
    API_BASE = "https://gmgn.ai/defi/router/v1"
    
    def __init__(self, use_playwright: bool = True, headless: bool = True):
        self.use_playwright = use_playwright
        self.headless = headless
        self.db = DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self.use_playwright:
            await self._init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.browser:
            await self.browser.close()
    
    async def _init_browser(self):
        """初始化Playwright浏览器"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.page = await self.browser.new_page()
            await self.page.set_viewport_size({'width': 1920, 'height': 1080})
            logger.info("浏览器初始化成功")
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            raise
    
    async def _fetch_with_playwright(self, url: str, wait_for: Optional[str] = None,
                                      timeout: int = 30000) -> str:
        """使用Playwright抓取页面"""
        if not self.page:
            raise RuntimeError("浏览器未初始化")
        
        try:
            await self.page.goto(url, wait_until='networkidle', timeout=timeout)
            if wait_for:
                await self.page.wait_for_selector(wait_for, timeout=timeout)
            # 等待页面加载完成
            await asyncio.sleep(2)
            content = await self.page.content()
            return content
        except Exception as e:
            logger.error(f"Playwright抓取失败 {url}: {e}")
            raise
    
    def _fetch_with_requests(self, url: str, params: Optional[Dict] = None) -> Dict:
        """使用requests抓取API数据"""
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Requests请求失败 {url}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise
    
    async def fetch_new_tokens(self, limit: int = 50) -> List[NewToken]:
        """
        获取新币列表
        
        Args:
            limit: 获取数量限制
            
        Returns:
            新币列表
        """
        tokens = []
        
        try:
            # 尝试使用API获取
            url = f"{self.API_BASE}/sol/tokens/new_tokens"
            params = {
                'limit': limit,
                'orderby': 'market_cap',
                'direction': 'desc'
            }
            
            if self.use_playwright and self.page:
                # 使用Playwright访问页面并提取数据
                page_url = f"{self.BASE_URL}/?chain=sol"
                await self._fetch_with_playwright(page_url, wait_for='.token-list')
                
                # 执行JavaScript提取数据
                data = await self.page.evaluate("""
                    () => {
                        const tokens = [];
                        const rows = document.querySelectorAll('.token-list .token-item');
                        rows.forEach(row => {
                            const token = {
                                address: row.getAttribute('data-address'),
                                symbol: row.querySelector('.token-symbol')?.textContent,
                                name: row.querySelector('.token-name')?.textContent,
                                marketCap: row.querySelector('.market-cap')?.textContent,
                                price: row.querySelector('.token-price')?.textContent,
                                volume: row.querySelector('.volume-24h')?.textContent
                            };
                            tokens.push(token);
                        });
                        return tokens;
                    }
                """)
                
                # 解析数据
                for item in data:
                    try:
                        token = NewToken(
                            token_address=item.get('address', ''),
                            symbol=item.get('symbol', 'Unknown'),
                            name=item.get('name', ''),
                            created_at=datetime.now(),
                            market_cap=self._parse_number(item.get('marketCap', '0')),
                            liquidity=0.0,
                            volume_24h=self._parse_number(item.get('volume', '0')),
                            price=self._parse_number(item.get('price', '0')),
                            price_change_24h=0.0,
                            holder_count=0
                        )
                        tokens.append(token)
                    except Exception as e:
                        logger.warning(f"解析token数据失败: {e}")
            else:
                # 使用requests
                response = self._fetch_with_requests(url, params)
                for item in response.get('data', {}).get('list', []):
                    try:
                        token = NewToken(
                            token_address=item.get('address', ''),
                            symbol=item.get('symbol', 'Unknown'),
                            name=item.get('name', ''),
                            created_at=datetime.fromtimestamp(item.get('created_at', 0)),
                            market_cap=float(item.get('market_cap', 0)),
                            liquidity=float(item.get('liquidity', 0)),
                            volume_24h=float(item.get('volume_24h', 0)),
                            price=float(item.get('price', 0)),
                            price_change_24h=float(item.get('price_change_24h', 0)),
                            holder_count=int(item.get('holder_count', 0)),
                            twitter_url=item.get('twitter'),
                            website_url=item.get('website')
                        )
                        tokens.append(token)
                    except Exception as e:
                        logger.warning(f"解析token数据失败: {e}")
            
            logger.info(f"成功获取 {len(tokens)} 个新币")
            
            # 保存到数据库
            if tokens:
                self.db.save_new_tokens(tokens)
            
        except Exception as e:
            logger.error(f"获取新币列表失败: {e}")
        
        return tokens
    
    async def fetch_smart_wallets(self, token_address: Optional[str] = None,
                                   limit: int = 100) -> List[SmartWallet]:
        """
        获取聪明钱包交易数据
        
        Args:
            token_address: 特定代币地址，None则获取所有
            limit: 获取数量限制
            
        Returns:
            聪明钱包交易列表
        """
        wallets = []
        
        try:
            if self.use_playwright and self.page:
                # 构建URL
                if token_address:
                    page_url = f"{self.BASE_URL}/token/{token_address}"
                else:
                    page_url = f"{self.BASE_URL}/smart-money"
                
                await self._fetch_with_playwright(page_url, wait_for='.wallet-list')
                
                # 提取聪明钱包数据
                data = await self.page.evaluate("""
                    () => {
                        const wallets = [];
                        const rows = document.querySelectorAll('.wallet-list .wallet-item');
                        rows.forEach(row => {
                            const wallet = {
                                address: row.getAttribute('data-address'),
                                action: row.querySelector('.action')?.textContent?.toLowerCase(),
                                amount: row.querySelector('.amount')?.textContent,
                                price: row.querySelector('.price')?.textContent,
                                value: row.querySelector('.value')?.textContent,
                                txHash: row.querySelector('.tx-hash')?.textContent,
                                timestamp: row.querySelector('.timestamp')?.textContent
                            };
                            wallets.push(wallet);
                        });
                        return wallets;
                    }
                """)
                
                for item in data:
                    try:
                        wallet = SmartWallet(
                            wallet_address=item.get('address', ''),
                            token_address=token_address or '',
                            token_symbol='',
                            action='buy' if 'buy' in item.get('action', '') else 'sell',
                            amount=self._parse_number(item.get('amount', '0')),
                            price=self._parse_number(item.get('price', '0')),
                            value_usd=self._parse_number(item.get('value', '0')),
                            tx_hash=item.get('txHash', ''),
                            timestamp=datetime.now()  # 简化处理
                        )
                        wallets.append(wallet)
                    except Exception as e:
                        logger.warning(f"解析钱包数据失败: {e}")
            else:
                # 使用API
                url = f"{self.API_BASE}/sol/wallets/smart_money"
                params = {'limit': limit}
                if token_address:
                    params['token_address'] = token_address
                
                response = self._fetch_with_requests(url, params)
                for item in response.get('data', {}).get('list', []):
                    try:
                        wallet = SmartWallet(
                            wallet_address=item.get('wallet_address', ''),
                            token_address=item.get('token_address', ''),
                            token_symbol=item.get('token_symbol', ''),
                            action=item.get('action', 'buy'),
                            amount=float(item.get('amount', 0)),
                            price=float(item.get('price', 0)),
                            value_usd=float(item.get('value_usd', 0)),
                            tx_hash=item.get('tx_hash', ''),
                            timestamp=datetime.fromtimestamp(item.get('timestamp', 0)),
                            pnl_24h=float(item.get('pnl_24h', 0)) if item.get('pnl_24h') else None,
                            win_rate=float(item.get('win_rate', 0)) if item.get('win_rate') else None
                        )
                        wallets.append(wallet)
                    except Exception as e:
                        logger.warning(f"解析钱包数据失败: {e}")
            
            logger.info(f"成功获取 {len(wallets)} 条聪明钱包数据")
            
            # 保存到数据库
            if wallets:
                self.db.save_smart_wallets(wallets)
            
        except Exception as e:
            logger.error(f"获取聪明钱包数据失败: {e}")
        
        return wallets
    
    async def fetch_token_heat(self, limit: int = 50) -> List[TokenHeat]:
        """
        获取代币热度指标
        
        Args:
            limit: 获取数量限制
            
        Returns:
            代币热度列表
        """
        heats = []
        
        try:
            if self.use_playwright and self.page:
                page_url = f"{self.BASE_URL}/trending"
                await self._fetch_with_playwright(page_url, wait_for='.trending-list')
                
                # 提取热度数据
                data = await self.page.evaluate("""
                    () => {
                        const heats = [];
                        const rows = document.querySelectorAll('.trending-list .token-item');
                        rows.forEach((row, index) => {
                            const heat = {
                                address: row.getAttribute('data-address'),
                                symbol: row.querySelector('.token-symbol')?.textContent,
                                heatScore: row.querySelector('.heat-score')?.textContent,
                                mentions: row.querySelector('.social-mentions')?.textContent,
                                sentiment: row.querySelector('.sentiment')?.textContent,
                                inflow: row.querySelector('.smart-inflow')?.textContent,
                                rank: index + 1
                            };
                            heats.push(heat);
                        });
                        return heats;
                    }
                """)
                
                for item in data:
                    try:
                        heat = TokenHeat(
                            token_address=item.get('address', ''),
                            symbol=item.get('symbol', 'Unknown'),
                            heat_score=self._parse_number(item.get('heatScore', '0')),
                            social_mentions=int(self._parse_number(item.get('mentions', '0'))),
                            twitter_sentiment=0.0,  # 需要额外计算
                            smart_money_inflow=self._parse_number(item.get('inflow', '0')),
                            buy_pressure=0.0,
                            sell_pressure=0.0,
                            trending_rank=item.get('rank', 0)
                        )
                        heats.append(heat)
                    except Exception as e:
                        logger.warning(f"解析热度数据失败: {e}")
            else:
                # 使用API
                url = f"{self.API_BASE}/sol/tokens/trending"
                params = {'limit': limit}
                
                response = self._fetch_with_requests(url, params)
                for item in response.get('data', {}).get('list', []):
                    try:
                        heat = TokenHeat(
                            token_address=item.get('address', ''),
                            symbol=item.get('symbol', 'Unknown'),
                            heat_score=float(item.get('heat_score', 0)),
                            social_mentions=int(item.get('social_mentions', 0)),
                            twitter_sentiment=float(item.get('twitter_sentiment', 0)),
                            smart_money_inflow=float(item.get('smart_money_inflow', 0)),
                            buy_pressure=float(item.get('buy_pressure', 0)),
                            sell_pressure=float(item.get('sell_pressure', 0)),
                            trending_rank=int(item.get('rank', 0))
                        )
                        heats.append(heat)
                    except Exception as e:
                        logger.warning(f"解析热度数据失败: {e}")
            
            logger.info(f"成功获取 {len(heats)} 条热度数据")
            
            # 保存到数据库
            if heats:
                self.db.save_token_heat(heats)
            
        except Exception as e:
            logger.error(f"获取热度数据失败: {e}")
        
        return heats
    
    def _parse_number(self, value: str) -> float:
        """解析数字字符串，处理K、M、B等后缀"""
        if not value:
            return 0.0
        
        value = str(value).strip().replace('$', '').replace(',', '').replace('%', '')
        
        multipliers = {
            'K': 1e3,
            'M': 1e6,
            'B': 1e9,
            'T': 1e12
        }
        
        for suffix, multiplier in multipliers.items():
            if suffix in value.upper():
                try:
                    return float(value.upper().replace(suffix, '')) * multiplier
                except ValueError:
                    return 0.0
        
        try:
            return float(value)
        except ValueError:
            return 0.0
    
    def calculate_heat_metrics(self, token_address: str) -> Dict[str, Any]:
        """
        计算特定代币的热度指标
        
        Args:
            token_address: 代币地址
            
        Returns:
            热度指标字典
        """
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取代币基本信息
                cursor.execute("""
                    SELECT * FROM gmgn_new_tokens 
                    WHERE token_address = ? 
                    ORDER BY fetched_at DESC LIMIT 1
                """, (token_address,))
                token_info = cursor.fetchone()
                
                # 获取聪明钱包活动
                cursor.execute("""
                    SELECT COUNT(*) as tx_count,
                           SUM(CASE WHEN action = 'buy' THEN value_usd ELSE 0 END) as buy_volume,
                           SUM(CASE WHEN action = 'sell' THEN value_usd ELSE 0 END) as sell_volume
                    FROM gmgn_smart_wallets 
                    WHERE token_address = ? 
                    AND timestamp > datetime('now', '-24 hours')
                """, (token_address,))
                wallet_stats = cursor.fetchone()
                
                # 获取热度历史
                cursor.execute("""
                    SELECT heat_score, social_mentions 
                    FROM gmgn_token_heat 
                    WHERE token_address = ? 
                    ORDER BY fetched_at DESC LIMIT 7
                """, (token_address,))
                heat_history = cursor.fetchall()
                
                metrics = {
                    'token_address': token_address,
                    'symbol': token_info[2] if token_info else 'Unknown',
                    'current_price': token_info[8] if token_info else 0,
                    'price_change_24h': token_info[9] if token_info else 0,
                    'smart_wallet_tx_count': wallet_stats[0] if wallet_stats else 0,
                    'buy_volume_24h': wallet_stats[1] if wallet_stats else 0,
                    'sell_volume_24h': wallet_stats[2] if wallet_stats else 0,
                    'net_flow': (wallet_stats[1] or 0) - (wallet_stats[2] or 0),
                    'heat_trend': [h[0] for h in heat_history] if heat_history else [],
                    'mentions_trend': [h[1] for h in heat_history] if heat_history else [],
                    'calculated_at': datetime.now()
                }
                
                return metrics
                
        except Exception as e:
            logger.error(f"计算热度指标失败: {e}")
            return {}


async def main():
    """主函数 - 示例用法"""
    # 创建抓取器实例
    async with GmgnFetcher(use_playwright=True, headless=True) as fetcher:
        # 获取新币列表
        logger.info("开始获取新币列表...")
        new_tokens = await fetcher.fetch_new_tokens(limit=50)
        print(f"\n新币列表 ({len(new_tokens)}个):")
        for token in new_tokens[:10]:
            print(f"  {token.symbol}: ${token.price:.6f} | 市值: ${token.market_cap:,.0f}")
        
        # 获取聪明钱包数据
        logger.info("开始获取聪明钱包数据...")
        smart_wallets = await fetcher.fetch_smart_wallets(limit=100)
        print(f"\n聪明钱包活动 ({len(smart_wallets)}条):")
        for wallet in smart_wallets[:10]:
            print(f"  {wallet.wallet_address[:8]}... {wallet.action} ${wallet.value_usd:,.2f}")
        
        # 获取代币热度
        logger.info("开始获取代币热度...")
        token_heats = await fetcher.fetch_token_heat(limit=50)
        print(f"\n热门代币 ({len(token_heats)}个):")
        for heat in token_heats[:10]:
            print(f"  {heat.symbol}: 热度 {heat.heat_score:.1f} | 排名 #{heat.trending_rank}")
        
        # 计算特定代币的热度指标
        if new_tokens:
            sample_token = new_tokens[0].token_address
            metrics = fetcher.calculate_heat_metrics(sample_token)
            print(f"\n代币 {metrics.get('symbol', 'Unknown')} 热度分析:")
            print(f"  价格变化(24h): {metrics.get('price_change_24h', 0):.2f}%")
            print(f"  聪明钱包交易: {metrics.get('smart_wallet_tx_count', 0)}次")
            print(f"  净流入: ${metrics.get('net_flow', 0):,.2f}")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
