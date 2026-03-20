#!/usr/bin/env python3
"""
使用 API Key/Secret 生成 Bearer Token
"""

import base64
import urllib.request
import urllib.error
import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(script_dir, ".env.twitter")

creds = {}
with open(env_file, 'r') as f:
    for line in f:
        if line.strip() and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            creds[key] = value.strip()

# 使用 API Key/Secret (Consumer Key/Secret)
api_key = creds.get('TWITTER_CONSUMER_KEY')
api_secret = creds.get('TWITTER_CONSUMER_SECRET')

print("使用 API Key/Secret 生成 Bearer Token...")
print(f"API Key: {api_key[:20]}...")

credentials = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()

data = "grant_type=client_credentials".encode()

req = urllib.request.Request(
    'https://api.twitter.com/oauth2/token',
    data=data,
    headers={
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        bearer = result.get('access_token')
        print(f"✅ 成功！")
        print(f"Bearer: {bearer}")
        
        # 测试
        print("\n测试搜索API...")
        test_req = urllib.request.Request(
            'https://api.twitter.com/2/tweets/search/recent?query=Bitcoin&max_results=5',
            headers={'Authorization': f'Bearer {bearer}'}
        )
        
        with urllib.request.urlopen(test_req) as test_resp:
            test_data = json.loads(test_resp.read().decode())
            print(f"✅ 搜索API正常！找到 {len(test_data.get('data', []))} 条推文")
            
except urllib.error.HTTPError as e:
    print(f"❌ 错误: {e.read().decode()}")
