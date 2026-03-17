"""
修复引擎 - 自动修复失败的定时任务，支持人工介入
"""

import os
import re
import sqlite3
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import threading
import time


class RepairStrategy(Enum):
    """修复策略"""
    RETRY = "retry"                     # 重试执行
    RETRY_WITH_DELAY = "retry_delay"    # 延迟重试
    FIX_PATH = "fix_path"               # 修复路径
    FIX_PERMISSION = "fix_permission"   # 修复权限
    RESTART_SERVICE = "restart"         # 重启服务
    MANUAL = "manual"                   # 需要人工介入


class RepairResult:
    """修复结果"""
    def __init__(self, success: bool, method: str, message: str, 
                 execution_time: float = 0):
        self.success = success
        self.method = method
        self.message = message
        self.execution_time = execution_time
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'method': self.method,
            'message': self.message,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp
        }


class RepairEngine:
    """修复引擎"""
    
    # 常见错误模式及自动修复策略
    ERROR_PATTERNS = {
        r'getcwd.*No such file or directory': {
            'strategy': RepairStrategy.FIX_PATH,
            'description': '工作目录错误'
        },
        r'No such file or directory.*python': {
            'strategy': RepairStrategy.FIX_PATH,
            'description': 'Python路径错误'
        },
        r'Permission denied': {
            'strategy': RepairStrategy.FIX_PERMISSION,
            'description': '权限不足'
        },
        r'Timeout': {
            'strategy': RepairStrategy.RETRY_WITH_DELAY,
            'description': '执行超时'
        },
        r'Connection.*refused|Connection.*reset': {
            'strategy': RepairStrategy.RETRY_WITH_DELAY,
            'description': '连接错误'
        },
        r'ModuleNotFoundError|ImportError': {
            'strategy': RepairStrategy.MANUAL,
            'description': '依赖缺失'
        },
        r'SyntaxError': {
            'strategy': RepairStrategy.MANUAL,
            'description': '代码语法错误'
        }
    }
    
    def __init__(self, db_path: str = "data/supervisor.db"):
        self.db_path = db_path
        self.repair_history = []  # 修复历史
        self._manual_callbacks = []  # 人工介入回调
        self._init_repair_log()
    
    def _init_repair_log(self):
        """初始化修复日志表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS supervisor_repairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                error_pattern TEXT,
                strategy TEXT,
                attempted_fixes TEXT,  -- JSON
                final_result TEXT,
                success BOOLEAN,
                repair_time TEXT DEFAULT CURRENT_TIMESTAMP,
                manual_intervention BOOLEAN DEFAULT 0,
                manual_command TEXT,
                executor TEXT DEFAULT 'auto'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def analyze_error(self, error_message: str, stderr: str = "") -> Dict[str, Any]:
        """分析错误类型"""
        full_error = f"{error_message}\n{stderr}"
        
        for pattern, info in self.ERROR_PATTERNS.items():
            if re.search(pattern, full_error, re.IGNORECASE):
                return {
                    'matched': True,
                    'pattern': pattern,
                    'strategy': info['strategy'],
                    'description': info['description']
                }
        
        return {
            'matched': False,
            'pattern': None,
            'strategy': RepairStrategy.MANUAL,
            'description': '未知错误类型，需要人工分析'
        }
    
    def get_repair_options(self, execution: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取可用的修复选项"""
        error_analysis = self.analyze_error(
            execution.get('error_message', ''),
            execution.get('stderr', '')
        )
        
        options = []
        strategy = error_analysis['strategy']
        
        # 基础选项
        options.append({
            'id': 'retry',
            'name': '立即重试',
            'description': '直接重新执行该任务',
            'auto': True,
            'action': lambda: self._retry_execution(execution)
        })
        
        if strategy == RepairStrategy.FIX_PATH:
            options.append({
                'id': 'fix_path',
                'name': '修复工作目录',
                'description': '使用绝对路径重新执行',
                'auto': True,
                'action': lambda: self._fix_path_and_retry(execution)
            })
        
        if strategy == RepairStrategy.FIX_PERMISSION:
            options.append({
                'id': 'fix_permission',
                'name': '修复权限',
                'description': 'chmod +x 并重新执行',
                'auto': True,
                'action': lambda: self._fix_permission_and_retry(execution)
            })
        
        if strategy == RepairStrategy.RETRY_WITH_DELAY:
            options.append({
                'id': 'retry_delay',
                'name': '延迟重试',
                'description': '30秒后重试',
                'auto': True,
                'action': lambda: self._retry_with_delay(execution, 30)
            })
        
        # 总是添加人工选项
        options.append({
            'id': 'manual',
            'name': '人工修复',
            'description': '通知管理员手动处理',
            'auto': False,
            'action': lambda: self._request_manual_repair(execution)
        })
        
        return options
    
    def auto_repair(self, execution: Dict[str, Any]) -> RepairResult:
        """尝试自动修复"""
        execution_id = execution.get('execution_id')
        task_id = execution.get('task_id')
        
        print(f"[RepairEngine] 尝试自动修复: {execution_id}")
        
        # 分析错误
        analysis = self.analyze_error(
            execution.get('error_message', ''),
            execution.get('stderr', '')
        )
        
        strategy = analysis['strategy']
        attempted = []
        
        start_time = time.time()
        
        try:
            if strategy == RepairStrategy.RETRY:
                attempted.append('retry')
                result = self._retry_execution(execution)
                
            elif strategy == RepairStrategy.FIX_PATH:
                attempted.append('fix_path')
                result = self._fix_path_and_retry(execution)
                
            elif strategy == RepairStrategy.FIX_PERMISSION:
                attempted.append('fix_permission')
                result = self._fix_permission_and_retry(execution)
                
            elif strategy == RepairStrategy.RETRY_WITH_DELAY:
                attempted.append('retry_delay')
                result = self._retry_with_delay(execution, 30)
                
            elif strategy == RepairStrategy.MANUAL:
                # 需要人工介入
                self._request_manual_repair(execution)
                return RepairResult(
                    success=False,
                    method="manual_request",
                    message=f"错误类型: {analysis['description']}，已通知管理员",
                    execution_time=time.time() - start_time
                )
            else:
                result = self._retry_execution(execution)
            
            execution_time = time.time() - start_time
            
            # 记录修复结果
            self._log_repair(execution_id, task_id, analysis, attempted, 
                           result, execution_time)
            
            return RepairResult(
                success=result,
                method=strategy.value,
                message="修复成功" if result else "修复失败，需要人工介入",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return RepairResult(
                success=False,
                method=strategy.value,
                message=f"修复异常: {str(e)}",
                execution_time=execution_time
            )
    
    def _retry_execution(self, execution: Dict[str, Any]) -> bool:
        """重试执行"""
        from supervisor.core.registry import TaskRegistry
        
        registry = TaskRegistry(self.db_path)
        task = registry.get_task(execution.get('task_id'))
        
        if not task:
            return False
        
        try:
            result = subprocess.run(
                task.command,
                shell=True,
                cwd=task.working_dir,
                capture_output=True,
                text=True,
                timeout=task.timeout_seconds
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"[RepairEngine] 重试失败: {e}")
            return False
    
    def _fix_path_and_retry(self, execution: Dict[str, Any]) -> bool:
        """修复路径并重试"""
        from supervisor.core.registry import TaskRegistry
        
        registry = TaskRegistry(self.db_path)
        task = registry.get_task(execution.get('task_id'))
        
        if not task:
            return False
        
        # 修改命令使用绝对路径
        fixed_command = task.command
        
        # 替换相对路径为绝对路径
        if 'cd ~/' in fixed_command or 'cd .' in fixed_command:
            fixed_command = fixed_command.replace('~/', '/Users/mac/')
        
        # 确保python3使用完整路径
        if 'python3 ' in fixed_command and not '/python3' in fixed_command:
            fixed_command = fixed_command.replace('python3 ', '/usr/local/bin/python3 ')
        
        print(f"[RepairEngine] 修复后命令: {fixed_command[:100]}...")
        
        try:
            result = subprocess.run(
                fixed_command,
                shell=True,
                cwd=task.working_dir,
                capture_output=True,
                text=True,
                timeout=task.timeout_seconds
            )
            
            # 如果成功，更新任务定义
            if result.returncode == 0:
                task.command = fixed_command
                registry.register_task(task)
                print(f"[RepairEngine] 已更新任务命令为绝对路径")
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"[RepairEngine] 路径修复失败: {e}")
            return False
    
    def _fix_permission_and_retry(self, execution: Dict[str, Any]) -> bool:
        """修复权限并重试"""
        command = execution.get('command', '')
        
        # 提取脚本路径
        script_match = re.search(r'python3\s+(\S+\.py)', command)
        if script_match:
            script_path = script_match.group(1)
            try:
                os.chmod(script_path, 0o755)
                print(f"[RepairEngine] 已修复权限: {script_path}")
            except Exception as e:
                print(f"[RepairEngine] 权限修复失败: {e}")
        
        # 然后重试
        return self._retry_execution(execution)
    
    def _retry_with_delay(self, execution: Dict[str, Any], delay: int) -> bool:
        """延迟重试"""
        print(f"[RepairEngine] {delay}秒后重试...")
        time.sleep(delay)
        return self._retry_execution(execution)
    
    def _request_manual_repair(self, execution: Dict[str, Any]):
        """请求人工修复"""
        print(f"[RepairEngine] 请求人工修复: {execution.get('execution_id')}")
        
        # 触发所有注册的回调
        for callback in self._manual_callbacks:
            try:
                callback(execution)
            except Exception as e:
                print(f"[RepairEngine] 回调错误: {e}")
    
    def on_manual_repair(self, callback: Callable):
        """注册人工修复回调"""
        self._manual_callbacks.append(callback)
    
    def manual_repair(self, execution_id: str, command: str, 
                     executor: str = "admin") -> RepairResult:
        """人工执行修复命令"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取执行记录
        cursor.execute('''
            SELECT * FROM task_executions WHERE execution_id = ?
        ''', (execution_id,))
        
        row = cursor.fetchone()
        if not row:
            return RepairResult(False, "manual", "执行记录不存在")
        
        # 执行人工命令
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            success = result.returncode == 0
            
            # 记录人工修复
            cursor.execute('''
                INSERT INTO supervisor_repairs 
                (execution_id, task_id, error_pattern, strategy, 
                 attempted_fixes, final_result, success, manual_intervention, 
                 manual_command, executor)
                VALUES (?, ?, ?, 'manual', ?, ?, ?, 1, ?, ?)
            ''', (
                execution_id, row[1], 'manual_repair',
                json.dumps(['manual']),
                'success' if success else 'failed',
                success,
                command,
                executor
            ))
            
            # 标记为已修复
            if success:
                cursor.execute('''
                    UPDATE task_executions 
                    SET repaired = 1, repair_method = 'manual'
                    WHERE execution_id = ?
                ''', (execution_id,))
            
            conn.commit()
            
            execution_time = time.time() - start_time
            
            return RepairResult(
                success=success,
                method="manual",
                message=result.stdout if success else result.stderr,
                execution_time=execution_time
            )
            
        except Exception as e:
            return RepairResult(
                success=False,
                method="manual",
                message=f"执行异常: {str(e)}"
            )
        finally:
            conn.close()
    
    def _log_repair(self, execution_id: str, task_id: str, 
                   analysis: Dict, attempted: List[str],
                   result: bool, execution_time: float):
        """记录修复日志"""
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO supervisor_repairs 
                (execution_id, task_id, error_pattern, strategy, 
                 attempted_fixes, final_result, success, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution_id,
                task_id,
                analysis.get('pattern'),
                analysis.get('strategy').value if analysis.get('strategy') else None,
                json.dumps(attempted),
                'success' if result else 'failed',
                result,
                execution_time
            ))
            
            conn.commit()
        except Exception as e:
            print(f"[RepairEngine] 记录修复日志失败: {e}")
        finally:
            conn.close()
    
    def get_repair_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取修复统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN manual_intervention = 1 THEN 1 ELSE 0 END) as manual
            FROM supervisor_repairs
            WHERE repair_time > datetime('now', '-{} days')
        '''.format(days))
        
        row = cursor.fetchone()
        conn.close()
        
        total = row[0] or 0
        success = row[1] or 0
        manual = row[2] or 0
        
        return {
            'total_repairs': total,
            'auto_success': success - manual,
            'manual_repairs': manual,
            'auto_success_rate': ((success - manual) / (total - manual) * 100) if (total - manual) > 0 else 0
        }


if __name__ == "__main__":
    engine = RepairEngine()
    
    # 测试错误分析
    test_errors = [
        "getcwd: error retrieving current directory",
        "Permission denied: ./script.py",
        "ModuleNotFoundError: No module named 'requests'",
        "Connection refused"
    ]
    
    for error in test_errors:
        result = engine.analyze_error(error)
        print(f"错误: {error[:50]}... -> 策略: {result['strategy'].value}")
