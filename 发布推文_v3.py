#!/usr/bin/env python3
"""
Twitter推文发布脚本
"""

import os
import sys

# 精简版推文（280字符以内）
TWEET_TEXT = """今天美股就一个感觉——磨 😤

全场震荡没方向，多空互相拉扯 💤

📈 美光 $MU 财报炸裂，别猜顶，继续盯 🚀
📉 黄金走熊，可能去4500，注意风险 ⚠️  
🔄 科技股躺平，英伟达谷歌Meta横盘 🤷‍♂️
🛢️ 原油坚挺，战事没完

总结：高度不确定，带好止损，别死扛 😂

#美股 #美光 #科技股 #黄金"""

def install_and_import():
    """尝试安装并导入tweepy"""
    try:
        import tweepy
        return tweepy
    except ImportError:
        print("正在安装 tweepy...")
        os.system("python3 -m pip install tweepy --user 2>/dev/null || pip3 install tweepy --user 2>/dev/null")
        try:
            import tweepy
            return tweepy
        except ImportError:
            print("❌ 安装失败")
            return None

def post_tweet(tweepy_module):
    """发布推文"""
    API_KEY = "G5vfIJMejdGilZBikJmEdS8Z8"
    API_SECRET = "wJEN04HOaKfJdArclAvSg2yW0bsCZqC9rf9W44ARmuAD5NWAqk"
    ACCESS_TOKEN = "1355655667046989827-C7zgkmHMfb7WypX4gRkQbEpGkW7REW"
    ACCESS_TOKEN_SECRET = "PVnW35wwsAkdAGxEq3xwBGccCJfctg63mwidQ7Px4oYtP"
    
    auth = tweepy_module.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy_module.API(auth)
    
    try:
        user = api.verify_credentials()
        print(f"✅ 认证成功: @{user.screen_name}")
    except Exception as e:
        print(f"❌ 认证失败: {e}")
        return None
    
    try:
        tweet = api.update_status(TWEET_TEXT)
        return tweet.id
    except Exception as e:
        print(f"❌ 发布失败: {e}")
        return None

def main():
    print("="*60)
    print("Twitter推文发布")
    print("="*60)
    print(f"\n推文 ({len(TWEET_TEXT)} 字符):")
    print("-"*60)
    print(TWEET_TEXT)
    print("-"*60)
    
    confirm = input("\n确认发布? (y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        return
    
    tweepy = install_and_import()
    if not tweepy:
        print("请手动安装: pip3 install tweepy")
        return
    
    os.environ['https_proxy'] = 'http://127.0.0.1:7897'
    print("\n正在发布...")
    
    tweet_id = post_tweet(tweepy)
    
    if tweet_id:
        print(f"\n✅ 发布成功!")
        print(f"   https://twitter.com/i/web/status/{tweet_id}")
    else:
        print("\n❌ 发布失败")

if __name__ == "__main__":
    main()
