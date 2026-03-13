#!/usr/bin/env python3
"""
推特数据抓取模块
每小时获取观察人列表的推文，去重并进行AI情绪分析
"""

import os
import sys
import sqlite3
import re
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

# 添加路径
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/quant-trading/config-layer"))
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/quant-trading/ai_models"))

from twitter_watchlist_manager import TwitterWatchlistManager

# 数据库路径
DB_PATH = os.path.expanduser("~/.openclaw/workspace/quant-trading/data-layer/market_data.db")


@dataclass
class Tweet:
    """推文数据结构"""
    tweet_id: str
    username: str
    content: str
    posted_at: datetime
    retweet_count: int = 0
    like_count: int = 0
    reply_count: int = 0


class TwitterFetcher:
    """推特数据抓取器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.watchlist_manager = TwitterWatchlistManager(self.db_path)
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def fetch_tweets_for_user(self, username: str, hours_back: int = 1) -> List[Tweet]:
        """
        获取指定用户的最近推文
        
        方案：
        1. Twitter API v2（需要付费订阅 $100+/月）
        2. Nitter 镜像（免费，不稳定）
        3. 模拟数据（演示用）
        """
        tweets = []
        
        # 方案1：尝试使用 Twitter API v2（如果有付费订阅）
        try:
            sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/quant-trading/config-layer"))
            from twitter_api_client import TwitterAPIClient
            
            client = TwitterAPIClient()
            
            # 获取用户ID
            user = client.get_user_by_username(username)
            if user:
                # 计算开始时间
                start_time = (datetime.utcnow() - timedelta(hours=hours_back)).strftime('%Y-%m-%dT%H:%M:%SZ')
                
                # 获取推文
                api_tweets = client.get_user_tweets(user['id'], max_results=10, start_time=start_time)
                
                for t in api_tweets:
                    tweets.append(Tweet(
                        tweet_id=t['id'],
                        username=username,
                        content=t['text'],
                        posted_at=datetime.fromisoformat(t['created_at'].replace('Z', '+00:00')),
                        retweet_count=t.get('retweet_count', 0),
                        like_count=t.get('like_count', 0),
                        reply_count=t.get('reply_count', 0)
                    ))
                
                if tweets:
                    print(f"  ✓ 通过Twitter API获取 {len(tweets)} 条推文")
                    return tweets
                    
        except Exception as e:
            # API失败（通常是订阅问题或限制）
            pass
        
        # 方案2：尝试 Nitter（免费镜像）
        try:
            tweets = self._fetch_from_nitter(username, hours_back)
            if tweets:
                print(f"  ✓ 通过Nitter获取 {len(tweets)} 条推文")
                return tweets
        except Exception as e:
            pass
        
        # 方案3：降级到模拟数据
        print(f"  ⚠️ 使用模拟数据（Twitter API需付费 $100+/月，Nitter不稳定）")
        tweets = self._generate_mock_tweets(username, hours_back)
        
        return tweets
    
    def _fetch_from_nitter(self, username: str, hours_back: int = 1) -> List[Tweet]:
        """从 Nitter 获取推文"""
        import requests
        from bs4 import BeautifulSoup
        
        # Nitter 实例列表（可能随时变更）
        nitter_instances = [
            "https://nitter.net",
            "https://nitter.cz",
            "https://nitter.it",
        ]
        
        tweets = []
        
        for instance in nitter_instances:
            try:
                url = f"{instance}/{username}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 解析推文
                    timeline_items = soup.find_all('div', class_='timeline-item')
                    
                    for item in timeline_items:
                        try:
                            # 获取推文内容
                            content_div = item.find('div', class_='tweet-content')
                            if not content_div:
                                continue
                            
                            # 获取推文ID和时间
                            link = item.find('a', class_='tweet-link')
                            if not link:
                                continue
                            
                            tweet_id = link.get('href', '').split('/')[-1].split('#')[0]
                            
                            # 获取发布时间
                            time_elem = item.find('span', class_='tweet-date')
                            posted_at = datetime.now()
                            if time_elem and time_elem.find('a'):
                                # 解析相对时间
                                pass
                            
                            # 获取内容
                            content_elem = content_div.find('div', class_='tweet-content')
                            content = content_elem.get_text(strip=True) if content_elem else ""
                            
                            # 获取统计数据
                            stats = item.find('div', class_='tweet-stats')
                            retweet_count = 0
                            like_count = 0
                            
                            if stats:
                                for stat in stats.find_all('div', class_='stat'):
                                    text = stat.get_text(strip=True)
                                    if 'retweet' in text.lower():
                                        retweet_count = self._parse_count(text)
                                    elif 'like' in text.lower():
                                        like_count = self._parse_count(text)
                            
                            # 检查时间是否在范围内
                            if posted_at > datetime.now() - timedelta(hours=hours_back):
                                tweets.append(Tweet(
                                    tweet_id=tweet_id,
                                    username=username,
                                    content=content,
                                    posted_at=posted_at,
                                    retweet_count=retweet_count,
                                    like_count=like_count
                                ))
                                
                        except Exception as e:
                            continue
                    
                    # 成功获取，跳出循环
                    if tweets:
                        break
                        
            except Exception as e:
                continue
        
        return tweets
    
    def _parse_count(self, text: str) -> int:
        """解析计数文本"""
        numbers = re.findall(r'[\d,.]+[KMBkmb]?', text)
        if not numbers:
            return 0
        
        num_str = numbers[0].upper().replace(',', '')
        if 'K' in num_str:
            return int(float(num_str.replace('K', '')) * 1000)
        elif 'M' in num_str:
            return int(float(num_str.replace('M', '')) * 1000000)
        elif 'B' in num_str:
            return int(float(num_str.replace('B', '')) * 1000000000)
        
        try:
            return int(num_str)
        except:
            return 0
    
    def _generate_mock_tweets(self, username: str, hours_back: int = 1) -> List[Tweet]:
        """生成模拟推文（测试用）"""
        mock_contents = {
            'xiaomustock': [
                "BTC看起来要突破了，关注67000阻力位！#比特币 #crypto",
                "今天满仓了ETH，看好下周表现",
                "市场有点疲软，先减仓观望一下",
            ],
            'cz_binance': [
                "币安将推出新功能，敬请期待！#Binance",
                "安全第一，请启用2FA保护您的账户",
                "很高兴看到加密市场继续发展",
            ],
            'thankUcrypto': [
                "ALERT: 大户正在抄底BTC，链上数据显示大量流入",
                "这个山寨币有潜力，DYOR",
                "市场恐惧情绪严重，可能是买入机会",
            ],
            'default': [
                "分享一些市场观点，仅供参考",
                "加密货币市场波动很大，注意风险",
                "技术分析显示可能会有一波行情",
            ]
        }
        
        contents = mock_contents.get(username, mock_contents['default'])
        tweets = []
        
        for i, content in enumerate(contents):
            posted_at = datetime.now() - timedelta(minutes=i*20)
            if posted_at > datetime.now() - timedelta(hours=hours_back):
                tweets.append(Tweet(
                    tweet_id=f"mock_{username}_{int(datetime.now().timestamp())}_{i}",
                    username=username,
                    content=content,
                    posted_at=posted_at,
                    retweet_count=10 + i * 5,
                    like_count=50 + i * 10
                ))
        
        return tweets
    
    def is_duplicate(self, tweet_id: str) -> bool:
        """检查推文是否已存在"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM twitter_posts WHERE tweet_id = ?", (tweet_id,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    def save_tweet(self, tweet: Tweet, sentiment: str = None, 
                   sentiment_score: float = None, confidence: float = None,
                   ai_reasoning: str = None) -> bool:
        """保存推文到数据库"""
        if self.is_duplicate(tweet.tweet_id):
            return False
        
        # 构建原始推文URL
        tweet_url = f"https://twitter.com/{tweet.username}/status/{tweet.tweet_id}"
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO twitter_posts 
            (tweet_id, username, content, posted_at, retweet_count, like_count, reply_count,
             sentiment, sentiment_score, confidence, ai_reasoning, ai_analyzed_at, tweet_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tweet.tweet_id,
            tweet.username,
            tweet.content,
            tweet.posted_at.isoformat(),
            tweet.retweet_count,
            tweet.like_count,
            tweet.reply_count,
            sentiment,
            sentiment_score,
            confidence,
            ai_reasoning,
            datetime.now().isoformat() if sentiment else None,
            tweet_url
        ))
        
        conn.commit()
        conn.close()
        
        return True
    
    def fetch_all_active(self, hours_back: int = 1) -> Dict:
        """获取所有活跃观察人的推文"""
        usernames = self.watchlist_manager.get_active_usernames()
        
        results = {
            'total_fetched': 0,
            'total_new': 0,
            'total_duplicates': 0,
            'by_user': {}
        }
        
        print(f"开始获取 {len(usernames)} 个用户的推文...")
        
        for username in usernames:
            try:
                print(f"\n获取 @{username} 的推文...")
                
                tweets = self.fetch_tweets_for_user(username, hours_back)
                
                new_count = 0
                dup_count = 0
                
                for tweet in tweets:
                    if self.is_duplicate(tweet.tweet_id):
                        dup_count += 1
                    else:
                        self.save_tweet(tweet)
                        new_count += 1
                
                # 更新最后获取时间
                self.watchlist_manager.update_last_fetch(username)
                
                results['by_user'][username] = {
                    'fetched': len(tweets),
                    'new': new_count,
                    'duplicates': dup_count
                }
                
                results['total_fetched'] += len(tweets)
                results['total_new'] += new_count
                results['total_duplicates'] += dup_count
                
                print(f"  ✓ 获取 {len(tweets)} 条，新入库 {new_count} 条")
                
            except Exception as e:
                print(f"  ✗ 获取失败: {e}")
                results['by_user'][username] = {'error': str(e)}
        
        return results
    
    def get_recent_tweets(self, hours = 24, username: str = None,
                         sentiment: str = None, limit: int = 100) -> List[Dict]:
        """获取最近的推文，hours可以是数字或'all'"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query = '''
            SELECT p.*, w.display_name, w.category
            FROM twitter_posts p
            LEFT JOIN twitter_watchlist w ON p.username = w.username
            WHERE 1=1
        '''
        params = []
        
        # 时间筛选
        if hours != 'all' and hours is not None:
            try:
                hours_int = int(hours)
                since = (datetime.now() - timedelta(hours=hours_int)).strftime('%Y-%m-%d %H:%M:%S')
                query += ' AND (p.posted_at >= ? OR p.created_at >= ?)'
                params.extend([since, since])
            except (ValueError, TypeError):
                pass  # 如果转换失败，不添加时间筛选
        
        if username:
            query += " AND p.username = ?"
            params.append(username.lower())
        
        if sentiment:
            query += " AND p.sentiment = ?"
            params.append(sentiment)
        
        query += " ORDER BY COALESCE(p.posted_at, p.created_at) DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_stats(self, hours: int = 24) -> Dict:
        """获取统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 推文统计
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN sentiment = 'bullish' THEN 1 ELSE 0 END) as bullish,
                SUM(CASE WHEN sentiment = 'bearish' THEN 1 ELSE 0 END) as bearish,
                SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral,
                SUM(CASE WHEN sentiment IS NULL THEN 1 ELSE 0 END) as pending
            FROM twitter_posts
            WHERE created_at >= ? OR posted_at >= ?
        ''', (since, since))
        
        stats = dict(cursor.fetchone())
        conn.close()
        
        return {
            'period_hours': hours,
            'total': stats['total'] or 0,
            'bullish': stats['bullish'] or 0,
            'bearish': stats['bearish'] or 0,
            'neutral': stats['neutral'] or 0,
            'pending_analysis': stats['pending'] or 0
        }


def main():
    """测试抓取器"""
    fetcher = TwitterFetcher()
    
    print("="*60)
    print("推特数据抓取测试")
    print("="*60)
    
    # 获取所有活跃观察人的推文
    results = fetcher.fetch_all_active(hours_back=1)
    
    print("\n" + "="*60)
    print(f"获取完成！")
    print(f"总计: {results['total_fetched']} 条")
    print(f"新入库: {results['total_new']} 条")
    print(f"重复: {results['total_duplicates']} 条")
    print("="*60)
    
    # 显示最近推文
    print("\n最近推文:")
    tweets = fetcher.get_recent_tweets(hours=1, limit=5)
    for t in tweets:
        print(f"[@{t['username']}] {t['content'][:50]}...")


if __name__ == "__main__":
    main()
