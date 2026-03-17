#!/usr/bin/env python3
"""
任务监工系统 CLI 工具
交互式命令行管理界面
"""

import sys
import os
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')

import argparse
from datetime import datetime
from supervisor.core.registry import TaskRegistry, TaskDefinition
from supervisor.core.heartbeat import HeartbeatMonitor
from supervisor.commands.repair_engine import RepairEngine
from supervisor.alerts.feishu_notifier import FeishuNotifier


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def cmd_status(args):
    """查看系统状态"""
    print_header("🎖️ 任务监工系统状态")
    
    registry = TaskRegistry()
    monitor = HeartbeatMonitor()
    
    # 今日统计
    today = datetime.now().strftime('%Y-%m-%d')
    report = registry.get_daily_report(today)
    
    print(f"📅 日期: {today}")
    print(f"📊 今日执行: {report['total_executions']} 次")
    print(f"   ✅ 成功: {report['success']}")
    print(f"   ❌ 失败: {report['failed']}")
    print(f"   ⏱  超时: {report['timeout']}")
    print(f"   ⏳ 待处理: {report['pending']}")
    
    if report['total_executions'] > 0:
        rate = (report['success'] / report['total_executions']) * 100
        print(f"\n📈 成功率: {rate:.1f}%")
    
    # 任务列表
    print("\n📋 监控任务:")
    print("-" * 60)
    tasks = registry.get_all_tasks()
    for task in tasks:
        health = monitor.check_task_health(task.task_id)
        status = "🟢" if health['status'] == 'healthy' else "🔴"
        critical = "🔴关键" if task.critical else "⚪普通"
        print(f"  {status} {task.name}")
        print(f"     ID: {task.task_id}")
        print(f"     计划: {task.schedule}")
        print(f"     级别: {critical}")
        if health.get('last_success'):
            print(f"     最后成功: {health['last_success']['planned']}")
        print()


def cmd_list(args):
    """列出任务"""
    print_header("📋 任务列表")
    
    registry = TaskRegistry()
    tasks = registry.get_all_tasks()
    
    print(f"共 {len(tasks)} 个任务\n")
    
    for i, task in enumerate(tasks, 1):
        print(f"{i}. {task.name}")
        print(f"   ID: {task.task_id}")
        print(f"   类型: {task.type}")
        print(f"   计划: {task.schedule}")
        print(f"   命令: {task.command[:60]}...")
        print(f"   目录: {task.working_dir}")
        print(f"   超时: {task.timeout_seconds}s")
        print(f"   重试: {task.retries}次")
        print(f"   关键: {'是' if task.critical else '否'}")
        print()


def cmd_add(args):
    """添加任务"""
    print_header("➕ 添加新任务")
    
    registry = TaskRegistry()
    
    task = TaskDefinition(
        task_id=args.id,
        name=args.name,
        type=args.type,
        schedule=args.schedule,
        command=args.command,
        working_dir=args.workdir or os.getcwd(),
        timeout_seconds=args.timeout,
        retries=args.retries,
        critical=args.critical,
        owner=args.owner or "admin",
        description=args.description or ""
    )
    
    if registry.register_task(task):
        print(f"✅ 任务 '{args.name}' 已注册")
        print(f"   ID: {args.id}")
        print(f"   计划: {args.schedule}")
    else:
        print("❌ 注册失败")


def cmd_failures(args):
    """查看失败任务"""
    print_header("⚠️  失败任务")
    
    registry = TaskRegistry()
    failures = registry.get_recent_failures(hours=args.hours)
    
    if not failures:
        print(f"🎉 最近 {args.hours} 小时内没有失败任务")
        return
    
    print(f"最近 {args.hours} 小时内有 {len(failures)} 个失败:\n")
    
    for i, f in enumerate(failures, 1):
        print(f"{i}. {f.get('name')} {'🔴' if f.get('critical') else ''}")
        print(f"   执行ID: {f.get('execution_id')}")
        print(f"   计划时间: {f.get('planned_time')}")
        print(f"   状态: {f.get('status')}")
        print(f"   重试: {f.get('retry_count')} 次")
        if f.get('error_message'):
            print(f"   错误: {f.get('error_message')[:200]}")
        print()


