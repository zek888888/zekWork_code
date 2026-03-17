#!/usr/bin/env python3
"""
通过 Openclaw 发送告警消息到飞书
"""

import os
import sys
import subprocess
import json
from datetime import datetime

FEISHU_USER_ID = "ou_dc38103cbe80263557de2b373fb5242d"


def send_openclaw_alert(title, content, level="error"):
    """通过 Openclaw CLI 发送告警"""
    
    # 构建消息
    emoji = {
        "info": "ℹ️",
        "warning": "⚠️", 
        "error": "❌",
        "critical": "🚨"
    }.get(level, "📢")
    
    full_message = f"""
{emoji} {title}
━━━━━━━━━━━━━━━━━━━━━
{content}
━━━━━━━━━━━━━━━━━━━━━
⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 发送者: 任务监工系统
"""
    
    try:
        # 尝试使用 openclaw 命令发送
        # 方法1: 使用 openclaw notify
        result = subprocess.run(
            ['openclaw', 'notify', '--user', FEISHU_USER_ID, full_message],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, "通过 openclaw notify 发送成功"
        
        # 方法2: 如果 notify 失败，打印消息让用户手动转发
        return False, "openclaw 命令失败，请手动转发下方消息"
        
    except FileNotFoundError:
        return False, "openclaw 命令未找到，请手动转发下方消息"
    except Exception as e:
        return False, f"发送异常: {str(e)}"


def test_task_missed():
    """测试任务漏执行告警"""
    title = "🚨 任务漏执行 - 神算子（AI预测）"
    
    content = """📋 任务: 神算子（AI预测） (BTC 15分钟预测)
⏰ 计划时间: 刚刚
❌ 原因: 未检测到执行记录 (cron未触发)
🔴 级别: 关键任务

🔧 监工系统正在尝试自动修复...
   1. 检查工作目录...
   2. 尝试使用绝对路径重试...
   
💡 如果持续收到此消息，请检查:
   • cron服务: crontab -l
   • 脚本路径是否正确
   • 使用CLI: python3 supervisor_cli.py repair"""
    
    return send_openclaw_alert(title, content, level="critical")


def test_daily_report():
    """测试每日报告"""
    title = "📊 任务执行日报"
    
    content = """📈 今日统计:
   • 总执行: 96次
   • 成功: 94次 ✅
   • 失败: 2次 ❌
   • 超时: 0次
   • 成功率: 97.9%

⚠️ 需要关注的任务:
   • 神算子（AI预测）: 失败1次 (已自动修复)
   • 数据同步: 正常

💻 查看详情: http://localhost:5001/supervisor"""
    
    return send_openclaw_alert(title, content, level="info")


def test_repair_request():
    """测试人工修复请求"""
    title = "🔧 需要人工修复 - 神算子（AI预测）"
    
    content = """❌ 监工系统无法自动修复此问题

📋 任务: 神算子（AI预测）
⏰ 失败时间: 刚刚
💥 错误: ModuleNotFoundError: No module named 'pandas'

🔨 可选修复方案:
   1. 安装依赖: pip3 install pandas
   2. 检查虚拟环境
   3. 手动执行测试

💻 执行命令:
   python3 supervisor_cli.py repair <id> --manual 'pip3 install pandas'"""
    
    return send_openclaw_alert(title, content, level="error")


def main():
    print("=" * 60)
    print("🎖️ 任务监工系统 - Openclaw 告警测试")
    print("=" * 60)
    print()
    print("正在发送测试告警到你的飞书...")
    print(f"用户ID: {FEISHU_USER_ID}")
    print()
    
    # 发送测试消息
    print("📤 发送【任务漏执行】告警...")
    success1, msg1 = test_task_missed()
    print(f"   结果: {msg1}")
    
    print()
    print("📤 发送【每日报告】...")
    success2, msg2 = test_daily_report()
    print(f"   结果: {msg2}")
    
    print()
    print("📤 发送【人工修复请求】...")
    success3, msg3 = test_repair_request()
    print(f"   结果: {msg3}")
    
    print()
    print("=" * 60)
    
    if any([success1, success2, success3]):
        print("✅ 测试消息已发送！")
        print("   请检查你的飞书消息")
    else:
        print("⚠️ 自动发送可能失败")
        print("   但你可以看到上面的消息内容")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
