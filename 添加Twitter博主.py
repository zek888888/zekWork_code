#!/usr/bin/env python3
"""
批量添加 Twitter 博主到观察列表
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))

from twitter_watchlist_manager import TwitterWatchlistManager, TwitterWatchlistItem

# 要添加的博主列表
new_bloggers = [
    {"username": "joely7758521", "category": "trader"},
    {"username": "stockwilsonrice", "category": "analyst"},
    {"username": "darrencao2024", "category": "trader"},
    {"username": "cnfinancewatch", "category": "analyst"},
    {"username": "aleabitoreddit", "category": "influencer"},
    {"username": "MarketMatrixs", "category": "analyst"},
    {"username": "11地主", "category": "trader"},
    {"username": "Areskapitalon", "category": "trader"},
    {"username": "Vito_168", "category": "trader"},
    {"username": "charliefish001", "category": "trader"},
    {"username": "RJCcapital", "category": "trader"},
    {"username": "cyrilxuq", "category": "analyst"},
    {"username": "LZRationalnvest", "category": "analyst"},
    {"username": "xhunt_ai", "category": "influencer"},
    {"username": "frankyluan", "category": "trader"},
    {"username": "0xSunNFT", "category": "influencer"},
    {"username": "dotyyds1234", "category": "influencer"},
]

def main():
    print("="*60)
    print("添加 Twitter 博主到观察列表")
    print("="*60)
    
    manager = TwitterWatchlistManager()
    
    # 获取现有列表
    existing = manager.get_all_watchlist()
    existing_usernames = {item['username'].lower() for item in existing}
    
    print(f"\n当前观察列表: {len(existing)} 人")
    print(f"待添加博主: {len(new_bloggers)} 人\n")
    
    added_count = 0
    skipped_count = 0
    
    for blogger in new_bloggers:
        username = blogger['username'].lower().replace('@', '')
        
        if username in existing_usernames:
            print(f"⏭️  跳过: @{username} (已存在)")
            skipped_count += 1
            continue
        
        try:
            item = TwitterWatchlistItem(
                username=username,
                display_name=username,
                category=blogger['category'],
                priority=1,
                is_active=True
            )
            
            item_id = manager.add_watchlist_item(item)
            print(f"✅ 添加: @{username} (ID: {item_id})")
            added_count += 1
            
        except Exception as e:
            print(f"❌ 失败: @{username} - {e}")
    
    print("\n" + "="*60)
    print(f"添加完成: 新增 {added_count} 人, 跳过 {skipped_count} 人")
    print(f"观察列表总数: {len(existing) + added_count} 人")
    print("="*60)
    
    # 显示完整列表
    print("\n📋 完整观察列表:")
    all_watchlist = manager.get_all_watchlist()
    for i, item in enumerate(all_watchlist, 1):
        print(f"   {i}. @{item['username']} ({item['category']})")

if __name__ == "__main__":
    main()