def cmd_repair(args):
    """修复任务"""
    print_header("🔧 修复任务")
    
    engine = RepairEngine()
    
    # 如果没有指定执行ID，列出可修复的失败
    if not args.execution_id:
        registry = TaskRegistry()
        failures = registry.get_recent_failures(hours=24)
        failures = [f for f in failures if not f.get('repaired')]
        
        if not failures:
            print("🎉 没有待修复的失败任务")
            return
        
        print("待修复的任务:\n")
        for i, f in enumerate(failures, 1):
            print(f"{i}. {f.get('name')} - {f.get('execution_id')}")
        
        print("\n使用: supervisor_cli repair <execution_id> [--auto|--manual <command>]")
        return
    
    # 自动修复
    if args.auto:
        print(f"🤖 尝试自动修复: {args.execution_id}")
        
        import sqlite3
        conn = sqlite3.connect("data/supervisor.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM task_executions WHERE execution_id = ?", (args.execution_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            print("❌ 执行记录不存在")
            return
        
        columns = ['execution_id', 'task_id', 'planned_time', 'actual_start', 
                  'actual_end', 'status', 'exit_code', 'stdout', 'stderr', 
                  'error_message', 'retry_count', 'repaired', 'repair_method']
        execution = dict(zip(columns, row))
        
        result = engine.auto_repair(execution)
        
        print(f"\n修复结果:")
        print(f"  成功: {'✅' if result.success else '❌'}")
        print(f"  方法: {result.method}")
        print(f"  消息: {result.message}")
        print(f"  耗时: {result.execution_time:.2f}s")
    
    # 手动修复
    elif args.manual:
        print(f"👨‍🔧 执行手动修复: {args.execution_id}")
        print(f"命令: {args.manual}")
        
        result = engine.manual_repair(args.execution_id, args.manual, args.user)
        
        print(f"\n修复结果:")
        print(f"  成功: {'✅' if result.success else '❌'}")
        print(f"  消息: {result.message}")
    
    else:
        # 显示修复选项
        import sqlite3
        conn = sqlite3.connect("data/supervisor.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM task_executions WHERE execution_id = ?", (args.execution_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            print("❌ 执行记录不存在")
            return
        
        columns = ['execution_id', 'task_id', 'planned_time', 'actual_start', 
                  'actual_end', 'status', 'exit_code', 'stdout', 'stderr', 
                  'error_message', 'retry_count', 'repaired', 'repair_method']
        execution = dict(zip(columns, row))
        
        options = engine.get_repair_options(execution)
        
        print(f"可用修复选项:\n")
        for opt in options:
            auto = "🤖" if opt['auto'] else "👨‍🔧"
            print(f"  {auto} {opt['id']}: {opt['name']}")
            print(f"     {opt['description']}")
            print()
        
        print(f"使用: supervisor_cli repair {args.execution_id} --auto")
        print(f"   或: supervisor_cli repair {args.execution_id} --manual '<command>'")


def cmd_report(args):
    """生成报告"""
    print_header("📊 执行报告")
    
    registry = TaskRegistry()
    date = args.date or datetime.now().strftime('%Y-%m-%d')
    
    report = registry.get_daily_report(date)
    
    print(f"日期: {report['date']}")
    print(f"总执行: {report['total_executions']}")
    print(f"成功: {report['success']}")
    print(f"失败: {report['failed']}")
    print(f"超时: {report['timeout']}")
    print(f"待处理: {report['pending']}")
    
    if report['total_executions'] > 0:
        rate = (report['success'] / report['total_executions']) * 100
        print(f"\n成功率: {rate:.1f}%")
    
    print("\n任务详情:")
    print("-" * 60)
    for task in report['tasks']:
        total = task['total']
        if total > 0:
            success_rate = (task['success'] / total) * 100
            status = "✅" if success_rate >= 95 else "⚠️" if success_rate >= 80 else "❌"
            print(f"  {status} {task['name']}: {task['success']}/{total} ({success_rate:.0f}%)")


def cmd_test_alert(args):
    """测试告警"""
    print_header("🧪 测试飞书告警")
    
    notifier = FeishuNotifier()
    
    test_data = {
        'task_name': '测试任务',
        'scheduled_time': datetime.now().isoformat(),
        'reason': '这是一条测试消息',
        'critical': True
    }
    
    result = notifier.notify_task_missed(test_data)
    
    if result:
        print("✅ 测试消息已发送，请检查飞书")
    else:
        print("❌ 发送失败，请检查webhook配置")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='任务监工系统 CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  supervisor_cli status              # 查看系统状态
  supervisor_cli list                # 列出所有任务
  supervisor_cli failures            # 查看失败任务
  supervisor_cli repair              # 查看可修复任务
  supervisor_cli repair <id> --auto  # 自动修复
  supervisor_cli report              # 今日报告
  supervisor_cli report --date 2024-03-17
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # status
    subparsers.add_parser('status', help='查看系统状态')
    
    # list
    subparsers.add_parser('list', help='列出所有任务')
    
    # add
    add_parser = subparsers.add_parser('add', help='添加新任务')
    add_parser.add_argument('--id', required=True, help='任务ID')
    add_parser.add_argument('--name', required=True, help='任务名称')
    add_parser.add_argument('--schedule', required=True, help='Cron表达式')
    add_parser.add_argument('--command', required=True, help='执行命令')
    add_parser.add_argument('--workdir', help='工作目录')
    add_parser.add_argument('--type', default='cron', help='任务类型')
    add_parser.add_argument('--timeout', type=int, default=300, help='超时时间(秒)')
    add_parser.add_argument('--retries', type=int, default=3, help='重试次数')
    add_parser.add_argument('--critical', action='store_true', help='是否关键任务')
    add_parser.add_argument('--owner', help='负责人')
    add_parser.add_argument('--description', help='描述')
    
    # failures
    failures_parser = subparsers.add_parser('failures', help='查看失败任务')
    failures_parser.add_argument('--hours', type=int, default=24, help='时间范围(小时)')
    
    # repair
    repair_parser = subparsers.add_parser('repair', help='修复任务')
    repair_parser.add_argument('execution_id', nargs='?', help='执行ID')
    repair_parser.add_argument('--auto', action='store_true', help='自动修复')
    repair_parser.add_argument('--manual', help='手动执行命令')
    repair_parser.add_argument('--user', default='admin', help='执行用户')
    
    # report
    report_parser = subparsers.add_parser('report', help='生成报告')
    report_parser.add_argument('--date', help='日期 (YYYY-MM-DD)')
    
    # test-alert
    subparsers.add_parser('test-alert', help='测试飞书告警')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    commands = {
        'status': cmd_status,
        'list': cmd_list,
        'add': cmd_add,
        'failures': cmd_failures,
        'repair': cmd_repair,
        'report': cmd_report,
        'test-alert': cmd_test_alert,
    }
    
    if args.command in commands:
        try:
            commands[args.command](args)
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
