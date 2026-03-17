"""
监工系统 Web Dashboard
"""

import os
import sys
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json

app = Flask(__name__, 
    template_folder='/Users/mac/.openclaw/workspace/quant-trading/supervisor/web/templates',
    static_folder='/Users/mac/.openclaw/workspace/quant-trading/supervisor/web/static'
)

DB_PATH = "/Users/mac/.openclaw/workspace/quant-trading/data/supervisor.db"


def get_db():
    """获取数据库连接"""
    import sqlite3
    return sqlite3.connect(DB_PATH)


@app.route('/supervisor')
def dashboard():
    """监工控制台主页"""
    return render_template('supervisor.html')


@app.route('/api/supervisor/status')
def api_status():
    """API: 系统状态"""
    try:
        from supervisor.core.registry import TaskRegistry
        from supervisor.core.heartbeat import HeartbeatMonitor
        
        registry = TaskRegistry(DB_PATH)
        
        # 今日统计
        today = datetime.now().strftime('%Y-%m-%d')
        report = registry.get_daily_report(today)
        
        # 任务健康状态
        tasks = registry.get_all_tasks()
        monitor = HeartbeatMonitor(DB_PATH)
        
        task_health = []
        for task in tasks:
            health = monitor.check_task_health(task.task_id)
            task_health.append(health)
        
        return jsonify({
            'success': True,
            'data': {
                'today': report,
                'tasks': task_health,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/supervisor/failures')
def api_failures():
    """API: 获取失败任务"""
    try:
        from supervisor.core.registry import TaskRegistry
        
        registry = TaskRegistry(DB_PATH)
        hours = request.args.get('hours', 24, type=int)
        
        failures = registry.get_recent_failures(hours=hours)
        
        return jsonify({
            'success': True,
            'data': failures
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/supervisor/repair', methods=['POST'])
def api_repair():
    """API: 手动修复任务"""
    try:
        from supervisor.commands.repair_engine import RepairEngine
        
        data = request.json
        execution_id = data.get('execution_id')
        command = data.get('command')
        
        if not execution_id or not command:
            return jsonify({'success': False, 'error': 'Missing parameters'})
        
        engine = RepairEngine(DB_PATH)
        result = engine.manual_repair(execution_id, command)
        
        return jsonify({
            'success': result.success,
            'data': result.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/supervisor/repair-options/<execution_id>')
def api_repair_options(execution_id):
    """API: 获取修复选项"""
    try:
        from supervisor.commands.repair_engine import RepairEngine
        import sqlite3
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM task_executions WHERE execution_id = ?
        ''', (execution_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': 'Execution not found'})
        
        columns = [desc[0] for desc in cursor.description]
        execution = dict(zip(columns, row))
        
        engine = RepairEngine(DB_PATH)
        options = engine.get_repair_options(execution)
        
        # 简化选项数据
        simple_options = [
            {
                'id': opt['id'],
                'name': opt['name'],
                'description': opt['description'],
                'auto': opt['auto']
            }
            for opt in options
        ]
        
        return jsonify({
            'success': True,
            'data': simple_options
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/supervisor/report/<date>')
def api_daily_report(date):
    """API: 获取日报"""
    try:
        from supervisor.core.registry import TaskRegistry
        
        registry = TaskRegistry(DB_PATH)
        report = registry.get_daily_report(date)
        
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/supervisor/executions')
def api_executions():
    """API: 获取执行历史"""
    try:
        import sqlite3
        
        conn = get_db()
        cursor = conn.cursor()
        
        task_id = request.args.get('task_id')
        limit = request.args.get('limit', 50, type=int)
        
        if task_id:
            cursor.execute('''
                SELECT e.*, d.name, d.critical
                FROM task_executions e
                JOIN task_definitions d ON e.task_id = d.task_id
                WHERE e.task_id = ?
                ORDER BY e.planned_time DESC
                LIMIT ?
            ''', (task_id, limit))
        else:
            cursor.execute('''
                SELECT e.*, d.name, d.critical
                FROM task_executions e
                JOIN task_definitions d ON e.task_id = d.task_id
                ORDER BY e.planned_time DESC
                LIMIT ?
            ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': [dict(zip(columns, row)) for row in rows]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/supervisor/github-status')
def api_github_status():
    """API: 获取GitHub提交状态"""
    try:
        import subprocess
        import sqlite3
        from datetime import datetime, timedelta
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 获取今日提交
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        result = subprocess.run(
            ['git', 'log', '--since', f'{today} 00:00:00', 
             '--until', f'{tomorrow} 00:00:00',
             '--pretty=format:%H|%s|%an|%ad', '--date=iso'],
            cwd='/Users/mac/.openclaw/workspace/quant-trading',
            capture_output=True,
            text=True
        )
        
        commits = []
        if result.returncode == 0:
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
        
        # 获取未推送提交数
        unpushed_result = subprocess.run(
            ['git', 'log', '@{u}..HEAD', '--oneline'],
            cwd='/Users/mac/.openclaw/workspace/quant-trading',
            capture_output=True,
            text=True
        )
        unpushed = len(unpushed_result.stdout.strip().split('\n')) if unpushed_result.returncode == 0 and unpushed_result.stdout.strip() else 0
        
        # 从数据库获取历史记录计算连续提交天数
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, commits_count FROM github_daily_status
            ORDER BY date DESC
            LIMIT 30
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        # 计算连续提交天数
        streak = 0
        for row in rows:
            if row[1] > 0:
                streak += 1
            else:
                break
        
        return jsonify({
            'success': True,
            'data': {
                'commits': len(commits),
                'unpushed': unpushed,
                'streak': streak,
                'commits_list': commits
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
