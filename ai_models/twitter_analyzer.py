#!/usr/bin/env python3
"""
推特AI分析模块
复用新闻分析的AI配置进行多AI投票分析
包含：内容总结(20-50字) + 情绪分析 + 具体原因
"""

import os
import sys
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/quant-trading/config-layer"))

from ai_config_manager import AIConfigManager
from news_analyzer import NewsAnalyzer, AnalysisResult

# 数据库路径
DB_PATH = os.path.expanduser("~/.openclaw/workspace/quant-trading/data-layer/market_data.db")


class TwitterAnalyzer:
    """推特AI分析器 - 复用新闻分析的AI配置"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.config_manager = AIConfigManager(self.db_path)
        # 复用新闻分析器的多AI投票功能
        self.news_analyzer = NewsAnalyzer(self.db_path)
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _build_analysis_prompt(self, username: str, content: str, display_name: str = None) -> str:
        """构建分析提示词 - 包含总结和情绪分析"""
        name = display_name or username
        
        return f"""请分析以下推特用户的推文：

【用户】@{username} ({name})
【推文内容】{content}

请完成以下分析任务并以JSON格式返回：

1. **内容总结** (20-50字)：提炼推文核心观点
2. **情绪判断**：分析对加密货币市场是利好(bullish)、利空(bearish)还是中性(neutral)
3. **分析原因** (简洁)：说明为什么，格式如"信息利好BTC"、"利空ETH"、"中性市场消息"等

请以以下JSON格式返回：
{{
    "summary": "20-50字的内容总结",
    "sentiment": "bullish|bearish|neutral",
    "analysis_reason": "如: 信息利好BNB",
    "confidence": 0.85,
    "detailed_reasoning": "详细的分析理由"
}}

