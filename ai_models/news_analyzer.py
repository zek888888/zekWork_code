#!/usr/bin/env python3
"""
新闻AI分析模块
使用多AI投票系统进行新闻情绪分析
"""

import os
import sys
import sqlite3
import json
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/quant-trading/config-layer"))
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/quant-trading/data-layer"))

from ai_config_manager import AIConfigManager, AIConfig


@dataclass
class AIVote:
    """单个AI的投票结果"""
    provider: str
    model: str
    sentiment: str  # bullish, bearish, neutral
    confidence: float
    reasoning: str


@dataclass
class AnalysisResult:
    """最终分析结果"""
    sentiment: str  # bullish, bearish, neutral
    confidence: float
    ai_votes: List[AIVote]
    final_reasoning: str


class NewsAnalyzer:
    """新闻分析器 - 多AI投票系统"""
    
    # 情绪映射
    SENTIMENT_MAP = {
        '利好': 'bullish',
        'bullish': 'bullish',
        'bull': 'bullish',
        '看漲': 'bullish',
        '利空': 'bearish',
        'bearish': 'bearish',
        'bear': 'bearish',
        '看跌': 'bearish',
        '中性': 'neutral',
        'neutral': 'neutral',
        '持平': 'neutral',
        'none': 'neutral'
    }
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser("~/.openclaw/workspace/quant-trading/data-layer/market_data.db")
        self.config_manager = AIConfigManager(self.db_path)
        self.min_confidence = 0.6
        
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _call_ai_api(self, config: AIConfig, prompt: str) -> Optional[AIVote]:
        """调用单个AI API进行分析"""
        try:
            if config.provider == 'moonshot':
                return self._call_moonshot(config, prompt)
            elif config.provider == 'openai':
                return self._call_openai(config, prompt)
            elif config.provider == 'anthropic':
                return self._call_anthropic(config, prompt)
            else:
                # 尝试使用OpenAI兼容格式
                return self._call_openai_compatible(config, prompt)
        except Exception as e:
            print(f"调用 {config.name} 失败: {e}")
            return None
    
    def _call_moonshot(self, config: AIConfig, prompt: str) -> Optional[AIVote]:
        """调用Moonshot (Kimi) API"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的新闻情绪分析助手。分析新闻对加密货币市场的情绪影响，只返回JSON格式结果。"},
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
            return self._parse_ai_response(config, content)
        else:
            print(f"Moonshot API错误: {response.status_code} - {response.text}")
            return None
    
    def _call_openai(self, config: AIConfig, prompt: str) -> Optional[AIVote]:
        """调用OpenAI API"""
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
            
            response = client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": "You are a financial news sentiment analysis expert. Return results in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
            content = response.choices[0].message.content
            return self._parse_ai_response(config, content)
            
        except Exception as e:
            print(f"OpenAI API错误: {e}")
            return None
    
    def _call_anthropic(self, config: AIConfig, prompt: str) -> Optional[AIVote]:
        """调用Anthropic (Claude) API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=config.api_key)
            
            response = client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                system="You are a financial news sentiment analysis expert. Return results in JSON format.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            return self._parse_ai_response(config, content)
            
        except Exception as e:
            print(f"Anthropic API错误: {e}")
            return None
    
    def _call_openai_compatible(self, config: AIConfig, prompt: str) -> Optional[AIVote]:
        """调用OpenAI兼容格式的API"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": "You are a financial news sentiment analysis expert. Return results in JSON format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens
        }
        
        base_url = config.base_url or "https://api.openai.com/v1"
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return self._parse_ai_response(config, content)
        else:
            print(f"API错误: {response.status_code} - {response.text}")
            return None
    
    def _parse_ai_response(self, config: AIConfig, content: str) -> AIVote:
        """解析AI响应"""
        # 尝试提取JSON
        try:
            # 查找JSON块
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                json_str = content.split('```')[1].split('```')[0].strip()
            else:
                json_str = content.strip()
            
            result = json.loads(json_str)
            
            sentiment_str = result.get('sentiment', 'neutral').lower()
            sentiment = self.SENTIMENT_MAP.get(sentiment_str, 'neutral')
            
            return AIVote(
                provider=config.provider,
                model=config.model,
                sentiment=sentiment,
                confidence=float(result.get('confidence', 0.5)),
                reasoning=result.get('reasoning', 'No reasoning provided')
            )
        except json.JSONDecodeError:
            # 解析失败，尝试简单关键词匹配
            content_lower = content.lower()
            if 'bullish' in content_lower or '利好' in content_lower:
                sentiment = 'bullish'
            elif 'bearish' in content_lower or '利空' in content_lower:
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
            
            return AIVote(
                provider=config.provider,
                model=config.model,
                sentiment=sentiment,
                confidence=0.5,
                reasoning="解析失败，使用关键词匹配"
            )
    
    def _build_prompt(self, title: str, content: str, category: str) -> str:
        """构建分析提示词"""
        return f"""请分析以下新闻对加密货币市场的情绪影响：

