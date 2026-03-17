"""
飞书告警通知器 - 与Openclaw配置集成
支持多种告警级别和模板
"""

import json
import requests
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"           # 信息
    WARNING = "warning"     # 警告
    ERROR = "error"         # 错误（需要关注）
    CRITICAL = "critical"   # 严重（需要立即处理）


class AlertTemplate:
    """告警模板"""
    
    @staticmethod
    def task_missed(task: Dict[str, Any], context: Dict = None) -> Dict[str, Any]:
        """任务漏执行告警"""
        return {
            "title": f"🚨 任务漏执行 - {task.get('task_name', 'Unknown')}",
            "content": [
                [{"tag": "text", "text": f"任务: {task.get('task_name', 'Unknown')}"}],
                [{"tag": "text", "text": f"计划时间: {task.get('scheduled_time', 'Unknown')}"}],
                [{"tag": "text", "text": f"原因: {task.get('reason', 'Unknown')}"}],
                [{"tag": "text", "text": f"级别: {'🔴 关键任务' if task.get('critical') else '🟡 普通任务'}"}],
            ]
        }
    
    @staticmethod
    def task_failed(execution: Dict[str, Any], context: Dict = None) -> Dict[str, Any]:
        """任务执行失败告警"""
        return {
            "title": f"❌ 任务执行失败 - {execution.get('name', 'Unknown')}",
            "content": [
                [{"tag": "text", "text": f"任务: {execution.get('name', 'Unknown')}"}],
                [{"tag": "text", "text": f"计划时间: {execution.get('planned_time', 'Unknown')}"}],
                [{"tag": "text", "text": f"退出码: {execution.get('exit_code', 'N/A')}"}],
                [{"tag": "text", "text": f"错误: {execution.get('error_message', 'Unknown')[:200]}"}],
            ]
        }
    
    @staticmethod
    def daily_report(report: Dict[str, Any], context: Dict = None) -> Dict[str, Any]:
        """每日报告"""
        lines = [
            [{"tag": "text", "text": f"📊 任务执行日报 ({report.get('date', 'Unknown')})"}],
            [{"tag": "hr"}],
            [{"tag": "text", "text": f"总执行: {report.get('total_executions', 0)} | 成功: {report.get('success', 0)} | 失败: {report.get('failed', 0)} | 超时: {report.get('timeout', 0)}"}],
            [{"tag": "text", "text": f"成功率: {report.get('success_rate', 0):.1f}%"}],
        ]
        
        # 添加失败任务详情
        failed_tasks = [t for t in report.get('tasks', []) if (t.get('failed', 0) + t.get('timeout', 0)) > 0]
        if failed_tasks:
            lines.append([{"tag": "text", "text": "⚠️ 失败任务:"}])
            for task in failed_tasks[:5]:  # 最多显示5个
                lines.append([{"tag": "text", "text": f"  - {task.get('name')}: 失败{task.get('failed', 0)}次"}])
        
        return {
            "title": f"📊 任务执行日报 - {report.get('date', 'Unknown')}",
            "content": lines
        }
    
    @staticmethod
    def repair_request(execution: Dict[str, Any], repair_options: List[str], context: Dict = None) -> Dict[str, Any]:
        """修复请求 - 需要人工介入"""
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(repair_options)])
        
        return {
            "title": f"🔧 需要人工修复 - {execution.get('name', 'Unknown')}",
            "content": [
                [{"tag": "text", "text": f"任务: {execution.get('name', 'Unknown')}"}],
                [{"tag": "text", "text": f"执行ID: {execution.get('execution_id', 'Unknown')}"}],
                [{"tag": "text", "text": f"失败时间: {execution.get('actual_end', 'Unknown')}"}],
                [{"tag": "text", "text": f"错误: {execution.get('error_message', 'Unknown')[:200]}"}],
                [{"tag": "hr"}],
                [{"tag": "text", "text": "可选修复方案:"}],
                [{"tag": "text", "text": options_text}],
                [{"tag": "text", "text": "\n回复: supervisor repair <execution_id> <option>"}],
            ]
        }


