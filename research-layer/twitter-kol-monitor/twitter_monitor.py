#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter KOL监控模块
用于监控指定KOL的推文，分析情绪并提取交易信号
"""

import os
import sys
import json
import sqlite3
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 默认KOL列表
DEFAULT_KOLS = [
    "cz_binance",
    "VitalikButerin", 
    "elonmusk"
]

# 数据库路径
DB_PATH = os.path.expanduser("~/.openclaw/workspace/quant-trading/data/market_data.db")

# 情绪关键词字典
SENTIMENT_KEYWORDS = {
    'positive': [
        'bullish', 'pump', 'moon', 'rocket', 'gain', 'profit', 'buy', 'long',
        '看涨', '买入', '做多', '暴涨', '牛市', '赚钱', '利好', '突破',
        'good', 'great', 'excellent', 'amazing', 'awesome', 'love', 'like',
        'support', 'strong', 'growth', 'opportunity', 'promising'
    ],
    'negative': [
        'bearish', 'dump', 'crash', 'bear', 'sell', 'short', 'loss', 'scam',
        '看跌', '卖出', '做空', '暴跌', '熊市', '亏损', '利空', '崩盘',
        'bad', 'terrible', 'awful', 'hate', 'dislike', 'fear', 'panic',
        'risk', 'danger', 'warning', 'alert', 'avoid'
    ]
}

# 交易信号关键词
TRADING_SIGNALS = {
    'buy': [
        'buy', 'bought', 'buying', 'long', 'entry', 'accumulate',
        '买入', '做多', '建仓', '加仓', '抄底', '进场'
    ],
    'sell': [
        'sell', 'sold', 'selling', 'short', 'exit', 'dump',
        '卖出', '做空', '清仓', '减仓', '逃顶', '离场'
    ]
}


@dataclass
class Tweet:
    """推文数据类"""
    id: str
    author: str
    text: str
    created_at: str
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    trading_signal: Optional[str] = None
    signal_confidence: float = 0.0
    collected_at: str = ""
    
    def __post_init__(self):
        if not self.collected_at:
            self.collected_at = datetime.now().isoformat()


class TwitterMonitor:
    """Twitter KOL监控器"""
    
    def __init__(self, db_path: str = DB_PATH, kols: List[str] = None):
        """
        初始化监控器
        
        Args:
            db_path: SQLite数据库路径
            kols: 要监控的KOL用户名列表
        """
        self.db_path = db_path
        self.kols = kols or DEFAULT_KOLS.copy()
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_db()
        
    def _init_db(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建推文表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tweets (
                    id TEXT PRIMARY KEY,
                    author TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    sentiment TEXT DEFAULT 'neutral',
                    sentiment_score REAL DEFAULT 0.0,
                    trading_signal TEXT,
                    signal_confidence REAL DEFAULT 0.0,
                    collected_at TEXT NOT NULL
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tweets_author ON tweets(author)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tweets_signal ON tweets(trading_signal)
            ''')
            
            conn.commit()
            conn.close()
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _get_user_id(self, username: str) -> Optional[str]:
        """
        通过用户名获取用户ID
        
        Args:
            username: Twitter用户名
            
        Returns:
            用户ID或None
        """
        if not self.bearer_token:
            logger.warning("未设置TWITTER_BEARER_TOKEN，无法获取用户ID")
            return None
            
        try:
            url = f"https://api.twitter.com/2/users/by/username/{username}"
            cmd = [
                'curl', '-s', url,
                '-H', f'Authorization: Bearer {self.bearer_token}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            data = json.loads(result.stdout)
            
            if 'data' in data:
                return data['data']['id']
            else:
                logger.warning(f"无法获取用户 {username} 的ID: {data}")
                return None
                
        except Exception as e:
            logger.error(f"获取用户ID失败 {username}: {e}")
            return None
    
    def fetch_tweets(self, username: str, max_results: int = 10) -> List[Tweet]:
        """
        获取指定用户的推文
        
        Args:
            username: Twitter用户名
            max_results: 最大获取推文数
            
        Returns:
            Tweet对象列表
        """
        tweets = []
        
        if not self.bearer_token:
            logger.warning("未设置TWITTER_BEARER_TOKEN，使用模拟数据")
            return self._generate_mock_tweets(username)
        
        try:
            # 获取用户ID
            user_id = self._get_user_id(username)
            if not user_id:
                return tweets
            
            # 获取推文
            url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = f"?max_results={max_results}&tweet.fields=created_at"
            
            cmd = [
                'curl', '-s', f"{url}{params}",
                '-H', f'Authorization: Bearer {self.bearer_token}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            data = json.loads(result.stdout)
            
            if 'data' in data:
                for item in data['data']:
                    tweet = Tweet(
                        id=item['id'],
                        author=username,
                        text=item['text'],
                        created_at=item['created_at']
                    )
                    tweets.append(tweet)
            else:
                logger.warning(f"获取推文失败: {data}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"获取推文超时: {username}")
        except json.JSONDecodeError as e:
            logger.error(f"解析推文JSON失败: {e}")
        except Exception as e:
            logger.error(f"获取推文失败 {username}: {e}")
            
        return tweets
    
    def _generate_mock_tweets(self, username: str) -> List[Tweet]:
        """
        生成模拟推文数据（用于测试）
        
        Args:
            username: Twitter用户名
            
        Returns:
            Tweet对象列表
        """
        mock_data = {
            "cz_binance": [
                "Bitcoin looking bullish today! 🚀 #BTC #crypto",
                "Market is recovering, good time to accumulate",
                "Stay safe, don't fall for scams"
            ],
            "VitalikButerin": [
                "Ethereum 2.0 progress update coming soon",
                "Layer 2 solutions are the future of scaling",
                "Decentralization matters more than speed"
            ],
            "elonmusk": [
                "Dogecoin to the moon! 🐕🌙",
                "Crypto markets are volatile, be careful",
                "Innovation in blockchain continues to amaze me"
            ]
        }
        
        tweets = []
        texts = mock_data.get(username, ["Test tweet for " + username])
        
        for i, text in enumerate(texts):
            tweet = Tweet(
                id=f"mock_{username}_{i}",
                author=username,
                text=text,
                created_at=(datetime.now() - timedelta(hours=i)).isoformat()
            )
            tweets.append(tweet)
            
        return tweets
    
    def analyze_sentiment(self, tweet: Tweet) -> Tweet:
        """
        分析推文情绪
        
        Args:
            tweet: Tweet对象
            
        Returns:
            更新后的Tweet对象
        """
        text_lower = tweet.text.lower()
        
        positive_count = sum(1 for word in SENTIMENT_KEYWORDS['positive'] if word in text_lower)
        negative_count = sum(1 for word in SENTIMENT_KEYWORDS['negative'] if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            tweet.sentiment = "neutral"
            tweet.sentiment_score = 0.0
        else:
            score = (positive_count - negative_count) / total
            tweet.sentiment_score = round(score, 2)
            
            if score > 0.2:
                tweet.sentiment = "positive"
            elif score < -0.2:
                tweet.sentiment = "negative"
            else:
                tweet.sentiment = "neutral"
                
        return tweet
    
    def extract_trading_signal(self, tweet: Tweet) -> Tweet:
        """
        提取交易信号
        
        Args:
            tweet: Tweet对象
            
        Returns:
            更新后的Tweet对象
        """
        text_lower = tweet.text.lower()
        
        buy_signals = sum(1 for word in TRADING_SIGNALS['buy'] if word in text_lower)
        sell_signals = sum(1 for word in TRADING_SIGNALS['sell'] if word in text_lower)
        
        if buy_signals > sell_signals and buy_signals > 0:
            tweet.trading_signal = "buy"
            tweet.signal_confidence = min(buy_signals * 0.3, 1.0)
        elif sell_signals > buy_signals and sell_signals > 0:
            tweet.trading_signal = "sell"
            tweet.signal_confidence = min(sell_signals * 0.3, 1.0)
        else:
            tweet.trading_signal = None
            tweet.signal_confidence = 0.0
            
        return tweet
    
    def save_tweet(self, tweet: Tweet) -> bool:
        """
        保存推文到数据库
        
        Args:
            tweet: Tweet对象
            
        Returns:
            是否保存成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO tweets 
                (id, author, text, created_at, sentiment, sentiment_score, 
                 trading_signal, signal_confidence, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tweet.id, tweet.author, tweet.text, tweet.created_at,
                tweet.sentiment, tweet.sentiment_score,
                tweet.trading_signal, tweet.signal_confidence, tweet.collected_at
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"保存推文失败: {e}")
            return False
    
    def check_tweet_exists(self, tweet_id: str) -> bool:
        """
        检查推文是否已存在
        
        Args:
            tweet_id: 推文ID
            
        Returns:
            是否存在
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM tweets WHERE id = ?', (tweet_id,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception as e:
            logger.error(f"检查推文存在性失败: {e}")
            return False
    
    def monitor_kol(self, username: str) -> List[Tweet]:
        """
        监控单个KOL
        
        Args:
            username: Twitter用户名
            
        Returns:
            新推文列表
        """
        logger.info(f"开始监控KOL: {username}")
        
        # 获取推文
        tweets = self.fetch_tweets(username)
        new_tweets = []
        
        for tweet in tweets:
            # 检查是否已存在
            if self.check_tweet_exists(tweet.id):
                continue
                
            # 分析情绪
            tweet = self.analyze_sentiment(tweet)
            
            # 提取交易信号
            tweet = self.extract_trading_signal(tweet)
            
            # 保存到数据库
            if self.save_tweet(tweet):
                new_tweets.append(tweet)
                logger.info(f"保存新推文 - {username}: {tweet.text[:50]}...")
                
                # 如果有交易信号，记录日志
                if tweet.trading_signal:
                    logger.info(f"🚨 发现交易信号! {username}: {tweet.trading_signal} "
                              f"(置信度: {tweet.signal_confidence:.2f})")
        
        logger.info(f"监控完成 - {username}: 发现 {len(new_tweets)} 条新推文")
        return new_tweets
    
    def monitor_all(self) -> Dict[str, List[Tweet]]:
        """
        监控所有KOL
        
        Returns:
            每个KOL的新推文字典
        """
        results = {}
        
        for kol in self.kols:
            try:
                new_tweets = self.monitor_kol(kol)
                results[kol] = new_tweets
            except Exception as e:
                logger.error(f"监控 {kol} 时出错: {e}")
                results[kol] = []
                
        return results
    
    def get_recent_signals(self, hours: int = 24) -> List[Tweet]:
        """
        获取最近的交易信号
        
        Args:
            hours: 最近多少小时
            
        Returns:
            包含交易信号的推文列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute('''
                SELECT id, author, text, created_at, sentiment, sentiment_score,
                       trading_signal, signal_confidence, collected_at
                FROM tweets
                WHERE trading_signal IS NOT NULL
                  AND created_at > ?
                ORDER BY created_at DESC
            ''', (since,))
            
            rows = cursor.fetchall()
            conn.close()
            
            tweets = []
            for row in rows:
                tweet = Tweet(
                    id=row[0],
                    author=row[1],
                    text=row[2],
                    created_at=row[3],
                    sentiment=row[4],
                    sentiment_score=row[5],
                    trading_signal=row[6],
                    signal_confidence=row[7],
                    collected_at=row[8]
                )
                tweets.append(tweet)
                
            return tweets
            
        except Exception as e:
            logger.error(f"获取交易信号失败: {e}")
            return []
    
    def get_kol_stats(self, username: str, days: int = 7) -> Dict:
        """
        获取KOL统计信息
        
        Args:
            username: KOL用户名
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 总推文数
            cursor.execute('''
                SELECT COUNT(*) FROM tweets 
                WHERE author = ? AND created_at > ?
            ''', (username, since))
            total_tweets = cursor.fetchone()[0]
            
            # 情绪分布
            cursor.execute('''
                SELECT sentiment, COUNT(*) FROM tweets 
                WHERE author = ? AND created_at > ?
                GROUP BY sentiment
            ''', (username, since))
            sentiment_dist = dict(cursor.fetchall())
            
            # 交易信号统计
            cursor.execute('''
                SELECT trading_signal, COUNT(*), AVG(signal_confidence)
                FROM tweets 
                WHERE author = ? AND created_at > ? AND trading_signal IS NOT NULL
                GROUP BY trading_signal
            ''', (username, since))
            signal_stats = {}
            for row in cursor.fetchall():
                signal_stats[row[0]] = {
                    'count': row[1],
                    'avg_confidence': round(row[2], 2) if row[2] else 0
                }
            
            conn.close()
            
            return {
                'username': username,
                'period_days': days,
                'total_tweets': total_tweets,
                'sentiment_distribution': sentiment_dist,
                'trading_signals': signal_stats
            }
            
        except Exception as e:
            logger.error(f"获取KOL统计失败: {e}")
            return {}


def main():
    """主函数 - 命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Twitter KOL监控工具')
    parser.add_argument('--kols', nargs='+', help='要监控的KOL用户名列表')
    parser.add_argument('--db', default=DB_PATH, help='数据库路径')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--signals', action='store_true', help='显示最近交易信号')
    parser.add_argument('--hours', type=int, default=24, help='查询最近几小时的数据')
    
    args = parser.parse_args()
    
    # 初始化监控器
    kols = args.kols if args.kols else DEFAULT_KOLS
    monitor = TwitterMonitor(db_path=args.db, kols=kols)
    
    if args.stats:
        # 显示统计信息
        for kol in kols:
            stats = monitor.get_kol_stats(kol)
            print(f"\n📊 {kol} 统计信息:")
            print(json.dumps(stats, indent=2, ensure_ascii=False))
            
    elif args.signals:
        # 显示交易信号
        signals = monitor.get_recent_signals(hours=args.hours)
        print(f"\n🚨 最近 {args.hours} 小时的交易信号:")
        for tweet in signals:
            print(f"\n[{tweet.author}] {tweet.trading_signal.upper()} "
                  f"(置信度: {tweet.signal_confidence:.2f})")
            print(f"  内容: {tweet.text[:100]}...")
            print(f"  时间: {tweet.created_at}")
            
    else:
        # 执行监控
        print("🚀 开始监控KOL推文...")
        results = monitor.monitor_all()
        
        total_new = sum(len(tweets) for tweets in results.values())
        print(f"\n✅ 监控完成! 共发现 {total_new} 条新推文")
        
        # 显示新推文
        for kol, tweets in results.items():
            if tweets:
                print(f"\n📱 {kol} ({len(tweets)} 条新推文):")
                for tweet in tweets:
                    signal_info = f" [{tweet.trading_signal.upper()}]" if tweet.trading_signal else ""
                    print(f"  - {tweet.text[:60]}... ({tweet.sentiment}){signal_info}")


if __name__ == "__main__":
    main()
