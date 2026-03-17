"""
任务注册表 - 管理所有需要监控的定时任务
"""

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class TaskDefinition:
    """任务定义"""
    task_id: str                    # 唯一标识
    name: str                       # 任务名称
    type: str                       # 类型: cron / interval / once
    schedule: str                   # cron表达式或间隔描述
    command: str                    # 执行命令
    working_dir: str                # 工作目录
    timeout_seconds: int = 300      # 超时时间
    retries: int = 3                # 重试次数
    critical: bool = True           # 是否关键任务
    owner: str = "system"           # 负责人
    description: str = ""           # 描述
    created_at: str = ""            # 创建时间
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class TaskExecution:
    """任务执行记录"""
    execution_id: str               # 执行ID
    task_id: str                    # 任务ID
    planned_time: str               # 计划执行时间
    actual_start: Optional[str]     # 实际开始时间
    actual_end: Optional[str]       # 实际结束时间
    status: str                     # pending / running / success / failed / timeout
    exit_code: Optional[int]        # 退出码
    stdout: str                     # 标准输出
    stderr: str                     # 错误输出
    error_message: str              # 错误信息
    retry_count: int = 0            # 重试次数
    repaired: bool = False          # 是否已修复
    repair_method: str = ""         # 修复方法
    

class TaskRegistry:
    """任务注册中心"""
    
    def __init__(self, db_path: str = "data/supervisor.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 任务定义表
        cursor.execute('''
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
        ''')
        
        # 任务执行记录表
        cursor.execute('''
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES task_definitions(task_id)
            )
        ''')
        
        # 任务统计表（每日汇总）
        cursor.execute('''
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
        ''')
        
        conn.commit()
        conn.close()
    
    def register_task(self, task: TaskDefinition) -> bool:
        """注册新任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO task_definitions 
                (task_id, name, type, schedule, command, working_dir, 
                 timeout_seconds, retries, critical, owner, description, 
                 created_at, updated_at, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                task.task_id, task.name, task.type, task.schedule,
                task.command, task.working_dir, task.timeout_seconds,
                task.retries, task.critical, task.owner, task.description,
                task.created_at, datetime.now().isoformat()
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"[TaskRegistry] 注册任务失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """获取任务定义"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id, name, type, schedule, command, working_dir,
                   timeout_seconds, retries, critical, owner, description, created_at
            FROM task_definitions WHERE task_id = ? AND enabled = 1
        ''', (task_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return TaskDefinition(*row)
        return None
    
    def get_all_tasks(self) -> List[TaskDefinition]:
        """获取所有启用的任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id, name, type, schedule, command, working_dir,
                   timeout_seconds, retries, critical, owner, description, created_at
            FROM task_definitions WHERE enabled = 1
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [TaskDefinition(*row) for row in rows]
    
    def record_execution(self, execution: TaskExecution) -> bool:
        """记录任务执行"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO task_executions
                (execution_id, task_id, planned_time, actual_start, actual_end,
                 status, exit_code, stdout, stderr, error_message, retry_count,
                 repaired, repair_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution.execution_id, execution.task_id, execution.planned_time,
                execution.actual_start, execution.actual_end, execution.status,
                execution.exit_code, execution.stdout, execution.stderr,
                execution.error_message, execution.retry_count, execution.repaired,
                execution.repair_method
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"[TaskRegistry] 记录执行失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_pending_executions(self) -> List[Dict[str, Any]]:
        """获取待执行和运行中的任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.*, d.name, d.critical, d.schedule
            FROM task_executions e
            JOIN task_definitions d ON e.task_id = d.task_id
            WHERE e.status IN ('pending', 'running')
            ORDER BY e.planned_time ASC
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_recent_failures(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近失败的执行"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.*, d.name, d.critical, d.owner
            FROM task_executions e
            JOIN task_definitions d ON e.task_id = d.task_id
            WHERE e.status IN ('failed', 'timeout')
            AND e.created_at > datetime('now', '-{} hours')
            AND e.repaired = 0
            ORDER BY e.created_at DESC
        '''.format(hours))
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_daily_report(self, date: str = None) -> Dict[str, Any]:
        """生成每日报告"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 今日概览
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeout,
                SUM(CASE WHEN status IN ('pending', 'running') THEN 1 ELSE 0 END) as pending
            FROM task_executions
            WHERE date(planned_time) = ?
        ''', (date,))
        
        overview = cursor.fetchone()
        
        # 各任务详情
        cursor.execute('''
            SELECT 
                d.task_id,
                d.name,
                d.critical,
                COUNT(e.execution_id) as total,
                SUM(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN e.status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN e.status = 'timeout' THEN 1 ELSE 0 END) as timeout
            FROM task_definitions d
            LEFT JOIN task_executions e ON d.task_id = e.task_id 
                AND date(e.planned_time) = ?
            WHERE d.enabled = 1
            GROUP BY d.task_id
        ''', (date,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'task_id': row[0],
                'name': row[1],
                'critical': bool(row[2]),
                'total': row[3],
                'success': row[4] or 0,
                'failed': row[5] or 0,
                'timeout': row[6] or 0
            })
        
        conn.close()
        
        return {
            'date': date,
            'total_executions': overview[0] or 0,
            'success': overview[1] or 0,
            'failed': overview[2] or 0,
            'timeout': overview[3] or 0,
            'pending': overview[4] or 0,
            'tasks': tasks
        }
    
    def mark_repaired(self, execution_id: str, method: str) -> bool:
        """标记任务已修复"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE task_executions 
                SET repaired = 1, repair_method = ?
                WHERE execution_id = ?
            ''', (method, execution_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"[TaskRegistry] 标记修复失败: {e}")
            return False
        finally:
            conn.close()


# 预定义的任务配置
DEFAULT_TASKS = [
    TaskDefinition(
        task_id="shen_suan_zi",
        name="神算子（AI预测）",
        type="cron",
        schedule="14,29,44,59 * * * *",
        command="cd /Users/mac/.openclaw/workspace/quant-trading && /usr/local/bin/python3 cron/prediction_agent_cron.py >> /Users/mac/.openclaw/workspace/quant-trading/logs/神算子.log 2>&1",
        working_dir="/Users/mac/.openclaw/workspace/quant-trading",
        timeout_seconds=120,
        retries=3,
        critical=True,
        owner="quant-trading",
        description="每15分钟执行一次BTC价格预测"
    ),
    TaskDefinition(
        task_id="shen_suan_zi_verify",
        name="神算子验算（验证预测）",
        type="cron",
        schedule="0 */2 * * *",
        command="cd /Users/mac/.openclaw/workspace/quant-trading && /usr/local/bin/python3 -c \"from .agents.神算子.agent import PredictionAgent; PredictionAgent().verify_pending()\" >> /Users/mac/.openclaw/workspace/quant-trading/logs/神算子验算.log 2>&1",
        working_dir="/Users/mac/.openclaw/workspace/quant-trading",
        timeout_seconds=300,
        retries=2,
        critical=False,
        owner="quant-trading",
        description="每2小时验证待处理的预测"
    ),
]


def init_default_tasks():
    """初始化默认任务"""
    registry = TaskRegistry()
    for task in DEFAULT_TASKS:
        registry.register_task(task)
        print(f"[Init] 已注册任务: {task.name}")


if __name__ == "__main__":
    init_default_tasks()
