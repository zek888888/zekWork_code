"""
心跳监控 - 检测任务是否按时执行，识别漏执行的任务
"""

import re
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import threading
import time


@dataclass
class MissedTask:
    """漏执行的任务"""
    task_id: str
    task_name: str
    scheduled_time: datetime
    reason: str
    critical: bool


class CronParser:
    """解析Cron表达式，计算下一次执行时间"""
    
    @staticmethod
    def parse(cron_expr: str) -> Dict[str, List[int]]:
        """解析cron表达式"""
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expr}")
        
        return {
            'minute': CronParser._parse_field(parts[0], 0, 59),
            'hour': CronParser._parse_field(parts[1], 0, 23),
            'day': CronParser._parse_field(parts[2], 1, 31),
            'month': CronParser._parse_field(parts[3], 1, 12),
            'weekday': CronParser._parse_field(parts[4], 0, 7),
        }
    
    @staticmethod
    def _parse_field(field: str, min_val: int, max_val: int) -> List[int]:
        """解析单个字段"""
        if field == '*':
            return list(range(min_val, max_val + 1))
        
        values = []
        for part in field.split(','):
            if '/' in part:
                # 步进表达式，如 */15
                base, step = part.split('/')
                if base == '*':
                    values.extend(range(min_val, max_val + 1, int(step)))
            elif '-' in part:
                # 范围表达式，如 1-5
                start, end = map(int, part.split('-'))
                values.extend(range(start, end + 1))
            else:
                # 具体值
                val = int(part)
                if val == 7 and max_val == 7:  # 周日处理
                    val = 0
                values.append(val)
        
        return sorted(set(v for v in values if min_val <= v <= max_val))
    
    @staticmethod
    def get_next_run(cron_expr: str, after: datetime = None) -> datetime:
        """获取下一次执行时间"""
        if after is None:
            after = datetime.now()
        
        parsed = CronParser.parse(cron_expr)
        
        # 从当前时间开始，逐分钟检查
        current = after.replace(second=0, microsecond=0)
        
        for _ in range(366 * 24 * 60):  # 最多检查一年
            current += timedelta(minutes=1)
            
            if current.minute not in parsed['minute']:
                continue
            if current.hour not in parsed['hour']:
                continue
            if current.day not in parsed['day']:
                continue
            if current.month not in parsed['month']:
                continue
            if current.weekday() not in parsed['weekday'] and current.isoweekday() % 7 not in parsed['weekday']:
                continue
            
            return current
        
        raise ValueError("Could not find next run time")
    
    @staticmethod
    def get_expected_runs(cron_expr: str, start: datetime, end: datetime) -> List[datetime]:
        """获取时间段内所有应该执行的时间点"""
        runs = []
        current = start
        
        while current < end:
            next_run = CronParser.get_next_run(cron_expr, current - timedelta(minutes=1))
            if next_run > end:
                break
            runs.append(next_run)
            current = next_run
        
        return runs


