#!/usr/bin/env python3
"""
Quant Trading Scheduler - 量化交易定时任务调度器
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
    result = subprocess.run([
        "python3", WORKSPACE / "research-layer/news-sentiment-scan/scan.py",
        "--fetch"
    ], capture_output=True, text=True)
    
    # 解析结果并输出
    try:
        output = result.stdout.strip().split('\n')[-1] if result.stdout else "{}"
        data = json.loads(output)
        if 'fetched' in data:
            print(f"  获取 {data.get('fetched', 0)} 条，新增 {data.get('saved', 0)} 条，重复 {data.get('duplicates', 0)} 条")
    except:
        pass

def run_gmgn_scan():
    """扫描冲狗市场"""
    print(f"[{datetime.now()}] 🐕 扫描冲狗市场...")
    subprocess.run([
        "python3", WORKSPACE / "data-layer/gmgn-fetch/gmgn_fetch.py",
        "--trending", "--limit", "20"
    ], capture_output=True)

def generate_report():
    """生成报告"""
    print(f"[{datetime.now()}] 📊 生成报告...")
    # 这里可以添加飞书推送
    subprocess.run([
        "python3", WORKSPACE / "feishu_reporter.py"
    ], capture_output=True)

def main():
    """主函数 - 设置定时任务"""
    print("=" * 60)
    print("🚀 量化交易定时任务调度器")
    print("=" * 60)
    print()
    
    # 每5分钟获取实时价格
    schedule.every(5).minutes.do(run_market_fetch)
    print("⏰ 每5分钟: 获取市场数据")
    
    # 每15分钟运行因子评分
    schedule.every(15).minutes.do(run_factor_score)
    print("⏰ 每15分钟: 因子评分")
    
    # 每30分钟扫描新闻（增量获取）
    schedule.every(30).minutes.do(run_news_scan)
    print("⏰ 每30分钟: 扫描新闻(增量)")
    
    # 每30分钟扫描冲狗市场
    schedule.every(30).minutes.do(run_gmgn_scan)
    print("⏰ 每30分钟: 冲狗市场扫描")
    
    # 每小时生成报告
    schedule.every().hour.do(generate_report)
    print("⏰ 每小时: 生成报告")
    
    # 每天早上8点发送日报
    schedule.every().day.at("08:00").do(generate_report)
    print("⏰ 每天08:00: 发送日报")
    
    print()
    print("-" * 60)
    print("定时任务已启动，按 Ctrl+C 停止")
    print("-" * 60)
    print()
    
    # 立即执行一次
    print("[启动] 立即执行首次任务...")
    run_market_fetch()
    run_news_scan()
    
    print()
    print("进入定时循环...")
    print()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 调度器已停止")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
