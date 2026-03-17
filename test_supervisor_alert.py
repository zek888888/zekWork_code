#!/usr/bin/env python3
"""
任务监工系统 - 飞书告警测试脚本
发送模拟告警消息到你的飞书
"""

import os
import sys
import requests
import json
from datetime import datetime


def load_feishu_webhook():
    """加载飞书 webhook 配置"""
    webhook = None
    
    # 1. 尝试从环境变量读取
    webhook = os.environ.get('FEISHU_WEBHOOK')
    if webhook:
        return webhook
    
    # 2. 尝试从 .env 文件读取
    env_paths = [
        '.env',
        '/Users/mac/.openclaw/workspace/quant-trading/.env'
    ]
    
    for path in env_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                for line in f:
                    if line.strip().startswith('FEISHU_WEBHOOK='):
                        webhook = line.strip().split('=', 1)[1].strip().strip('"').strip("'")
                        return webhook
    
    # 3. 尝试从 config.yaml 读取
    try:
        import yaml
        config_path = '/Users/mac/.openclaw/workspace/quant-trading/config.yaml'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                webhook = config.get('notification', {}).get('feishu', {}).get('webhook', '')
                if webhook and not webhook.startswith('${'):
                    return webhook
    except:
        pass
    
    return None


def save_feishu_webhook(webhook):
    """保存飞书 webhook 到 .env 文件"""
    env_path = '/Users/mac/.openclaw/workspace/quant-trading/.env'
    
    # 读取现有内容
    existing_lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            existing_lines = f.readlines()
    
    # 查找并替换或添加
    found = False
    new_lines = []
    for line in existing_lines:
        if line.strip().startswith('FEISHU_WEBHOOK='):
            new_lines.append(f'FEISHU_WEBHOOK={webhook}\n')
            found = True
        else:
            new_lines.append(line)
    
    if not found:
        new_lines.append(f'FEISHU_WEBHOOK={webhook}\n')
    
    # 写入文件
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    return env_path


