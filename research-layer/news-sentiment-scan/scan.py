#!/usr/bin/env python3
"""
News Sentiment Scanner - 新闻情绪扫描器
支持: 金十数据、Twitter/X KOL
功能: 增量获取、自动去重、定时更新
"""

import sys
import json
import sqlite3
import argparse
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error

# 配置
DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"

# 全局配置
CONFIG = {
    "fetch_interval_minutes": 30,  # 每30分钟获取一次
    "dedup_window_hours": 24,      # 24小时内的去重窗口
    "sources": ["jin10"],          # 启用的数据源
}

def init_news_table():
    """初始化新闻表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        # 创建新表
        cursor.execute('''
            CREATE TABLE news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                external_id TEXT UNIQUE,
                title TEXT,
                content TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                keywords TEXT,
                impact_market TEXT,
                published_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ 创建新闻表")
    else:
        # 检查是否需要添加新列
        cursor.execute('PRAGMA table_info(news)')
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'external_id' not in columns:
            cursor.execute('ALTER TABLE news ADD COLUMN external_id TEXT')
            print("✅ 添加 external_id 列")
        
        if 'updated_at' not in columns:
            cursor.execute('ALTER TABLE news ADD COLUMN updated_at DATETIME')
            # 更新现有数据
            cursor.execute('UPDATE news SET updated_at = created_at WHERE updated_at IS NULL')
            print("✅ 添加 updated_at 列")
    
    # 创建索引优化查询
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_time ON news(published_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_source ON news(source)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_external_id ON news(external_id)')
    
    # 抓取日志表 - 记录每次抓取状态
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_fetch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            items_fetched INTEGER DEFAULT 0,
            items_new INTEGER DEFAULT 0,
            items_duplicate INTEGER DEFAULT 0,
            status TEXT DEFAULT 'success',
            error_message TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 新闻表和索引初始化完成")

def generate_content_hash(title: str, content: str) -> str:
    """生成内容哈希用于去重"""
    text = f"{title or ''}{content or ''}"
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:16]

def analyze_sentiment(text):
    """简单的情绪分析"""
    bullish_words = ['涨', '突破', '新高', '利好', '大涨', '暴涨', '反弹', '牛市', '买入', '加仓', '企稳', '回暖',
                     'up', 'surge', 'breakout', 'bullish', 'buy', 'pump', 'moon', 'adoption', 'rally', 'soar']
    bearish_words = ['跌', '跌破', '新低', '利空', '大跌', '暴跌', '崩盘', '熊市', '卖出', '减仓', '回落', '下跌',
                     'down', 'crash', 'dump', 'bearish', 'sell', 'fud', 'hack', 'ban', 'plunge', 'tumble']
    
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
    crypto_keywords = ['BTC', 'ETH', 'SOL', '比特币', '以太坊', '山寨币', '加密货币', '区块链', 'DeFi', 'NFT']
    stock_keywords = ['AAPL', 'TSLA', 'NVDA', '苹果', '特斯拉', '英伟达', '美股', '港股', 'A股', '纳指']
    forex_keywords = ['美元', '欧元', '日元', '英镑', '美联储', '加息', '降息', 'CPI', 'PPI', '非农']
    
    found = []
    all_keywords = crypto_keywords + stock_keywords + forex_keywords
    for kw in all_keywords:
        if kw in text:
            found.append(kw)
    return list(set(found))  # 去重

def check_duplicate(external_id: str = None, content_hash: str = None, 
                   hours: int = 24) -> bool:
    """
    检查是否重复
    
    Args:
        external_id: 外部ID
        content_hash: 内容哈希
        hours: 检查时间窗口（小时）
    
    Returns:
        True表示重复，False表示新内容
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    
    # 优先检查external_id
    if external_id:
        cursor.execute('''
            SELECT COUNT(*) FROM news 
            WHERE external_id = ? AND created_at > ?
        ''', (external_id, since))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return True
    
    # 检查内容哈希
    if content_hash:
        cursor.execute('''
            SELECT COUNT(*) FROM news 
            WHERE (external_id = ? OR content LIKE ?) AND created_at > ?
        ''', (content_hash, f'%{content_hash}%', since))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return True
    
    conn.close()
    return False

