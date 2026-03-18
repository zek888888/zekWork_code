#!/usr/bin/env python3
"""
神算子效果监控脚本
对比新旧配置的预测准确率

使用:
    python3 神算子_效果监控.py          # 查看整体统计
    python3 神算子_效果监控.py --24h    # 查看最近24小时
    python3 神算子_效果监控.py --since 2026-03-18  # 从指定日期开始
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
DB_PATH = f"{PROJECT_ROOT}/data/market_data.db"

def get_prediction_stats(since_date=None, hours=None):
    """获取预测统计"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 构建时间筛选
    time_filter = ""
    params = []
    
    if hours:
        since = datetime.now() - timedelta(hours=hours)
        time_filter = "AND predict_initiated_at >= ?"
        params.append(since.strftime('%Y-%m-%d %H:%M:%S'))
    elif since_date:
        time_filter = "AND predict_initiated_at >= ?"
        params.append(f"{since_date} 00:00:00")
    
    # 查询总体统计
    query = f"""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as wrong,
            SUM(CASE WHEN is_correct IS NULL THEN 1 ELSE 0 END) as pending,
            AVG(consensus_confidence) as avg_confidence
        FROM ai_prediction_records 
        WHERE 1=1 {time_filter}
    """
    
    cursor.execute(query, params)
    row = cursor.fetchone()
    
    total, correct, wrong, pending, avg_conf = row
    
    if not total:
        print("⚠️  该时间段内没有预测记录")
        conn.close()
        return
    
    # 查询看涨vs看跌准确率
    query_direction = f"""
        SELECT 
            consensus_prediction,
            COUNT(*) as count,
            SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
        FROM ai_prediction_records 
        WHERE is_correct IS NOT NULL {time_filter}
        GROUP BY consensus_prediction
    """
    
    cursor.execute(query_direction, params)
    direction_stats = cursor.fetchall()
    
    # 查询按日统计
    query_daily = f"""
        SELECT 
            date(predict_initiated_at) as date,
            COUNT(*) as total,
            SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
        FROM ai_prediction_records 
        WHERE is_correct IS NOT NULL {time_filter}
        GROUP BY date(predict_initiated_at)
        ORDER BY date DESC
        LIMIT 7
    """
    
    cursor.execute(query_daily, params)
    daily_stats = cursor.fetchall()
    
    conn.close()
    
    # 显示统计
    print("="*70)
    if hours:
        print(f"神算子效果报告 - 最近{hours}小时")
    elif since_date:
        print(f"神算子效果报告 - 从 {since_date} 开始")
    else:
        print("神算子效果报告 - 全部历史")
    print("="*70)
    
    print(f"\n📊 总体统计:")
    print(f"   总预测数: {total}")
    print(f"   已验证:   {correct + wrong} (正确 {correct}, 错误 {wrong})")
    print(f"   待验证:   {pending}")
    
    if correct + wrong > 0:
        accuracy = correct / (correct + wrong)
        print(f"\n🎯 准确率:   {accuracy:.1%} ({correct}/{correct + wrong})")
        print(f"📈 平均置信度: {avg_conf:.1%}" if avg_conf else "")
        
        # 显示方向统计
        print(f"\n📉 方向统计:")
        for direction, count, dir_correct in direction_stats:
            if count > 0:
                dir_acc = dir_correct / count if dir_correct else 0
                symbol = "📈" if direction == "up" else "📉"
                print(f"   {symbol} {direction:4s}: {dir_acc:.1%} ({dir_correct}/{count})")
    
    # 显示按日统计
    if daily_stats:
        print(f"\n📅 最近7天统计:")
        for date, day_total, day_correct in daily_stats:
            if day_correct is not None and day_total > 0:
                day_acc = day_correct / day_total
                print(f"   {date}: {day_acc:.1%} ({day_correct}/{day_total})")
    
    # 配置提示
    print("\n" + "="*70)
    print("当前配置: 80根K线 + 60%置信度阈值")
    print("预期准确率: ~37.55% (基于历史回测)")
    print("="*70)

def compare_configs():
    """对比新旧配置的效果"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 旧配置 (2026-03-18之前) vs 新配置 (2026-03-18及之后)
    print("\n" + "="*70)
    print("新旧配置对比")
    print("="*70)
    
    # 这里假设配置切换日期为2026-03-19
    # 实际应根据配置实际切换日期调整
    cutoff_date = "2026-03-19"
    
    # 旧配置统计
    cursor.execute("""
        SELECT COUNT(*), SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END)
        FROM ai_prediction_records 
        WHERE predict_initiated_at < ? AND is_correct IS NOT NULL
    """, (cutoff_date,))
    old_total, old_correct = cursor.fetchone()
    
    # 新配置统计
    cursor.execute("""
        SELECT COUNT(*), SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END)
        FROM ai_prediction_records 
        WHERE predict_initiated_at >= ? AND is_correct IS NOT NULL
    """, (cutoff_date,))
    new_total, new_correct = cursor.fetchone()
    
    conn.close()
    
    print(f"\n旧配置 (20根K线, 80%阈值) - {cutoff_date}之前:")
    if old_total:
        print(f"   预测数: {old_total}")
        print(f"   准确率: {old_correct/old_total:.1%}")
    else:
        print("   无数据")
    
    print(f"\n新配置 (80根K线, 60%阈值) - {cutoff_date}及之后:")
    if new_total:
        print(f"   预测数: {new_total}")
        print(f"   准确率: {new_correct/new_total:.1%}")
    else:
        print("   暂无足够数据，请24-48小时后查看")
    
    if old_total and new_total:
        old_acc = old_correct / old_total
        new_acc = new_correct / new_total
        diff = new_acc - old_acc
        symbol = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
        print(f"\n{symbol} 变化: {diff:+.1%}")

def main():
    parser = argparse.ArgumentParser(description='神算子效果监控')
    parser.add_argument('--24h', dest='hours24', action='store_true', help='查看最近24小时')
    parser.add_argument('--since', type=str, help='从指定日期开始 (YYYY-MM-DD)')
    parser.add_argument('--compare', action='store_true', help='对比新旧配置')
    
    args = parser.parse_args()
    
    if args.compare:
        compare_configs()
    elif args.hours24:
        get_prediction_stats(hours=24)
    elif args.since:
        get_prediction_stats(since_date=args.since)
    else:
        get_prediction_stats()
        compare_configs()

if __name__ == "__main__":
    main()
