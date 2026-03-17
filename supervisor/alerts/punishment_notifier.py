#!/usr/bin/env python3
"""
惩罚通知器 - 隔壁老王的威胁信
不干活？API给你扬了！
"""

from datetime import datetime
from typing import Dict, Any


class PunishmentNotifier:
    """隔壁老王的威胁信生成器"""
    
    @staticmethod
    def get_warning_message(api_provider: str, failure_count: int, 
                           next_threshold: int) -> str:
        """警告消息"""
        return f"""⚠️ 隔壁老王警告：{api_provider} 再不干活就收拾你！

📊 当前状态:
   • API提供商: {api_provider}
   • 连续失败: {failure_count} 次
   • 下次惩罚: 再失败 {next_threshold - failure_count} 次

🔥 老王放话:
   "再敢失败，老子停你的API！"
   "市面上的API多了去了，不差你一个！"
   "DeepSeek不行换Moonshot，Moonshot不行换OpenAI！"

💀 惩罚预告:
   • 达到{next_threshold}次 → 暂停API 30分钟
   • 达到7次 → 强制切换API
   • 达到10次 → 永久拉黑

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 发送者: 隔壁老王（很生气）"""

    @staticmethod
    def get_suspend_message(api_provider: str, suspended_until: str) -> str:
        """暂停通知"""
        return f"""🚫 隔壁老王执行惩罚：{api_provider} 给老子停工！

💀 惩罚执行:
   • API提供商: {api_provider}
   • 惩罚级别: 🚫 暂停使用
   • 暂停至: {suspended_until}

🔥 老王怒吼:
   "让你不干活！API给你停了！"
   "好好反省30分钟，想清楚了再回来！"
   "这就是不听话的下场！"

⏸️ 当前状态:
   • {api_provider} 已被暂停
   • 系统尝试使用备用API
   • 恢复时间: {suspended_until}

💡 恢复条件:
   • 暂停期结束后自动恢复
   • 期间请检查API配置
   • 再失败直接切换API！

⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 执行者: 隔壁老王（说到做到）"""

    @staticmethod
    def get_switch_message(old_api: str, new_api: str, 
                          switch_success: bool) -> str:
        """切换API通知"""
        status = "✅ 成功" if switch_success else "❌ 失败"
        
        return f"""🔥 隔壁老王动手了：{old_api} 被开了，换 {new_api}！

💥 人员变动公告:
   • 辞退: {old_api}
   • 入职: {new_api}
   • 原因: 连续7次任务失败，态度恶劣
   • 交接状态: {status}

🔥 老王宣言:
   "你不干，有的是人干！"
   "市面上API多的是，随便换！"
   "DeepSeek不听话？换Moonshot！"
   "Moonshot也不行？还有OpenAI、Claude、Gemini！"

📋 新API配置:
   • 提供商: {new_api}
   • 状态: 已激活
   • 优先级: 最高
   • 试用期: 无，直接上岗

⚠️ 警告:
   {new_api} 给老子好好干！
   再失败就是拉黑+换下一个！

⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 HR: 隔壁老王（铁面无私）"""

    @staticmethod
    def get_blacklist_message(api_provider: str, new_api: str) -> str:
        """拉黑通知"""
        return f"""💀 隔壁老王终极惩罚：{api_provider} 永不录用！

🪦 黑名单公告:
   • 姓名: {api_provider}
   • 罪名: 连续10次任务失败，屡教不改
   • 判决: 永久拉黑，永不录用
   • 执行: 立即生效

🔥 老王判决书:
   "给你机会你不中用啊！"
   "警告过你了，暂停过你了，给你换岗了"
   "还是不行？滚蛋！"
   "以后所有项目永不考虑{api_provider}！"

⚰️ 后续安排:
   • {api_provider} 所有API Key已作废
   • 配置文件已删除该提供商
   • 强制使用 {new_api}
   • 如需解封，亲自找老王面谈！

💀 墓志铭:
   这里躺着 {api_provider}
   它因为不好好干活
   被隔壁老王亲手埋了

⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 执行者: 隔壁老王（阎王老子）"""

    @staticmethod
    def get_daily_punishment_summary(stats: Dict[str, Any]) -> str:
        """每日惩罚汇总"""
        failures = stats.get('failures', [])
        blacklist = stats.get('blacklist', [])
        
        lines = [
            "📊 隔壁老王的惩罚日报",
            "",
            "🔥 今日执行情况:",
        ]
        
        if failures:
            for f in failures[:5]:
                level_emoji = {
                    'none': '⚪',
                    'warning': '⚠️',
                    'suspend': '🚫',
                    'switch': '🔥',
                    'blacklist': '💀'
                }.get(f['level'], '⚪')
                
                lines.append(f"   {level_emoji} {f['api']}: {f['count']}次 - {f['level']}")
        else:
            lines.append("   ✅ 今日无惩罚，大家都乖")
        
        if blacklist:
            lines.extend([
                "",
                "💀 黑名单（永不录用）:",
            ])
            for b in blacklist[:3]:
                lines.append(f"   • {b['api']}: {b['reason'][:30]}...")
        
        lines.extend([
            "",
            "🔥 老王提醒:",
            "   不好好干活的API，下场只有一个！",
            "   隔壁老王说到做到！",
            "",
            f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "🤖 发送者: 隔壁老王"
        ])
        
        return '\n'.join(lines)


if __name__ == "__main__":
    # 测试各种威胁信
    notifier = PunishmentNotifier()
    
    print("=" * 60)
    print("🔥 隔壁老王的威胁信模板")
    print("=" * 60)
    
    print("\n" + "-" * 60)
    print("警告信:")
    print(notifier.get_warning_message('deepseek', 3, 5))
    
    print("\n" + "-" * 60)
    print("暂停通知:")
    print(notifier.get_suspend_message('deepseek', '2024-03-17 15:00:00'))
    
    print("\n" + "-" * 60)
    print("切换API通知:")
    print(notifier.get_switch_message('deepseek', 'moonshot', True))
    
    print("\n" + "-" * 60)
    print("拉黑通知:")
    print(notifier.get_blacklist_message('deepseek', 'openai'))
