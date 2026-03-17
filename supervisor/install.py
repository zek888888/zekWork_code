#!/usr/bin/env python3
"""
隔壁老王安装脚本
"""

import os
import sys
import sqlite3
import subprocess

def check_and_install_deps():
    """检查并安装依赖"""
    print("📦 检查依赖...")
    
    deps = ['flask', 'requests']
    for dep in deps:
        try:
            __import__(dep)
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ⬇ 安装 {dep}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                         capture_output=True)
    
    print("✅ 依赖检查完成\n")

def init_database():
    """初始化数据库"""
    print("🗄️ 初始化数据库...")
    
    db_path = "data/supervisor.db"
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建表
    tables = [
        '''
        CREATE TABLE IF NOT EXISTS task_definitions (
            task_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            schedule TEXT NOT NULL,
            command TEXT NOT NULL,
            working_dir TEXT NOT NULL,
            timeout_seconds INTEGER DEFAULT 300,
            retries INTEGER DEFAULT 3,
            critical BOOLEAN DEFAULT 1,
            owner TEXT DEFAULT 'system',
            description TEXT,
            created_at TEXT,
            updated_at TEXT,
            enabled BOOLEAN DEFAULT 1
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS task_executions (
            execution_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            planned_time TEXT NOT NULL,
            actual_start TEXT,
            actual_end TEXT,
            status TEXT NOT NULL,
            exit_code INTEGER,
            stdout TEXT,
            stderr TEXT,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            repaired BOOLEAN DEFAULT 0,
            repair_method TEXT,
            alert_sent BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS task_daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            task_id TEXT NOT NULL,
            planned_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            timeout_count INTEGER DEFAULT 0,
            missed_count INTEGER DEFAULT 0,
            avg_duration_seconds REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, task_id)
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS supervisor_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            target TEXT NOT NULL,
            content TEXT,
            level TEXT NOT NULL,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            acknowledged BOOLEAN DEFAULT 0,
            execution_id TEXT
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS supervisor_repairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            error_pattern TEXT,
            strategy TEXT,
            attempted_fixes TEXT,
            final_result TEXT,
            success BOOLEAN,
            repair_time TEXT DEFAULT CURRENT_TIMESTAMP,
            manual_intervention BOOLEAN DEFAULT 0,
            manual_command TEXT,
            executor TEXT DEFAULT 'auto'
        )
        '''
    ]
    
    for sql in tables:
        cursor.execute(sql)
    
    conn.commit()
    conn.close()
    
    print(f"✅ 数据库初始化完成: {db_path}\n")

def register_default_tasks():
    """注册默认任务"""
    print("📝 注册默认任务...")
    
    sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')
    
    from supervisor.core.registry import TaskRegistry, TaskDefinition
    
    registry = TaskRegistry("data/supervisor.db")
    
    tasks = [
        TaskDefinition(
            task_id="shen_suan_zi",
            name="神算子（AI预测）",
            type="cron",
            schedule="14,29,44,59 * * * *",
            command="cd /Users/mac/.openclaw/workspace/quant-trading && /usr/local/bin/python3 cron/prediction_agent_cron.py >> /Users/mac/.openclaw/workspace/quant-trading/logs/prediction_agent.log 2>&1",
            working_dir="/Users/mac/.openclaw/workspace/quant-trading",
            timeout_seconds=120,
            retries=3,
            critical=True,
            owner="quant-trading",
            description="神算子每15分钟预测一次BTC价格"
        ),
        TaskDefinition(
            task_id="shen_suan_zi_verify",
            name="神算子验算（验证预测）",
            type="cron",
            schedule="0 */2 * * *",
            command="cd /Users/mac/.openclaw/workspace/quant-trading && /usr/local/bin/python3 -c \"from agents.prediction_agent.agent import PredictionAgent; agent = PredictionAgent(); agent.verify_pending()\" >> /Users/mac/.openclaw/workspace/quant-trading/logs/verify.log 2>&1",
            working_dir="/Users/mac/.openclaw/workspace/quant-trading",
            timeout_seconds=300,
            retries=2,
            critical=False,
            owner="quant-trading",
            description="神算子每2小时验证历史预测准确率"
        ),
    ]
    
    for task in tasks:
        registry.register_task(task)
        print(f"  ✓ {task.name}")
    
    print(f"✅ 已注册 {len(tasks)} 个任务\n")

