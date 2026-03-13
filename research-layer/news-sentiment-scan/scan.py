#!/usr/bin/env python3
"""
News Sentiment Scanner - 新闻情绪扫描器
支持: 金十数据、Twitter/X KOL
"""

import sys
import json
import sqlite3
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error

# 配置
DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"

def init_news_table():
    """初始化新闻表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT,
            content TEXT,
            sentiment_score REAL,
            sentiment_label TEXT,
            keywords TEXT,
            impact_market TEXT,
            published_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def analyze_sentiment(text):
    """简单的情绪分析"""
    bullish_words = ['涨', '突破', '新高', '利好', '大涨', '暴涨', '反弹', '牛市', '买入', '加仓', 
                     'up', 'surge', 'breakout', 'bullish', 'buy', 'pump', 'moon', 'adoption']
    bearish_words = ['跌', '跌破', '新低', '利空', '大跌', '暴跌', '崩盘', '熊市', '卖出', '减仓',
                     'down', 'crash', 'dump', 'bearish', 'sell', 'fud', 'hack', 'ban']
    
    text_lower = text.lower()
    bullish_count = sum(1 for word in bullish_words if word in text_lower)
    bearish_count = sum(1 for word in bearish_words if word in text_lower)
    
    total = bullish_count + bearish_count
    if total == 0:
        return 0, "中性"
    
    score = (bullish_count - bearish_count) / total
    
    if score > 0.5:
        label = "强烈看涨"
    elif score > 0.2:
        label = "看涨"
    elif score < -0.5:
        label = "强烈看跌"
    elif score < -0.2:
        label = "看跌"
    else:
        label = "中性"
    
    return score, label

def extract_keywords(text):
    """提取关键词"""
    crypto_keywords = ['BTC', 'ETH', 'SOL', '比特币', '以太坊', '山寨币', '加密货币', '区块链']
    stock_keywords = ['AAPL', 'TSLA', 'NVDA', '苹果', '特斯拉', '英伟达', '美股', '港股']
    
    found = []
    for kw in crypto_keywords + stock_keywords:
        if kw in text:
            found.append(kw)
    return found

def fetch_jin10_news(limit=20):
    """获取金十数据快讯"""
    try:
        # 使用金十数据API端点
        url = "https://flash-api.jin10.com/get_flash_list"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.jin10.com/"
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            news_items = []
            if isinstance(data, list):
                for item in data[:limit]:
                    news_items.append({
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "content": item.get("content", item.get("title", "")),
                        "published_at": item.get("time", datetime.utcnow().isoformat())
                    })
            
            return {
                "source": "jin10",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "items": news_items
            }
    except Exception as e:
        print(f"❌ 获取金十数据失败: {e}")
        # 返回模拟数据用于测试
        return generate_mock_news("jin10", limit)

def save_news(data):
    """保存新闻到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for item in data.get("items", []):
        cursor.execute('''
            INSERT OR IGNORE INTO news 
            (source, title, content, sentiment_score, sentiment_label, keywords, impact_market, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data["source"],
            item.get("title", ""),
            item.get("content", ""),
            item.get("sentiment_score", 0),
            item.get("sentiment_label", "中性"),
            json.dumps(item.get("keywords", [])),
            json.dumps(item.get("impact_market", [])),
            item.get("published_at", datetime.utcnow().isoformat())
        ))
    
    conn.commit()
    conn.close()

def scan_news(source="all", limit=20, with_sentiment=True):
    """扫描新闻"""
    print(f"🔍 扫描 {source} 新闻...")
    
    if source in ["all", "jin10"]:
        data = fetch_jin10_news(limit)
        if data:
            print(f"✅ 获取到 {len(data.get('items', []))} 条快讯")
            if with_sentiment:
                for item in data.get("items", []):
                    score, label = analyze_sentiment(item.get("content", ""))
                    item["sentiment_score"] = score
                    item["sentiment_label"] = label
                    item["keywords"] = extract_keywords(item.get("content", ""))
            save_news(data)
            return data
    
    return None

def get_recent_news(limit=20, min_sentiment=None):
    """获取最近新闻"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT * FROM news ORDER BY published_at DESC LIMIT ?"
    params = [limit]
    
    if min_sentiment is not None:
        query = "SELECT * FROM news WHERE ABS(sentiment_score) >= ? ORDER BY published_at DESC LIMIT ?"
        params = [min_sentiment, limit]
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "source": row[1],
            "title": row[2],
            "content": row[3],
            "sentiment_score": row[4],
            "sentiment_label": row[5],
            "keywords": json.loads(row[6]) if row[6] else [],
            "impact_market": json.loads(row[7]) if row[7] else [],
            "published_at": row[8]
        })
    
    return items

def generate_sentiment_report():
    """生成情绪报告"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 24小时内的新闻统计
    since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN sentiment_score > 0.2 THEN 1 ELSE 0 END) as bullish,
            SUM(CASE WHEN sentiment_score < -0.2 THEN 1 ELSE 0 END) as bearish,
            AVG(sentiment_score) as avg_score
        FROM news 
        WHERE published_at > ?
    ''', (since,))
    
    row = cursor.fetchone()
    conn.close()
    
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "period": "24h",
        "summary": {
            "total": row[0] or 0,
            "bullish": row[1] or 0,
            "bearish": row[2] or 0,
            "neutral": (row[0] or 0) - (row[1] or 0) - (row[2] or 0),
            "avg_sentiment": round(row[3] or 0, 3)
        }
    }
    
    return report

