#!/usr/bin/env python3
"""
Twitter API 客户端
使用 Twitter API v2 获取推文数据
"""

import os
import base64
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta


def load_twitter_credentials():
    """从.env.twitter文件加载凭证"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env.twitter')
    credentials = {}
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    credentials[key] = value
    
    return credentials


class TwitterAPIClient:
    """Twitter API 客户端"""
    
    def __init__(self, bearer_token: str = None):
        """
        初始化Twitter API客户端
        
        Args:
            bearer_token: Twitter API Bearer Token (从Developer Portal获取)
        """
        # 优先使用传入的参数，其次环境变量，最后.env文件
        credentials = load_twitter_credentials()
        
        self.bearer_token = (
            bearer_token or 
            os.environ.get('TWITTER_BEARER_TOKEN', '') or 
            credentials.get('TWITTER_BEARER_TOKEN', '')
        )
        self.base_url = "https://api.twitter.com/2"
        
        if not self.bearer_token:
            raise ValueError("Twitter Bearer Token 未配置")
    
    def _get_headers(self) -> Dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """通过用户名获取用户信息"""
        url = f"{self.base_url}/users/by/username/{username}"
        
        params = {
            "user.fields": "id,name,username,public_metrics,description"
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code == 200:
                return response.json().get('data')
            elif response.status_code == 401:
                print(f"❌ Twitter API 认证失败，请检查Bearer Token")
                return None
            else:
                print(f"❌ 获取用户 @{username} 失败: {response.status_code}")
                print(f"   错误: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None
    
    def get_user_tweets(self, user_id: str, max_results: int = 10, 
                       start_time: str = None) -> List[Dict]:
        """
        获取用户最近推文
        
        Args:
            user_id: 用户ID
            max_results: 最大返回数量 (5-100)
            start_time: ISO 8601格式时间，获取此时间之后的推文
        """
        url = f"{self.base_url}/users/{user_id}/tweets"
        
        params = {
            "max_results": min(max(max_results, 5), 100),
            "tweet.fields": "id,text,created_at,public_metrics,context_annotations",
            "exclude": "replies,retweets"  # 排除回复和转发
        }
        
        if start_time:
            params["start_time"] = start_time
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code == 200:
                data = response.json()
                tweets = data.get('data', [])
                
                # 格式化推文数据
                formatted_tweets = []
                for tweet in tweets:
                    metrics = tweet.get('public_metrics', {})
                    formatted_tweets.append({
                        'id': tweet['id'],
                        'text': tweet['text'],
                        'created_at': tweet['created_at'],
                        'retweet_count': metrics.get('retweet_count', 0),
                        'like_count': metrics.get('like_count', 0),
                        'reply_count': metrics.get('reply_count', 0),
                        'quote_count': metrics.get('quote_count', 0)
                    })
                
                return formatted_tweets
                
            elif response.status_code == 401:
                print(f"❌ Twitter API 认证失败")
                return []
            elif response.status_code == 429:
                print(f"❌ Twitter API 请求限制已达上限")
                return []
            else:
                print(f"❌ 获取推文失败: {response.status_code}")
                print(f"   错误: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return []
    
    def get_tweets_by_usernames(self, usernames: List[str], 
                                 hours_back: int = 1) -> Dict[str, List[Dict]]:
        """
        批量获取多个用户的推文
        
        Args:
            usernames: 用户名列表
            hours_back: 获取多少小时内的推文
        
        Returns:
            Dict: {username: [tweets]}
        """
        results = {}
        
        # 计算开始时间
        start_time = (datetime.utcnow() - timedelta(hours=hours_back)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        print(f"获取过去 {hours_back} 小时的推文...")
        print(f"开始时间: {start_time}")
        
        for username in usernames:
            print(f"\n获取 @{username} 的推文...")
            
            # 1. 获取用户ID
            user = self.get_user_by_username(username)
            if not user:
                print(f"  ✗ 用户不存在或获取失败")
                results[username] = []
                continue
            
            user_id = user['id']
            print(f"  ✓ 用户ID: {user_id}")
            
            # 2. 获取用户推文
            tweets = self.get_user_tweets(user_id, max_results=10, start_time=start_time)
            results[username] = tweets
            
            print(f"  ✓ 获取 {len(tweets)} 条推文")
        
        return results


def test_twitter_api():
    """测试Twitter API"""
    print("="*60)
    print("Twitter API 测试")
    print("="*60)
    
    # 从环境变量获取Bearer Token
    bearer_token = os.environ.get('TWITTER_BEARER_TOKEN', '')
    
    if not bearer_token:
        print("\n❌ TWITTER_BEARER_TOKEN 未设置")
        print("请设置环境变量: export TWITTER_BEARER_TOKEN='your_token'")
        return
    
    print(f"\nBearer Token: {bearer_token[:20]}...")
    
    try:
        client = TwitterAPIClient(bearer_token)
        
        # 测试获取单个用户
        test_username = "cz_binance"
        print(f"\n测试获取用户 @{test_username}...")
        
        user = client.get_user_by_username(test_username)
        if user:
            print(f"✓ 用户存在: {user.get('name')} (@{user.get('username')})")
            print(f"  ID: {user.get('id')}")
            
            # 测试获取推文
            print(f"\n测试获取最近推文...")
            tweets = client.get_user_tweets(user['id'], max_results=5)
            
            if tweets:
                print(f"✓ 获取 {len(tweets)} 条推文:")
                for i, tweet in enumerate(tweets[:3], 1):
                    print(f"  [{i}] {tweet['text'][:60]}...")
                    print(f"      点赞: {tweet['like_count']} 转发: {tweet['retweet_count']}")
            else:
                print("✗ 未获取到推文")
        else:
            print("✗ 用户获取失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_twitter_api()
