#!/usr/bin/env python3
"""
Twitter推文发布脚本 - 使用tweepy库（更稳定）
安装: pip3 install tweepy requests
"""

import os
import sys

# 推文内容
TWEET_TEXT = """今天美股就一个感觉——磨 😤

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

def install_and_import():
    """尝试安装并导入tweepy"""
    try:
        import tweepy
        return tweepy
    except ImportError:
        print("正在安装 tweepy...")
        os.system("pip3 install tweepy --user")
        try:
            import tweepy
            return tweepy
        except ImportError:
            print("❌ 安装失败，请手动运行: pip3 install tweepy")
            sys.exit(1)

def post_tweet(tweepy_module):
    """使用tweepy发布推文"""
    
    # API凭证
    API_KEY = "G5vfIJMejdGilZBikJmEdS8Z8"
    API_SECRET = "wJEN04HOaKfJdArclAvSg2yW0bsCZqC9rf9W44ARmuAD5NWAqk"
    ACCESS_TOKEN = "1355655667046989827-C7zgkmHMfb7WypX4gRkQbEpGkW7REW"
    ACCESS_TOKEN_SECRET = "PVnW35wwsAkdAGxEq3xwBGccCJfctg63mwidQ7Px4oYtP"
    
    # 认证
    auth = tweepy_module.OAuth1UserHandler(
        API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
    )
    
    # 创建API对象
    api = tweepy_module.API(auth)
    
    # 测试认证
    try:
        user = api.verify_credentials()
        print(f"✅ 认证成功: @{user.screen_name}")
    except Exception as e:
        print(f"❌ 认证失败: {e}")
        return False
    
    # 发布推文
    try:
        tweet = api.update_status(TWEET_TEXT)
        print(f"✅ 推文发布成功!")
        print(f"   Tweet ID: {tweet.id}")
        print(f"   链接: https://twitter.com/i/web/status/{tweet.id}")
        return True
    except Exception as e:
        print(f"❌ 发布失败: {e}")
        return False

def main():
    print("="*60)
    print("Twitter推文发布工具")
    print("="*60)
    
    # 检查推文长度
    if len(TWEET_TEXT) > 280:
        print(f"\n⚠️ 警告: 推文超过280字符 ({len(TWEET_TEXT)} 字符)")
        print("需要删减内容")
        return
    
    print(f"\n推文内容 ({len(TWEET_TEXT)} 字符):")
    print("-"*60)
    print(TWEET_TEXT)
    print("-"*60)
    
    # 确认发布
    confirm = input("\n确认发布? (y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        return
    
    # 安装并导入tweepy
    tweepy = install_and_import()
    
    # 设置代理
    os.environ['https_proxy'] = 'http://127.0.0.1:7897'
    os.environ['http_proxy'] = 'http://127.0.0.1:7897'
    
    print("\n正在发布...")
    success = post_tweet(tweepy)
    
    if success:
        print("\n✅ 发布完成!")
    else:
        print("\n❌ 发布失败")

if __name__ == "__main__":
    main()
