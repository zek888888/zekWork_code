#!/usr/bin/env python3
"""
注册 GitHub 监控任务到隔壁老王的任务清单
"""

import sys
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')

from supervisor.core.registry import TaskRegistry, TaskDefinition


def register_github_monitor():
    """注册GitHub监控任务"""
    registry = TaskRegistry()
    
    task = TaskDefinition(
        task_id="github_daily_commit",
        name="GitHub每日提交监控",
        type="cron",
        schedule="0 22 * * *",  # 每天晚上22:00检查
        command="cd /Users/mac/.openclaw/workspace/quant-trading && /usr/local/bin/python3 cron/github_monitor_cron.py >> logs/github_monitor.log 2>&1",
        working_dir="/Users/mac/.openclaw/workspace/quant-trading",
        timeout_seconds=60,
        retries=2,
        critical=False,  # 不是关键任务，只是提醒
        owner="developer",
        description="隔壁老王每天22点检查GitHub提交，没提交就唠叨你"
    )
    
    if registry.register_task(task):
        print("✅ GitHub监控任务已注册")
        print(f"   任务ID: {task.task_id}")
        print(f"   执行时间: 每天22:00")
        print(f"   检查内容: 今日是否有Git提交")
        return True
    else:
        print("❌ 注册失败")
        return False


def register_github_push_reminder():
    """注册GitHub推送提醒任务（中午检查一次）"""
    registry = TaskRegistry()
    
    task = TaskDefinition(
        task_id="github_push_reminder",
        name="GitHub推送提醒",
        type="cron",
        schedule="0 12 * * *",  # 每天中午12:00检查
        command="cd /Users/mac/.openclaw/workspace/quant-trading && /usr/local/bin/python3 cron/github_monitor_cron.py >> logs/github_monitor.log 2>&1",
        working_dir="/Users/mac/.openclaw/workspace/quant-trading",
        timeout_seconds=60,
        retries=1,
        critical=False,
        owner="developer",
        description="中午检查是否有未推送的提交，提醒你push"
    )
    
    if registry.register_task(task):
        print("✅ GitHub推送提醒任务已注册")
        print(f"   任务ID: {task.task_id}")
        print(f"   执行时间: 每天12:00")
        return True
    else:
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧑‍🔧 隔壁老王：注册GitHub监控任务")
    print("=" * 60)
    print()
    
    register_github_monitor()
    print()
    register_github_push_reminder()
    
    print()
    print("老王说：\"代码不提交，等于没写！我帮你盯着！\"")
    print("=" * 60)