def send_feishu_alert(webhook_url, title, content, level="error"):
    """发送飞书告警消息"""
    
    # 根据级别设置颜色/表情
    level_emoji = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "critical": "🚨"
    }
    
    emoji = level_emoji.get(level, "❌")
    full_title = f"{emoji} {title}"
    
    # 构建飞书消息体
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
    
    try:
        response = requests.post(
            webhook_url,
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                return True, "消息发送成功"
            else:
                return False, f"飞书返回错误: {result}"
        else:
            return False, f"HTTP错误: {response.status_code}"
            
    except Exception as e:
        return False, f"发送异常: {str(e)}"


def test_task_missed_alert(webhook_url):
    """测试【任务漏执行】告警"""
    print("\n📤 正在发送【任务漏执行】测试告警...")
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    content = [
        [{"tag": "text", "text": "🤖 这是任务监工系统的测试消息"}],
        [{"tag": "hr"}],
        [{"tag": "text", "text": f"📋 任务: 神算子（AI预测） (BTC 15分钟预测)"}],
        [{"tag": "text", "text": f"⏰ 计划时间: {now}"}],
        [{"tag": "text", "text": "❌ 原因: 未检测到执行记录 (cron未触发)"}],
        [{"tag": "text", "text": "🔴 级别: 关键任务"}],
        [{"tag": "hr"}],
        [{"tag": "text", "text": "🔧 自动修复尝试中..."}],
        [{"tag": "text", "text": "\n如果持续收到此消息，请检查:"}],
        [{"tag": "text", "text": "1. cron服务是否运行: crontab -l"}],
        [{"tag": "text", "text": "2. 脚本路径是否正确"}],
        [{"tag": "text", "text": "3. 使用CLI修复: python3 supervisor_cli.py repair"}],
    ]
    
    success, msg = send_feishu_alert(
        webhook_url,
        "任务漏执行 - 神算子（AI预测）",
        content,
        level="critical"
    )
    
    return success, msg


def test_daily_report(webhook_url):
    """测试【每日报告】告警"""
    print("\n📤 正在发送【每日报告】测试消息...")
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    content = [
        [{"tag": "text", "text": f"📊 任务执行日报 ({today})"}],
        [{"tag": "hr"}],
        [{"tag": "text", "text": "📈 执行统计:"}],
        [{"tag": "text", "text": "   • 总执行: 96次"}],
        [{"tag": "text", "text": "   • 成功: 94次 ✅"}],
        [{"tag": "text", "text": "   • 失败: 2次 ❌"}],
        [{"tag": "text", "text": "   • 超时: 0次"}],
        [{"tag": "text", "text": "   • 成功率: 97.9%"}],
        [{"tag": "hr"}],
        [{"tag": "text", "text": "⚠️ 需要关注的任务:"}],
        [{"tag": "text", "text": "   • 神算子（AI预测）: 失败1次 (已修复)"}],
        [{"tag": "text", "text": "\n💡 查看详情: http://localhost:5001/supervisor"}],
    ]
    
    success, msg = send_feishu_alert(
        webhook_url,
        f"任务执行日报 - {today}",
        content,
        level="info"
    )
    
    return success, msg


def test_repair_needed(webhook_url):
    """测试【需要人工修复】告警"""
    print("\n📤 正在发送【人工修复请求】测试消息...")
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    content = [
        [{"tag": "text", "text": "🔧 监工系统无法自动修复此问题，需要人工介入"}],
        [{"tag": "hr"}],
        [{"tag": "text", "text": f"📋 任务: 神算子（AI预测）"}],
        [{"tag": "text", "text": f"⏰ 失败时间: {now}"}],
        [{"tag": "text", "text": "❌ 错误: ModuleNotFoundError: No module named 'pandas'"}],
        [{"tag": "hr"}],
        [{"tag": "text", "text": "🔨 可选修复方案:"}],
        [{"tag": "text", "text": "   1. 安装依赖: pip3 install pandas"}],
        [{"tag": "text", "text": "   2. 检查虚拟环境: source venv/bin/activate"}],
        [{"tag": "text", "text": "   3. 手动执行测试: python3 cron/prediction_agent_cron.py"}],
        [{"tag": "hr"}],
        [{"tag": "text", "text": "\n💻 执行修复命令:"}],
        [{"tag": "text", "text": "   python3 supervisor_cli.py repair <execution_id> --manual 'pip3 install pandas'"}],
    ]
    
    success, msg = send_feishu_alert(
        webhook_url,
        "需要人工修复 - 神算子（AI预测）",
        content,
        level="error"
    )
    
    return success, msg


def main():
    """主函数"""
    print("=" * 60)
    print("🎖️ 任务监工系统 - 飞书告警测试")
    print("=" * 60)
    
    # 1. 获取 webhook
    webhook = load_feishu_webhook()
    
    if not webhook:
        print("\n⚠️  未找到飞书 Webhook 配置")
        print("\n请提供你的飞书机器人 Webhook URL:")
        print("  获取方式: 飞书群 → 设置 → 群机器人 → 添加机器人 → 复制 Webhook")
        print()
        
        webhook = input("Webhook URL: ").strip()
        
        if not webhook:
            print("❌ 未提供 Webhook，退出")
            return
        
        if not webhook.startswith('https://'):
            print("❌ 无效的 Webhook URL")
            return
        
        # 保存配置
        env_path = save_feishu_webhook(webhook)
        print(f"✅ Webhook 已保存到: {env_path}")
    else:
        print(f"\n✅ 已找到 Webhook 配置")
        print(f"   URL: {webhook[:50]}...")
    
    # 2. 选择测试类型
    print("\n" + "-" * 60)
    print("请选择要测试的告警类型:")
    print()
    print("  1. 🚨 任务漏执行告警 (Critical)")
    print("  2. 📊 每日执行报告 (Info)")
    print("  3. 🔧 人工修复请求 (Error)")
    print("  4. 全部发送")
    print()
    
    choice = input("请输入选项 (1-4): ").strip()
    
    results = []
    
    if choice == '1':
        success, msg = test_task_missed_alert(webhook)
        results.append(("任务漏执行", success, msg))
    
    elif choice == '2':
        success, msg = test_daily_report(webhook)
        results.append(("每日报告", success, msg))
    
    elif choice == '3':
        success, msg = test_repair_needed(webhook)
        results.append(("人工修复请求", success, msg))
    
    elif choice == '4':
        success1, msg1 = test_task_missed_alert(webhook)
        results.append(("任务漏执行", success1, msg1))
        
        success2, msg2 = test_daily_report(webhook)
        results.append(("每日报告", success2, msg2))
        
        success3, msg3 = test_repair_needed(webhook)
        results.append(("人工修复请求", success3, msg3))
    
    else:
        print("❌ 无效选项")
        return
    
    # 3. 显示结果
    print("\n" + "=" * 60)
    print("📋 发送结果")
    print("=" * 60)
    
    for name, success, msg in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}: {msg}")
    
    print("\n" + "-" * 60)
    if any(r[1] for r in results):
        print("✅ 请检查你的飞书，应该已收到测试消息！")
        print()
        print("如果没有收到，请检查:")
        print("  1. Webhook URL 是否正确")
        print("  2. 飞书群机器人是否已启用")
        print("  3. 群消息通知是否开启")
    else:
        print("❌ 发送失败，请检查 Webhook 配置")
    print("-" * 60)


if __name__ == "__main__":
    main()