def fetch_jin10_news(limit=50):
    """获取金十数据快讯 - 增量获取"""
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
                    news_id = item.get("id", "")
                    title = item.get("title", "")
                    content = item.get("content", item.get("title", ""))
                    
                    # 生成内容哈希用于去重
                    content_hash = generate_content_hash(title, content)
                    
                    # 检查是否重复
                    if check_duplicate(external_id=news_id, content_hash=content_hash):
                        continue
                    
                    # 解析发布时间
                    pub_time = item.get("time", "")
                    if pub_time:
                        try:
                            # 尝试解析各种时间格式
                            if 'T' in pub_time:
                                published_at = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                            else:
                                published_at = datetime.strptime(pub_time, '%Y-%m-%d %H:%M:%S')
                        except:
                            published_at = datetime.utcnow()
                    else:
                        published_at = datetime.utcnow()
                    
                    # 只保留今天的新闻
                    today = datetime.now().date()
                    if published_at.date() != today:
                        continue
                    
                    news_items.append({
                        "id": news_id,
                        "external_id": news_id or content_hash,
                        "title": title,
                        "content": content,
                        "published_at": published_at.isoformat(),
                        "content_hash": content_hash
                    })
            
            return {
                "source": "jin10",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "items": news_items,
                "total_fetched": len(data) if isinstance(data, list) else 0,
                "new_items": len(news_items)
            }
            
    except Exception as e:
        print(f"❌ 获取金十数据失败: {e}")
        # 返回空结果，不生成模拟数据
        return {
            "source": "jin10",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "items": [],
            "total_fetched": 0,
            "new_items": 0,
            "error": str(e)
        }

def save_news(data, with_sentiment=True):
    """
    保存新闻到数据库 - 增量保存
    
    Returns:
        dict: 保存统计信息
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {
        "total": len(data.get("items", [])),
        "saved": 0,
        "duplicates": 0,
        "errors": 0
    }
    
    for item in data.get("items", []):
        try:
            # 再次检查重复（双重保险）
            cursor.execute('SELECT COUNT(*) FROM news WHERE external_id = ?', (item.get('external_id'),))
            if cursor.fetchone()[0] > 0:
                stats["duplicates"] += 1
                continue
            
            # 情绪分析
            if with_sentiment:
                score, label = analyze_sentiment(item.get("content", ""))
                item["sentiment_score"] = score
                item["sentiment_label"] = label
            else:
                score = item.get("sentiment_score", 0)
                label = item.get("sentiment_label", "中性")
            
            # 提取关键词
            keywords = extract_keywords(item.get("content", ""))
            
            cursor.execute('''
                INSERT INTO news 
                (source, external_id, title, content, sentiment_score, sentiment_label, keywords, impact_market, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data["source"],
                item.get("external_id", ""),
                item.get("title", ""),
                item.get("content", ""),
                score,
                label,
                json.dumps(keywords),
                json.dumps([]),
                item.get("published_at", datetime.utcnow().isoformat())
            ))
            
            stats["saved"] += 1
            
        except Exception as e:
            print(f"❌ 保存新闻失败: {e}")
            stats["errors"] += 1
    
    conn.commit()
    conn.close()
    
    return stats

def log_fetch_status(source: str, fetched: int, new: int, duplicates: int, 
                    status: str = "success", error: str = None):
    """记录抓取日志"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO news_fetch_log (source, items_fetched, items_new, items_duplicate, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (source, fetched, new, duplicates, status, error))
    
    conn.commit()
    conn.close()