class FeishuNotifier:
    """飞书通知器"""
    
    def __init__(self, webhook_url: str = None, 
                 secret: str = None,
                 db_path: str = "data/supervisor.db"):
        self.db_path = db_path
        self.webhook_url = webhook_url
        self.secret = secret
        
        # 如果没有提供webhook，尝试从配置读取
        if not webhook_url:
            self._load_config()
    
    def _load_config(self):
        """从Openclaw配置加载飞书webhook"""
        # 尝试多个可能的配置位置
        config_paths = [
            "config.yaml",
            "/Users/mac/.openclaw/workspace/quant-trading/config.yaml",
            ".env",
            "/Users/mac/.openclaw/workspace/quant-trading/.env"
        ]
        
        for path in config_paths:
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    # 查找飞书webhook配置
                    if 'feishu' in content.lower() or 'webhook' in content.lower():
                        # 简单解析YAML格式
                        for line in content.split('\n'):
                            if 'webhook' in line.lower() and 'http' in line:
                                self.webhook_url = line.split(': ')[-1].strip().strip('"').strip("'")
                                print(f"[FeishuNotifier] 从 {path} 加载webhook")
                                return
            except:
                continue
        
        print("[FeishuNotifier] 警告: 未找到飞书webhook配置")
    
    def send_alert(self, title: str, content: List[List[Dict]], 
                   level: AlertLevel = AlertLevel.ERROR,
                   at_users: List[str] = None) -> bool:
        """发送告警消息"""
        if not self.webhook_url:
            print("[FeishuNotifier] 错误: 未配置webhook")
            return False
        
        # 根据级别添加前缀
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        full_title = f"{level_emoji.get(level, '❌')} {title}"
        
        # 构建消息体
        message = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": full_title,
                        "content": content
                    }
                }
            }
        }
        
        # 添加@用户
        if at_users:
            for user in at_users:
                content.append([{
                    "tag": "at",
                    "user_id": user
                }])
        
        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    print(f"[FeishuNotifier] 消息发送成功: {title}")
                    return True
                else:
                    print(f"[FeishuNotifier] 发送失败: {result}")
                    return False
            else:
                print(f"[FeishuNotifier] HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[FeishuNotifier] 发送异常: {e}")
            return False
    
    def send_template_alert(self, template_name: str, data: Dict[str, Any], 
                           level: AlertLevel = AlertLevel.ERROR,
                           context: Dict = None) -> bool:
        """使用模板发送告警"""
        template_method = getattr(AlertTemplate, template_name, None)
        if not template_method:
            print(f"[FeishuNotifier] 未知模板: {template_name}")
            return False
        
        template_data = template_method(data, context)
        return self.send_alert(
            template_data['title'],
            template_data['content'],
            level
        )
    
    def notify_task_missed(self, task: Dict[str, Any]) -> bool:
        """通知任务漏执行"""
        level = AlertLevel.CRITICAL if task.get('critical') else AlertLevel.ERROR
        return self.send_template_alert('task_missed', task, level)
    
    def notify_task_failed(self, execution: Dict[str, Any]) -> bool:
        """通知任务失败"""
        level = AlertLevel.CRITICAL if execution.get('critical') else AlertLevel.ERROR
        return self.send_template_alert('task_failed', execution, level)
    
    def notify_daily_report(self, report: Dict[str, Any]) -> bool:
        """发送每日报告"""
        # 计算成功率
        total = report.get('total_executions', 0)
        success = report.get('success', 0)
        report['success_rate'] = (success / total * 100) if total > 0 else 0
        
        # 根据成功率决定级别
        if report['success_rate'] >= 95:
            level = AlertLevel.INFO
        elif report['success_rate'] >= 80:
            level = AlertLevel.WARNING
        else:
            level = AlertLevel.ERROR
        
        return self.send_template_alert('daily_report', report, level)
    
    def notify_repair_needed(self, execution: Dict[str, Any], 
                            repair_options: List[str]) -> bool:
        """通知需要人工修复"""
        return self.send_template_alert(
            'repair_request', 
            execution, 
            AlertLevel.CRITICAL,
            context={'repair_options': repair_options}
        )
    
    def record_alert(self, alert_type: str, target: str, 
                    content: str, level: AlertLevel) -> bool:
        """记录告警到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 确保告警记录表存在
        cursor.execute('''
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
        ''')
        
        try:
            cursor.execute('''
                INSERT INTO supervisor_alerts 
                (alert_type, target, content, level, execution_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (alert_type, target, content, level.value, 
                  target if 'execution' in alert_type else None))
            conn.commit()
            return True
        except Exception as e:
            print(f"[FeishuNotifier] 记录告警失败: {e}")
            return False
        finally:
            conn.close()


class AlertManager:
    """告警管理器 - 统一管理所有告警"""
    
    def __init__(self, db_path: str = "data/supervisor.db"):
        self.db_path = db_path
        # 优先使用 Openclaw 通知器
        try:
            from .openclaw_notifier import OpenclawNotifier
            self.notifier = OpenclawNotifier()
            self.use_openclaw = True
            print("[AlertManager] 使用 Openclaw 通知器")
        except Exception as e:
            print(f"[AlertManager] Openclaw 不可用，使用 Webhook: {e}")
            self.notifier = FeishuNotifier(db_path=db_path)
            self.use_openclaw = False
        
        self._alert_cooldown = {}  # 告警冷却，避免重复告警
    
    def should_alert(self, key: str, cooldown_minutes: int = 30) -> bool:
        """检查是否应该发送告警（避免重复）"""
        now = datetime.now()
        last_alert = self._alert_cooldown.get(key)
        
        if last_alert and (now - last_alert).seconds < cooldown_minutes * 60:
            return False
        
        self._alert_cooldown[key] = now
        return True
    
    def alert_task_missed(self, task: Dict[str, Any]) -> bool:
        """任务漏执行告警"""
        key = f"missed_{task.get('task_id')}"
        
        # 关键任务立即告警，普通任务有冷却
        cooldown = 5 if task.get('critical') else 30
        
        if not self.should_alert(key, cooldown):
            return False
        
        success = self.notifier.notify_task_missed(task)
        
        # 记录到数据库
        if success and not self.use_openclaw:
            self.notifier.record_alert(
                'task_missed',
                task.get('task_id'),
                f"任务 {task.get('task_name')} 漏执行",
                AlertLevel.CRITICAL if task.get('critical') else AlertLevel.ERROR
            )
        
        return success
    
    def alert_task_failed(self, execution: Dict[str, Any]) -> bool:
        """任务失败告警"""
        key = f"failed_{execution.get('execution_id')}"
        
        if not self.should_alert(key, 15):  # 15分钟冷却
            return False
        
        success = self.notifier.notify_task_failed(execution)
        
        if success and not self.use_openclaw:
            self.notifier.record_alert(
                'task_failed',
                execution.get('execution_id'),
                f"任务 {execution.get('name')} 执行失败",
                AlertLevel.CRITICAL if execution.get('critical') else AlertLevel.ERROR
            )
        
        return success
    
    def alert_repair_needed(self, execution: Dict[str, Any], 
                           repair_options: List[str]) -> bool:
        """需要人工修复告警"""
        return self.notifier.notify_repair_needed(execution, repair_options)
    
    def send_daily_report(self, report: Dict[str, Any]) -> bool:
        """发送每日报告"""
        return self.notifier.notify_daily_report(report)


if __name__ == "__main__":
    # 测试
    notifier = FeishuNotifier()
    
    # 测试发送
    test_task = {
        'task_name': '神算子（AI预测）',
        'scheduled_time': '2024-01-01 12:00:00',
        'reason': '未检测到执行记录',
        'critical': True
    }
    
    notifier.notify_task_missed(test_task)
