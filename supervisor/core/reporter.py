"""
日报生成器 - 隔壁老王的每日汇报
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List


class DailyReporter:
    """隔壁老王的日报生成器"""
    
    def __init__(self, db_path: str = "data/supervisor.db"):
        self.db_path = db_path
    
    def generate_daily_report(self, date: str = None) -> Dict[str, Any]:
        """生成每日执行报告"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 任务执行统计
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeout,
                SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed
            FROM task_executions
            WHERE date(planned_time) = ?
        ''', (date,))
        
        row = cursor.fetchone()
        
        # GitHub提交统计
        cursor.execute('''
            SELECT commits_count, unpushed_count, alert_sent
            FROM github_daily_status
            WHERE date = ?
        ''', (date,))
        
        github_row = cursor.fetchone()
        
        conn.close()
        
        total = row[0] or 0
        success = row[1] or 0
        
        report = {
            'date': date,
            'tasks': {
                'total': total,
                'success': success,
                'failed': row[2] or 0,
                'timeout': row[3] or 0,
                'missed': row[4] or 0,
                'success_rate': (success / total * 100) if total > 0 else 0
            },
            'github': {
                'commits': github_row[0] if github_row else 0,
                'unpushed': github_row[1] if github_row else 0,
                'alert_sent': bool(github_row[2]) if github_row else False
            } if github_row else None
        }
        
        return report
    
    def format_report_for_feishu(self, report: Dict[str, Any]) -> str:
        """格式化为飞书消息"""
        date = report['date']
        tasks = report['tasks']
        github = report.get('github')
        
        lines = [
            f"📊 隔壁老王日报 - {date}",
            "",
            "📈 任务执行:",
            f"   • 总执行: {tasks['total']}次",
            f"   • 成功: {tasks['success']}次 ✅",
            f"   • 失败: {tasks['failed']}次 ❌",
            f"   • 漏执行: {tasks['missed']}次 ⚠️",
            f"   • 成功率: {tasks['success_rate']:.1f}%",
        ]
        
        if github:
            lines.extend([
                "",
                "💻 GitHub提交:",
                f"   • 今日提交: {github['commits']}次",
            ])
            if github['unpushed'] > 0:
                lines.append(f"   • 未推送: {github['unpushed']}个 📦")
            if github['commits'] == 0:
                lines.append("   ⚠️ 老王唠叨: 今天没写代码？")
        
        lines.extend([
            "",
            "⏰ 报告时间: " + datetime.now().strftime('%H:%M:%S'),
            "🤖 发送者: 隔壁老王"
        ])
        
        return '\n'.join(lines)


if __name__ == "__main__":
    reporter = DailyReporter()
    report = reporter.generate_daily_report()
    print(reporter.format_report_for_feishu(report))
