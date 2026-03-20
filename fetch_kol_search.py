#!/usr/bin/env python3
"""
使用Twitter Bearer Token搜索KOL推文
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

def load_bearer_token():
    """加载Bearer Token"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, ".env.twitter")
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('TWITTER_BEARER_TOKEN='):
                return line.split('=', 1)[1].strip()
    return None

def search_tweets(bearer_token, query, max_results=10):
    """搜索推文"""
    
    # 计算时间范围
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    url = f'https://api.twitter.com/2/tweets/search/recent?query={urllib.parse.quote(query)}&max_results={max_results}&tweet.fields=created_at,public_metrics,author_id&start_time={yesterday}'
    
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {bearer_token}'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error = e.read().decode()
        print(f"  ❌ API错误: {error}")
        return None

def main():
    print("="*70)
    print("  战颅将军 - KOL推文搜索系统 (Bearer Token)")
    print("="*70)
    print()
    
    bearer_token = load_bearer_token()
    if not bearer_token:
        print("❌ 未找到Bearer Token")
        return
    
    print(f"Token: {bearer_token[:30]}...")
    print()
    
    # KOL列表 + 搜索关键词
    searches = [
        # 搜索特定KOL的推文
        ("from:joely7758521", "joely7758521"),
        ("from:0xSunNFT", "0xSunNFT"),
        ("from:cz_binance", "cz_binance"),
        ("from:BTC563", "BTC563"),
        ("from:monkeyjiang", "monkeyjiang"),
        ("from:thankUcrypto", "thankUcrypto"),
        # 搜索热门话题
        ("BTC OR Bitcoin OR 比特币 lang:zh", "BTC话题"),
        ("ETH OR Ethereum lang:zh", "ETH话题"),
        ("BSC OR 币安智能链 lang:zh", "BSC话题"),
        ("crypto OR 加密货币 OR 币圈 lang:zh", "币圈综合"),
    ]
    
    all_results = []
    
    for query, label in searches:
        print(f"【搜索: {label}】")
        print(f"  查询: {query}")
        
        result = search_tweets(bearer_token, query, max_results=5)
        
        if result and 'data' in result:
            tweets = result['data']
            print(f"  ✅ 找到 {len(tweets)} 条推文")
            
            for tweet in tweets[:3]:
                text = tweet.get('text', '')[:80]
                print(f"     - {text}...")
            
            all_results.append({
                'label': label,
                'query': query,
                'count': len(tweets),
                'tweets': tweets
            })
        elif result and 'errors' in result:
            print(f"  ❌ API错误: {result['errors']}")
        else:
            print(f"  ⚠️ 无结果或权限不足")
        
        print()
    
    # 保存结果
    output = {
        'collection_time': datetime.now().isoformat(),
        'total_searches': len(searches),
        'successful': len(all_results),
        'data': all_results
    }
    
    output_file = f"kol_search_0320_{datetime.now().strftime('%H%M')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("="*70)
    print(f"✅ 搜索完成！成功: {len(all_results)}/{len(searches)}")
    print(f"📁 已保存: {output_file}")
    print("="*70)

if __name__ == '__main__':
    main()
