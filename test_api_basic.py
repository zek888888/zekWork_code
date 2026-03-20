#!/usr/bin/env python3
"""
测试 Twitter API Basic 权限
"""

import os
import json
import urllib.request

def load_credentials():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, ".env.twitter")
    creds = {}
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                creds[key] = value.strip()
    
    return creds

def test_bearer_search(creds):
    """测试 Bearer Token 搜索"""
    print("【测试1】Bearer Token 搜索...")
    
    bearer = creds.get('TWITTER_BEARER_TOKEN')
    url = 'https://api.twitter.com/2/tweets/search/recent?query=from:cz_binance&max_results=5'
    
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {bearer}'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            count = len(data.get('data', []))
            print(f"  ✅ 成功！获取 {count} 条推文")
            return True
    except urllib.error.HTTPError as e:
        print(f"  ❌ 失败: {e.code} - {e.read().decode()[:200]}")
        return False

def test_user_timeline(creds):
    """测试用户时间线 API"""
    print("\n【测试2】用户时间线 API...")
    
    import base64
    import hashlib
    import hmac
    import random
    import string
    import time
    import urllib.parse
    
    def create_auth_header(url, method, creds):
        params = {
            'oauth_consumer_key': creds['TWITTER_CONSUMER_KEY'],
            'oauth_nonce': ''.join(random.choices(string.ascii_letters + string.digits, k=42)),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_token': creds['TWITTER_ACCESS_TOKEN'],
            'oauth_version': '1.0',
        }
        
        # 签名
        sorted_params = sorted(params.items())
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
            urllib.parse.quote(creds['TWITTER_CONSUMER_SECRET'], safe=''),
            urllib.parse.quote(creds['TWITTER_ACCESS_TOKEN_SECRET'], safe='')
        ])
        
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        
        params['oauth_signature'] = signature
        
        return 'OAuth ' + ', '.join(
            f'{urllib.parse.quote(k)}="{urllib.parse.quote(str(v))}"'
            for k, v in sorted(params.items())
        )
    
    # 先获取用户ID
    url = 'https://api.twitter.com/2/users/by/username/cz_binance'
    auth_header = create_auth_header(url, 'GET', creds)
    
    req = urllib.request.Request(
        url,
        headers={'Authorization': auth_header}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            user_id = data['data']['id']
            print(f"  ✅ 获取用户ID成功: {user_id}")
            
            # 获取推文
            tweets_url = f'https://api.twitter.com/2/users/{user_id}/tweets?max_results=5'
            auth_header = create_auth_header(tweets_url, 'GET', creds)
            
            req2 = urllib.request.Request(
                tweets_url,
                headers={'Authorization': auth_header}
            )
            
            with urllib.request.urlopen(req2) as response2:
                tweets_data = json.loads(response2.read().decode())
                count = len(tweets_data.get('data', []))
                print(f"  ✅ 获取推文成功: {count} 条")
                
                # 显示最新推文
                if tweets_data.get('data'):
                    latest = tweets_data['data'][0]
                    print(f"     最新: {latest['text'][:60]}...")
                
                return True
                
    except urllib.error.HTTPError as e:
        error = e.read().decode()
        print(f"  ❌ 失败: {e.code} - {error[:300]}")
        return False

def main():
    print("="*70)
    print("  Twitter API Basic 权限测试")
    print("="*70)
    print()
    
    creds = load_credentials()
    print(f"Client ID: {creds.get('TWITTER_CLIENT_ID', 'N/A')[:20]}...")
    print()
    
    # 测试各项权限
    results = {
        'Bearer搜索': test_bearer_search(creds),
        '用户时间线': test_user_timeline(creds),
    }
    
    print("\n" + "="*70)
    print("【测试结果汇总】")
    print("="*70)
    
    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n🎉 API Basic 权限正常！可以开始收集KOL推文了！")
    else:
        print("\n⚠️ 部分权限受限，可能需要重新授权")

if __name__ == '__main__':
    main()
