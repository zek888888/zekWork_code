#!/usr/bin/env python3
"""
战颅将军 - BTC底部反转监控系统
监控任务: 5浪末端反转信号确认
创建时间: 2026-03-19 22:50
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
import subprocess

# 配置
DB_PATH = "/Users/mac/.openclaw/workspace/quant-trading/data/market_data.db"
ALERT_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")

# 监控参数
MONITOR_CONFIG = {
    "symbol": "BTCUSDT",
    "interval": "1h",
    "wave5_low": 69081.51,      # 5浪低点
    "stop_loss": 68500,          # 止损位
    "entry_trigger": 70500,      # 试仓触发位
    "neckline": 71100,           # 颈线位（加仓点）
    "target1": 72000,            # 目标1
    "target2": 74000,            # 目标2
}

class BTCBottomMonitor:
    def __init__(self):
        self.db_path = DB_PATH
        self.signals = {
            "bottom_fractal": False,     # 底分型
            "macd_golden_cross": False,  # MACD金叉
            "volume_confirm": False,     # 成交量确认
            "neckline_break": False,     # 颈线突破
        }
        self.current_price = 0
        self.last_macd_hist = 0
        
    def get_latest_klines(self, limit=10):
        """获取最新K线数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT timestamp, open, high, low, close, volume, 
               macd, macd_signal, macd_hist
        FROM kline_data 
        WHERE symbol = ? AND interval = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """
        
        cursor.execute(query, (MONITOR_CONFIG["symbol"], MONITOR_CONFIG["interval"], limit))
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    
    def check_bottom_fractal(self, klines):
        """检查底分型"""
        if len(klines) < 3:
            return False
            
        # klines是按时间倒序排列的，需要反转
        k0 = klines[2]  # 最早
        k1 = klines[1]  # 中间（可能的低点）
        k2 = klines[0]  # 最新
        
        # 底分型条件:
        # 1. 中间K线低点最低
        # 2. 右侧K线收盘价高于中间K线高点
        
        # 列索引: timestamp(0), open(1), high(2), low(3), close(4), volume(5)...
        low0, high0, close0 = k0[3], k0[2], k0[4]
        low1, high1, close1 = k1[3], k1[2], k1[4]
        low2, high2, close2 = k2[3], k2[2], k2[4]
        
        # 简化版底分型：中间K线低点最低，且右侧K线收盘价 > 中间K线高点
        # 注意：klines是倒序，所以k1是中间，k2是最新（右侧）
        if low1 < low0 and close2 > high1:
            return True
        return False
    
    def check_macd_signal(self, klines):
        """检查MACD信号"""
        if len(klines) < 2:
            return False
            
        latest = klines[0]
        prev = klines[1]
        
        # 检查数据完整性
        if len(latest) < 10 or len(prev) < 10:
            return False
        if latest[9] is None or prev[9] is None:
            return False
            
        macd_hist = latest[9]  # macd_hist是第10列
        prev_hist = prev[9]
        
        self.last_macd_hist = macd_hist
        
        # MACD绿柱收敛（从负值向0靠近）
        if macd_hist < 0 and macd_hist > prev_hist:
            return True
        # 或者已经出现金叉（hist由负转正）
        if prev_hist < 0 and macd_hist >= 0:
            return True
        return False
    
    def check_volume(self, klines):
        """检查成交量"""
        if len(klines) < 4:
            return False
            
        # 检查数据完整性
        if klines[0][6] is None:
            return False
            
        # 最新K线成交量应该大于前几根平均
        latest_vol = klines[0][6]
        prev_vols = [k[6] for k in klines[1:4] if k[6] is not None]
        if not prev_vols:
            return False
        avg_vol = sum(prev_vols) / len(prev_vols)
        
        if latest_vol > avg_vol * 1.2:  # 放量20%
            return True
        return False
    
    def check_price_levels(self, klines):
        """检查价格关键位"""
        if not klines:
            return {}
            
        latest = klines[0]
        # timestamp(0), open(1), high(2), low(3), close(4), volume(5), macd(6), signal(7), hist(8)
        current_price = latest[4]  # close是第5列（索引4）
        self.current_price = current_price
        
        levels = {
            "current": current_price,
            "above_70500": current_price > 70500,
            "above_neckline": current_price > 71100,
            "below_stop_loss": current_price < 68500,
        }
        return levels
    
    def send_alert(self, message, priority="normal"):
        """发送警报"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] BTC底部监控: {message}"
        
        print(full_message)
        
        # 如果配置了飞书webhook，发送通知
        if ALERT_WEBHOOK and priority == "high":
            try:
                import json
                import urllib.request
                
                data = json.dumps({"msg_type": "text", "content": {"text": full_message}}).encode()
                req = urllib.request.Request(ALERT_WEBHOOK, data=data, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=5)
            except Exception as e:
                print(f"飞书通知失败: {e}")
    
    def run_monitor(self):
        """执行监控"""
        print("="*60)
        print(f"战颅将军 BTC底部反转监控 - {datetime.now()}")
        print("="*60)
        
        klines = self.get_latest_klines(10)
        if not klines:
            self.send_alert("无法获取K线数据！", "high")
            return
        
        latest_time = klines[0][0]
        print(f"最新数据时间: {latest_time}")
        print(f"5浪低点参考: ${MONITOR_CONFIG['wave5_low']:,.2f}")
        print()
        
        # 检查各项信号
        self.signals["bottom_fractal"] = self.check_bottom_fractal(klines)
        self.signals["macd_golden_cross"] = self.check_macd_signal(klines)
        self.signals["volume_confirm"] = self.check_volume(klines)
        
        levels = self.check_price_levels(klines)
        self.signals["neckline_break"] = levels.get("above_neckline", False)
        
        # 打印信号状态
        print("【信号检测】")
        for signal, status in self.signals.items():
            status_str = "✅ 满足" if status else "❌ 未满足"
            print(f"  {signal}: {status_str}")
        
        print(f"\n当前价格: ${levels['current']:,.2f}")
        print(f"MACD柱状图: {self.last_macd_hist:.2f}")
        
        # 价格位置提醒
        print("\n【价格位置】")
        if levels.get("below_stop_loss"):
            print("  ⚠️ 价格跌破止损位$68,500！5浪可能延伸，严禁抄底！")
            self.send_alert("跌破止损位$68,500！重新评估5浪结构！", "high")
        elif levels.get("above_neckline"):
            print("  🎉 价格突破颈线位$71,100！反转确认，可考虑加仓！")
            self.send_alert("突破颈线位$71,100！反转信号确认！", "high")
        elif levels.get("above_70500"):
            print("  🟡 价格突破$70,500，关注能否突破颈线$71,100")
        else:
            print("  🔴 价格在$70,500下方，继续等待底分型确认")
        
        # 综合判断
        satisfied_signals = sum(self.signals.values())
        total_signals = len(self.signals)
        
        print(f"\n【综合评估】信号满足: {satisfied_signals}/{total_signals}")
        
        if satisfied_signals == 0:
            print("  ⛔ 无任何反转信号，严禁进场！")
        elif satisfied_signals <= 2:
            print("  🟡 部分信号出现，继续观察，耐心等待！")
        elif satisfied_signals >= 3:
            print("  ✅ 多数信号满足，准备试仓（10-20%）！")
            if self.signals["neckline_break"]:
                print("  🚀 颈线突破确认，可加仓至30-50%！")
                self.send_alert("反转信号齐全！可以进场试仓！", "high")
        
        print("="*60)

if __name__ == "__main__":
    monitor = BTCBottomMonitor()
    monitor.run_monitor()
