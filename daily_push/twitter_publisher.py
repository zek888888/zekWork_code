#!/usr/bin/env python3
"""
Twitter自动发布模块
自动将生成的推文发布到Twitter
"""

import os
import sys
import json
import urllib.request
import base64
import hashlib
import hmac
import random
import string
import time
import urllib.parse


class TwitterPublisher:
    """Twitter自动发布器"""
    
    def __init__(self):
        self.creds = self._load_credentials()
    
    def _load_credentials(self):
        """加载Twitter凭证"""
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_file = os.path.join(root_dir, ".env.twitter")
        
        creds = {}
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        creds[key] = value.strip()
        return creds
    
    def _create_oauth_header(self, url, method):
        """创建OAuth认证头"""
        oauth_params = {
            'oauth_consumer_key': self.creds['TWITTER_CONSUMER_KEY'],
            'oauth_nonce': ''.join(random.choices(string.ascii_letters + string.digits, k=42)),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_token': self.creds['TWITTER_ACCESS_TOKEN'],
            'oauth_version': '1.0',
        }
        
        # 创建签名
        sorted_params = sorted(oauth_params.items())
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
            urllib.parse.quote(self.creds['TWITTER_CONSUMER_SECRET'], safe=''),
            urllib.parse.quote(self.creds['TWITTER_ACCESS_TOKEN_SECRET'], safe='')
        ])
        
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        
        oauth_params['oauth_signature'] = signature
        
        return 'OAuth ' + ', '.join(
            f'{urllib.parse.quote(k)}="{urllib.parse.quote(str(v))}"'
            for k, v in sorted(oauth_params.items())
        )
    
    def publish_tweet(self, text):
        """
        发布推文
        
        Args:
            text: 推文内容
            
        Returns:
            dict: 包含tweet_id和link的字典
        """
        # 检查长度
        if len(text) > 4000:
            # Twitter API v2限制
            raise ValueError(f"推文长度{len(text)}超过4000字符限制")
        
        url = 'https://api.twitter.com/2/tweets'
        
        payload = {'text': text}
        data = json.dumps(payload).encode()
        
        auth_header = self._create_oauth_header(url, 'POST')
        
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
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                tweet_id = result['data']['id']
                return {
                    'success': True,
                    'tweet_id': tweet_id,
                    'link': f'https://twitter.com/i/web/status/{tweet_id}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def publish_thread(self, posts):
        """
        发布Thread（多条推文）
        
        Args:
            posts: 推文内容列表
            
        Returns:
            dict: 包含tweet_ids和links的字典
        """
        results = []
        last_tweet_id = None
        
        for i, post in enumerate(posts, 1):
            # 如果是回复，需要设置reply_to
            if last_tweet_id:
                payload = {
                    'text': post,
                    'reply': {'in_reply_to_tweet_id': last_tweet_id}
                }
                
                url = 'https://api.twitter.com/2/tweets'
                data = json.dumps(payload).encode()
                auth_header = self._create_oauth_header(url, 'POST')
                
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
                    with urllib.request.urlopen(req, timeout=30) as response:
                        result = json.loads(response.read().decode())
                        last_tweet_id = result['data']['id']
                        results.append({
                            'success': True,
                            'tweet_id': last_tweet_id,
                            'index': i
                        })
                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e),
                        'index': i
                    })
                    break
            else:
                # 第一条推文
                result = self.publish_tweet(post)
                if result['success']:
                    last_tweet_id = result['tweet_id']
                    results.append(result)
                else:
                    results.append(result)
                    break
            
            time.sleep(1)  # 避免请求过快
        
        return {
            'success': all(r.get('success') for r in results),
            'posts': results,
            'first_link': results[0]['link'] if results and results[0].get('success') else None
        }


if __name__ == '__main__':
    # 测试
    publisher = TwitterPublisher()
    
    test_content = "这是一条测试推文，由每日一推系统自动发布。"
    
    print("测试发布推文...")
    result = publisher.publish_tweet(test_content)
    
    if result['success']:
        print(f"✅ 发布成功！")
        print(f"   Tweet ID: {result['tweet_id']}")
        print(f"   链接: {result['link']}")
    else:
        print(f"❌ 发布失败: {result['error']}")
