#!/usr/bin/env python3
"""
使用 API Basic 收集 KOL 推文
Bearer Token 有 50,000 次/月 读取权限
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

def load_credentials():
    """加载凭证"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, ".env.twitter")
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('TWITTER_BEARER_TOKEN='):
                return line.split('=', 1)[1].strip()
    return None

def search_tweets(bearer, query, max_results=10):
    """搜索推文 - Basic 权限需要 max_results >= 10"""
    
    # 计算时间范围 (过去24小时)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # URL 编码查询
    encoded_query = urllib.parse.quote(query)
    
    # Basic 权限: max_results 必须是 10-100
    url = f'https://api.twitter.com/2/tweets/search/recent?query={encoded_query}&max_results={max_results}&tweet.fields=created_at,public_metrics,author_id&start_time={yesterday}'
    
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {bearer}'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error = e.read().decode()
        print(f"    API错误: {error[:200]}")
        return None

def main():
    print("="*70)
    print("  战颅将军 - KOL推文收集系统 (API Basic)")
    print("="*70)
    print()
    
    bearer = load_credentials()
    if not bearer:
        print("❌ 未找到 Bearer Token")
        return
    
    print(f"Bearer: {bearer[:40]}...")
    print()
    
    # KOL列表 - 使用搜索查询 from:username
    kols = [
        ("joely7758521", "交易员"),
        ("stockwilsonrice", "分析师"),
        ("darrencao2024", "交易员"),
        ("xhunt_ai", "Influencer"),
        ("0xSunNFT", "Influencer"),
        ("cz_binance", "官方"),
        ("BTC563", "交易员"),
        ("monkeyjiang", "交易员"),
        ("thankUcrypto", "Influencer"),
        ("xiaomustock", "交易员"),
    ]
    
    print(f"目标日期: 2026-03-20")
    print(f"监控KOL: {len(kols)}位")
    print()
    
    all_results = []
    
    for username, category in kols:
        print(f"【@{username}】({category})")
        
        # 搜索该用户的推文
        query = f"from:{username}"
        result = search_tweets(bearer, query, max_results=10)
        
        if result and 'data' in result:
            tweets = result['data']
            print(f"  ✅ 找到 {len(tweets)} 条推文")
            
            # 显示最新推文
            for tweet in tweets[:2]:
                text = tweet.get('text', '')[:70]
                created = tweet.get('created_at', '')[:10]
                print(f"     [{created}] {text}...")
            
            all_results.append({
                'username': username,
                'category': category,
                'count': len(tweets),
                'tweets': tweets
            })
        elif result and 'errors' in result:
            print(f"  ❌ API错误")
        else:
            print(f"  ⚠️ 无推文或无法访问")
        
        print()
    
    # 搜索热门话题
    print("【热门话题搜索】")
    topics = [
        ("Bitcoin OR BTC OR 比特币", "BTC话题"),
        ("Ethereum OR ETH", "ETH话题"),
        ("BSC OR Binance", "BSC话题"),
        ("crypto cryptocurrency", "币圈综合"),
    ]
    
    topic_results = []
    for query, label in topics:
        print(f"  {label}...", end=" ")
        result = search_tweets(bearer, query, max_results=10)
        if result and 'data' in result:
            print(f"✅ {len(result['data'])}条")
            topic_results.append({'label': label, 'count': len(result['data']), 'tweets': result['data'][:3]})
        else:
            print("⚠️ 无数据")
    
    # 保存结果
    output = {
        'collection_time': datetime.now().isoformat(),
        'target_date': '2026-03-20',
        'kol_count': len(kols),
        'successful_kols': len(all_results),
        'kol_data': all_results,
        'topic_data': topic_results
    }
    
    output_file = f"kol_tweets_0320_{datetime.now().strftime('%H%M')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print()
    print("="*70)
    print(f"✅ 收集完成！成功: {len(all_results)}/{len(kols)} 位KOL")
    print(f"📁 已保存: {output_file}")
    print("="*70)
    
    # 生成汇总
    generate_summary(all_results, topic_results)

def generate_summary(kol_data, topic_data):
    """生成汇总报告"""
    print("\n" + "="*70)
    print("【汇总分析】")
    print("="*70)
    
    # 统计每个KOL的推文数
    print(f"\n📊 KOL推文统计:")
    for kol in kol_data:
        print(f"   @{kol['username']}: {kol['count']}条 ({kol['category']})")
    
    # 热门话题
    if topic_data:
        print(f"\n🔥 热门话题:")
        for topic in topic_data:
            print(f"   {topic['label']}: {topic['count']}条相关推文")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    main()
