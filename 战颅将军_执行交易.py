#!/usr/bin/env python3
"""
战颅将军 - 执行一次交易决策
"""

import os
import sys
import sqlite3
import json
from datetime import datetime

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
DB_PATH = f"{PROJECT_ROOT}/data/market_data.db"

sys.path.insert(0, PROJECT_ROOT)

# 导入战颅将军
from 战颅将军_core import 战颅将军

def 获取最新市场数据():
    """从数据库获取最新市场数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取最新的15m K线数据
    cursor.execute('''
        SELECT close, macd, macd_signal, kdj_k, kdj_d, high, low
        FROM kline_data
        WHERE symbol = 'BTCUSDT' AND interval = '15m'
        ORDER BY timestamp DESC
        LIMIT 1
    ''')
    
    row = cursor.fetchone()
    if not row:
        print("❌ 未找到市场数据")
        conn.close()
        return None
    
    close, macd, macd_signal, kdj_k, kdj_d, high, low = row
    
    # 获取支持阻力位（使用最近100根K线）
    cursor.execute('''
        SELECT MAX(high) as resistance, MIN(low) as support
        FROM (
            SELECT high, low
            FROM kline_data
            WHERE symbol = 'BTCUSDT' AND interval = '15m'
            ORDER BY timestamp DESC
            LIMIT 100
        )
    ''')
    
    row2 = cursor.fetchone()
    resistance, support = row2 if row2 else (close * 1.02, close * 0.98)
    
    conn.close()
    
    # 根据MACD判断预测方向
    prediction = 'up' if macd and macd_signal and macd > macd_signal else 'down' if macd and macd_signal and macd < macd_signal else 'flat'
    
    market_data = {
        'current_price': close,
        'price_change_24h': 0,
        'volume_24h': 0,
        'prediction_15m': prediction,
        'support': support,
        'resistance': resistance,
        'volatility': 0.025,
        'macd': macd,
        'macd_signal': macd_signal,
        'kdj_k': kdj_k,
        'kdj_d': kdj_d,
        'historical': []
    }
    
    return market_data

if __name__ == "__main__":
    print("=" * 60)
    print("⚔️  战颅将军 - 执行交易决策")
    print("=" * 60)
    
    # 获取市场数据
    print("\n📊 获取市场数据...")
    market_data = 获取最新市场数据()
    
    if not market_data:
        sys.exit(1)
    
    print(f"   当前价格: ${market_data['current_price']:,.2f}")
    print(f"   15m预测: {market_data['prediction_15m']}")
    print(f"   支撑位: ${market_data['support']:,.2f}")
    print(f"   阻力位: ${market_data['resistance']:,.2f}")
    
    # 创建战颅将军实例
    print("\n⚔️  初始化战颅将军...")
    将军 = 战颅将军(initial_balance=10000.0)
    
    # 执行交易周期
    print("\n🎯 开始交易决策...")
    trade = 将军.执行交易周期(market_data)
    
    if trade:
        print("\n✅ 交易执行成功!")
        print(f"   交易ID: {trade.trade_id}")
        print(f"   方向: {trade.direction.upper()}")
        print(f"   入场价: ${trade.entry_price:,.2f}")
        print(f"   杠杆: {trade.leverage}x")
    else:
        print("\n⏸️  未执行交易（建议观望）")
    
    # 显示当前统计
    print("\n📊 当前交易统计:")
    stats = 将军.获取统计()
    print(f"   当前资金: ${stats['current_balance']:.2f} USDT")
    print(f"   总交易数: {stats['total_trades']}")
    print(f"   胜率: {stats.get('win_rate', 0)*100:.1f}%")
    print(f"   总盈亏: {stats['total_pnl']:+.2f} USDT")
    
    print("\n" + "=" * 60)
    print("决策完成")
    print("=" * 60)