def create_directories():
    """创建必要目录"""
    print("📁 创建目录结构...")
    
    dirs = [
        'logs',
        'supervisor/logs',
        'supervisor/web/static',
        'supervisor/web/templates'
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  ✓ {d}")
    
    print()

def create_startup_scripts():
    """创建启动脚本"""
    print("🔧 创建启动脚本...")
    
    # 主监工启动脚本
    supervisor_script = '''#!/bin/bash
# 隔壁老王启动脚本

cd /Users/mac/.openclaw/workspace/quant-trading

# 确保日志目录存在
mkdir -p logs

# 启动监工系统
/usr/local/bin/python3 supervisor/core/scheduler.py >> logs/supervisor.log 2>&1 &
echo $! > supervisor.pid

echo "✅ 监工系统已启动"
echo "📊 Web控制台: http://localhost:5001/supervisor"
echo "📝 日志: tail -f logs/supervisor.log"
'''
    
    with open('start_supervisor.sh', 'w') as f:
        f.write(supervisor_script)
    os.chmod('start_supervisor.sh', 0o755)
    print("  ✓ start_supervisor.sh")
    
    # Web dashboard 启动脚本
    web_script = '''#!/bin/bash
# 监工Web控制台启动脚本

cd /Users/mac/.openclaw/workspace/quant-trading
/usr/local/bin/python3 supervisor/web/app.py
'''
    
    with open('start_supervisor_web.sh', 'w') as f:
        f.write(web_script)
    os.chmod('start_supervisor_web.sh', 0o755)
    print("  ✓ start_supervisor_web.sh")
    
    # 停止脚本
    stop_script = '''#!/bin/bash
# 停止监工系统

if [ -f supervisor.pid ]; then
    PID=$(cat supervisor.pid)
    kill $PID 2>/dev/null
    rm supervisor.pid
    echo "✅ 监工系统已停止"
else
    echo "⚠️ 监工系统未运行"
fi
'''
    
    with open('stop_supervisor.sh', 'w') as f:
        f.write(stop_script)
    os.chmod('stop_supervisor.sh', 0o755)
    print("  ✓ stop_supervisor.sh")
    
    print()

def print_summary():
    """打印安装总结"""
    print("=" * 60)
    print("🎉 隔壁老王安装完成！")
    print("=" * 60)
    print()
    print("📋 使用说明:")
    print()
    print("1️⃣ 启动监工系统:")
    print("   ./start_supervisor.sh")
    print()
    print("2️⃣ 启动Web控制台:")
    print("   ./start_supervisor_web.sh")
    print("   然后访问: http://localhost:5001/supervisor")
    print()
    print("3️⃣ 查看日志:")
    print("   tail -f logs/supervisor.log")
    print()
    print("4️⃣ 停止监工系统:")
    print("   ./stop_supervisor.sh")
    print()
    print("=" * 60)
    print()
    print("⚙️ 配置飞书通知:")
    print("   在 config.yaml 中添加:")
    print("   feishu_webhook: https://open.feishu.cn/...")
    print()

def main():
    """主函数"""
    print("=" * 60)
    print("🎖️ 隔壁老王安装程序")
    print("=" * 60)
    print()
    
    os.chdir('/Users/mac/.openclaw/workspace/quant-trading')
    
    check_and_install_deps()
    create_directories()
    init_database()
    register_default_tasks()
    create_startup_scripts()
    print_summary()

if __name__ == "__main__":
    main()
