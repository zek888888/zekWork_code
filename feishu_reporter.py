#!/usr/bin/env python3
"""
Feishu Reporter - 飞书报告推送
"""

import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"

def get_market_summary():
    """获取市场概况"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT symbol, price, change_24h FROM realtime_price 
        ORDER BY symbol
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows

def get_top_signals():
    """获取交易信号"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT symbol, total_score, rating, signal, MAX(timestamp)
        FROM factor_scores 
        WHERE timestamp > datetime('now', '-1 hour')
        GROUP BY symbol
        ORDER BY total_score DESC
        LIMIT 5
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows

def generate_feishu_message():
    """生成飞书消息"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 市场概况
    prices = get_market_summary()
    price_text = "\n".join([
        f"• **{row[0]}**: ${row[1]:,.2f} ({row[2]:+.2f}%)"
        for row in prices
    ])
    
    # 交易信号
    signals = get_top_signals()
    signal_text = "\n".join([
        f"• **{row[0]}**: {row[1]}分 [{row[2]}] - {row[3]}"
        for row in signals
    ])
    
    message = f"""## 📊 量化交易报告 - {now}

### 💰 市场行情
{price_text}

### 🎯 交易信号 (Top 5)
{signal_text}

---
🤖 虾哥量化交易系统
"""
    
    return message

def main():
    message = generate_feishu_message()
    print(message)

if __name__ == "__main__":
    main()
