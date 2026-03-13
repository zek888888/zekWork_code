#!/usr/bin/env python3
"""
Quant Trading Scheduler - 量化交易定时任务
"""

import schedule
import time
import subprocess
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw/workspace/quant-trading"

def run_market_fetch():
    """获取市场数据"""
    print(f"[{datetime.now()}] 🔄 获取市场数据...")
    subprocess.run([
        "python3", WORKSPACE / "data-layer/market-data-fetch/fetch.py",
        "--watchlist"
    ], capture_output=True)

def run_factor_score():
    """运行因子评分"""
    print(f"[{datetime.now()}] 🎯 运行因子评分...")
    subprocess.run([
        "python3", WORKSPACE / "research-layer/factor-score-engine/score.py",
        "--watchlist"
    ], capture_output=True)

def run_news_scan():
    """扫描新闻"""
    print(f"[{datetime.now()}] 📰 扫描新闻...")
    subprocess.run([
        "python3", WORKSPACE / "research-layer/news-sentiment-scan/scan.py",
        "--source", "jin10", "--limit", "20"
    ], capture_output=True)

def generate_report():
    """生成报告"""
    print(f"[{datetime.now()}] 📊 生成报告...")
    # 这里可以添加飞书推送

def main():
    # 每5分钟获取实时价格
    schedule.every(5).minutes.do(run_market_fetch)
    
    # 每15分钟运行因子评分
    schedule.every(15).minutes.do(run_factor_score)
    
    # 每10分钟扫描新闻
    schedule.every(10).minutes.do(run_news_scan)
    
    # 每小时生成报告
    schedule.every().hour.do(generate_report)
    
    print("⏰ 定时任务已启动...")
    print("  - 每5分钟: 获取市场数据")
    print("  - 每10分钟: 扫描新闻")
    print("  - 每15分钟: 因子评分")
    print("  - 每小时: 生成报告")
    print("\n按 Ctrl+C 停止")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
