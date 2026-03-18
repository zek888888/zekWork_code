#!/usr/bin/env python3
"""
系统状态检查工具 - 随时查看神算子是否正常运行
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime, timedelta

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"

def 检查服务状态():
    """检查LaunchAgent服务状态"""
    print("=" * 60)
    print("🔍 系统服务状态检查")
    print("=" * 60)
    
    # 检查LaunchAgent
    result = subprocess.run(
        ["launchctl", "list"],
        capture_output=True,
        text=True
    )
    
    services = [line for line in result.stdout.split("\n") if "quant-trading" in line]
    
    if services:
        print("\n✅ 系统服务已安装:")
        for svc in services:
            parts = svc.split()
            if len(parts) >= 3:
                pid = parts[0]
                status = parts[1]
                name = parts[2]
                if pid != "-":
                    print(f"   🟢 {name} - 运行中 (PID: {pid})")
                else:
                    print(f"   🔴 {name} - 未运行 (退出码: {status})")
    else:
        print("\n❌ 未找到系统服务")
        print("   请运行: bash 一键修复系统.sh")
    
    return len(services) > 0

def 检查最近预测():
    """检查最近的预测记录"""
    print("\n" + "=" * 60)
    print("📊 预测记录检查 (最近24小时)")
    print("=" * 60)
    
    conn = sqlite3.connect(f"{PROJECT_ROOT}/data/market_data.db")
    cursor = conn.cursor()
    
    # 获取最近24小时的记录
    cursor.execute("""
        SELECT datetime(predict_initiated_at) as time, 
               symbol, consensus_prediction, consensus_confidence
        FROM ai_prediction_records 
        WHERE predict_initiated_at >= datetime('now', '-24 hours')
        ORDER BY predict_initiated_at DESC
    """)
    
    records = cursor.fetchall()
    conn.close()
    
    if not records:
        print("\n❌ 最近24小时无预测记录！")
        return False
    
    print(f"\n✅ 最近24小时共有 {len(records)} 条预测记录")
    
    # 检查时间间隔
    print("\n⏱️  运行间隔分析:")
    
    issues = []
    for i in range(min(5, len(records)-1)):
        t1 = datetime.strptime(records[i][0], '%Y-%m-%d %H:%M:%S')
        t2 = datetime.strptime(records[i+1][0], '%Y-%m-%d %H:%M:%S')
        diff = (t1 - t2).total_seconds() / 60  # 分钟
        
        status = "✅" if 10 <= diff <= 20 else "⚠️ "
        if diff > 20:
            issues.append(f"   {records[i+1][0]} -> {records[i][0]}: {diff:.1f}分钟 (间隔过长)")
        
        print(f"   {status} {records[i+1][0]} -> {records[i][0]}: {diff:.1f}分钟")
    
    if issues:
        print("\n❌ 发现运行异常:")
        for issue in issues:
            print(issue)
        return False
    else:
        print("\n✅ 运行间隔正常 (每15分钟左右)")
        return True

def 检查Mac睡眠设置():
    """检查Mac睡眠设置"""
    print("\n" + "=" * 60)
    print("🔋 Mac电源管理检查")
    print("=" * 60)
    
    result = subprocess.run(
        ["pmset", "-g"],
        capture_output=True,
        text=True
    )
    
    # 检查睡眠设置
    sleep_setting = None
    for line in result.stdout.split("\n"):
        if " sleep " in line and "disksleep" not in line.lower():
            sleep_setting = line.strip()
            break
    
    if sleep_setting:
        if "0" in sleep_setting:
            print("\n✅ Mac不会自动睡眠")
            return True
        else:
            print(f"\n⚠️  Mac睡眠设置: {sleep_setting}")
            print("   建议运行: sudo pmset -c sleep 0")
            return False
    
    return True

def 显示建议():
    """根据检查结果给出建议"""
    print("\n" + "=" * 60)
    print("💡 建议操作")
    print("=" * 60)
    print("""
如果系统运行不正常，请执行:

1. 运行修复脚本:
   bash 一键修复系统.sh

2. 手动触发一次预测测试:
   python3 cron/prediction_agent_cron.py

3. 查看详细日志:
   tail -f logs/launchd_prediction.log

4. 重启服务:
   launchctl unload ~/Library/LaunchAgents/com.quant-trading.shen-suan-zi.plist
   launchctl load ~/Library/LaunchAgents/com.quant-trading.shen-suan-zi.plist
""")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🤖 神算子系统状态检查")
    print(f"   检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    service_ok = 检查服务状态()
    prediction_ok = 检查最近预测()
    sleep_ok = 检查Mac睡眠设置()
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 检查结果总结")
    print("=" * 60)
    
    all_ok = service_ok and prediction_ok and sleep_ok
    
    if all_ok:
        print("""
✅ 系统运行正常！

   • 服务已正确安装
   • 预测任务按时运行
   • Mac不会自动睡眠

   现在即使您离开电脑，系统也会持续运行！
""")
    else:
        print("""
⚠️  系统存在问题！

   某些检查项未通过，建议运行修复脚本:
   
   bash 一键修复系统.sh
""")
        显示建议()
