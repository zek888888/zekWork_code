#!/usr/bin/env python3
"""
测试隔壁老王的自监控功能
"""

import sys
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')

from supervisor.core.self_monitor import SelfMonitor


def main():
    print("=" * 60)
    print("🧑‍🔧 隔壁老王的自监控测试")
    print("=" * 60)
    print()
    
    monitor = SelfMonitor()
    
    # 测试1: 记录心跳
    print("📤 测试1: 记录老王心跳...")
    result1 = monitor.record_heartbeat()
    print(f"   {'✅ 成功' if result1 else '❌ 失败'}")
    
    # 测试2: 检查进程状态
    print()
    print("📤 测试2: 检查老王进程状态...")
    running, info = monitor.is_supervisor_running()
    if running:
        print(f"   ✅ 老王进程健康")
        print(f"      PID: {info.get('pid')}")
        print(f"      CPU: {info.get('cpu', 0):.1f}%")
        print(f"      内存: {info.get('memory_mb', 0):.1f}MB")
    else:
        print(f"   ⚠️  {info}")
    
    # 测试3: 检查最近心跳
    print()
    print("📤 测试3: 检查老王最近心跳...")
    has_heartbeat, msg = monitor.check_last_heartbeat()
    print(f"   {'✅' if has_heartbeat else '❌'} {msg}")
    
    # 测试4: 数据库健康
    print()
    print("📤 测试4: 检查数据库健康...")
    healthy, db_msg = monitor.check_database_health()
    print(f"   {'✅' if healthy else '❌'} {db_msg}")
    
    # 测试5: 磁盘空间
    print()
    print("📤 测试5: 检查磁盘空间...")
    has_space, disk_msg = monitor.check_disk_space()
    print(f"   {'✅' if has_space else '❌'} {disk_msg}")
    
    # 测试6: 全面健康检查
    print()
    print("📤 测试6: 全面健康检查...")
    health = monitor.perform_health_check()
    print(f"   整体健康: {'✅ 健康' if health['is_healthy'] else '❌ 有问题'}")
    for check, result in health['checks'].items():
        status = "✅" if result['healthy'] else "❌"
        print(f"   {status} {check}: {result['message']}")
    
    # 测试7: 获取自监控状态报告
    print()
    print("📤 测试7: 老王自监控报告...")
    status = monitor.get_self_status()
    hb = status['heartbeat_24h']
    print(f"   24小时心跳: {hb['count']} 次")
    print(f"   平均CPU: {hb['avg_cpu']}%")
    print(f"   平均内存: {hb['avg_memory_mb']:.1f}MB")
    
    if status['recent_issues']:
        print(f"   最近问题: {len(status['recent_issues'])} 个")
    else:
        print("   最近问题: 无")
    
    print()
    print("=" * 60)
    print("✅ 自监控测试完成！")
    print("老王既能监督别人，也能监督自己！")
    print("=" * 60)


if __name__ == "__main__":
    main()
