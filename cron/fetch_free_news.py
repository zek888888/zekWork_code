#!/usr/bin/env python3
"""
免费新闻定时获取任务
每小时执行一次，获取多源免费新闻
"""

import os
import sys
from datetime import datetime

BASE_PATH = os.path.expanduser("~/.openclaw/workspace/quant-trading")
sys.path.insert(0, os.path.join(BASE_PATH, "research-layer/news-sentiment-scan"))

from free_news_fetcher import FreeNewsFetcher


def main():
    """主任务"""
    print("="*70)
    print(f"免费新闻定时获取 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    fetcher = FreeNewsFetcher()
    result = fetcher.fetch_all()
    
    print(f"\n✓ 任务完成!")
    print(f"  获取: {result['total']} 条")
    print(f"  保存: {result['saved']} 条")
    print(f"  来源: {result['stats']}")
    print("="*70)


if __name__ == "__main__":
    main()
