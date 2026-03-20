#!/usr/bin/env python3
"""
使用 OAuth 2.0 发布推文

使用方法:
  python3 post_tweet_oauth2.py "推文内容"
  python3 post_tweet_oauth2.py --file tweet.txt
  python3 post_tweet_oauth2.py --image /path/to/image.png "带图片的推文"
"""

import os
import sys
import json
import urllib.request
import urllib.error
import mimetypes
from datetime import datetime

ENV_FILE = ".env.twitter.oauth2"

def load_config():
    """加载配置"""
    config = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
    return config

def refresh_access_token(config):
    """刷新访问令牌"""
    client_id = config.get('TWITTER_CLIENT_ID')
    client_secret = config.get('TWITTER_CLIENT_SECRET')
    refresh_token = config.get('TWITTER_OAUTH2_REFRESH_TOKEN')
    
    if not refresh_token:
        print("❌ 没有 Refresh Token，需要重新授权")
        return None
    
    import base64
    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()
    
    data = f"refresh_token={refresh_token}&grant_type=refresh_token".encode()
    
    req = urllib.request.Request(
        'https://api.twitter.com/2/oauth2/token',
        data=data,
        headers={
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            
            # 更新配置
            config['TWITTER_OAUTH2_ACCESS_TOKEN'] = result['access_token']
            if 'refresh_token' in result:
                config['TWITTER_OAUTH2_REFRESH_TOKEN'] = result['refresh_token']
            
            expires_at = datetime.now() + result.get('expires_in', 7200)
            config['TWITTER_OAUTH2_TOKEN_EXPIRES_AT'] = expires_at.isoformat()
            
            # 保存
            lines = []
            with open(ENV_FILE, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#') and '=' in line:
                        key = line.split('=', 1)[0]
                        if key in ['TWITTER_OAUTH2_ACCESS_TOKEN', 'TWITTER_OAUTH2_REFRESH_TOKEN', 'TWITTER_OAUTH2_TOKEN_EXPIRES_AT']:
                            continue
                    lines.append(line)
            
            with open(ENV_FILE, 'w') as f:
                f.writelines(lines)
                f.write(f"TWITTER_OAUTH2_ACCESS_TOKEN={result['access_token']}\n")
                if 'refresh_token' in result:
                    f.write(f"TWITTER_OAUTH2_REFRESH_TOKEN={result['refresh_token']}\n")
                f.write(f"TWITTER_OAUTH2_TOKEN_EXPIRES_AT={expires_at.isoformat()}\n")
            
            print("✅ 令牌已刷新")
            return result['access_token']
            
    except urllib.error.HTTPError as e:
        print(f"❌ 刷新令牌失败: {e.read().decode()}")
        return None

def check_token_valid(config):
    """检查令牌是否有效"""
    expires_at = config.get('TWITTER_OAUTH2_TOKEN_EXPIRES_AT')
    if expires_at:
        try:
            from datetime import datetime
            expires = datetime.fromisoformat(expires_at)
            if datetime.now() > expires:
                print("⚠️ 访问令牌已过期，正在刷新...")
                return refresh_access_token(config)
        except:
            pass
    return config.get('TWITTER_OAUTH2_ACCESS_TOKEN')

def upload_media(access_token, media_path):
    """上传媒体文件"""
    
    # 读取文件
    with open(media_path, 'rb') as f:
        media_data = f.read()
    
    # 获取MIME类型
    mime_type, _ = mimetypes.guess_type(media_path)
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    # 媒体上传API v1.1 (OAuth 2.0不支持媒体上传，需要特殊处理)
    # 这里使用简化版，实际需要OAuth 1.0a或特殊授权
    
    print(f"⚠️ OAuth 2.0 暂不支持媒体上传")
    print(f"   如需发图片，请使用 OAuth 1.0a")
    return None

def post_tweet(access_token, text, reply_to=None):
    """发布推文"""
    
    payload = {'text': text}
    
    if reply_to:
        payload['reply'] = {'in_reply_to_tweet_id': reply_to}
    
    data = json.dumps(payload).encode()
    
    req = urllib.request.Request(
        'https://api.twitter.com/2/tweets',
        data=data,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ 发布失败: {error_body}")
        return None

def main():
    print("="*60)
    print("  Twitter OAuth 2.0 发推工具")
    print("="*60)
    print()
    
    # 解析参数
    if len(sys.argv) < 2:
        print("使用方法:")
        print(f"  python3 {sys.argv[0]} '推文内容'")
        print(f"  python3 {sys.argv[0]} --file tweet.txt")
        print()
        print("选项:")
        print("  --file FILE    从文件读取推文内容")
        print("  --reply ID     回复指定推文ID")
        return
    
    text = None
    reply_to = None
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--file' and i + 1 < len(sys.argv):
            file_path = sys.argv[i + 1]
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    text = f.read().strip()
                print(f"✅ 已从文件加载: {file_path}")
            else:
                print(f"❌ 文件不存在: {file_path}")
                return
            i += 2
        elif arg == '--reply' and i + 1 < len(sys.argv):
            reply_to = sys.argv[i + 1]
            i += 2
        else:
            if text is None:
                text = arg
            else:
                text += ' ' + arg
            i += 1
    
    if not text:
        print("❌ 请提供推文内容")
        return
    
    # 检查长度
    if len(text) > 280:
        print(f"⚠️ 警告: 推文长度 {len(text)} 超过280字符限制")
        print("   将被截断或发送失败")
    
    print(f"推文内容: {text[:50]}..." if len(text) > 50 else f"推文内容: {text}")
    print()
    
    # 加载配置
    config = load_config()
    
    if not config.get('TWITTER_OAUTH2_ACCESS_TOKEN'):
        print("❌ 未找到 Access Token")
        print("   请先运行: python3 twitter_oauth2_authorize.py")
        return
    
    # 检查并刷新令牌
    access_token = check_token_valid(config)
    if not access_token:
        print("❌ 无法获取有效访问令牌")
        return
    
    print("【发布推文】...")
    result = post_tweet(access_token, text, reply_to)
    
    if result and 'data' in result:
        tweet_id = result['data']['id']
        tweet_text = result['data']['text']
        
        print("✅ 推文发布成功！")
        print(f"   Tweet ID: {tweet_id}")
        print(f"   链接: https://twitter.com/i/web/status/{tweet_id}")
        
        # 保存到历史记录
        history_file = ".tweet_history.json"
        history = []
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        history.append({
            'id': tweet_id,
            'text': tweet_text,
            'created_at': datetime.now().isoformat(),
        })
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
    else:
        print("❌ 推文发布失败")
        if result:
            print(f"   响应: {json.dumps(result, indent=2)}")

if __name__ == '__main__':
    main()
