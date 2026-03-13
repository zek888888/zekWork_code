#!/usr/bin/env python3
"""
新闻汇总模块
- 整合多个新闻源
- 智能去重
- 分类标签（国际大事/政治/金融/AI/加密货币）
- 生成摘要
"""

import sqlite3
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict

DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"


class NewsSummarizer:
    """新闻汇总器"""
    
    # 新闻分类关键词
    CATEGORY_KEYWORDS = {
        '国际大事': ['战争', '冲突', '和平', '联合国', 'G20', 'G7', '峰会', '外交', '制裁', '协议',
                  'war', 'conflict', 'peace', 'united nations', 'summit', 'diplomatic', 'sanctions'],
        '政治': ['选举', '投票', '总统', '总理', '政府', '政策', '法案', '议会', '国会', '立法',
               'election', 'vote', 'president', 'prime minister', 'government', 'policy', 'bill', 'congress'],
        '金融': ['央行', '美联储', '加息', '降息', '利率', '通胀', 'CPI', 'PPI', 'GDP', '就业',
               '银行', '信贷', '货币', '财政', '央行', 'Fed', 'interest rate', 'inflation', 'monetary'],
        'AI': ['人工智能', 'AI', '大模型', 'ChatGPT', '机器学习', '深度学习', '算法', '算力',
             'artificial intelligence', 'machine learning', 'deep learning', 'LLM', 'neural network', 'AI model'],
        '加密货币': ['比特币', '以太坊', '加密货币', '区块链', 'DeFi', 'NFT', '挖矿', '交易所',
                  'Bitcoin', 'Ethereum', 'crypto', 'blockchain', 'defi', 'nft', 'mining', 'digital asset']
    }
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def categorize_news(self, title: str, content: str) -> List[str]:
        """
        对新闻进行分类
        
        Returns:
            分类列表（一条新闻可能属于多个分类）
        """
        text = f"{title} {content}".lower()
        categories = []
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    categories.append(category)
                    break
        
        return categories if categories else ['其他']
    
    def deduplicate_news(self, news_list: List[Dict], similarity_threshold: float = 0.7) -> List[Dict]:
        """
        智能去重
        
        策略:
        1. 完全相同的标题去重
        2. 相似度高的内容去重（基于关键词重叠）
        3. 保留最新的
        """
        unique_news = []
        seen_hashes = set()
        
        # 按时间排序，最新的在前
        sorted_news = sorted(news_list, key=lambda x: x.get('published_at', ''), reverse=True)
        
        for news in sorted_news:
            title = news.get('title', '') or ''
            content = news.get('content', '') or ''
            
            # 生成标题哈希
            title_hash = self._generate_hash(title)
            
            # 检查完全重复
            if title_hash in seen_hashes:
                continue
            
            # 检查相似内容
            is_duplicate = False
            for existing in unique_news:
                if self._calculate_similarity(news, existing) > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_hashes.add(title_hash)
                unique_news.append(news)
        
        return unique_news
    
    def _generate_hash(self, text: str) -> str:
        """生成文本哈希"""
        import hashlib
        # 清洗文本后生成哈希
        clean_text = re.sub(r'[^\w]', '', text.lower())
        return hashlib.md5(clean_text.encode()).hexdigest()[:16]
    
    def _calculate_similarity(self, news1: Dict, news2: Dict) -> float:
        """计算两条新闻的相似度"""
        text1 = f"{news1.get('title', '')} {news1.get('content', '')}"
        text2 = f"{news2.get('title', '')} {news2.get('content', '')}"
        
        # 提取关键词
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard相似度
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def generate_summary(self, news_list: List[Dict], category: str = None) -> Dict:
        """
        生成新闻摘要
        
        Args:
            news_list: 新闻列表
            category: 指定分类（可选）
        
        Returns:
            摘要数据
        """
        if category:
            filtered_news = [n for n in news_list if category in n.get('categories', [])]
        else:
            filtered_news = news_list
        
        if not filtered_news:
            return {'count': 0, 'summary': '无相关新闻'}
        
        # 统计
        total = len(filtered_news)
        bullish = sum(1 for n in filtered_news if n.get('ai_label') == 'bullish')
        bearish = sum(1 for n in filtered_news if n.get('ai_label') == 'bearish')
        neutral = total - bullish - bearish
        
        # 提取重要新闻（置信度高的）
        important = sorted(
            [n for n in filtered_news if n.get('ai_confidence', 0) > 0.7],
            key=lambda x: x.get('ai_confidence', 0),
            reverse=True
        )[:5]
        
        # 生成摘要文本
        summary_text = self._generate_summary_text(filtered_news, category)
        
        return {
            'category': category or '全部',
            'count': total,
            'sentiment': {
                'bullish': bullish,
                'bearish': bearish,
                'neutral': neutral,
                'ratio': bullish / total if total > 0 else 0
            },
            'important_news': [
                {
                    'id': n['id'],
                    'title': n.get('title', '')[:100],
                    'label': n.get('ai_label'),
                    'confidence': n.get('ai_confidence')
                }
                for n in important
            ],
            'summary_text': summary_text,
            'latest_update': max(n.get('published_at', '') for n in filtered_news) if filtered_news else None
        }
    
    def _generate_summary_text(self, news_list: List[Dict], category: str) -> str:
        """生成摘要文本"""
        if not news_list:
            return "暂无相关新闻"
        
        # 获取最新的几条新闻标题
        recent_titles = [n.get('title', '') for n in news_list[:3] if n.get('title')]
        
        if category:
            text = f"【{category}】最近{len(news_list)}条新闻："
        else:
            text = f"共{len(news_list)}条新闻："
        
        if recent_titles:
            text += " | ".join(recent_titles[:3])
        
        return text
    
    def process_and_summarize(self, hours: int = 24) -> Dict:
        """
        处理和汇总新闻
        
        完整流程:
        1. 获取原始新闻
        2. 智能去重
        3. 分类标记
        4. 生成各分类摘要
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取最近新闻
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        cursor.execute('''
            SELECT n.id, n.source, n.title, n.content, n.sentiment_score, n.sentiment_label,
                   n.keywords, n.published_at, n.created_at,
                   nd.final_label, nd.final_score, nd.confidence
            FROM news n
            LEFT JOIN news_decisions nd ON n.id = nd.news_id
            WHERE n.published_at > ?
            ORDER BY n.published_at DESC
        ''', (since,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {
                'period_hours': hours,
                'total_raw': 0,
                'total_unique': 0,
                'categories': {},
                'summaries': {}
            }
        
        # 转换为字典列表
        news_list = []
        for row in rows:
            news_list.append({
                'id': row[0],
                'source': row[1],
                'title': row[2],
                'content': row[3],
                'sentiment_score': row[4],
                'sentiment_label': row[5],
                'keywords': json.loads(row[6]) if row[6] else [],
                'published_at': row[7],
                'created_at': row[8],
                'ai_label': row[9],
                'ai_score': row[10],
                'ai_confidence': row[11]
            })
        
        total_raw = len(news_list)
        
        # 去重
        unique_news = self.deduplicate_news(news_list)
        
        # 分类
        for news in unique_news:
            news['categories'] = self.categorize_news(
                news.get('title', ''),
                news.get('content', '')
            )
        
        # 按分类统计
        category_counts = defaultdict(int)
        for news in unique_news:
            for cat in news['categories']:
                category_counts[cat] += 1
        
        # 生成各分类摘要
        summaries = {}
        for category in list(self.CATEGORY_KEYWORDS.keys()) + ['其他']:
            summaries[category] = self.generate_summary(unique_news, category)
        
        # 总体摘要
        summaries['全部'] = self.generate_summary(unique_news)
        
        return {
            'period_hours': hours,
            'total_raw': total_raw,
            'total_unique': len(unique_news),
            'deduplication_rate': (total_raw - len(unique_news)) / total_raw if total_raw > 0 else 0,
            'categories': dict(category_counts),
            'summaries': summaries,
            'latest_news': unique_news[:10]  # 最新的10条
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='新闻汇总器')
    parser.add_argument('--summarize', action='store_true', help='生成新闻汇总')
    parser.add_argument('--hours', type=int, default=24, help='时间范围（小时）')
    parser.add_argument('--category', help='指定分类')
    parser.add_argument('--json', action='store_true', help='输出JSON格式')
    
    args = parser.parse_args()
    
    summarizer = NewsSummarizer()
    
    if args.summarize:
        result = summarizer.process_and_summarize(args.hours)
        
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n📰 新闻汇总报告（最近{result['period_hours']}小时）")
            print("=" * 60)
            print(f"原始新闻: {result['total_raw']} 条")
            print(f"去重后: {result['total_unique']} 条")
            print(f"去重率: {result['deduplication_rate']*100:.1f}%")
            print()
            
            print("📊 分类统计:")
            for cat, count in result['categories'].items():
                print(f"  {cat}: {count} 条")
            print()
            
            print("📋 各分类摘要:")
            for cat, summary in result['summaries'].items():
                if summary['count'] > 0 and cat != '全部':
                    sentiment = summary['sentiment']
                    print(f"\n【{cat}】{summary['count']}条")
                    print(f"  情绪: 🟢{sentiment['bullish']} 🔴{sentiment['bearish']} ⚪{sentiment['neutral']}")
                    if summary['important_news']:
                        print(f"  重要: {summary['important_news'][0]['title'][:50]}...")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
