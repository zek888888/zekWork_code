#!/usr/bin/env python3
"""
隔壁老王的自监控模块 - 老王也要被监督！
如果老王自己出问题了，必须立即发现、立即修复、立即告警
"""

import os
import sys
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')

# 尝试导入psutil，如果没有就使用备用方案
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("[老王] 警告: psutil未安装，使用备用监控方案")


class SelfMonitor:
    """
    隔壁老王的自监控 - 监督者也要被监督
    """
    
    def __init__(self, db_path: str = "data/supervisor.db"):
        self.db_path = db_path
        self.supervisor_pid_file = "supervisor.pid"
        self._init_self_monitor_table()
    
    def _init_self_monitor_table(self):
        """初始化自监控表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 老王自己的心跳表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS supervisor_heartbeat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                pid INTEGER,
                cpu_percent REAL,
                memory_mb REAL,
                status TEXT,
                next_check TEXT,
                alert_sent BOOLEAN DEFAULT 0
            )
        ''')
        
        # 老王的健康检查日志
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS supervisor_health_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_time TEXT DEFAULT CURRENT_TIMESTAMP,
                is_healthy BOOLEAN,
                issues TEXT,
                action_taken TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def is_supervisor_running(self) -> tuple:
        """检查老王自己是否还在运行"""
        try:
            if not os.path.exists(self.supervisor_pid_file):
                return False, "PID文件不存在，老王可能挂了"
            
            with open(self.supervisor_pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            if HAS_PSUTIL:
                if not psutil.pid_exists(pid):
                    return False, f"老王进程 {pid} 不存在，可能已崩溃"
                
                process = psutil.Process(pid)
                
                # 检查进程状态
                if process.status() == psutil.STATUS_ZOMBIE:
                    return False, f"老王进程 {pid} 已成僵尸进程"
                
                # 检查CPU和内存
                cpu_percent = process.cpu_percent(interval=1)
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                if cpu_percent > 90:
                    return False, f"老王CPU占用过高 ({cpu_percent}%)，可能卡死"
                
                if memory_mb > 500:
                    return False, f"老王内存占用过高 ({memory_mb:.1f}MB)，可能内存泄漏"
                
                return True, {
                    'pid': pid,
                    'cpu': cpu_percent,
                    'memory_mb': memory_mb,
                    'status': process.status()
                }
            else:
                # 备用方案：使用ps命令
                result = subprocess.run(
                    ['ps', '-p', str(pid), '-o', 'pid='],
                    capture_output=True
                )
                if result.returncode != 0:
                    return False, f"老王进程 {pid} 不存在，可能已崩溃"
                
                return True, {'pid': pid, 'cpu': 0, 'memory_mb': 0, 'status': 'unknown'}
            
        except Exception as e:
            return False, f"检查老王状态时出错: {str(e)}"
    
    def check_last_heartbeat(self) -> tuple:
        """检查老王最近是否有心跳"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp FROM supervisor_heartbeat
            ORDER BY timestamp DESC LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return False, "没有老王的心跳记录，可能从未启动"
        
        last_heartbeat = datetime.fromisoformat(row[0])
        now = datetime.now()
        
        # 如果超过5分钟没有心跳，说明老王卡死了
        if now - last_heartbeat > timedelta(minutes=5):
            return False, f"老王已经 {int((now - last_heartbeat).total_seconds() / 60)} 分钟没有心跳，可能卡死"
        
        return True, f"老王最近心跳: {last_heartbeat.strftime('%H:%M:%S')}"
    
    def record_heartbeat(self) -> bool:
        """老王记录自己的心跳"""
        try:
            # 获取当前进程信息
            if HAS_PSUTIL:
                process = psutil.Process()
                pid = process.pid
                cpu = process.cpu_percent(interval=0.1)
                memory = process.memory_info().rss / 1024 / 1024
            else:
                pid = os.getpid()
                cpu = 0
                memory = 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            next_check = (datetime.now() + timedelta(minutes=1)).isoformat()
            
            cursor.execute('''
                INSERT INTO supervisor_heartbeat 
                (pid, cpu_percent, memory_mb, status, next_check)
                VALUES (?, ?, ?, ?, ?)
            ''', (pid, cpu, memory, 'running', next_check))
            
            # 清理旧记录（只保留最近24小时）
            cursor.execute('''
                DELETE FROM supervisor_heartbeat
                WHERE timestamp < datetime('now', '-24 hours')
            ''')
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"[老王] 记录心跳失败: {e}")
            return False
    
    def check_database_health(self) -> tuple:
        """检查数据库是否正常"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查关键表是否存在
            tables = ['task_definitions', 'task_executions', 'supervisor_heartbeat']
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    return False, f"关键表 {table} 不存在"
            
            # 检查数据库大小
            cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0] / 1024 / 1024  # MB
            
            if db_size > 100:
                return False, f"数据库过大 ({db_size:.1f}MB)，可能影响性能"
            
            conn.close()
            return True, f"数据库健康，大小: {db_size:.1f}MB"
            
        except Exception as e:
            return False, f"数据库检查失败: {str(e)}"
    
    def check_disk_space(self) -> tuple:
        """检查磁盘空间"""
        try:
            stat = os.statvfs('/')
            free_gb = (stat.f_bavail * stat.f_frsize) / 1024 / 1024 / 1024
            total_gb = (stat.f_blocks * stat.f_frsize) / 1024 / 1024 / 1024
            used_percent = (1 - stat.f_bavail / stat.f_blocks) * 100
            
            if free_gb < 1:
                return False, f"磁盘空间严重不足！仅剩 {free_gb:.2f}GB"
            
            if used_percent > 90:
                return False, f"磁盘使用率过高 ({used_percent:.1f}%)"
            
            return True, f"磁盘空间充足: {free_gb:.1f}GB 可用"
            
        except Exception as e:
            return False, f"磁盘检查失败: {str(e)}"
    
    def perform_health_check(self) -> Dict[str, Any]:
        """执行全面健康检查"""
        checks = {
            'process': self.is_supervisor_running(),
            'heartbeat': self.check_last_heartbeat(),
            'database': self.check_database_health(),
            'disk': self.check_disk_space()
        }
        
        all_healthy = all(result[0] for result in checks.values())
        
        issues = []
        for check_name, (is_healthy, message) in checks.items():
            if not is_healthy:
                issues.append(f"{check_name}: {message}")
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'is_healthy': all_healthy,
            'checks': {name: {'healthy': r[0], 'message': r[1]} for name, r in checks.items()},
            'issues': issues
        }
        
        # 记录健康日志
        self._log_health_check(all_healthy, issues)
        
        return health_report
    
    def _log_health_check(self, is_healthy: bool, issues: List[str]):
        """记录健康检查日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO supervisor_health_log 
            (is_healthy, issues, action_taken)
            VALUES (?, ?, ?)
        ''', (
            is_healthy,
            '\n'.join(issues) if issues else '无问题',
            '已发送告警' if issues else '正常运行'
        ))
        
        conn.commit()
        conn.close()
    
    def auto_heal(self, issue: str) -> bool:
        """老王自我修复"""
        print(f"[老王] 尝试自我修复: {issue}")
        
        if "PID文件不存在" in issue or "进程不存在" in issue:
            # 老王挂了，尝试重启
            return self._restart_supervisor()
        
        elif "僵尸进程" in issue:
            # 清理僵尸进程并重启
            self._kill_zombie()
            return self._restart_supervisor()
        
        elif "没有心跳" in issue:
            # 老王卡死了，强制重启
            return self._restart_supervisor()
        
        return False
    
    def _restart_supervisor(self) -> bool:
        """重启隔壁老王"""
        try:
            print("[老王] 正在尝试重启...")
            
            # 先停止可能存在的残留进程
            if os.path.exists(self.supervisor_pid_file):
                try:
                    with open(self.supervisor_pid_file, 'r') as f:
                        old_pid = int(f.read().strip())
                    os.kill(old_pid, 9)
                except:
                    pass
                os.remove(self.supervisor_pid_file)
            
            # 启动新的老王
            subprocess.Popen(
                ['/usr/local/bin/python3', 'supervisor/core/scheduler.py'],
                cwd='/Users/mac/.openclaw/workspace/quant-trading',
                stdout=open('logs/supervisor.log', 'a'),
                stderr=subprocess.STDOUT
            )
            
            print("[老王] 已重启")
            return True
            
        except Exception as e:
            print(f"[老王] 重启失败: {e}")
            return False
    
    def _kill_zombie(self):
        """清理僵尸进程"""
        if not HAS_PSUTIL:
            return
            
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                if proc.info['status'] == psutil.STATUS_ZOMBIE and 'python' in proc.info['name']:
                    try:
                        os.kill(proc.info['pid'], 9)
                        print(f"[老王] 已清理僵尸进程 {proc.info['pid']}")
                    except:
                        pass
        except:
            pass
    
    def get_self_status(self) -> Dict[str, Any]:
        """获取老王自己的状态报告"""
        health = self.perform_health_check()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 最近24小时的心跳统计
        cursor.execute('''
            SELECT COUNT(*), AVG(cpu_percent), AVG(memory_mb)
            FROM supervisor_heartbeat
            WHERE timestamp > datetime('now', '-24 hours')
        ''')
        
        row = cursor.fetchone()
        
        # 最近的健康问题
        cursor.execute('''
            SELECT check_time, issues FROM supervisor_health_log
            WHERE is_healthy = 0
            ORDER BY check_time DESC
            LIMIT 5
        ''')
        
        recent_issues = cursor.fetchall()
        conn.close()
        
        return {
            'health': health,
            'heartbeat_24h': {
                'count': row[0] or 0,
                'avg_cpu': round(row[1], 2) if row[1] else 0,
                'avg_memory_mb': round(row[2], 2) if row[2] else 0
            },
            'recent_issues': [
                {'time': i[0], 'issue': i[1]} for i in recent_issues
            ]
        }


class Watchdog:
    """
    看门狗 - 监督隔壁老王的独立进程
    如果老王挂了，看门狗负责重启并告警
    """
    
    def __init__(self):
        self.monitor = SelfMonitor()
    
    def run(self):
        """看门狗主循环"""
        print("🐕 看门狗已启动，正在监督隔壁老王...")
        
        while True:
            try:
                # 检查老王是否健康
                health = self.monitor.perform_health_check()
                
                if not health['is_healthy']:
                    print(f"🚨 看门狗发现老王异常: {health['issues']}")
                    
                    # 发送告警（双重保险）
                    self._send_critical_alert(health['issues'])
                    
                    # 尝试自我修复
                    for issue in health['issues']:
                        if self.monitor.auto_heal(issue):
                            print("✅ 看门狗已成功修复老王")
                            break
                    else:
                        print("❌ 看门狗无法修复，需要人工介入！")
                        self._send_emergency_alert()
                
                else:
                    print(f"✅ 看门狗检查: 老王健康 ({datetime.now().strftime('%H:%M:%S')})")
                
                # 每分钟检查一次
                import time
                time.sleep(60)
                
            except Exception as e:
                print(f"[看门狗] 异常: {e}")
                time.sleep(60)
    
    def _send_critical_alert(self, issues: List[str]):
        """发送严重告警 - 双重保险"""
        try:
            from supervisor.alerts.openclaw_notifier import OpenclawNotifier
            
            notifier = OpenclawNotifier()
            
            message = f"""🚨 看门狗告警：隔壁老王出问题了！

⚠️ 检测到异常:
{chr(10).join(['   • ' + i for i in issues])}

🔥 看门狗正在尝试修复...

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🐕 监督者: 看门狗"""
            
            # 尝试发送，失败不抛异常
            try:
                notifier.send_message(message)
            except:
                pass
            
        except Exception as e:
            print(f"[看门狗] 发送告警失败: {e}")
    
    def _send_emergency_alert(self):
        """发送紧急告警 - 老王和看门狗都救不了"""
        try:
            # 如果Openclaw也失败了，尝试写入文件
            emergency_file = "EMERGENCY_ALERT.txt"
            with open(emergency_file, 'w') as f:
                f.write(f"""🚨 紧急告警

时间: {datetime.now().isoformat()}
问题: 隔壁老王和看门狗都挂了！

需要立即人工处理！
请检查:
1. 服务器是否运行
2. 磁盘空间是否充足
3. 数据库是否正常

启动命令:
./start_supervisor.sh
""")
            print(f"[看门狗] 已写入紧急告警文件: {emergency_file}")
            
        except:
            pass


if __name__ == "__main__":
    # 测试自监控
    monitor = SelfMonitor()
    
    print("=" * 60)
    print("🧑‍🔧 隔壁老王的自监控测试")
    print("=" * 60)
    print()
    
    # 记录一次心跳
    monitor.record_heartbeat()
    print("✅ 已记录心跳")
    
    # 健康检查
    health = monitor.perform_health_check()
    print()
    print("健康检查结果:")
    for check, result in health['checks'].items():
        status = "✅" if result['healthy'] else "❌"
        print(f"  {status} {check}: {result['message']}")
    
    print()
    print("=" * 60)
