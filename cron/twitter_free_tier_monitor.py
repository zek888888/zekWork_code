#!/usr/bin/env python3
"""
Twitter API 免费额度监控器
每月自动检测额度是否恢复，并尝试获取真实数据
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

BASE_PATH = os.path.expanduser("~/.openclaw/workspace/quant-trading")
sys.path.insert(0, os.path.join(BASE_PATH, "config-layer"))
sys.path.insert(0, os.path.join(BASE_PATH, "research-layer/twitter-sentiment"))

from twitter_api_client import TwitterAPIClient, load_twitter_credentials
from twitter_fetcher import TwitterFetcher
from twitter_watchlist_manager import TwitterWatchlistManager

DB_PATH = os.path.join(BASE_PATH, "data-layer/market_data.db")


def check_api_quota():
    """检查API剩余额度"""
    try:
        credentials = load_twitter_credentials()
        bearer_token = credentials.get('TWITTER_BEARER_TOKEN', '')
        
        if not bearer_token:
            return False, "Bearer Token 未配置"
        
        client = TwitterAPIClient(bearer_token)
        
        # 尝试获取一个用户测试额度
        user = client.get_user_by_username("twitter")
        
        if user:
            return True, "API额度充足"
        else:
            # 检查错误类型
            return False, "API额度已用完或受限"
            
    except Exception as e:
        return False, f"API检查失败: {str(e)}"


def get_last_fetch_time():
    """获取上次成功获取真实数据的时间"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查是否有非测试数据（真实tweet_id是纯数字）
    cursor.execute('''
        SELECT MAX(created_at) 
        FROM twitter_posts 
        WHERE tweet_id NOT LIKE 'test_%' 
        AND tweet_id NOT LIKE 'demo_%'
        AND tweet_id NOT LIKE 'mock_%'
    ''')
    
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        return datetime.fromisoformat(result[0].replace('Z', '+00:00'))
    return None


def get_monthly_reset_date():
    """获取下次额度重置日期（每月1号）"""
    now = datetime.now()
    if now.day == 1:
        return now
    # 下个月1号
    if now.month == 12:
        return datetime(now.year + 1, 1, 1)
    else:
        return datetime(now.year, now.month + 1, 1)


def monitor_and_fetch():
    """监控额度并尝试获取数据"""
    print("="*60)
    print("Twitter API 免费额度监控器")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 1. 检查API额度
    print("\n[1/3] 检查API额度...")
    has_quota, message = check_api_quota()
    
    print(f"  结果: {message}")
    
    if not has_quota:
        # 计算下次重置时间
        reset_date = get_monthly_reset_date()
        days_until_reset = (reset_date - datetime.now()).days + 1
        
        print(f"\n  ⚠️ 免费额度已用完")
        print(f"  📅 下次重置: {reset_date.strftime('%Y年%m月%d日')} ({days_until_reset}天后)")
        print(f"  💡 当前使用演示数据")
        
        # 记录到日志
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS twitter_api_quota_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                has_quota INTEGER,
                message TEXT,
                next_reset_date TIMESTAMP
            )
        ''')
        cursor.execute('''
            INSERT INTO twitter_api_quota_log (has_quota, message, next_reset_date)
            VALUES (?, ?, ?)
        ''', (0, message, reset_date.isoformat()))
        conn.commit()
        conn.close()
        
        print("\n  ✓ 监控记录已保存")
        return False
    
    # 2. 有额度，获取真实数据
    print("\n[2/3] API额度充足，开始获取真实数据...")
    
    manager = TwitterWatchlistManager()
    fetcher = TwitterFetcher()
    
    usernames = manager.get_active_usernames()
    print(f"  观察人数量: {len(usernames)}")
    
    total_fetched = 0
    total_new = 0
    
    for username in usernames:
        try:
            print(f"\n  获取 @{username}...")
            
            # 强制使用API获取（不走模拟数据）
            sys.path.insert(0, os.path.join(BASE_PATH, "config-layer"))
            from twitter_api_client import TwitterAPIClient
            
            client = TwitterAPIClient()
            user = client.get_user_by_username(username)
            
            if not user:
                print(f"    ✗ 用户不存在")
                continue
            
            # 获取最近1小时推文
            start_time = (datetime.utcnow() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
            api_tweets = client.get_user_tweets(user['id'], max_results=10, start_time=start_time)
            
            print(f"    ✓ API返回 {len(api_tweets)} 条")
            
            for t in api_tweets:
                from twitter_fetcher import Tweet
                from datetime import datetime
                
                tweet = Tweet(
                    tweet_id=t['id'],
                    username=username,
                    content=t['text'],
                    posted_at=datetime.fromisoformat(t['created_at'].replace('Z', '+00:00')),
                    retweet_count=t.get('retweet_count', 0),
                    like_count=t.get('like_count', 0),
                    reply_count=t.get('reply_count', 0)
                )
                
                if fetcher.save_tweet(tweet):
                    total_new += 1
                total_fetched += 1
                
        except Exception as e:
            print(f"    ✗ 错误: {e}")
    
    print(f"\n  总计: 获取 {total_fetched} 条，新入库 {total_new} 条")
    
    # 3. 触发AI分析
    if total_new > 0:
        print("\n[3/3] 触发AI分析...")
        sys.path.insert(0, os.path.join(BASE_PATH, "ai_models"))
        from twitter_analyzer import TwitterAnalyzer
        
        analyzer = TwitterAnalyzer()
        result = analyzer.batch_analyze_pending(hours=1, limit=50)
        
        print(f"  分析完成: {result['analyzed']} 条")
        print(f"    利好: {result['results']['bullish']}")
        print(f"    利空: {result['results']['bearish']}")
        print(f"    中性: {result['results']['neutral']}")
    
    # 记录成功日志
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS twitter_api_quota_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            has_quota INTEGER,
            message TEXT,
            tweets_fetched INTEGER,
            tweets_new INTEGER
        )
    ''')
    cursor.execute('''
        INSERT INTO twitter_api_quota_log (has_quota, message, tweets_fetched, tweets_new)
        VALUES (?, ?, ?, ?)
    ''', (1, f"成功获取真实数据", total_fetched, total_new))
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("✓ 真实数据获取完成！")
    print("="*60)
    
    return True


def main():
    """主函数"""
    monitor_and_fetch()


if __name__ == "__main__":
    main()
