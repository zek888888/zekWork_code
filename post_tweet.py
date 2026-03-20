#!/usr/bin/env python3
"""
Twitter OAuth 1.0a 发推工具
支持文字推文和带图片推文

使用方法:
  python3 post_tweet.py "推文内容"
  python3 post_tweet.py --image /path/to/image.png "带图片的推文"
  python3 post_tweet.py --file tweet.txt
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
import mimetypes
from datetime import datetime

def load_credentials():
    """从.env文件加载凭证"""
    # 获取脚本所在目录
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
    """创建 OAuth 1.0a 签名"""
    # 1. 收集参数（不包括signature）
    sig_params = {}
    sig_params.update(params)
    
    # 2. 按字母顺序排序并编码
    sorted_params = sorted(sig_params.items())
    param_string = '&'.join(
        f'{urllib.parse.quote(k, safe="")}={urllib.parse.quote(str(v), safe="")}'
        for k, v in sorted_params
    )
    
    # 3. 构建签名基础字符串
    base_string = '&'.join([
        method.upper(),
        urllib.parse.quote(url, safe=''),
        urllib.parse.quote(param_string, safe='')
    ])
    
    # 4. 创建签名密钥
    signing_key = '&'.join([
        urllib.parse.quote(consumer_secret, safe=''),
        urllib.parse.quote(token_secret, safe='')
    ])
    
    # 5. HMAC-SHA1 签名
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    
    return signature

def create_oauth_header(url, method, creds, extra_params=None):
    """创建OAuth认证头"""
    
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
    
    # 创建签名
    signature = create_oauth_signature(
        method, url, oauth_params,
        creds['TWITTER_CONSUMER_SECRET'],
        creds['TWITTER_ACCESS_TOKEN_SECRET']
    )
    oauth_params['oauth_signature'] = signature
    
    # 构建Authorization头
    auth_header = 'OAuth ' + ', '.join(
        f'{urllib.parse.quote(k)}="{urllib.parse.quote(str(v))}"'
        for k, v in sorted(oauth_params.items())
    )
    
    return auth_header

def upload_media_v1(creds, media_path):
    """使用API v1.1上传媒体"""
    
    # 读取媒体文件
    with open(media_path, 'rb') as f:
        media_data = f.read()
    
    # 获取MIME类型
    mime_type, _ = mimetypes.guess_type(media_path)
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    # Base64编码
    media_base64 = base64.b64encode(media_data).decode()
    
    # 构建请求
    url = 'https://upload.twitter.com/1.1/media/upload.json'
    
    boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    body = (
        f'------WebKitFormBoundary{boundary}\r\n'
        f'Content-Disposition: form-data; name="media_data"\r\n\r\n'
        f'{media_base64}\r\n'
        f'------WebKitFormBoundary{boundary}--\r\n'
    ).encode()
    
    auth_header = create_oauth_header(url, 'POST', creds)
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            'Authorization': auth_header,
            'Content-Type': f'multipart/form-data; boundary=----WebKitFormBoundary{boundary}',
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result.get('media_id_string')
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ 媒体上传失败: {error_body}")
        return None

def post_tweet_v2(creds, text, media_ids=None, reply_to=None):
    """使用API v2发布推文"""
    
    url = 'https://api.twitter.com/2/tweets'
    
    payload = {'text': text}
    
    if media_ids:
        payload['media'] = {'media_ids': media_ids}
    
    if reply_to:
        payload['reply'] = {'in_reply_to_tweet_id': reply_to}
    
    data = json.dumps(payload).encode()
    
    # OAuth 1.0a 也可以访问 v2 API
    auth_header = create_oauth_header(url, 'POST', creds)
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': auth_header,
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
        print(f"❌ 发推失败: {error_body}")
        return None

def main():
    print("="*60)
    print("  Twitter OAuth 1.0a 发推工具")
    print("="*60)
    print()
    
    # 加载凭证
    creds = load_credentials()
    
    # 检查凭证
    required_keys = ['TWITTER_CONSUMER_KEY', 'TWITTER_CONSUMER_SECRET', 
                     'TWITTER_ACCESS_TOKEN', 'TWITTER_ACCESS_TOKEN_SECRET']
    
    for key in required_keys:
        if not creds.get(key):
            print(f"❌ 缺少配置项: {key}")
            print(f"   请检查 .env.twitter 文件")
            return
    
    # 解析参数
    text = None
    media_paths = []
    reply_to = None
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--image' and i + 1 < len(sys.argv):
            media_paths.append(sys.argv[i + 1])
            i += 2
        elif arg == '--file' and i + 1 < len(sys.argv):
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
        print(f"\n使用方法:")
        print(f"  python3 {sys.argv[0]} '推文内容'")
        print(f"  python3 {sys.argv[0]} --image photo.png '带图片的推文'")
        print(f"  python3 {sys.argv[0]} --file tweet.txt")
        return
    
    # 检查长度
    if len(text) > 280:
        print(f"⚠️ 警告: 推文长度 {len(text)} 超过280字符")
        print("   将被截断")
        text = text[:280]
    
    print(f"推文内容: {text[:60]}..." if len(text) > 60 else f"推文内容: {text}")
    
    # 上传媒体
    media_ids = []
    if media_paths:
        print(f"\n【上传媒体】{len(media_paths)}个文件...")
        for path in media_paths:
            if not os.path.exists(path):
                print(f"❌ 文件不存在: {path}")
                continue
            
            print(f"  上传: {path}...")
            media_id = upload_media_v1(creds, path)
            if media_id:
                media_ids.append(media_id)
                print(f"  ✅ Media ID: {media_id}")
        
        if not media_ids:
            print("❌ 媒体上传失败，将发送纯文字推文")
    
    # 发布推文
    print("\n【发布推文】...")
    result = post_tweet_v2(creds, text, media_ids if media_ids else None, reply_to)
    
    if result and 'data' in result:
        tweet_id = result['data']['id']
        tweet_text = result['data']['text']
        
        print("✅ 推文发布成功！")
        print(f"   Tweet ID: {tweet_id}")
        print(f"   链接: https://twitter.com/i/web/status/{tweet_id}")
        
        # 保存历史
        script_dir = os.path.dirname(os.path.abspath(__file__))
        history_file = os.path.join(script_dir, ".tweet_history.json")
        history = []
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        history.append({
            'id': tweet_id,
            'text': tweet_text,
            'created_at': datetime.now().isoformat(),
            'media_count': len(media_ids),
        })
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
    else:
        print("❌ 推文发布失败")
        if result:
            print(f"   响应: {json.dumps(result, indent=2)}")

if __name__ == '__main__':
    main()