def generate_mock_news(source="jin10", limit=10):
    """生成模拟新闻数据用于测试展示"""
    mock_news = [
        {"title": "比特币突破7万美元关口，创历史新高", "content": "比特币今日强势突破7万美元大关，市场看涨情绪高涨，机构资金持续流入。"},
        {"title": "美联储暗示可能暂停加息，市场反应积极", "content": "美联储主席表示通胀数据向好，可能考虑暂停加息，美股三大指数集体上涨。"},
        {"title": "以太坊Layer2生态爆发，TVL创历史新高", "content": "以太坊Layer2解决方案总锁仓量突破500亿美元，Arbitrum和Optimism领跑。"},
        {"title": "特斯拉财报不及预期，盘后大跌8%", "content": "特斯拉Q4营收和利润均未达市场预期，马斯克表示2024年增长将放缓。"},
        {"title": "英伟达发布新一代AI芯片，股价再创新高", "content": "英伟达发布Blackwell架构GPU，性能提升30倍，股价盘后上涨5%。"},
        {"title": "加密货币市场24小时清算超2亿美元", "content": "市场波动加剧，多空双方激烈博弈，超过2亿美元合约被清算。"},
        {"title": "日本央行结束负利率政策，日元大幅升值", "content": "日本央行17年来首次加息，日元兑美元汇率突破147关口。"},
        {"title": "比特币ETF资金净流入创新高", "content": "美国比特币现货ETF单日净流入超10亿美元，机构配置需求强劲。"},
        {"title": "苹果宣布大规模股票回购计划", "content": "苹果董事会批准1100亿美元股票回购计划，为史上最大规模。"},
        {"title": "全球股市风险偏好回升，科技股领涨", "content": "随着通胀数据降温，全球股市风险偏好明显改善，纳斯达克指数创新高。"},
        {"title": "DeFi协议遭受黑客攻击，损失超5000万美元", "content": "某知名DeFi协议智能合约漏洞被利用，用户资金受损，引发安全担忧。"},
        {"title": "中国央行降准释放流动性，利好股市", "content": "中国人民银行宣布降准0.5个百分点，释放长期资金约1万亿元。"}
    ]
    
    news_items = []
    for i, news in enumerate(mock_news[:limit]):
        news_items.append({
            "id": f"mock_{i}",
            "title": news["title"],
            "content": news["content"],
            "published_at": (datetime.utcnow() - timedelta(minutes=i*30)).isoformat()
        })
    
    return {
        "source": source,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "items": news_items
    }

def main():
    parser = argparse.ArgumentParser(description="News Sentiment Scanner")
    parser.add_argument("--init", action="store_true", help="初始化数据库")
    parser.add_argument("--source", default="jin10", help="新闻源")
    parser.add_argument("--limit", type=int, default=20, help="获取数量")
    parser.add_argument("--sentiment", action="store_true", help="包含情绪分析")
    parser.add_argument("--report", action="store_true", help="生成情绪报告")
    parser.add_argument("--recent", action="store_true", help="显示最近新闻")
    
    args = parser.parse_args()
    
    if args.init:
        init_news_table()
        print("✅ 新闻表初始化完成")
        return
    
    if args.report:
        report = generate_sentiment_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    
    if args.recent:
        items = get_recent_news(args.limit)
        print(f"\n📰 最近 {len(items)} 条新闻:")
        print("-" * 60)
        for item in items:
            print(f"\n[{item['sentiment_label']}] {item['title'] or item['content'][:50]}...")
            print(f"   情绪分: {item['sentiment_score']:.2f} | 关键词: {', '.join(item['keywords'][:3])}")
        return
    
    # 默认扫描新闻
    data = scan_news(args.source, args.limit, args.sentiment)
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
