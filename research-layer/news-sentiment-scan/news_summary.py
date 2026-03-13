#!/usr/bin/env python3
"""
新闻汇总模块
提供新闻去重、聚类和汇总功能
"""

import os
import sys
import sqlite3
import hashlib
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/quant-trading/data-layer"))


class NewsSummarizer:
    """新闻汇总器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser("~/.openclaw/workspace/quant-trading/data-layer/market_data.db")
        self.similarity_threshold = 0.7  # 相似度阈值
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度（使用简单的Jaccard相似度）"""
        # 分词（简单按字符）
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _get_content_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.lower().strip().encode()).hexdigest()[:16]
    
    def deduplicate_news(self, news_list: List[Dict]) -> Tuple[List[Dict], List[Tuple[int, int]]]:
        """去重新闻列表"""
        unique_news = []
        duplicates = []
        seen_hashes = {}
        
        for item in news_list:
            content = item.get('content') or item.get('title', '')
            content_hash = self._get_content_hash(content)
            
            if content_hash in seen_hashes:
                # 标记为重复
                duplicates.append((item['id'], seen_hashes[content_hash]))
            else:
                seen_hashes[content_hash] = item['id']
                unique_news.append(item)
        
        return unique_news, duplicates
    
    def cluster_by_topic(self, news_list: List[Dict]) -> Dict[str, List[Dict]]:
        """按主题聚类新闻"""
        clusters = defaultdict(list)
        
        for item in news_list:
            # 使用分类作为主要聚类依据
            category = item.get('category', '未分类')
            clusters[category].append(item)
        
        return dict(clusters)
    
    def get_sentiment_summary(self, news_list: List[Dict]) -> Dict:
        """计算情绪汇总"""
        if not news_list:
            return {'bullish': 0, 'bearish': 0, 'neutral': 0, 'total': 0}
        
        # 情绪映射
        sentiment_counts = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        
        for item in news_list:
            sentiment = item.get('sentiment', 0)
            sentiment_label = item.get('sentiment_label', '')
            
            # 处理不同的sentiment格式
            if sentiment > 0.2 or sentiment_label in ['利好', 'bullish']:
                sentiment_counts['bullish'] += 1
            elif sentiment < -0.2 or sentiment_label in ['利空', 'bearish']:
                sentiment_counts['bearish'] += 1
            else:
                sentiment_counts['neutral'] += 1
        
        return {
            'bullish': sentiment_counts['bullish'],
            'bearish': sentiment_counts['bearish'],
            'neutral': sentiment_counts['neutral'],
            'total': len(news_list)
        }
    
    def get_news_summary_by_category(self, hours: int = 24) -> Dict:
        """按类别获取新闻汇总"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute("""
            SELECT * FROM news 
            WHERE created_at >= ?
            ORDER BY created_at DESC
        """, (since,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        news_list = [dict(row) for row in rows]
        
        # 去重
        unique_news, duplicates = self.deduplicate_news(news_list)
        
        # 按类别聚类
        clusters = self.cluster_by_topic(unique_news)
        
        # 生成汇总
        summary = {}
        for category, items in clusters.items():
            sentiment = self.get_sentiment_summary(items)
            summary[category] = {
                'count': len(items),
                'sentiment': sentiment,
                'latest': items[0] if items else None
            }
        
        # 全部汇总
        all_sentiment = self.get_sentiment_summary(unique_news)
        
        return {
            'total_raw': len(news_list),
            'total_unique': len(unique_news),
            'duplicates': len(duplicates),
            'deduplication_rate': len(duplicates) / len(news_list) if news_list else 0,
            'summaries': summary,
            'all': {
                'count': len(unique_news),
                'sentiment': all_sentiment
            }
        }
    
    def process_and_summarize(self, hours: int = 24) -> Dict:
        """处理并汇总新闻"""
        summary = self.get_news_summary_by_category(hours)
        
        # 生成人类可读的文字汇总
        text_summary = self._generate_text_summary(summary)
        summary['text_summary'] = text_summary
        
        return summary
    
    def _generate_text_summary(self, summary: Dict) -> str:
        """生成文字汇总"""
        parts = []
        
        # 总体统计
        total = summary['total_unique']
        parts.append(f"过去24小时共 {total} 条新闻（去重后）")
        
        # 按类别
        if 'summaries' in summary:
            for category, data in sorted(summary['summaries'].items(), 
                                        key=lambda x: x[1]['count'], reverse=True):
                if data['count'] > 0:
                    sentiment = data['sentiment']
                    emoji = {'利好': '🟢', '利空': '🔴', '中性': '⚪'}
                    sentiment_str = f"利好:{sentiment['bullish']} 利空:{sentiment['bearish']} 中性:{sentiment['neutral']}"
                    parts.append(f"  • {category}: {data['count']}条 ({sentiment_str})")
        
        return '\n'.join(parts)
    
    def get_key_events(self, hours: int = 24, min_mentions: int = 3) -> List[Dict]:
        """获取关键事件（被多次提及的新闻）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        # 获取所有新闻
        cursor.execute("""
            SELECT * FROM news 
            WHERE created_at >= ?
            ORDER BY created_at DESC
        """, (since,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        news_list = [dict(row) for row in rows]
        
        # 使用简单方法：按关键词分组
        events = []
        
        # 预定义的关键事件类型
        event_keywords = {
            'ETF': ['etf', '现货', '批准', 'sec'],
            '美联储': ['fed', '美联储', '加息', '降息', '利率'],
            '监管': ['监管', 'sec', 'cz', '币安', '合规'],
            '技术': ['升级', 'fork', 'layer2', '二层', '闪电网络'],
            '黑客': ['黑客', '攻击', '盗币', '漏洞', '安全']
        }
        
        for event_type, keywords in event_keywords.items():
            matching_news = []
            for news in news_list:
                content = (news.get('title', '') + ' ' + (news.get('content', ''))).lower()
                if any(kw.lower() in content for kw in keywords):
                    matching_news.append(news)
            
            if len(matching_news) >= min_mentions:
                sentiment = self.get_sentiment_summary(matching_news)
                events.append({
                    'type': event_type,
                    'mentions': len(matching_news),
                    'sentiment': sentiment,
                    'news': matching_news[:3]  # 最多3条代表性新闻
                })
        
        # 按提及次数排序
        events.sort(key=lambda x: x['mentions'], reverse=True)
        
        return events


def main():
    """测试新闻汇总器"""
    summarizer = NewsSummarizer()
    
    # 获取汇总
    print("=" * 60)
    print("新闻汇总")
    print("=" * 60)
    
    summary = summarizer.process_and_summarize(hours=24)
    print(summary['text_summary'])
    
    # 关键事件
    print("\n" + "=" * 60)
    print("关键事件")
    print("=" * 60)
    
    events = summarizer.get_key_events(hours=24, min_mentions=2)
    for event in events:
        print(f"\n【{event['type']}】{event['mentions']} 次提及")
        sentiment = event['sentiment']
        print(f"  情绪: 利好{sentiment['bullish']} 利空{sentiment['bearish']} 中性{sentiment['neutral']}")


if __name__ == "__main__":
    main()