def fetch_and_save_news(source="jin10", with_sentiment=True):
    """
    获取并保存新闻 - 主入口函数
    
    Returns:
        dict: 抓取结果统计
    """
    print(f"[{datetime.now()}] 🔍 开始获取 {source} 新闻...")
    
    result = {
        "source": source,
        "fetch_time": datetime.now().isoformat(),
        "fetched": 0,
        "saved": 0,
        "duplicates": 0,
        "status": "success"
    }
    
    try:
        if source == "jin10":
            data = fetch_jin10_news(limit=50)
            result["fetched"] = data.get("total_fetched", 0)
            
            if data.get("items"):
                stats = save_news(data, with_sentiment)
                result["saved"] = stats["saved"]
                result["duplicates"] = stats["duplicates"]
                print(f"✅ 获取 {result['fetched']} 条，新增 {result['saved']} 条，重复 {result['duplicates']} 条")
            else:
                print(f"ℹ️ 没有新新闻（已获取 {result['fetched']} 条，全部重复或不符合条件）")
                
            # 记录日志
            log_fetch_status(source, result["fetched"], result["saved"], 
                           result["duplicates"], "success")
        else:
            result["status"] = "error"
            result["error"] = f"不支持的数据源: {source}"
            log_fetch_status(source, 0, 0, 0, "error", result["error"])
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        log_fetch_status(source, 0, 0, 0, "error", str(e))
        print(f"❌ 获取新闻失败: {e}")
    
    return result

