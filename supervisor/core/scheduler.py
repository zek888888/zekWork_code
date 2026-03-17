"""
任务监工调度器 - 中央控制器，协调所有监控和修复流程
"""

import os
import sys
import time
import signal
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import threading


class SupervisorScheduler:
    """监工调度器 - 中央控制器"""
    
    def __init__(self, db_path: str = "data/supervisor.db"):
        self.db_path = db_path
        self.running = False
        self.threads = []
        
        # 导入子模块
        from .registry import TaskRegistry
        from .heartbeat import HeartbeatMonitor
        from supervisor.alerts.feishu_notifier import AlertManager
        from supervisor.commands.repair_engine import RepairEngine
        from .punishment_engine import PunishmentEngine
        
        self.registry = TaskRegistry(db_path)
        self.heartbeat = HeartbeatMonitor(db_path)
        self.alerts = AlertManager(db_path)
        self.repair = RepairEngine(db_path)
        self.punishment = PunishmentEngine(db_path)
        
        # 注册回调
        self._register_callbacks()
        
        # 信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _register_callbacks(self):
        """注册各种回调"""
        # 心跳检测到漏执行 -> 告警 + 尝试修复
        self.heartbeat.on_missed_task(self._on_task_missed)
        
        # 修复引擎需要人工介入 -> 发送告警
        self.repair.on_manual_repair(self._on_manual_repair_needed)
    
    def _on_task_missed(self, missed_task):
        """处理漏执行的任务"""
        print(f"[Scheduler] 任务漏执行: {missed_task.task_name}")
        
        # 1. 发送告警
        task_dict = {
            'task_id': missed_task.task_id,
            'task_name': missed_task.task_name,
            'scheduled_time': missed_task.scheduled_time.isoformat(),
            'reason': missed_task.reason,
            'critical': missed_task.critical
        }
        self.alerts.alert_task_missed(task_dict)
        
        # 2. 如果是关键任务，立即尝试修复
        if missed_task.critical:
            print(f"[Scheduler] 关键任务漏执行，尝试立即修复...")
            
            # 获取任务定义
            execution = {
                'execution_id': f"{missed_task.task_id}_{missed_task.scheduled_time.strftime('%Y%m%d%H%M%S')}",
                'task_id': missed_task.task_id,
                'error_message': missed_task.reason,
                'stderr': ''
            }
            
            result = self.repair.auto_repair(execution)
            print(f"[Scheduler] 自动修复结果: {result.message}")
    
    def _on_manual_repair_needed(self, execution):
        """需要人工修复"""
        print(f"[Scheduler] 需要人工修复: {execution.get('execution_id')}")
        
        # 获取修复选项
        options = self.repair.get_repair_options(execution)
        option_names = [opt['name'] for opt in options]
        
        # 发送告警
        self.alerts.alert_repair_needed(execution, option_names)
    
    def start(self):
        """启动监工系统"""
        print("=" * 60)
        print("🚀 隔壁老王开始上班了 🧑‍🔧")
        print("=" * 60)
        print(f"数据库: {self.db_path}")
        print(f"时间: {datetime.now().isoformat()}")
        print("-" * 60)
        
        self.running = True
        
        # 1. 启动心跳监控线程
        heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name="HeartbeatMonitor",
            daemon=True
        )
        heartbeat_thread.start()
        self.threads.append(heartbeat_thread)
        
        # 2. 启动执行扫描线程
        scan_thread = threading.Thread(
            target=self._execution_scan_loop,
            name="ExecutionScanner",
            daemon=True
        )
        scan_thread.start()
        self.threads.append(scan_thread)
        
        # 3. 启动自监控线程（老王监督自己）
        self_monitor_thread = threading.Thread(
            target=self._self_monitor_loop,
            name="SelfMonitor",
            daemon=True
        )
        self_monitor_thread.start()
        self.threads.append(self_monitor_thread)
        
        # 4. 启动日报线程
        report_thread = threading.Thread(
            target=self._daily_report_loop,
            name="DailyReporter",
            daemon=True
        )
        report_thread.start()
        self.threads.append(report_thread)
        
        print("[Scheduler] 所有监控线程已启动")
        print("=" * 60)
        
        # 保持主线程运行
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Scheduler] 收到中断信号")
        finally:
            self.stop()
    
    def stop(self):
        """停止监工系统"""
        print("\n[Scheduler] 隔壁老王下班了...")
        self.running = False
        
        self.heartbeat.stop_monitoring()
        
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        print("[Scheduler] 隔壁老王已休息")
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        print(f"\n[老王] 收到信号: {signum}")
        self.stop()
        sys.exit(0)
    
    def _self_monitor_loop(self):
        """隔壁老王的自监控循环 - 老王也要监督自己"""
        from .self_monitor import SelfMonitor
        
        monitor = SelfMonitor(self.db_path)
        
        print("[老王] 自监控已启动")
        
        while self.running:
            try:
                # 记录心跳
                monitor.record_heartbeat()
                
                # 每5分钟做一次全面健康检查
                if datetime.now().minute % 5 == 0:
                    health = monitor.perform_health_check()
                    
                    if not health['is_healthy']:
                        print(f"[老王] 自监控发现问题: {health['issues']}")
                        
                        # 发送告警（老王出问题了）
                        self._alert_supervisor_issue(health['issues'])
                        
                        # 尝试自我修复
                        for issue in health['issues']:
                            if monitor.auto_heal(issue):
                                print("[老王] 自我修复成功")
                                break
                
            except Exception as e:
                print(f"[老王] 自监控异常: {e}")
            
            time.sleep(60)  # 每分钟检查一次
    
    def _alert_supervisor_issue(self, issues: list):
        """老王自己出问题了，必须立即告警"""
        try:
            from supervisor.alerts.openclaw_notifier import OpenclawNotifier
            
            notifier = OpenclawNotifier()
            
            message = f"""🚨 隔壁老王自曝：我出问题了！

⚠️ 老王自检发现异常:
{chr(10).join(['   • ' + i for i in issues])}

🔥 老王说:
   "监督别人的时候，发现自己也不对劲！"
   "正在尝试自我修复..."
   "如果我修不好，看门狗会接手！"

💡 如果持续收到此消息:
   1. 检查老王进程: ps aux | grep supervisor
   2. 检查日志: tail -f logs/supervisor.log
   3. 手动重启: ./stop_supervisor.sh && ./start_supervisor.sh

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 自曝者: 隔壁老王（正在自救）"""
            
            notifier.send_message(message)
            
        except Exception as e:
            print(f"[老王] 自曝告警发送失败: {e}")
            # 如果连告警都发不出去，写入紧急文件
            with open("supervisor_emergency.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - 老王自曝: {issues}\n")
    
    def _heartbeat_loop(self):
        """心跳监控循环"""
        while self.running:
            try:
                # 每分钟检查一次
                self.heartbeat.check_all_tasks()
            except Exception as e:
                print(f"[Scheduler] 心跳检查错误: {e}")
            
            time.sleep(60)
    
    def _execution_scan_loop(self):
        """执行扫描循环 - 检查失败的执行，不听话就惩罚"""
        while self.running:
            try:
                # 检查最近失败的执行
                failures = self.registry.get_recent_failures(hours=1)
                
                for failure in failures:
                    # 检查是否已经告警过
                    if not failure.get('alert_sent'):
                        print(f"[老王] 发现失败任务: {failure.get('name')}")
                        
                        # 发送告警
                        self.alerts.alert_task_failed(failure)
                        
                        # 标记已告警
                        self._mark_alert_sent(failure.get('execution_id'))
                        
                        # 🔥 隔壁老王的惩罚机制
                        self._apply_punishment(failure)
                        
                        # 尝试自动修复
                        if failure.get('retry_count', 0) < 3:
                            result = self.repair.auto_repair(failure)
                            if result.success:
                                self.registry.mark_repaired(
                                    failure.get('execution_id'),
                                    result.method
                                )
                
            except Exception as e:
                print(f"[老王] 执行扫描错误: {e}")
            
            time.sleep(30)  # 每30秒扫描一次
    
    def _apply_punishment(self, failure: Dict[str, Any]):
        """隔壁老王的惩罚机制 - 不干活就收拾你"""
        from supervisor.alerts.openclaw_notifier import OpenclawNotifier
        
        # 根据任务类型判断是哪个API
        api_provider = self._detect_api_provider(failure)
        if not api_provider:
            return
        
        task_id = failure.get('task_id', 'unknown')
        error_message = failure.get('error_message', '')
        
        # 记录失败并获取惩罚决策
        result = self.punishment.record_failure(api_provider, task_id, error_message)
        
        level = result.get('level')
        if level in ['warning', 'suspend', 'switch', 'blacklist']:
            print(f"[老王] 执行惩罚: {api_provider} -> {level}")
            
            notifier = OpenclawNotifier()
            
            if level == 'warning':
                notifier.notify_punishment(
                    'warning',
                    api_provider=api_provider,
                    failure_count=result.get('failure_count'),
                    next_threshold=result.get('next_threshold')
                )
            elif level == 'suspend':
                notifier.notify_punishment(
                    'suspend',
                    api_provider=api_provider,
                    suspended_until=result.get('suspended_until')
                )
            elif level == 'switch':
                notifier.notify_punishment(
                    'switch',
                    old_api=result.get('old_api'),
                    new_api=result.get('new_api'),
                    switch_success=result.get('switch_success')
                )
            elif level == 'blacklist':
                notifier.notify_punishment(
                    'blacklist',
                    api_provider=result.get('old_api'),
                    new_api=result.get('new_api')
                )
    
    def _detect_api_provider(self, failure: Dict[str, Any]) -> str:
        """检测失败涉及哪个API提供商"""
        error_msg = failure.get('error_message', '').lower()
        task_name = failure.get('name', '').lower()
        
        # 根据错误消息判断
        if 'deepseek' in error_msg or 'deepseek' in task_name:
            return 'deepseek'
        elif 'moonshot' in error_msg or 'kimi' in error_msg or 'kimi' in task_name:
            return 'moonshot'
        elif 'binance' in error_msg or 'binance' in task_name:
            return 'binance'
        
        # AI预测任务默认使用DeepSeek
        if 'prediction' in task_name or '预测' in task_name:
            return 'deepseek'
        
        return None
    
    def _daily_report_loop(self):
        """日报循环"""
        from supervisor.core.reporter import DailyReporter
        
        reporter = DailyReporter(self.db_path)
        
        while self.running:
            now = datetime.now()
            
            # 每天早上8点发送日报
            if now.hour == 8 and now.minute == 0:
                try:
                    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
                    report = reporter.generate_daily_report(yesterday)
                    
                    # 使用老王的通知器发送
                    from supervisor.alerts.openclaw_notifier import OpenclawNotifier
                    notifier = OpenclawNotifier()
                    message = reporter.format_report_for_feishu(report)
                    success = notifier.send_message(message)
                    
                    if success:
                        print(f"[老王] 已发送日报: {yesterday}")
                    else:
                        print(f"[老王] 日报发送失败")
                    
                    # 等待一分钟避免重复发送
                    time.sleep(60)
                    
                except Exception as e:
                    print(f"[老王] 发送日报错误: {e}")
            
            time.sleep(30)  # 每30秒检查一次时间
    
    def _mark_alert_sent(self, execution_id: str):
        """标记已发送告警"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE task_executions SET alert_sent = 1 
            WHERE execution_id = ?
        ''', (execution_id,))
        
        conn.commit()
        conn.close()
    
    def get_status(self) -> Dict[str, Any]:
        """获取监工系统状态"""
        now = datetime.now()
        
        # 最近24小时统计
        report = self.registry.get_daily_report(now.strftime('%Y-%m-%d'))
        
        # 待处理失败
        pending_failures = self.registry.get_recent_failures(hours=24)
        pending_failures = [f for f in pending_failures if not f.get('repaired')]
        
        # 修复统计
        repair_stats = self.repair.get_repair_stats(days=7)
        
        return {
            'running': self.running,
            'threads_alive': [t.name for t in self.threads if t.is_alive()],
            'today': {
                'total': report['total_executions'],
                'success': report['success'],
                'failed': report['failed'],
                'pending_failures': len(pending_failures)
            },
            'repair_stats': repair_stats,
            'pending_repairs': [
                {
                    'execution_id': f.get('execution_id'),
                    'name': f.get('name'),
                    'error': f.get('error_message', '')[:100]
                }
                for f in pending_failures[:5]
            ]
        }


def run_supervisor():
    """运行监工系统（入口函数）"""
    scheduler = SupervisorScheduler()
    scheduler.start()


if __name__ == "__main__":
    run_supervisor()