【分类】{category}
【标题】{title}
【内容】{content}

请从以下维度分析：
1. 此新闻对加密货币市场的整体影响是利好还是利空？
2. 你的信心度有多高（0-1）？
3. 给出详细的分析理由

请以JSON格式返回结果：
{{
    "sentiment": "bullish|bearish|neutral",
    "confidence": 0.8,
    "reasoning": "详细分析理由..."
}}

sentiment取值说明：
- bullish: 利好，可能推动加密货币上涨
- bearish: 利空，可能导致加密货币下跌
- neutral: 中性，对市场影响不大
"""
    
    def analyze_single_news(self, news_id: int) -> Optional[AnalysisResult]:
        """分析单条新闻"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM news WHERE id = ?", (news_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._analyze_news_content(
            news_id=row['id'],
            title=row['title'],
            content=row['content'] or row['title'],
            category=row['category'] or 'general'
        )
    
    def _analyze_news_content(self, news_id: int, title: str, content: str, category: str) -> AnalysisResult:
        """分析新闻内容（多AI投票）"""
        # 获取活跃AI配置
        configs = self.config_manager.get_active_configs()
        
        if not configs:
            print("警告: 没有可用的AI配置")
            return AnalysisResult(
                sentiment='neutral',
                confidence=0,
                ai_votes=[],
                final_reasoning="没有可用的AI配置"
            )
        
        prompt = self._build_prompt(title, content, category)
        
        # 并行调用所有AI
        votes = []
        with ThreadPoolExecutor(max_workers=len(configs)) as executor:
            future_to_config = {
                executor.submit(self._call_ai_api, config, prompt): config 
                for config in configs
            }
            
            for future in as_completed(future_to_config):
                config = future_to_config[future]
                try:
                    vote = future.result()
                    if vote:
                        votes.append(vote)
                        print(f"  ✓ {config.name}: {vote.sentiment} ({vote.confidence:.2f})")
                except Exception as e:
                    print(f"  ✗ {config.name}: {e}")
        
        # 多数投票决策
        result = self._majority_vote(votes)
        
        # 保存分析结果到数据库
        self._save_analysis_result(news_id, result)
        
        return result
    
    def _majority_vote(self, votes: List[AIVote]) -> AnalysisResult:
        """多数投票决策"""
        if not votes:
            return AnalysisResult(
                sentiment='neutral',
                confidence=0,
                ai_votes=[],
                final_reasoning="无投票结果"
            )
        
        # 统计票数
        sentiments = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        confidences = {'bullish': [], 'bearish': [], 'neutral': []}
        
        for vote in votes:
            sentiments[vote.sentiment] += 1
            confidences[vote.sentiment].append(vote.confidence)
        
        # 找出最高票
        max_sentiment = max(sentiments, key=sentiments.get)
        max_count = sentiments[max_sentiment]
        total_votes = len(votes)
        
        # 计算信心度
        vote_ratio = max_count / total_votes
        avg_confidence = sum(confidences[max_sentiment]) / len(confidences[max_sentiment]) if confidences[max_sentiment] else 0
        final_confidence = vote_ratio * avg_confidence
        
        # 构建理由
        reasons = []
        for vote in votes:
            emoji = {'bullish': '🟢', 'bearish': '🔴', 'neutral': '⚪'}[vote.sentiment]
            reasons.append(f"{emoji} {vote.provider}/{vote.model}: {vote.reasoning[:50]}...")
        
        return AnalysisResult(
            sentiment=max_sentiment,
            confidence=final_confidence,
            ai_votes=votes,
            final_reasoning=f"多数投票结果: {max_sentiment} ({max_count}/{total_votes}票)\n\n" + "\n".join(reasons)
        )
    
    def _save_analysis_result(self, news_id: int, result: AnalysisResult):
        """保存分析结果到数据库"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 检查是否有分析表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id INTEGER UNIQUE,
                sentiment TEXT,
                confidence REAL,
                ai_votes TEXT,
                final_reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 保存分析结果
        cursor.execute("""
            INSERT OR REPLACE INTO news_ai_analysis 
            (news_id, sentiment, confidence, ai_votes, final_reasoning)
            VALUES (?, ?, ?, ?, ?)
        """, (
            news_id,
            result.sentiment,
            result.confidence,
            json.dumps([{'provider': v.provider, 'model': v.model, 
                        'sentiment': v.sentiment, 'confidence': v.confidence} 
                       for v in result.ai_votes]),
            result.final_reasoning
        ))
        
        # 更新news表的sentiment字段
        sentiment_map_db = {'bullish': 1, 'bearish': -1, 'neutral': 0}
        cursor.execute("""
            UPDATE news SET sentiment = ? WHERE id = ?
        """, (sentiment_map_db.get(result.sentiment, 0), news_id))
        
        conn.commit()
        conn.close()
    
    def batch_analyze_news(self, hours: int = 24, limit: int = 50):
        """批量分析新闻"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 获取需要分析的新闻（未分析或最新的）
        cursor.execute("""
            SELECT n.* FROM news n
            LEFT JOIN news_ai_analysis a ON n.id = a.news_id
            WHERE n.created_at >= datetime('now', '-{hours} hours')
            AND (a.id IS NULL OR n.created_at > a.created_at)
            ORDER BY n.created_at DESC
            LIMIT {limit}
        """.format(hours=hours, limit=limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        print(f"找到 {len(rows)} 条待分析新闻")
        
        analyzed_count = 0
        for row in rows:
            print(f"\n分析新闻 [{row['id']}]: {row['title'][:40]}...")
            try:
                self._analyze_news_content(
                    news_id=row['id'],
                    title=row['title'],
                    content=row['content'] or row['title'],
                    category=row['category'] or 'general'
                )
                analyzed_count += 1
            except Exception as e:
                print(f"分析失败: {e}")
        
        print(f"\n✓ 完成分析 {analyzed_count}/{len(rows)} 条新闻")
        return analyzed_count
    
    def get_news_with_decision(self, hours: int = 24, limit: int = 50) -> List[Dict]:
        """获取带AI决策的新闻"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT n.*, a.sentiment as ai_sentiment, a.confidence, a.final_reasoning
            FROM news n
            LEFT JOIN news_ai_analysis a ON n.id = a.news_id
            WHERE n.created_at >= datetime('now', '-? hours')
            ORDER BY n.created_at DESC
            LIMIT ?
        """, (hours, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            sentiment_map = {'bullish': '利好', 'bearish': '利空', 'neutral': '中性', 
                           '1': '利好', '-1': '利空', '0': '中性'}
            
            # 优先使用AI分析结果
            if row['ai_sentiment']:
                sentiment = sentiment_map.get(row['ai_sentiment'], '中性')
                confidence = row['confidence']
                decision_type = 'ai'
            else:
                sentiment = sentiment_map.get(str(row['sentiment']), '中性')
                confidence = 0.5
                decision_type = 'keyword'
            
            results.append({
                'id': row['id'],
                'title': row['title'],
                'category': row['category'],
                'sentiment': sentiment,
                'confidence': round(confidence * 100, 1) if confidence else None,
                'decision_type': decision_type,
                'created_at': row['created_at'],
                'source': row['source']
            })
        
        return results


def main():
    """测试新闻分析器"""
    analyzer = NewsAnalyzer()
    
    # 显示当前AI配置
    configs = analyzer.config_manager.get_active_configs()
    print("=" * 60)
    print(f"活跃AI配置: {len(configs)} 个")
    for config in configs:
        print(f"  - {config.name} ({config.provider}/{config.model})")
    print("=" * 60)
    
    # 批量分析
    analyzer.batch_analyze_news(hours=24, limit=10)
    
    # 显示结果
    print("\n最近新闻分析结果:")
    print("-" * 60)
    results = analyzer.get_news_with_decision(hours=24, limit=5)
    
    for item in results:
        emoji = {'利好': '🟢', '利空': '🔴', '中性': '⚪'}.get(item['sentiment'], '⚪')
        print(f"{emoji} [{item['sentiment']}] {item['title'][:40]}...")
        if item['confidence']:
            print(f"   置信度: {item['confidence']}% ({item['decision_type']})")


if __name__ == "__main__":
    main()
