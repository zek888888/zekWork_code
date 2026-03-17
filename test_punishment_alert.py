#!/usr/bin/env python3
"""
测试隔壁老王的惩罚通知
"""

import sys
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')

from supervisor.alerts.openclaw_notifier import OpenclawNotifier


def main():
    print("=" * 60)
    print("🔥 隔壁老王的惩罚通知测试")
    print("=" * 60)
    print()
    
    notifier = OpenclawNotifier()
    
    # 测试1: 警告信
    print("📤 发送警告信...")
    result1 = notifier.notify_punishment(
        'warning',
        api_provider='deepseek',
        failure_count=3,
        next_threshold=5
    )
    print(f"   {'✅ 成功' if result1 else '❌ 失败'}")
    
    # 测试2: 暂停通知
    print()
    print("📤 发送暂停通知...")
    result2 = notifier.notify_punishment(
        'suspend',
        api_provider='deepseek',
        suspended_until='2026-03-17 15:00:00'
    )
    print(f"   {'✅ 成功' if result2 else '❌ 失败'}")
    
    # 测试3: 切换API通知
    print()
    print("📤 发送API切换通知...")
    result3 = notifier.notify_punishment(
        'switch',
        old_api='deepseek',
        new_api='moonshot',
        switch_success=True
    )
    print(f"   {'✅ 成功' if result3 else '❌ 失败'}")
    
    # 测试4: 拉黑通知
    print()
    print("📤 发送拉黑通知...")
    result4 = notifier.notify_punishment(
        'blacklist',
        api_provider='deepseek',
        new_api='openai'
    )
    print(f"   {'✅ 成功' if result4 else '❌ 失败'}")
    
    print()
    print("=" * 60)
    success_count = sum([result1, result2, result3, result4])
    print(f"📊 测试结果: {success_count}/4 成功")
    print()
    
    if success_count == 4:
        print("✅ 所有惩罚通知发送成功！")
        print("   请检查飞书，感受老王的威严！")
    else:
        print("⚠️ 部分通知发送失败")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
