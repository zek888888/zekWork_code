#!/usr/bin/env python3
"""
免费多源新闻获取模块
支持: 新浪财经、加密货币新闻、AI新闻、宏观经济
"""

import os
import sys
import json
import sqlite3
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urlencode

sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/quant-trading/data-layer"))

DB_PATH = os.path.expanduser("~/.openclaw/workspace/quant-trading/data-layer/market_data.db")


class FreeNewsFetcher:
    """免费新闻获取器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def save_news(self, news_list: List[Dict]) -> int:
        """保存新闻到数据库"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        saved_count = 0
        for news in news_list:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO news 
                    (external_id, source, title, content, category, 
                     sentiment_score, sentiment_label, keywords, published_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ''', (
                    news.get('external_id'),
                    news.get('source'),
                    news.get('title'),
                    news.get('content'),
                    news.get('category'),
                    news.get('sentiment_score', 0),
                    news.get('sentiment_label', '中性'),
                    json.dumps(news.get('keywords', []), ensure_ascii=False),
                    news.get('published_at')
                ))
                
                if cursor.rowcount > 0:
                    saved_count += 1
                    
            except Exception as e:
                print(f"  ✗ 保存失败: {e}")
        
        conn.commit()
        conn.close()
        return saved_count
    
    # ==================== 1. 新浪财经 RSS ====================
    def fetch_sina_finance(self) -> List[Dict]:
        """获取新浪财经新闻"""
        print("\n[新浪财经] 获取财经新闻...")
        
        # 新浪财经RSS源
        rss_urls = [
            ('https://rss.sina.com.cn/roll/finance/hot_roll.xml', '财经'),
            ('https://rss.sina.com.cn/roll/stock/hot_roll.xml', '股票'),
            ('https://rss.sina.com.cn/roll/forex/hot_roll.xml', '外汇'),
        ]
        
        news_list = []
        
        for url, category in rss_urls:
            try:
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:10]:  # 每个源取前10条
                    news = {
                        'external_id': f"sina_{entry.get('id', entry.link)}",
                        'source': 'sina_finance',
                        'title': entry.title,
                        'content': entry.get('summary', entry.title),
                        'category': category,
                        'published_at': self._parse_date(entry.get('published')),
                        'keywords': self._extract_keywords(entry.title + entry.get('summary', ''))
                    }
                    news['sentiment_score'], news['sentiment_label'] = self._analyze_sentiment(news['title'])
                    news_list.append(news)
                
                print(f"  ✓ {category}: {len(feed.entries[:10])} 条")
                
            except Exception as e:
                print(f"  ✗ {category}: {e}")
        
        return news_list
    
    # ==================== 2. 金色财经 API ====================
    def fetch_jinse_crypto(self) -> List[Dict]:
        """获取金色财经加密货币新闻"""
        print("\n[金色财经] 获取加密货币新闻...")
        
        # 金色财经API（免费）
        api_url = "https://api.jinse.com/v4/information/list"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.jinse.com/'
        }
        
        news_list = []
        
        try:
            # 获取不同分类的新闻
            categories = [
                ('news', '币快讯'),
                ('politics', '政策'),
                ('technology', '技术'),
            ]
            
            for cat_id, cat_name in categories:
                params = {
                    'catelogue_key': cat_id,
                    'limit': 10,
                    'information_id': 0
                }
                
                response = self.session.get(api_url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, dict) and 'list' in data:
                        items = data['list']
                    elif isinstance(data, list):
                        items = data
                    else:
                        items = []
                    
                    for item in items:
                        news = {
                            'external_id': f"jinse_{item.get('id', '')}",
                            'source': 'jinse_crypto',
                            'title': item.get('title', ''),
                            'content': item.get('content', item.get('summary', item.get('title', ''))),
                            'category': '加密货币',
                            'published_at': self._parse_timestamp(item.get('created_at')),
                            'keywords': ['加密货币', '区块链'] + self._extract_keywords(item.get('title', ''))
                        }
                        news['sentiment_score'], news['sentiment_label'] = self._analyze_sentiment(news['title'])
                        news_list.append(news)
                    
                    print(f"  ✓ {cat_name}: {len(items)} 条")
                
        except Exception as e:
            print(f"  ✗ 获取失败: {e}")
        
        return news_list
    
    # ==================== 3. 币世界 API ====================
    def fetch_bishijie_crypto(self) -> List[Dict]:
        """获取币世界快讯"""
        print("\n[币世界] 获取币圈快讯...")
        
        # 币世界API
        api_url = "https://api.bishijie.com/kuaixun/v1/kuaixun"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36',
            'Referer': 'https://www.bishijie.com/'
        }
        
        news_list = []
        
        try:
            params = {
                'size': 20,
                'client': 'web'
            }
            
            response = self.session.get(api_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('code') == 200 and 'data' in data:
                    items = data['data'].get('list', [])
                    
                    for item in items:
                        news = {
                            'external_id': f"bishijie_{item.get('id', '')}",
                            'source': 'bishijie',
                            'title': item.get('title', ''),
                            'content': item.get('content', item.get('title', '')),
                            'category': '加密货币',
                            'published_at': self._parse_timestamp(item.get('publish_time')),
                            'keywords': ['币圈', '快讯'] + self._extract_keywords(item.get('title', ''))
                        }
                        news['sentiment_score'], news['sentiment_label'] = self._analyze_sentiment(news['title'])
                        news_list.append(news)
                    
                    print(f"  ✓ 快讯: {len(items)} 条")
            else:
                print(f"  ✗ 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ 获取失败: {e}")
        
        return news_list
    
    # ==================== 4. NewsAPI (免费版) ====================
    def fetch_newsapi(self, query: str = None) -> List[Dict]:
        """使用 NewsAPI 获取新闻 (免费版: 100次/天)"""
        print(f"\n[NewsAPI] 获取{'AI' if query else '金融'}新闻...")
        
        # NewsAPI 免费密钥 (共享，可能有限制)
        api_key = "pub_42878e84c0684d9b6f3b9e8e6e5a8b7c5d4e"  # 示例，实际使用时需要替换
        
        base_url = "https://newsapi.org/v2/everything"
        
        queries = {
            'AI': 'artificial intelligence OR AI OR ChatGPT OR OpenAI',
            '金融': 'finance OR stock market OR Federal Reserve',
            '加密货币': 'bitcoin OR crypto OR cryptocurrency',
            '政治': 'politics OR government OR policy',
        }
        
        if query and query in queries:
            search_queries = {query: queries[query]}
        else:
            search_queries = queries
        
        news_list = []
        
        for category, q in search_queries.items():
            try:
                params = {
                    'q': q,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': 5,
                    'apiKey': api_key
                }
                
                response = self.session.get(base_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('status') == 'ok':
                        articles = data.get('articles', [])
                        
                        for article in articles:
                            news = {
                                'external_id': f"newsapi_{article.get('url', '').replace('/', '_')[:50]}",
                                'source': 'newsapi',
                                'title': article.get('title', ''),
                                'content': article.get('description', article.get('title', '')),
                                'category': category,
                                'published_at': article.get('publishedAt'),
                                'keywords': [category] + self._extract_keywords(article.get('title', ''))
                            }
                            news['sentiment_score'], news['sentiment_label'] = self._analyze_sentiment(news['title'])
                            news_list.append(news)
                        
                        print(f"  ✓ {category}: {len(articles)} 条")
                elif response.status_code == 429:
                    print(f"  ✗ API限额已用完")
                    break
                else:
                    print(f"  ✗ {category}: {response.status_code}")
                    
            except Exception as e:
                print(f"  ✗ {category}: {e}")
        
        return news_list
    
    # ==================== 5. 自定义RSS源 ====================
    def fetch_rss_sources(self) -> List[Dict]:
        """获取自定义RSS源"""
        print("\n[RSS聚合] 获取多源新闻...")
        
        rss_sources = [
            # 中文科技/AI
            ('https://www.techweb.com.cn/rss/hot.xml', '科技', 'AI'),
            ('https://www.ithome.com/rss/', '科技', 'IT'),
            # 国际新闻
            ('https://feeds.bbci.co.uk/news/business/rss.xml', '国际', '财经'),
            ('https://feeds.reuters.com/reuters/businessNews', '国际', '财经'),
        ]
        
        news_list = []
        
        for url, category, sub_category in rss_sources:
            try:
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:5]:  # 每个源取前5条
                    news = {
                        'external_id': f"rss_{entry.get('id', entry.link)[:50]}",
                        'source': f'rss_{sub_category}',
                        'title': entry.title,
                        'content': entry.get('summary', entry.title)[:500],
                        'category': category,
                        'published_at': self._parse_date(entry.get('published')),
                        'keywords': [category, sub_category]
                    }
                    news['sentiment_score'], news['sentiment_label'] = self._analyze_sentiment(news['title'])
                    news_list.append(news)
                
                print(f"  ✓ {sub_category}: {len(feed.entries[:5])} 条")
                
            except Exception as e:
                print(f"  ✗ {sub_category}: {e}")
        
        return news_list
    
    # ==================== 工具函数 ====================
    def _parse_date(self, date_str: str) -> str:
        """解析日期字符串"""
        if not date_str:
            return datetime.now().isoformat()
        
        try:
            # 尝试多种格式
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat()
                except:
                    continue
            
            return datetime.now().isoformat()
        except:
            return datetime.now().isoformat()
    
    def _parse_timestamp(self, timestamp) -> str:
        """解析时间戳"""
        if not timestamp:
            return datetime.now().isoformat()
        
        try:
            if isinstance(timestamp, (int, float)):
                # 秒级或毫秒级时间戳
                if timestamp > 1e12:
                    timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp).isoformat()
            else:
                return self._parse_date(str(timestamp))
        except:
            return datetime.now().isoformat()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # 金融关键词
        finance_kw = ['股票', '基金', '债券', '期货', '外汇', '黄金', '美元', '人民币', '美联储', '央行']
        # 加密货币关键词
        crypto_kw = ['BTC', 'ETH', '比特币', '以太坊', '区块链', 'DeFi', 'NFT', '挖矿']
        # AI关键词
        ai_kw = ['AI', '人工智能', 'ChatGPT', 'OpenAI', '大模型', '机器学习', '深度学习']
        # 政治关键词
        politics_kw = ['政策', '监管', '法规', '政治', '政府', '央行', '美联储']
        
        all_keywords = finance_kw + crypto_kw + ai_kw + politics_kw
        
        for kw in all_keywords:
            if kw in text:
                keywords.append(kw)
        
        return list(set(keywords))[:5]  # 最多5个
    
    def _analyze_sentiment(self, text: str) -> tuple:
        """简单情绪分析"""
        bullish = ['涨', '突破', '新高', '利好', '大涨', '暴涨', '反弹', '牛市', '买入', '看好',
                   'up', 'surge', 'breakout', 'bullish', 'rally', 'moon', 'pump']
        bearish = ['跌', '跌破', '新低', '利空', '大跌', '暴跌', '崩盘', '熊市', '卖出', '看空',
                   'down', 'crash', 'dump', 'bearish', 'plunge', 'collapse']
        
        text_lower = text.lower()
        b_count = sum(1 for w in bullish if w in text_lower)
        be_count = sum(1 for w in bearish if w in text_lower)
        
        total = b_count + be_count
        if total == 0:
            return 0, "中性"
        
        score = (b_count - be_count) / total
        
        if score > 0.5:
            return score, "强烈看涨"
        elif score > 0.2:
            return score, "看涨"
        elif score < -0.5:
            return score, "强烈看跌"
        elif score < -0.2:
            return score, "看跌"
        else:
            return score, "中性"
    
    # ==================== 主函数 ====================
    def fetch_all(self) -> Dict:
        """获取所有来源的新闻"""
        print("="*70)
        print("免费多源新闻获取")
        print("="*70)
        
        all_news = []
        stats = {}
        
        # 1. 新浪财经
        sina_news = self.fetch_sina_finance()
        all_news.extend(sina_news)
        stats['sina'] = len(sina_news)
        
        # 2. 金色财经
        jinse_news = self.fetch_jinse_crypto()
        all_news.extend(jinse_news)
        stats['jinse'] = len(jinse_news)
        
        # 3. 币世界
        bishijie_news = self.fetch_bishijie_crypto()
        all_news.extend(bishijie_news)
        stats['bishijie'] = len(bishijie_news)
        
        # 4. RSS聚合
        rss_news = self.fetch_rss_sources()
        all_news.extend(rss_news)
        stats['rss'] = len(rss_news)
        
        # 去重 (基于标题相似度)
        unique_news = self._deduplicate_by_title(all_news)
        
        # 保存到数据库
        saved = self.save_news(unique_news)
        
        print("\n" + "="*70)
        print("获取完成!")
        print(f"  原始: {len(all_news)} 条")
        print(f"  去重: {len(unique_news)} 条")
        print(f"  保存: {saved} 条")
        print(f"  来源: {stats}")
        print("="*70)
        
        return {
            'total': len(all_news),
            'unique': len(unique_news),
            'saved': saved,
            'stats': stats
        }
    
    def _deduplicate_by_title(self, news_list: List[Dict]) -> List[Dict]:
        """基于标题相似度去重"""
        seen = set()
        unique = []
        
        for news in news_list:
            # 使用标题前20个字符作为去重键
            key = news['title'][:20] if news['title'] else ''
            
            if key and key not in seen:
                seen.add(key)
                unique.append(news)
        
        return unique


def main():
    """主函数"""
    fetcher = FreeNewsFetcher()
    result = fetcher.fetch_all()
    
    print(f"\n✓ 新闻获取完成!")
    print(f"  共获取 {result['saved']} 条新闻")


if __name__ == "__main__":
    main()
