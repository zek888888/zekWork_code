#!/usr/bin/env python3
"""
推特数据定时任务
每小时执行一次，获取观察人列表的推文并进行AI分析
"""

import os
import sys
from datetime import datetime

# 添加项目路径
BASE_PATH = os.path.expanduser("~/.openclaw/workspace/quant-trading")
sys.path.insert(0, os.path.join(BASE_PATH, "config-layer"))
sys.path.insert(0, os.path.join(BASE_PATH, "research-layer/twitter-sentiment"))
sys.path.insert(0, os.path.join(BASE_PATH, "ai_models"))

from twitter_watchlist_manager import TwitterWatchlistManager
from twitter_fetcher import TwitterFetcher
from twitter_analyzer import TwitterAnalyzer


def main():
    """主任务"""
    print("="*60)
    print("推特数据定时任务 - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    # 1. 获取推文数据
    print("\n[1/3] 获取推文数据...")
    fetcher = TwitterFetcher()
    result = fetcher.fetch_all_active(hours_back=1)
    
    print(f"  ✓ 获取完成: {result['total_fetched']} 条")
    print(f"  ✓ 新入库: {result['total_new']} 条")
    print(f"  ✓ 重复: {result['total_duplicates']} 条")
    
    # 2. AI情绪分析
    if result['total_new'] > 0:
        print("\n[2/3] 执行AI情绪分析...")
        analyzer = TwitterAnalyzer()
        analysis_result = analyzer.batch_analyze_pending(hours=1, limit=100)
        
        print(f"  ✓ 分析完成: {analysis_result['analyzed']}/{analysis_result['total']} 条")
        print(f"  - 利好: {analysis_result['results']['bullish']} 条")
        print(f"  - 利空: {analysis_result['results']['bearish']} 条")
        print(f"  - 中性: {analysis_result['results']['neutral']} 条")
    else:
        print("\n[2/3] 无新推文，跳过分析")
    
    # 3. 输出统计
    print("\n[3/3] 统计信息...")
    stats = fetcher.get_stats(hours=24)
    print(f"  过去24小时总计: {stats['total']} 条")
    print(f"  - 利好: {stats['bullish']} 条")
    print(f"  - 利空: {stats['bearish']} 条")
    print(f"  - 中性: {stats['neutral']} 条")
    print(f"  - 待分析: {stats['pending_analysis']} 条")
    
    print("\n" + "="*60)
    print("任务完成")
    print("="*60)


if __name__ == "__main__":
    main()