def get_news_by_time_range(start_time: datetime = None, end_time: datetime = None,
                          source: str = None, limit: int = 50,
                          min_sentiment: float = None) -> list:
    """
    根据时间范围获取新闻
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        source: 新闻源过滤
        limit: 数量限制
        min_sentiment: 最小情绪分数（绝对值）
    
    Returns:
        list: 新闻列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 构建查询条件
    conditions = []
    params = []
    
    if start_time:
        conditions.append("published_at >= ?")
        params.append(start_time.isoformat())
    
    if end_time:
        conditions.append("published_at <= ?")
        params.append(end_time.isoformat())
    
    if source:
        conditions.append("source = ?")
        params.append(source)
    
    if min_sentiment is not None:
        conditions.append("ABS(sentiment_score) >= ?")
        params.append(min_sentiment)
    
    # 构建SQL
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"SELECT * FROM news {where_clause} ORDER BY published_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "source": row[1],
            "external_id": row[2],
            "title": row[3],
            "content": row[4],
            "sentiment_score": row[5],
            "sentiment_label": row[6],
            "keywords": json.loads(row[7]) if row[7] else [],
            "impact_market": json.loads(row[8]) if row[8] else [],
            "published_at": row[9],
            "created_at": row[10]
        })
    
    return items

def get_recent_news(limit=20, hours=24, min_sentiment=None):
    """获取最近新闻"""
    since = datetime.now() - timedelta(hours=hours)
    return get_news_by_time_range(start_time=since, limit=limit, min_sentiment=min_sentiment)

def get_news_stats(hours=24) -> dict:
    """获取新闻统计信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    
    # 新闻数量统计
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN sentiment_score > 0.2 THEN 1 ELSE 0 END) as bullish,
            SUM(CASE WHEN sentiment_score < -0.2 THEN 1 ELSE 0 END) as bearish,
            AVG(sentiment_score) as avg_score,
            MAX(published_at) as latest
        FROM news 
        WHERE published_at > ?
    ''', (since,))
    
    row = cursor.fetchone()
    
    # 抓取日志统计
    cursor.execute('''
        SELECT 
            COUNT(*) as fetch_count,
            SUM(items_new) as total_new,
            MAX(fetch_time) as last_fetch
        FROM news_fetch_log 
        WHERE fetch_time > ? AND status = 'success'
    ''', (since,))
    
    log_row = cursor.fetchone()
    conn.close()
    
    return {
        "period_hours": hours,
        "total_news": row[0] or 0,
        "bullish_count": row[1] or 0,
        "bearish_count": row[2] or 0,
        "neutral_count": (row[0] or 0) - (row[1] or 0) - (row[2] or 0),
        "avg_sentiment": round(row[3] or 0, 3),
        "latest_news_time": row[4],
        "fetch_count": log_row[0] or 0,
        "total_new_items": log_row[1] or 0,
        "last_fetch_time": log_row[2]
    }

def generate_sentiment_report():
    """生成情绪报告"""
    stats_24h = get_news_stats(hours=24)
    stats_1h = get_news_stats(hours=1)
    
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "24h": stats_24h,
        "1h": stats_1h
    }

def run_scheduled_fetch():
    """运行定时获取 - 每30分钟调用一次"""
    print(f"\n[{datetime.now()}] ⏰ 执行定时新闻获取...")
    
    for source in CONFIG["sources"]:
        result = fetch_and_save_news(source, with_sentiment=True)
        
        # 如果获取失败且没有错误记录，打印警告
        if result["status"] != "success":
            print(f"⚠️  {source} 获取失败: {result.get('error', '未知错误')}")
    
    print(f"[{datetime.now()}] ✅ 定时任务完成\n")

def main():
    parser = argparse.ArgumentParser(description="News Sentiment Scanner - 新闻情绪扫描器")
    parser.add_argument("--init", action="store_true", help="初始化数据库")
    parser.add_argument("--source", default="jin10", help="新闻源 (默认: jin10)")
    parser.add_argument("--limit", type=int, default=20, help="获取数量")
    parser.add_argument("--sentiment", action="store_true", help="包含情绪分析")
    parser.add_argument("--report", action="store_true", help="生成情绪报告")
    parser.add_argument("--recent", action="store_true", help="显示最近新闻")
    parser.add_argument("--hours", type=int, default=24, help="时间范围(小时)")
    parser.add_argument("--fetch", action="store_true", help="执行一次获取")
    parser.add_argument("--scheduled", action="store_true", help="启动定时任务(每30分钟)")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    
    args = parser.parse_args()
    
    if args.init:
        init_news_table()
        return
    
    if args.report:
        report = generate_sentiment_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    
    if args.stats:
        stats = get_news_stats(hours=args.hours)
        print(f"\n📊 最近{args.hours}小时新闻统计:")
        print(f"  总新闻数: {stats['total_news']}")
        print(f"  看涨: {stats['bullish_count']} | 看跌: {stats['bearish_count']} | 中性: {stats['neutral_count']}")
        print(f"  平均情绪: {stats['avg_sentiment']}")
        print(f"  抓取次数: {stats['fetch_count']}")
        print(f"  上次抓取: {stats['last_fetch_time']}")
        return
    
    if args.fetch:
        result = fetch_and_save_news(args.source, args.sentiment)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    if args.scheduled:
        import schedule
        import time
        
        print(f"⏰ 启动定时新闻获取 (每{CONFIG['fetch_interval_minutes']}分钟)")
        print("按 Ctrl+C 停止\n")
        
        # 立即执行一次
        run_scheduled_fetch()
        
        # 设置定时任务
        schedule.every(CONFIG['fetch_interval_minutes']).minutes.do(run_scheduled_fetch)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 停止定时任务")
        return
    
    if args.recent:
        items = get_recent_news(limit=args.limit, hours=args.hours)
        print(f"\n📰 最近 {len(items)} 条新闻 (最近{args.hours}小时):")
        print("-" * 60)
        for item in items:
            time_str = item['published_at'][:16] if item['published_at'] else ''
            print(f"\n[{item['sentiment_label']}] {time_str}")
            print(f"  {item['title'] or item['content'][:60]}...")
            print(f"  情绪分: {item['sentiment_score']:.2f} | 关键词: {', '.join(item['keywords'][:3])}")
        return
    
    # 默认执行一次获取
    result = fetch_and_save_news(args.source, args.sentiment)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