注意：
- sentiment只能取: bullish(利好)、bearish(利空)、neutral(中性)
- analysis_reason要具体说明利好/利空什么币种或市场
- summary控制在20-50字之间
"""
    
    def analyze_single_tweet(self, tweet_id: int, tweet_content: str, 
                            username: str, display_name: str = None) -> Dict:
        """
        分析单条推文
        返回：总结、情绪、原因、置信度
        """
        # 获取活跃AI配置
        configs = self.config_manager.get_active_configs()
        
        if not configs:
            print("警告: 没有可用的AI配置")
            return {
                'summary': tweet_content[:40] + '...' if len(tweet_content) > 40 else tweet_content,
                'sentiment': 'neutral',
                'analysis_reason': '无AI配置，默认中性',
                'confidence': 0,
                'detailed_reasoning': '没有可用的AI配置'
            }
        
        # 使用第一个可用AI进行分析（简化版，可扩展为多AI投票）
        config = configs[0]
        prompt = self._build_analysis_prompt(username, tweet_content, display_name)
        
        try:
            result = self._call_ai_api(config, prompt)
            return result
        except Exception as e:
            print(f"AI分析失败: {e}")
            return {
                'summary': tweet_content[:40] + '...' if len(tweet_content) > 40 else tweet_content,
                'sentiment': 'neutral',
                'analysis_reason': '分析失败',
                'confidence': 0,
                'detailed_reasoning': f'分析失败: {str(e)}'
            }
    
    def _call_ai_api(self, config, prompt: str) -> Dict:
        """调用AI API"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的加密货币市场情绪分析助手。分析推文内容，提供简洁的总结和准确的情绪判断。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens
        }
        
        base_url = config.base_url or "https://api.moonshot.cn/v1"
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return self._parse_ai_response(content)
        else:
            raise Exception(f"API错误: {response.status_code}")
    
    def _parse_ai_response(self, content: str) -> Dict:
        """解析AI响应"""
        import json
        
        try:
            # 查找JSON块
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                json_str = content.split('```')[1].split('```')[0].strip()
            else:
                json_str = content.strip()
            
            result = json.loads(json_str)
            
            # 标准化sentiment
            sentiment_map = {
                'bullish': 'bullish', '利好': 'bullish', '看涨': 'bullish',
                'bearish': 'bearish', '利空': 'bearish', '看跌': 'bearish',
                'neutral': 'neutral', '中性': 'neutral', '持平': 'neutral'
            }
            
            sentiment_str = result.get('sentiment', 'neutral').lower()
            sentiment = sentiment_map.get(sentiment_str, 'neutral')
            
            return {
                'summary': result.get('summary', '无总结'),
                'sentiment': sentiment,
                'analysis_reason': result.get('analysis_reason', '未提供原因'),
                'confidence': float(result.get('confidence', 0.5)),
                'detailed_reasoning': result.get('detailed_reasoning', '无详细理由')
            }
            
        except json.JSONDecodeError:
            # 解析失败，尝试关键词匹配
            content_lower = content.lower()
            if 'bullish' in content_lower or '利好' in content_lower:
                sentiment = 'bullish'
                reason = '信息利好'
            elif 'bearish' in content_lower or '利空' in content_lower:
                sentiment = 'bearish'
                reason = '信息利空'
            else:
                sentiment = 'neutral'
                reason = '中性消息'
            
            return {
                'summary': content[:40] + '...' if len(content) > 40 else content,
                'sentiment': sentiment,
                'analysis_reason': reason,
                'confidence': 0.5,
                'detailed_reasoning': 'JSON解析失败，使用关键词匹配'
            }
    
    def save_analysis_result(self, tweet_id: int, result: Dict):
        """保存分析结果到数据库"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE twitter_posts 
            SET sentiment = ?,
                confidence = ?,
                summary = ?,
                analysis_reason = ?,
                ai_reasoning = ?,
                ai_analyzed_at = CURRENT_TIMESTAMP,
                is_processed = 1
            WHERE id = ?
        ''', (
            result['sentiment'],
            result['confidence'],
            result['summary'],
            result['analysis_reason'],
            result['detailed_reasoning'],
            tweet_id
        ))
        
        conn.commit()
        conn.close()
    
    def batch_analyze_pending(self, hours: int = 24, limit: int = 50) -> Dict:
        """批量分析待处理的推文"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取待分析的推文
        cursor.execute('''
            SELECT p.*, w.display_name
            FROM twitter_posts p
            LEFT JOIN twitter_watchlist w ON p.username = w.username
            WHERE p.sentiment IS NULL
            AND (p.created_at >= ? OR p.posted_at >= ?)
            ORDER BY COALESCE(p.posted_at, p.created_at) DESC
            LIMIT ?
        ''', (since, since, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        print(f"找到 {len(rows)} 条待分析推文")
        
        analyzed_count = 0
        results = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        
        for row in rows:
            try:
                print(f"\n分析推文 [{row['id']}]: @{row['username']}")
                print(f"  原文: {row['content'][:50]}...")
                
                # AI分析
                analysis = self.analyze_single_tweet(
                    tweet_id=row['id'],
                    tweet_content=row['content'],
                    username=row['username'],
                    display_name=row['display_name']
                )
                
                # 保存结果
                self.save_analysis_result(row['id'], analysis)
                
                results[analysis['sentiment']] += 1
                analyzed_count += 1
                
                print(f"  ✓ 总结: {analysis['summary']}")
                print(f"  ✓ 情绪: {analysis['sentiment']}")
                print(f"  ✓ 原因: {analysis['analysis_reason']}")
                print(f"  ✓ 置信度: {analysis['confidence']:.2f}")
                
            except Exception as e:
                print(f"  ✗ 分析失败: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n完成分析 {analyzed_count}/{len(rows)} 条推文")
        print(f"  利好: {results['bullish']} 条")
        print(f"  利空: {results['bearish']} 条")
        print(f"  中性: {results['neutral']} 条")
        
        return {
            'total': len(rows),
            'analyzed': analyzed_count,
            'results': results
        }
    
    def get_analysis_stats(self, hours: int = 24) -> Dict:
        """获取分析统计"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN sentiment = 'bullish' THEN 1 ELSE 0 END) as bullish,
                SUM(CASE WHEN sentiment = 'bearish' THEN 1 ELSE 0 END) as bearish,
                SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral,
                SUM(CASE WHEN sentiment IS NULL THEN 1 ELSE 0 END) as pending,
                AVG(confidence) as avg_confidence
            FROM twitter_posts
            WHERE created_at >= ? OR posted_at >= ?
        ''', (since, since))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'period_hours': hours,
            'total': row['total'] or 0,
            'bullish': row['bullish'] or 0,
            'bearish': row['bearish'] or 0,
            'neutral': row['neutral'] or 0,
            'pending': row['pending'] or 0,
            'avg_confidence': round(row['avg_confidence'] or 0, 2)
        }


def generate_test_data():
    """生成5条测试推文数据"""
    import sys
    sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/quant-trading/research-layer/twitter-sentiment"))
    from twitter_fetcher import TwitterFetcher, Tweet
    
    test_tweets = [
        {
            'username': 'cz_binance',
            'content': '币安即将上线新的Launchpool项目，BNB持有者可以参与挖矿。这次项目质量很高，值得关注！#Binance #BNB',
            'display_name': 'CZ 🔶 Binance'
        },
        {
            'username': 'xiaomustock',
            'content': 'BTC突破关键阻力位，机构资金持续流入。看好后续行情，建议逢低布局。目标价位75000美元',
            'display_name': '小木'
        },
        {
            'username': 'thankUcrypto',
            'content': 'WARNING: 某大型交易所出现资金异常流出，建议用户暂时提币避险。链上数据显示大量USDT转移',
            'display_name': 'ThankU Crypto'
        },
        {
            'username': 'dotyyds1234',
            'content': 'DOT生态系统持续增长，平行链拍卖进展顺利。长期看好Web3.0基础设施发展',
            'display_name': 'DOT YYDS'
        },
        {
            'username': 'monkeyjiang',
            'content': '今天天气不错，大家注意身体。市场波动大，保持心态平和很重要。投资有风险，入市需谨慎',
            'display_name': 'Monkey Jiang'
        }
    ]
    
    fetcher = TwitterFetcher()
    
    print("="*60)
    print("生成5条测试推文数据")
    print("="*60)
    
    for i, data in enumerate(test_tweets, 1):
        tweet = Tweet(
            tweet_id=f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}",
            username=data['username'],
            content=data['content'],
            posted_at=datetime.now() - timedelta(minutes=i*10),
            retweet_count=10 + i * 5,
            like_count=50 + i * 10
        )
        
        fetcher.save_tweet(tweet)
        print(f"✓ [{i}] @{data['username']}: {data['content'][:40]}...")
    
    print(f"\n✓ 已生成 {len(test_tweets)} 条测试数据")
    return len(test_tweets)


def main():
    """测试分析器"""
    print("="*60)
    print("推特AI分析测试（含总结和原因分析）")
    print("="*60)
    
    # 1. 生成测试数据
    generate_test_data()
    
    # 2. 检查AI配置
    analyzer = TwitterAnalyzer()
    configs = analyzer.config_manager.get_active_configs()
    print(f"\n活跃AI配置: {len(configs)} 个")
    for c in configs:
        print(f"  - {c.name} ({c.provider})")
    
    if not configs:
        print("\n⚠️ 没有活跃AI配置，请先配置AI")
        print("在系统配置页面添加Kimi或其他AI的API密钥")
        return
    
    # 3. 批量分析
    print("\n" + "="*60)
    print("开始AI分析...")
    print("="*60)
    
    result = analyzer.batch_analyze_pending(hours=24, limit=5)
    
    # 4. 显示结果
    print("\n" + "="*60)
    print("分析完成！统计信息")
    print("="*60)
    
    stats = analyzer.get_analysis_stats(hours=24)
    print(f"总计: {stats['total']} 条")
    print(f"利好: {stats['bullish']} 条")
    print(f"利空: {stats['bearish']} 条")
    print(f"中性: {stats['neutral']} 条")
    
    # 显示详细结果
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, content, summary, sentiment, analysis_reason, confidence
        FROM twitter_posts
        ORDER BY id DESC
        LIMIT 5
    ''')
    
    print("\n详细分析结果:")
    print("-"*60)
    for row in cursor.fetchall():
        print(f"\n@{row['username']}:")
        print(f"  原文: {row['content'][:50]}...")
        print(f"  总结: {row['summary']}")
        print(f"  情绪: {row['sentiment']} | 原因: {row['analysis_reason']} | 置信度: {row['confidence']:.2f}")
    
    conn.close()


if __name__ == "__main__":
    main()
