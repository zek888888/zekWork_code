#!/usr/bin/env python3
"""
修复隔壁老王启动问题
"""

import subprocess
import sys
import os
import time

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"

def 检查cron任务():
    """检查cron任务是否正常"""
    print("=" * 60)
    print("📋 检查 Cron 任务...")
    print("=" * 60)
    
    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True
    )
    
    if "prediction_agent_cron.py" in result.stdout:
        print("✅ 神算子 cron 任务已配置")
        # 提取时间配置
        for line in result.stdout.split("\n"):
            if "prediction" in line:
                print(f"   配置: {line.strip()}")
    else:
        print("❌ 神算子 cron 任务未配置")
    
    return "prediction_agent_cron.py" in result.stdout

def 检查最近预测记录():
    """检查数据库中的预测记录"""
    print("\n" + "=" * 60)
    print("📊 检查最近预测记录...")
    print("=" * 60)
    
    import sqlite3
    conn = sqlite3.connect(f"{PROJECT_ROOT}/data/market_data.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT datetime(predict_initiated_at) as time, 
               symbol, consensus_prediction, consensus_confidence
        FROM ai_prediction_records 
        WHERE predict_initiated_at >= datetime('now', '-24 hours')
        ORDER BY predict_initiated_at DESC
        LIMIT 15
    """)
    
    records = cursor.fetchall()
    conn.close()
    
    if records:
        print(f"   最近24小时共 {len(records)} 条预测记录\n")
        print(f"{'时间':<25} {'交易对':<10} {'预测':<8} {'置信度':<8}")
        print("-" * 60)
        for r in records:
            print(f"{r[0]:<25} {r[1]:<10} {r[2]:<8} {r[3]:<8}")
    else:
        print("   ⚠️  最近24小时无预测记录")
    
    return records

def 分析问题原因(records):
    """分析问题原因"""
    print("\n" + "=" * 60)
    print("🔍 分析问题原因...")
    print("=" * 60)
    
    if not records or len(records) < 4:
        print("⚠️  预测记录异常少！")
        print("\n可能原因:")
        print("   1. ❌ 隔壁老王(Task Supervisor)已停止运行")
        print("   2. ❌ Cron 任务执行失败")
        print("   3. ❌ Python 路径配置错误")
        print("   4. ❌ API 配额耗尽或网络问题")
        return False
    
    # 检查时间间隔
    from datetime import datetime
    
    print("\n⏱️  运行时间间隔分析:")
    
    for i in range(min(5, len(records)-1)):
        t1 = datetime.strptime(records[i][0], '%Y-%m-%d %H:%M:%S')
        t2 = datetime.strptime(records[i+1][0], '%Y-%m-%d %H:%M:%S')
        diff = (t1 - t2).total_seconds() / 60  # 分钟
        
        status = "✅" if diff < 20 else "❌"  # 应该每15分钟运行
        print(f"   {records[i+1][0]} -> {records[i][0]}: {diff:.1f}分钟 {status}")
    
    return True

def 手动触发预测():
    """手动触发一次预测"""
    print("\n" + "=" * 60)
    print("🚀 手动触发一次神算子预测...")
    print("=" * 60)
    
    result = subprocess.run(
        [sys.executable, f"{PROJECT_ROOT}/cron/prediction_agent_cron.py"],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode == 0:
        print("✅ 预测任务执行成功")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    else:
        print("❌ 预测任务执行失败")
        print(result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    print("=" * 60)
    print("🛠️  隔壁老王修复工具")
    print("=" * 60)
    
    # 1. 检查cron
    cron_ok = 检查cron任务()
    
    # 2. 检查记录
    records = 检查最近预测记录()
    
    # 3. 分析原因
    normal = 分析问题原因(records)
    
    # 4. 如果异常，手动触发一次
    if not normal:
        print("\n" + "=" * 60)
        print("⚠️  系统运行异常，尝试手动修复...")
        print("=" * 60)
        
        success = 手动触发预测()
        
        if success:
            print("\n✅ 手动修复成功！")
            print("\n📌 建议:")
            print("   1. 隔壁老王需要修复启动脚本")
            print("   2. 检查 cron 日志: grep CRON /var/log/syslog")
            print("   3. 确保 /usr/bin/python3 路径正确")
        else:
            print("\n❌ 手动修复失败，请检查日志")
    else:
        print("\n✅ 系统运行正常！")
