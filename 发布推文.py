#!/usr/bin/env python3
"""
Twitter推文发布脚本
使用Twitter API v1.1发布推文
"""

import os
import sys
import requests
from requests_oauthlib import OAuth1
import json

# Twitter API凭证
API_KEY = "G5vfIJMejdGilZBikJmEdS8Z8"
API_SECRET = "wJEN04HOaKfJdArclAvSg2yW0bsCZqC9rf9W44ARmuAD5NWAqk"
ACCESS_TOKEN = "1355655667046989827-C7zgkmHMfb7WypX4gRkQbEpGkW7REW"
ACCESS_TOKEN_SECRET = "PVnW35wwsAkdAGxEq3xwBGccCJfctg63mwidQ7Px4oYtP"

def post_tweet(text):
    """发布推文"""
    
    # OAuth1认证
    auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    
    # API端点
    url = "https://api.twitter.com/2/tweets"
    
    # 请求体
    payload = {"text": text}
    
    # 发送请求
    try:
        response = requests.post(url, auth=auth, json=payload, timeout=30)
        
        if response.status_code == 201:
            data = response.json()
            tweet_id = data.get('data', {}).get('id')
            print(f"✅ 推文发布成功!")
            print(f"   Tweet ID: {tweet_id}")
            print(f"   链接: https://twitter.com/i/web/status/{tweet_id}")
            return True, tweet_id
        else:
            print(f"❌ 发布失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False, None

def main():
    # 推文内容
    tweet_text = """今天美股就一个感觉——磨 😤

全场震荡没方向，多空互相拉扯，看得人直打瞌睡 💤

简单说几个重点 👇

📈 美光 $MU 财报炸裂，业绩大超预期，盘后还有戏
这种创新高的票，别猜顶，继续盯着就行 🚀

📉 黄金白银走熊了，空头趋势明显
黄金可能要去4500，手里的注意风险 ⚠️

🔄 科技股集体躺平
英伟达、谷歌、Meta 都在横盘，涨不动也跌不透
英特尔AMD有点反弹，但别指望太多 🤷‍♂️

🛢️ 原油倒是坚挺，那边战事没完，一时半会下不来

总结：市场高度不确定，做多记得带止损，不想折腾的减仓观望也行
反正别死扛，这行情一切皆有可能 😂

#美股 #美光 #科技股 #黄金 #交易心得"""

    print("="*60)
    print("Twitter推文发布工具")
    print("="*60)
    print(f"\n推文内容 ({len(tweet_text)} 字符):")
    print("-"*60)
    print(tweet_text)
    print("-"*60)
    
    # 检查字符限制
    if len(tweet_text) > 280:
        print(f"\n⚠️ 警告: 推文超过280字符限制 ({len(tweet_text)} 字符)")
        print("需要删减内容")
        return
    
    # 确认发布
    confirm = input("\n确认发布? (y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        return
    
    # 设置代理
    os.environ['https_proxy'] = 'http://127.0.0.1:7897'
    os.environ['http_proxy'] = 'http://127.0.0.1:7897'
    
    print("\n正在发布...")
    success, tweet_id = post_tweet(tweet_text)
    
    if success:
        print("\n✅ 发布完成!")
        print(f"   查看: https://twitter.com/i/web/status/{tweet_id}")
    else:
        print("\n❌ 发布失败，请检查网络或API凭证")

if __name__ == "__main__":
    main()
