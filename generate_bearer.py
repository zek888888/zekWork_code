#!/usr/bin/env python3
"""
使用 Client ID/Secret 生成 Bearer Token (API Basic)
"""

import base64
import urllib.request
import urllib.error
import json

def generate_bearer_token(client_id, client_secret):
    """生成 Bearer Token"""
    
    # Basic Auth
    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()
    
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
            return result.get('access_token')
    except urllib.error.HTTPError as e:
        print(f"错误: {e.read().decode()}")
        return None

def test_bearer(bearer_token):
    """测试 Bearer Token"""
    url = 'https://api.twitter.com/2/tweets/search/recent?query=from:cz_binance&max_results=5'
    
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {bearer_token}'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            count = len(data.get('data', []))
            return count > 0
    except Exception as e:
        return False

if __name__ == '__main__':
    # 读取配置
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, ".env.twitter")
    
    creds = {}
    with open(env_file, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                creds[key] = value.strip()
    
    client_id = creds.get('TWITTER_CLIENT_ID')
    client_secret = creds.get('TWITTER_CLIENT_SECRET')
    
    print("="*60)
    print("  生成 Bearer Token (API Basic)")
    print("="*60)
    print()
    
    print(f"Client ID: {client_id[:30]}...")
    print()
    
    print("【步骤1】生成 Bearer Token...")
    bearer = generate_bearer_token(client_id, client_secret)
    
    if bearer:
        print(f"✅ 生成成功！")
        print(f"   Bearer: {bearer[:50]}...")
        print()
        
        print("【步骤2】测试权限...")
        if test_bearer(bearer):
            print("✅ 搜索API权限正常！")
            
            # 保存到文件
            print("\n【步骤3】更新配置文件...")
            lines = []
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # 更新 Bearer Token
            new_lines = []
            for line in lines:
                if line.startswith('TWITTER_BEARER_TOKEN='):
                    new_lines.append(f'TWITTER_BEARER_TOKEN={bearer}\n')
                else:
                    new_lines.append(line)
            
            with open(env_file, 'w') as f:
                f.writelines(new_lines)
            
            print(f"✅ 已更新 {env_file}")
            print()
            print("="*60)
            print("🎉 API Basic 配置完成！")
            print("="*60)
            print("\n现在可以使用以下功能：")
            print("  - 搜索推文 (50,000次/月)")
            print("  - 获取用户时间线")
            print("  - 读取推文数据")
        else:
            print("❌ 测试失败，Token可能无效")
    else:
        print("❌ 生成失败")
