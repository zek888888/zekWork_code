#!/usr/bin/env python3
"""
通知推送系统
支持飞书、邮件、短信等多种推送方式
"""

import os
import json
import smtplib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from enum import Enum
import urllib.request

# 配置
DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"


class NotificationType(Enum):
    TRADE_SIGNAL = "交易信号"
    ORDER_EXECUTED = "订单执行"
    PRICE_ALERT = "价格预警"
    RISK_WARNING = "风险警告"
    DAILY_REPORT = "日报"
    SYSTEM_ALERT = "系统提醒"


@dataclass
class NotificationMessage:
    """通知消息"""
    type: str
    title: str
    content: str
    priority: str = "normal"  # low/normal/high/urgent
    data: Dict = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.data is None:
            self.data = {}


class FeishuNotifier:
    """飞书通知器"""
    
    def __init__(self, webhook_url: Optional[str] = None, chat_id: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('FEISHU_WEBHOOK_URL')
        self.chat_id = chat_id or os.getenv('FEISHU_CHAT_ID', 'oc_4db6083a476458269556aa3ff77a6fbd')
    
    def send_text(self, text: str) -> bool:
        """发送文本消息"""
        if not self.webhook_url:
            print(f"[飞书] {text}")
            return True
        
        try:
            payload = {
                "msg_type": "text",
                "content": {"text": text}
            }
            
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode())
                return result.get('code') == 0
                
        except Exception as e:
            print(f"飞书发送失败: {e}")
            print(f"[飞书] {text}")
            return False
    
    def send_card(self, title: str, content: str, 
                  buttons: Optional[List[Dict]] = None) -> bool:
        """发送卡片消息"""
        if not self.webhook_url:
            print(f"[飞书卡片] {title}\n{content}")
            return True
        
        try:
            elements = [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
            
            if buttons:
                elements.append({
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": btn['text']},
                            "url": btn.get('url', ''),
                            "type": "primary"
                        }
                        for btn in buttons
                    ]
                })
            
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": title},
                        "template": self._get_template_by_priority(content)
                    },
                    "elements": elements
                }
            }
            
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode())
                return result.get('code') == 0
                
        except Exception as e:
            print(f"飞书卡片发送失败: {e}")
            return False
    
    def _get_template_by_priority(self, content: str) -> str:
        """根据内容获取卡片颜色"""
        if '🚨' in content or '紧急' in content or '风险' in content:
            return "red"
        elif '⚠️' in content or '警告' in content:
            return "orange"
        elif '✅' in content or '成功' in content or '盈利' in content:
            return "green"
        elif '📈' in content or '买入' in content:
            return "blue"
        else:
            return "grey"
    
    def send_trade_signal(self, symbol: str, signal: str, 
                         price: float, confidence: float,
                         strategy: str = ""):
        """发送交易信号通知"""
        emoji = "🟢 买入" if "买入" in signal or "BUY" in signal else "🔴 卖出" if "卖出" in signal or "SELL" in signal else "⚪ 观望"
        
        content = f"""
**标的**: {symbol}
**信号**: {emoji}
**价格**: ${price:,.2f}
**置信度**: {confidence*100:.1f}%
**策略**: {strategy or '多因子综合'}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return self.send_card(
            title=f"🎯 交易信号 - {symbol}",
            content=content,
            buttons=[
                {"text": "查看详情", "url": f"http://localhost:5000/signals"},
                {"text": "立即交易", "url": f"http://localhost:5000/trade"}
            ]
        )
    
    def send_order_notification(self, symbol: str, side: str, 
                               quantity: float, price: float,
                               pnl: Optional[float] = None):
        """发送订单执行通知"""
        emoji = "🟢 买入" if side == "BUY" else "🔴 卖出"
        
        content = f"""
**标的**: {symbol}
**方向**: {emoji}
**数量**: {quantity}
**价格**: ${price:,.2f}
**总价值**: ${quantity * price:,.2f}
        """
        
        if pnl is not None:
            pnl_emoji = "📈" if pnl > 0 else "📉"
            content += f"\n**盈亏**: {pnl_emoji} ${pnl:,.2f}"
        
        content += f"\n**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_card(
            title=f"💰 订单执行 - {symbol}",
            content=content
        )
    
    def send_risk_alert(self, alert_type: str, message: str,
                       current_drawdown: float = 0):
        """发送风险警告"""
        content = f"""
**⚠️ {alert_type}**

{message}

**当前回撤**: {current_drawdown*100:.2f}%
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请立即检查持仓和账户状况！
        """
        
        return self.send_card(
            title="🚨 风险警告",
            content=content
        )
    
    def send_daily_report(self, report_data: Dict):
        """发送日报"""
        content = f"""
**📊 今日交易概况**

**账户权益**: ${report_data.get('total_equity', 0):,.2f}
**今日盈亏**: {report_data.get('daily_pnl', 0):+,.2f} ({report_data.get('daily_pnl_pct', 0):+.2f}%)
**总收益率**: {report_data.get('total_return', 0):+.2f}%

**交易统计**:
- 交易次数: {report_data.get('trade_count', 0)}
- 胜率: {report_data.get('win_rate', 0):.1f}%
- 最大回撤: {report_data.get('max_drawdown', 0):.2f}%
        """
        
        return self.send_card(
            title=f"📈 交易日报 - {datetime.now().strftime('%Y-%m-%d')}",
            content=content,
            buttons=[
                {"text": "查看详情", "url": "http://localhost:5000/reports"}
            ]
        )


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.feishu = FeishuNotifier()
        self.init_database()
    
    def init_database(self):
        """初始化通知记录表"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                channel TEXT,
                status TEXT DEFAULT 'pending',
                sent_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def notify_trade_signal(self, symbol: str, signal: str, 
                           price: float, confidence: float,
                           strategy: str = ""):
        """交易信号通知"""
        return self.feishu.send_trade_signal(symbol, signal, price, confidence, strategy)
    
    def notify_order(self, symbol: str, side: str, 
                    quantity: float, price: float, pnl: float = None):
        """订单执行通知"""
        return self.feishu.send_order_notification(symbol, side, quantity, price, pnl)
    
    def notify_risk(self, alert_type: str, message: str, current_drawdown: float = 0):
        """风险警告通知"""
        return self.feishu.send_risk_alert(alert_type, message, current_drawdown)
    
    def notify_daily_report(self, report_data: Dict):
        """日报通知"""
        return self.feishu.send_daily_report(report_data)


def main():
    """命令行测试"""
    import argparse
    
    parser = argparse.ArgumentParser(description='通知推送系统')
    parser.add_argument('--test-feishu', action='store_true', help='测试飞书通知')
    parser.add_argument('--test-trade', action='store_true', help='测试交易信号通知')
    parser.add_argument('--test-risk', action='store_true', help='测试风险警告')
    parser.add_argument('--symbol', default='BTCUSDT', help='交易标的')
    
    args = parser.parse_args()
    
    notifier = NotificationManager()
    
    if args.test_feishu:
        print("测试飞书文本通知...")
        notifier.feishu.send_text("🧪 测试消息\n这是一条来自量化交易系统的测试通知。")
    
    elif args.test_trade:
        print(f"测试交易信号通知: {args.symbol}")
        notifier.notify_trade_signal(
            symbol=args.symbol,
            signal="买入",
            price=72456.78,
            confidence=0.82,
            strategy="均线趋势跟踪"
        )
    
    elif args.test_risk:
        print("测试风险警告通知...")
        notifier.notify_risk(
            alert_type="单日亏损超限",
            message="当前单日亏损已达到5.2%，超过设定阈值5%",
            current_drawdown=0.052
        )
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
