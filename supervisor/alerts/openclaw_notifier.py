#!/usr/bin/env python3
"""
Openclaw 告警通知器 - 通过 Openclaw CLI 发送飞书消息
"""

import subprocess
import shlex
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class OpenclawNotifier:
    """Openclaw 通知器 - 通过 openclaw message send 发送飞书消息"""
    
    FEISHU_USER_ID = "ou_dc38103cbe80263557de2b373fb5242d"
    OPENCLAW_BIN = "/Users/mac/.nvm/versions/node/v24.14.0/bin/openclaw"
    
    def __init__(self):
        pass
    
    def send_message(self, message: str) -> bool:
        """通过 Openclaw 发送飞书消息 - 带双重保险"""
        try:
            cmd = [
                self.OPENCLAW_BIN,
                'message', 'send',
                '--channel', 'feishu',
                '--target', self.FEISHU_USER_ID,
                '--message', message
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 检查输出中是否有成功标识
            if 'Sent via Feishu' in result.stderr or result.returncode == 0:
                return True
            else:
                print(f"[老王] Openclaw发送失败: {result.stderr}")
                # 备用方案：写入紧急文件
                return self._fallback_alert(message)
                
        except Exception as e:
            print(f"[老王] Openclaw发送异常: {e}")
            # 备用方案：写入紧急文件
            return self._fallback_alert(message)
    
    def _fallback_alert(self, message: str) -> bool:
        """备用告警方案 - 当Openclaw失败时写入文件"""
        try:
            from datetime import datetime
            
            fallback_file = "/Users/mac/.openclaw/workspace/quant-trading/FALLBACK_ALERTS.txt"
            
            with open(fallback_file, 'a', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("状态: Openclaw发送失败，使用备用方案\n")
                f.write("-" * 60 + "\n")
                f.write(message)
                f.write("\n\n")
            
            print(f"[老王] 已写入备用告警文件: {fallback_file}")
            return True
            
        except Exception as e:
            print(f"[老王] 备用告警也失败了: {e}")
            return False
    
    def notify_task_missed(self, task: Dict[str, Any]) -> bool:
        """任务漏执行告警"""
        emoji = "🚨" if task.get('critical') else "⚠️"
        level = "关键任务" if task.get('critical') else "普通任务"
        
        message = f"""{emoji} 任务漏执行 - {task.get('task_name', 'Unknown')}

📋 任务: {task.get('task_name', 'Unknown')}
⏰ 计划时间: {task.get('scheduled_time', 'Unknown')}
❌ 原因: {task.get('reason', '未检测到执行记录')}
🔴 级别: {level}

🔧 监工系统正在尝试自动修复...
   1. 检查工作目录...
   2. 尝试使用绝对路径重试...

💡 如果持续收到此消息，请检查:
   • cron服务: crontab -l
   • 脚本路径是否正确
   • 使用CLI: python3 supervisor_cli.py repair

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 发送者: 隔壁老王"""
        
        return self.send_message(message)
    
    def notify_task_failed(self, execution: Dict[str, Any]) -> bool:
        """任务执行失败告警"""
        emoji = "🚨" if execution.get('critical') else "❌"
        
        error = execution.get('error_message', 'Unknown')[:150]
        
        message = f"""{emoji} 任务执行失败 - {execution.get('name', 'Unknown')}

📋 任务: {execution.get('name', 'Unknown')}
⏰ 计划时间: {execution.get('planned_time', 'Unknown')}
📤 退出码: {execution.get('exit_code', 'N/A')}
❌ 错误: {error}

🔧 监工系统已尝试自动修复 {execution.get('retry_count', 0)} 次

💻 查看详情: http://localhost:5001/supervisor

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 发送者: 隔壁老王"""
        
        return self.send_message(message)
    
    def notify_daily_report(self, report: Dict[str, Any]) -> bool:
        """每日报告"""
        date = report.get('date', datetime.now().strftime('%Y-%m-%d'))
        total = report.get('total_executions', 0)
        success = report.get('success', 0)
        failed = report.get('failed', 0)
        timeout = report.get('timeout', 0)
        
        success_rate = (success / total * 100) if total > 0 else 0
        
        # 根据成功率选择表情
        if success_rate >= 95:
            emoji = "✅"
        elif success_rate >= 80:
            emoji = "⚠️"
        else:
            emoji = "❌"
        
        # 失败任务列表
        failed_tasks = [t for t in report.get('tasks', []) 
                       if (t.get('failed', 0) + t.get('timeout', 0)) > 0]
        
        failed_text = ""
        if failed_tasks:
            failed_text = "\n⚠️ 需要关注的任务:\n"
            for task in failed_tasks[:3]:
                failed_text += f"   • {task.get('name')}: 失败{task.get('failed', 0)}次\n"
        
        message = f"""📊 任务执行日报 - {date}

📈 执行统计:
   • 总执行: {total}次
   • 成功: {success}次 ✅
   • 失败: {failed}次 ❌
   • 超时: {timeout}次 ⏱
   • 成功率: {success_rate:.1f}% {emoji}
{failed_text}
💻 查看详情: http://localhost:5001/supervisor

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 发送者: 隔壁老王"""
        
        return self.send_message(message)
    
    def notify_repair_needed(self, execution: Dict[str, Any], 
                             repair_options: List[str]) -> bool:
        """需要人工修复告警"""
        error = execution.get('error_message', 'Unknown')[:150]
        
        options_text = "\n".join([f"   {i+1}. {opt}" for i, opt in enumerate(repair_options[:3])])
        
        message = f"""🔧 需要人工修复 - {execution.get('name', 'Unknown')}

❌ 监工系统无法自动修复此问题

📋 任务: {execution.get('name', 'Unknown')}
⏰ 失败时间: {execution.get('actual_end', '刚刚')}
💥 错误: {error}

🔨 可选修复方案:
{options_text}

💻 执行命令:
   python3 supervisor_cli.py repair {execution.get('execution_id')} --auto

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 发送者: 隔壁老王"""
        
        return self.send_message(message)
    
    def notify_system_startup(self) -> bool:
        """系统启动通知 - 带责任承诺"""
        message = f"""🧑‍🔧 隔壁老王开始上班了（带责任承诺）

✅ 监工系统已启动
📊 Web控制台: http://localhost:5001/supervisor

👷 监控任务:
   • 神算子（AI预测）(每15分钟) - 失败就惩罚API
   • 验证历史预测 (每2小时)
   • GitHub提交检查 (每天12:00+22:00)

🔥 老王的承诺:
   "我既监督别人，也监督自己！"
   "如果我出问题了，看门狗会立即发现并告警！"
   "你得不到结果也收不到告警，那是我的失职！"

🐕 监督机制:
   • 老王每分钟自我健康检查
   • 看门狗每分钟检查老王是否活着
   • 告警失败自动写入备用文件
   • 双重保险，确保告警必达

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 发送者: 隔壁老王（说到做到）"""
        
        return self.send_message(message)
    
    def notify_system_shutdown(self) -> bool:
        """系统停止通知"""
        message = f"""🛑 隔壁老王已休息

⚠️ 隔壁老王已关闭，定时任务将不再被监控

💡 如需重启:
   ./start_supervisor.sh

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 发送者: 隔壁老王"""
        
        return self.send_message(message)
    
    def notify_punishment(self, level: str, **kwargs) -> bool:
        """发送惩罚通知"""
        from .punishment_notifier import PunishmentNotifier
        
        notifier = PunishmentNotifier()
        
        if level == 'warning':
            message = notifier.get_warning_message(
                kwargs.get('api_provider'),
                kwargs.get('failure_count'),
                kwargs.get('next_threshold')
            )
        elif level == 'suspend':
            message = notifier.get_suspend_message(
                kwargs.get('api_provider'),
                kwargs.get('suspended_until')
            )
        elif level == 'switch':
            message = notifier.get_switch_message(
                kwargs.get('old_api'),
                kwargs.get('new_api'),
                kwargs.get('switch_success')
            )
        elif level == 'blacklist':
            message = notifier.get_blacklist_message(
                kwargs.get('api_provider'),
                kwargs.get('new_api')
            )
        else:
            return False
        
        return self.send_message(message)


# 全局通知器实例
_notifier = None

def get_notifier() -> OpenclawNotifier:
    """获取通知器实例（单例）"""
    global _notifier
    if _notifier is None:
        _notifier = OpenclawNotifier()
    return _notifier


if __name__ == "__main__":
    # 测试
    notifier = OpenclawNotifier()
    
    # 发送测试消息
    test_task = {
        'task_name': '测试任务',
        'scheduled_time': datetime.now().isoformat(),
        'reason': '这是一条测试消息',
        'critical': True
    }
    
    result = notifier.notify_task_missed(test_task)
    print(f"发送结果: {'成功' if result else '失败'}")
