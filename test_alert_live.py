#!/usr/bin/env python3
"""
测试监工系统告警功能 - 发送真实告警到飞书
"""

import sys
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')

from datetime import datetime
from supervisor.alerts.openclaw_notifier import OpenclawNotifier

def main():
    print("=" * 60)
    print("🧑‍🔧 隔壁老王 - 实时告警测试")
    print("=" * 60)
    print()
    
    notifier = OpenclawNotifier()
    
    # 测试1: 系统启动通知
    print("📤 发送系统启动通知...")
    result1 = notifier.notify_system_startup()
    print(f"   {'✅ 成功' if result1 else '❌ 失败'}")
    
    # 测试2: 任务漏执行
    print()
    print("📤 发送任务漏执行告警...")
    test_task = {
        'task_name': '神算子（AI预测）',
        'scheduled_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'reason': '未检测到执行记录 (cron未触发)',
        'critical': True
    }
    result2 = notifier.notify_task_missed(test_task)
    print(f"   {'✅ 成功' if result2 else '❌ 失败'}")
    
    # 测试3: 每日报告
    print()
    print("📤 发送每日报告...")
    report = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total_executions': 96,
        'success': 94,
        'failed': 2,
        'timeout': 0,
        'tasks': [
            {'name': '神算子（AI预测）', 'failed': 1, 'timeout': 0},
            {'name': '验证历史预测', 'failed': 0, 'timeout': 0}
        ]
    }
    result3 = notifier.notify_daily_report(report)
    print(f"   {'✅ 成功' if result3 else '❌ 失败'}")
    
    # 测试4: 人工修复请求
    print()
    print("📤 发送人工修复请求...")
    execution = {
        'name': '神算子（AI预测）',
        'execution_id': 'prediction_agent_20240317142900',
        'actual_end': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'error_message': 'ModuleNotFoundError: No module named pandas'
    }
    options = ['安装依赖: pip3 install pandas', '检查虚拟环境', '手动执行测试']
    result4 = notifier.notify_repair_needed(execution, options)
    print(f"   {'✅ 成功' if result4 else '❌ 失败'}")
    
    print()
    print("=" * 60)
    success_count = sum([result1, result2, result3, result4])
    print(f"📊 测试结果: {success_count}/4 成功")
    print()
    
    if success_count == 4:
        print("✅ 所有告警类型发送成功！")
        print("   请检查你的飞书消息")
    else:
        print("⚠️ 部分消息发送失败")
        print("   请检查 Openclaw 配置")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