class HeartbeatMonitor:
    """心跳监控器 - 检测任务是否按时执行"""
    
    def __init__(self, db_path: str = "data/supervisor.db", 
                 grace_period_minutes: int = 5):
        self.db_path = db_path
        self.grace_period = timedelta(minutes=grace_period_minutes)
        self._running = False
        self._thread = None
        self._callbacks = []
    
    def on_missed_task(self, callback):
        """注册漏执行回调"""
        self._callbacks.append(callback)
    
    def check_all_tasks(self) -> List[MissedTask]:
        """检查所有任务，返回漏执行的任务"""
        from .registry import TaskRegistry
        
        registry = TaskRegistry(self.db_path)
        tasks = registry.get_all_tasks()
        missed = []
        
        now = datetime.now()
        check_window_start = now - timedelta(hours=2)  # 检查最近2小时
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for task in tasks:
            if task.type != 'cron':
                continue
            
            # 获取应该执行的所有时间点
            try:
                expected_runs = CronParser.get_expected_runs(
                    task.schedule, check_window_start, now
                )
            except Exception as e:
                print(f"[Heartbeat] 解析cron失败 {task.task_id}: {e}")
                continue
            
            for expected_time in expected_runs:
                # 检查这个时间点是否已经执行
                grace_end = expected_time + self.grace_period
                
                if now < grace_end:
                    # 还在宽限期内，不判定为漏执行
                    continue
                
                cursor.execute('''
                    SELECT execution_id, status, actual_start
                    FROM task_executions
                    WHERE task_id = ? 
                    AND planned_time = ?
                    AND status != 'missed'
                ''', (task.task_id, expected_time.isoformat()))
                
                row = cursor.fetchone()
                
                if not row:
                    # 完全没有任何记录 - 漏执行
                    missed.append(MissedTask(
                        task_id=task.task_id,
                        task_name=task.name,
                        scheduled_time=expected_time,
                        reason="未检测到执行记录",
                        critical=task.critical
                    ))
                    
                    # 记录为missed
                    self._record_missed(task.task_id, expected_time)
                    
                elif row[1] in ('failed', 'timeout'):
                    # 执行失败且未修复
                    if not self._is_repaired(row[0]):
                        missed.append(MissedTask(
                            task_id=task.task_id,
                            task_name=task.name,
                            scheduled_time=expected_time,
                            reason=f"执行失败: {row[1]}",
                            critical=task.critical
                        ))
        
        conn.close()
        
        # 触发回调
        for task in missed:
            for callback in self._callbacks:
                try:
                    callback(task)
                except Exception as e:
                    print(f"[Heartbeat] 回调错误: {e}")
        
        return missed
    
    def _record_missed(self, task_id: str, scheduled_time: datetime):
        """记录漏执行"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        execution_id = f"{task_id}_{scheduled_time.strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute('''
            INSERT OR IGNORE INTO task_executions
            (execution_id, task_id, planned_time, status, error_message)
            VALUES (?, ?, ?, 'missed', '心跳监控检测到漏执行')
        ''', (execution_id, task_id, scheduled_time.isoformat()))
        
        conn.commit()
        conn.close()
    
    def _is_repaired(self, execution_id: str) -> bool:
        """检查是否已修复"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT repaired FROM task_executions WHERE execution_id = ?
        ''', (execution_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return row and row[0]
    
    def start_monitoring(self, interval_seconds: int = 60):
        """启动持续监控"""
        self._running = True
        
        def monitor_loop():
            while self._running:
                try:
                    missed = self.check_all_tasks()
                    if missed:
                        print(f"[Heartbeat] 检测到 {len(missed)} 个漏执行任务")
                except Exception as e:
                    print(f"[Heartbeat] 监控错误: {e}")
                
                time.sleep(interval_seconds)
        
        self._thread = threading.Thread(target=monitor_loop, daemon=True)
        self._thread.start()
        print(f"[Heartbeat] 监控已启动，检查间隔: {interval_seconds}秒")
    
    def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[Heartbeat] 监控已停止")
    
    def check_task_health(self, task_id: str) -> Dict[str, Any]:
        """检查单个任务的健康状态"""
        from .registry import TaskRegistry
        
        registry = TaskRegistry(self.db_path)
        task = registry.get_task(task_id)
        
        if not task:
            return {'error': 'Task not found'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 最近24小时执行统计
        cursor.execute('''
            SELECT 
                status,
                COUNT(*) as count,
                MAX(created_at) as last_time
            FROM task_executions
            WHERE task_id = ?
            AND created_at > datetime('now', '-24 hours')
            GROUP BY status
        ''', (task_id,))
        
        stats = {row[0]: {'count': row[1], 'last': row[2]} for row in cursor.fetchall()}
        
        # 最后一次成功执行
        cursor.execute('''
            SELECT planned_time, actual_start, actual_end
            FROM task_executions
            WHERE task_id = ? AND status = 'success'
            ORDER BY planned_time DESC
            LIMIT 1
        ''', (task_id,))
        
        last_success = cursor.fetchone()
        
        # 下一次应该执行
        next_run = None
        if task.type == 'cron':
            try:
                next_run = CronParser.get_next_run(task.schedule)
            except:
                pass
        
        conn.close()
        
        return {
            'task_id': task_id,
            'name': task.name,
            'schedule': task.schedule,
            'critical': task.critical,
            'stats_24h': stats,
            'last_success': {
                'planned': last_success[0],
                'started': last_success[1],
                'ended': last_success[2]
            } if last_success else None,
            'next_expected_run': next_run.isoformat() if next_run else None,
            'status': 'healthy' if last_success else 'unknown'
        }


if __name__ == "__main__":
    # 测试
    monitor = HeartbeatMonitor()
    
    def on_miss(task):
        print(f"🚨 漏执行: {task.task_name} @ {task.scheduled_time}")
    
    monitor.on_missed_task(on_miss)
    missed = monitor.check_all_tasks()
    print(f"发现 {len(missed)} 个漏执行任务")
