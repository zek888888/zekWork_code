#!/usr/bin/env python3
"""
使用Selenium自动抓取Twitter KOL推文
需要：已登录Twitter的Chrome浏览器
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
from datetime import datetime

# KOL列表
KOLS = [
    {"name": "joely7758521", "url": "https://x.com/joely7758521"},
    {"name": "stockwilsonrice", "url": "https://x.com/stockwilsonrice"},
    {"name": "darrencao2024", "url": "https://x.com/darrencao2024"},
    {"name": "xhunt_ai", "url": "https://x.com/xhunt_ai"},
    {"name": "0xSunNFT", "url": "https://x.com/0xSunNFT"},
]

def setup_driver():
    """设置Chrome浏览器"""
    chrome_options = Options()
    
    # 连接到已打开的Chrome（需提前手动打开）
    # 或使用用户数据目录保持登录状态
    chrome_options.add_argument("--user-data-dir=/Users/mac/Library/Application Support/Google/Chrome/Default")
    
    # 无头模式（可选）
    # chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_tweets(driver, username, url):
    """抓取单个KOL的推文"""
    print(f"\n正在获取 @{username} 的推文...")
    
    try:
        driver.get(url)
        time.sleep(3)  # 等待页面加载
        
        # 滚动加载更多推文
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # 查找推文（XPath可能随Twitter更新而变化）
        tweets = driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
        
        results = []
        for tweet in tweets[:5]:  # 只取前5条
            try:
                # 提取文字
                text_elem = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
                text = text_elem.text
                
                # 提取时间
                time_elem = tweet.find_element(By.TAG_NAME, "time")
                tweet_time = time_elem.get_attribute("datetime")
                
                # 只保留今日推文（3月19日）
                if "2026-03-19" in tweet_time or "Mar 19" in text:
                    results.append({
                        "username": username,
                        "text": text[:200],  # 只取前200字
                        "time": tweet_time
                    })
                    print(f"  ✅ 找到推文: {text[:60]}...")
                    
            except Exception as e:
                continue
        
        return results
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return []

def main():
    print("="*60)
    print("Twitter KOL推文自动抓取工具")
    print("="*60)
    print("\n⚠️  使用前请确保：")
    print("1. 已安装Chrome浏览器")
    print("2. 已登录Twitter账号")
    print("3. 已安装Selenium: pip install selenium")
    print("4. 已下载ChromeDriver")
    print("\n按Ctrl+C随时停止")
    print("="*60)
    
    try:
        driver = setup_driver()
        all_tweets = []
        
        for kol in KOLS:
            tweets = fetch_tweets(driver, kol["name"], kol["url"])
            all_tweets.extend(tweets)
            time.sleep(2)  # 避免请求过快
        
        # 保存结果
        output_file = "kol_tweets_0319.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_tweets, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 抓取完成！共 {len(all_tweets)} 条推文")
        print(f"📁 已保存到: {output_file}")
        
        # 显示汇总
        print("\n" + "="*60)
        print("推文汇总:")
        print("="*60)
        for tweet in all_tweets[:10]:
            print(f"\n@{tweet['username']}:")
            print(f"  {tweet['text']}")
        
        driver.quit()
        
    except KeyboardInterrupt:
        print("\n\n已停止")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

if __name__ == "__main__":
    main()
