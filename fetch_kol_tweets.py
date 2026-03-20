#!/usr/bin/env python3
"""
使用Twitter OAuth 1.0a API获取KOL推文
"""

import os
import sys
import json
import base64
import hashlib
import hmac
import random
import string
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

def load_credentials():
    """加载凭证"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, ".env.twitter")
    creds = {}
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    creds[key] = value
    
    return creds

def create_oauth_signature(method, url, params, consumer_secret, token_secret):
    """创建OAuth签名"""
    sig_params = {}
    sig_params.update(params)
    
    sorted_params = sorted(sig_params.items())
    param_string = '&'.join(
        f'{urllib.parse.quote(k, safe="")}={urllib.parse.quote(str(v), safe="")}'
        for k, v in sorted_params
    )
    
    base_string = '&'.join([
        method.upper(),
        urllib.parse.quote(url, safe=''),
        urllib.parse.quote(param_string, safe='')
    ])
    
    signing_key = '&'.join([
        urllib.parse.quote(consumer_secret, safe=''),
        urllib.parse.quote(token_secret, safe='')
    ])
    
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    
    return signature

def create_oauth_header(url, method, creds, extra_params=None):
    """创建OAuth头"""
    oauth_params = {
        'oauth_consumer_key': creds['TWITTER_CONSUMER_KEY'],
        'oauth_nonce': ''.join(random.choices(string.ascii_letters + string.digits, k=42)),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_token': creds['TWITTER_ACCESS_TOKEN'],
        'oauth_version': '1.0',
    }
    
    if extra_params:
        oauth_params.update(extra_params)
    
    signature = create_oauth_signature(
        method, url, oauth_params,
        creds['TWITTER_CONSUMER_SECRET'],
        creds['TWITTER_ACCESS_TOKEN_SECRET']
    )
    oauth_params['oauth_signature'] = signature
    
    auth_header = 'OAuth ' + ', '.join(
        f'{urllib.parse.quote(k)}="{urllib.parse.quote(str(v))}"'
        for k, v in sorted(oauth_params.items())
    )
    
    return auth_header

def get_user_tweets_v2(creds, username, max_results=10):
    """使用API v2获取用户推文"""
    
    # 首先获取用户ID
    user_url = f'https://api.twitter.com/2/users/by/username/{username}'
    auth_header = create_oauth_header(user_url, 'GET', creds)
    
    req = urllib.request.Request(
        user_url,
        headers={'Authorization': auth_header}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            user_data = json.loads(response.read().decode())
            user_id = user_data['data']['id']
    except urllib.error.HTTPError as e:
        print(f"  ❌ 获取用户ID失败: {e.read().decode()}")
        return []
    
    # 获取用户推文
    # 计算 yesterday (2026-03-19)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    today = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    tweets_url = f'https://api.twitter.com/2/users/{user_id}/tweets?max_results={max_results}&tweet.fields=created_at,public_metrics&start_time={yesterday}'
    
    auth_header = create_oauth_header(tweets_url, 'GET', creds)
    
    req = urllib.request.Request(
        tweets_url,
        headers={'Authorization': auth_header}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            tweets_data = json.loads(response.read().decode())
            return tweets_data.get('data', [])
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"  ❌ 获取推文失败: {error_body}")
        return []

def search_user_tweets_v2(creds, username, max_results=10):
    """使用搜索API获取用户最近推文"""
    
    # 搜索特定用户的推文
    query = f"from:{username}"
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    search_url = f'https://api.twitter.com/2/tweets/search/recent?query={urllib.parse.quote(query)}&max_results={max_results}&tweet.fields=created_at,public_metrics,author_id&start_time={yesterday}'
    
    auth_header = create_oauth_header(search_url, 'GET', creds)
    
    req = urllib.request.Request(
        search_url,
        headers={'Authorization': auth_header}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            search_data = json.loads(response.read().decode())
            return search_data.get('data', [])
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"  ❌ 搜索失败: {error_body}")
        return []

def analyze_tweets(tweets):
    """分析推文内容"""
    analysis = {
        'sentiment': 'neutral',
        'keywords': [],
        'coins': [],
        'themes': []
    }
    
    # 简单的关键词提取
    text = ' '.join([t.get('text', '') for t in tweets]).lower()
    
    # 检测币种
    coins = ['btc', 'eth', 'sol', 'bsc', 'bnb', 'doge', 'shib', 'pepe', 'ai', 'nft']
    found_coins = [c.upper() for c in coins if c in text]
    analysis['coins'] = found_coins
    
    # 检测情绪
    if any(word in text for word in ['bull', 'pump', 'moon', ' ATH', 'breakout', 'long', 'buy']):
        analysis['sentiment'] = 'bullish'
    elif any(word in text for word in ['bear', 'dump', 'crash', 'short', 'sell', 'correction']):
        analysis['sentiment'] = 'bearish'
    
    return analysis

def main():
    print("="*70)
    print("  战颅将军 - KOL推文收集系统")
    print("="*70)
    print()
    
    # 加载凭证
    creds = load_credentials()
    
    required = ['TWITTER_CONSUMER_KEY', 'TWITTER_CONSUMER_SECRET', 
                'TWITTER_ACCESS_TOKEN', 'TWITTER_ACCESS_TOKEN_SECRET']
    
    for key in required:
        if not creds.get(key):
            print(f"❌ 缺少配置: {key}")
            return
    
    # KOL列表
    kols = [
        "joely7758521",
        "stockwilsonrice", 
        "darrencao2024",
        "xhunt_ai",
        "0xSunNFT",
        "cz_binance",
        "BTC563",
        "monkeyjiang",
        "thankUcrypto",
        "xiaomustock",
        "cnfinancewatch",
        "cyrilxuq"
    ]
    
    print(f"目标日期: 2026-03-20")
    print(f"监控KOL: {len(kols)}位")
    print()
    
    all_data = []
    
    for username in kols:
        print(f"【@{username}】")
        
        # 尝试获取推文
        tweets = get_user_tweets_v2(creds, username, max_results=5)
        
        if not tweets:
            # 如果失败，尝试搜索
            print("  尝试搜索API...")
            tweets = search_user_tweets_v2(creds, username, max_results=5)
        
        if tweets:
            analysis = analyze_tweets(tweets)
            
            kol_data = {
                'username': username,
                'tweet_count': len(tweets),
                'tweets': tweets,
                'analysis': analysis
            }
            all_data.append(kol_data)
            
            print(f"  ✅ 获取 {len(tweets)} 条推文")
            print(f"  📊 情绪: {analysis['sentiment']}")
            print(f"  💰 提及: {', '.join(analysis['coins']) if analysis['coins'] else '无'}")
            
            # 显示最新推文
            if tweets:
                latest = tweets[0]
                print(f"  📝 {latest.get('text', '')[:60]}...")
        else:
            print("  ⚠️ 无数据")
        
        print()
        time.sleep(1)  # 避免请求过快
    
    # 保存结果
    output = {
        'collection_time': datetime.now().isoformat(),
        'target_date': '2026-03-20',
        'total_kols': len(kols),
        'successful': len(all_data),
        'data': all_data
    }
    
    output_file = f"kol_tweets_0320_{datetime.now().strftime('%H%M')}.json"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("="*70)
    print(f"✅ 收集完成！成功: {len(all_data)}/{len(kols)} 位KOL")
    print(f"📁 已保存: {output_path}")
    print("="*70)
    
    # 生成汇总报告
    generate_summary(all_data)

def generate_summary(all_data):
    """生成汇总报告"""
    print("\n" + "="*70)
    print("【汇总分析】")
    print("="*70)
    
    # 统计情绪
    sentiments = {'bullish': 0, 'bearish': 0, 'neutral': 0}
    all_coins = []
    
    for kol in all_data:
        sentiments[kol['analysis']['sentiment']] += 1
        all_coins.extend(kol['analysis']['coins'])
    
    print(f"\n📊 情绪分布:")
    total = len(all_data)
    if total > 0:
        print(f"   🟢 看多: {sentiments['bullish']} ({sentiments['bullish']/total*100:.0f}%)")
        print(f"   🔴 看空: {sentiments['bearish']} ({sentiments['bearish']/total*100:.0f}%)")
        print(f"   ⚪ 中性: {sentiments['neutral']} ({sentiments['neutral']/total*100:.0f}%)")
    
    # 热门币种
    from collections import Counter
    coin_counts = Counter(all_coins)
    if coin_counts:
        print(f"\n💰 热门币种:")
        for coin, count in coin_counts.most_common(5):
            print(f"   {coin}: {count}次提及")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    import time
    main()
