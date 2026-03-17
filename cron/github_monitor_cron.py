#!/usr/bin/env python3
"""
GitHub 每日提交监控 - 隔壁老王的新任务
检查每天是否有代码提交到GitHub，没有就@你
"""

import os
import sys
import sqlite3
import subprocess
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')


def get_today_commits():
    """获取今天的Git提交记录"""
    try:
        # 获取今天的日期范围
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 使用git log检查今天的提交
        result = subprocess.run(
            ['git', 'log', '--since', f'{today} 00:00:00', 
             '--until', f'{tomorrow} 00:00:00',
             '--pretty=format:%H|%s|%an|%ad', '--date=iso'],
            cwd='/Users/mac/.openclaw/workspace/quant-trading',
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return None, f"Git命令失败: {result.stderr}"
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|', 3)
                if len(parts) >= 3:
                    commits.append({
                        'hash': parts[0][:8],
                        'message': parts[1],
                        'author': parts[2],
                        'date': parts[3] if len(parts) > 3 else today
                    })
        
        return commits, None
        
    except Exception as e:
        return None, str(e)


def check_push_status():
    """检查本地提交是否已推送到远程"""
    try:
        # 检查是否有未推送的提交
        result = subprocess.run(
            ['git', 'log', '@{u}..HEAD', '--oneline'],
            cwd='/Users/mac/.openclaw/workspace/quant-trading',
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            unpushed = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return len(unpushed), None
        else:
            return 0, "无法检查推送状态"
            
    except Exception as e:
        return 0, str(e)


def record_commit_status(commits_count, unpushed_count, details=""):
    """记录提交状态到数据库"""
    db_path = '/Users/mac/.openclaw/workspace/quant-trading/data/supervisor.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建Git监控记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS github_daily_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            commits_count INTEGER DEFAULT 0,
            unpushed_count INTEGER DEFAULT 0,
            details TEXT,
            alert_sent BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('''
        INSERT OR REPLACE INTO github_daily_status 
        (date, commits_count, unpushed_count, details, alert_sent)
        VALUES (?, ?, ?, ?, 
            COALESCE((SELECT alert_sent FROM github_daily_status WHERE date = ?), 0)
        )
    ''', (today, commits_count, unpushed_count, details, today))
    
    conn.commit()
    conn.close()


def send_no_commit_alert():
    """发送今日无提交告警（通过老王）"""
    try:
        from supervisor.alerts.openclaw_notifier import OpenclawNotifier
        
        notifier = OpenclawNotifier()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        message = f"""⚠️ 隔壁老王提醒：今日无代码提交

📅 日期: {today}
📊 GitHub仓库: AI_Quantitative_trading
❌ 今日提交: 0 次

🤔 老王唠叨:
   "今天没写代码？是不是偷懒了？"
   "哪怕改个README也行啊！"
   "保持每日提交的习惯，代码不会骗人！"

💡 快速提交:
   git add .
   git commit -m "update: {today} daily commit"
   git push

⏰ 时间: {datetime.now().strftime('%H:%M:%S')}
🤖 发送者: 隔壁老王"""
        
        return notifier.send_message(message)
        
    except Exception as e:
        print(f"[GitHubMonitor] 发送告警失败: {e}")
        return False


def send_unpushed_alert(count):
    """发送有未推送提交告警"""
    try:
        from supervisor.alerts.openclaw_notifier import OpenclawNotifier
        
        notifier = OpenclawNotifier()
        
        message = f"""📝 隔壁老王提醒：有未推送的提交

📦 本地提交: {count} 个未推送
🌐 远程仓库: GitHub

⚠️ 老王唠叨:
   "写了代码不push，等于白写！"
   "是不是忘了？还是要藏着掖着？"

💡 快速推送:
   git push

⏰ 时间: {datetime.now().strftime('%H:%M:%S')}
🤖 发送者: 隔壁老王"""
        
        return notifier.send_message(message)
        
    except Exception as e:
        print(f"[GitHubMonitor] 发送告警失败: {e}")
        return False


def main():
    """隔壁老王的GitHub监控主程序"""
    print("=" * 60)
    print("🧑‍🔧 隔壁老王：GitHub每日提交检查")
    print("=" * 60)
    print()
    
    now = datetime.now()
    print(f"检查时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 获取今日提交
    commits, error = get_today_commits()
    
    if error:
        print(f"❌ 获取提交失败: {error}")
        return
    
    commits_count = len(commits)
    
    # 2. 检查未推送提交
    unpushed_count, push_error = check_push_status()
    
    # 3. 记录状态
    details = f"Commits: {commits_count}, Unpushed: {unpushed_count}"
    record_commit_status(commits_count, unpushed_count, details)
    
    # 4. 打印提交详情
    if commits_count > 0:
        print(f"✅ 今日提交: {commits_count} 次")
        print()
        print("提交详情:")
        for i, commit in enumerate(commits, 1):
            print(f"  {i}. [{commit['hash']}] {commit['message']}")
            print(f"     作者: {commit['author']}")
            print()
    else:
        print("⚠️  今日无提交")
        print()
    
    # 5. 检查未推送
    if unpushed_count > 0:
        print(f"📝 未推送提交: {unpushed_count} 个")
        print()
    
    # 6. 判断是否需要告警
    should_alert = False
    alert_type = None
    
    # 规则：晚上22点后检查，如果没有提交则告警
    if now.hour >= 22 and commits_count == 0:
        should_alert = True
        alert_type = "no_commit"
        print("🚨 触发告警：今日无提交（22:00后检查）")
    
    # 规则：如果有未推送提交，提醒一下
    elif unpushed_count > 0:
        should_alert = True
        alert_type = "unpushed"
        print(f"🚨 触发告警：有 {unpushed_count} 个未推送提交")
    
    # 7. 发送告警
    if should_alert:
        print()
        print("📤 正在发送飞书通知...")
        
        if alert_type == "no_commit":
            success = send_no_commit_alert()
        else:
            success = send_unpushed_alert(unpushed_count)
        
        if success:
            print("✅ 隔壁老王已通知你")
            
            # 标记已告警
            db_path = '/Users/mac/.openclaw/workspace/quant-trading/data/supervisor.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            today = now.strftime('%Y-%m-%d')
            cursor.execute('''
                UPDATE github_daily_status SET alert_sent = 1 WHERE date = ?
            ''', (today,))
            conn.commit()
            conn.close()
        else:
            print("❌ 通知发送失败")
    else:
        print("✅ 一切正常，老王不打扰你")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
