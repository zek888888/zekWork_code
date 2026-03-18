#!/usr/bin/env python3
"""
战颅将军 - 测试案例：BTC多单，20倍杠杆，5%仓位，涨10刀平仓
"""

import os
import sys
import sqlite3
from datetime import datetime

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
DB_PATH = f"{PROJECT_ROOT}/data/market_data.db"

sys.path.insert(0, PROJECT_ROOT)
from 模拟盘_engine import 模拟盘引擎

def 获取当前价格():
    """从数据库获取BTC当前价格"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT close FROM kline_data 
        WHERE symbol = 'BTCUSDT' AND interval = '5m'
        ORDER BY timestamp DESC LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 73700

if __name__ == "__main__":
    print("=" * 70)
    print("⚔️  战颅将军 - 测试案例执行")
    print("=" * 70)
    print("\n📋 交易策略:")
    print("   • 方向: 做多 (LONG)")
    print("   • 杠杆: 20x")
    print("   • 仓位: 5%")
    print("   • 止盈: 入场价 + $10")
    print("   • 止损: 入场价 - $50 (保护性止损)")
    
    # 获取当前价格
    current_price = 获取当前价格()
    entry_price = current_price
    take_profit = entry_price + 10  # 涨10刀平仓
    stop_loss = entry_price - 50     # 跌50刀止损
    
    print("\n📊 市场数据:")
    print(f"   当前BTC价格: ${current_price:,.2f}")
    print(f"   入场价: ${entry_price:,.2f}")
    print(f"   止盈价: ${take_profit:,.2f} (+${take_profit-entry_price:.2f})")
    print(f"   止损价: ${stop_loss:,.2f} (${stop_loss-entry_price:.2f})")
    
    # 初始化模拟盘引擎
    print("\n⚔️  初始化模拟盘引擎...")
    引擎 = 模拟盘引擎(initial_balance=10000.0)
    
    # 计算交易参数
    position_size = 0.05  # 5%仓位
    leverage = 20
    margin = 10000 * position_size / leverage  # 保证金 = 10000 * 5% / 20 = 25 USDT
    
    print("\n💰 交易参数:")
    print(f"   启动资金: $10,000 USDT")
    print(f"   仓位比例: {position_size*100}%")
    print(f"   杠杆倍数: {leverage}x")
    print(f"   所需保证金: ${margin:.2f} USDT")
    print(f"   名义仓位: ${10000 * position_size:.2f} USDT")
    
    # 执行开仓
    print("\n🚀 执行开仓...")
    trade = 引擎.开仓(
        symbol='BTCUSDT',
        direction='long',
        entry_price=entry_price,
        position_size=position_size,
        leverage=leverage,
        stop_loss=stop_loss,
        take_profit=[take_profit],
        confidence=0.95,
        reasoning='测试案例：BTC多单，20倍杠杆，5%仓位，涨10刀平仓'
    )
    
    if trade:
        print("\n" + "=" * 70)
        print("✅ 开仓成功!")
        print("=" * 70)
        print(f"交易ID: {trade.trade_id}")
        print(f"方向: {trade.direction.upper()} 📈")
        print(f"入场价: ${trade.entry_price:,.2f}")
        print(f"杠杆: {trade.leverage}x")
        print(f"仓位: {trade.position_size*100:.1f}%")
        print(f"保证金: ${trade.margin:.2f} USDT")
        print(f"止损: ${trade.stop_loss:,.2f}")
        print(f"止盈: ${trade.take_profit[0]:,.2f}")
        print("=" * 70)
        
        # 显示持仓后状态
        print("\n📊 开仓后账户状态:")
        print(f"   冻结保证金: ${trade.margin:.2f} USDT")
        print(f"   可用资金: ${引擎.current_balance:.2f} USDT")
        print(f"   当前持仓: {len(引擎.positions)} 个")
        
        # 模拟平仓（假设价格到达止盈）
        print("\n📈 模拟价格到达止盈...")
        print(f"   当前价格: ${take_profit:,.2f} (+${take_profit-entry_price:.2f})")
        
        # 计算盈亏
        pnl_percent = (take_profit - entry_price) / entry_price * leverage
        pnl_amount = trade.margin * pnl_percent
        
        print(f"\n💰 预期盈亏:")
        print(f"   价格变动: +${take_profit-entry_price:.2f}")
        print(f"   杠杆倍数: {leverage}x")
        print(f"   盈亏比例: {pnl_percent*100:+.2f}%")
        print(f"   盈亏金额: ${pnl_amount:+.2f} USDT")
        
        # 执行平仓
        引擎.平仓(trade.trade_id, take_profit, 'take_profit')
        
        # 显示最终统计
        print("\n📊 最终账户统计:")
        stats = 引擎.获取统计()
        print(f"   当前资金: ${stats['current_balance']:.2f} USDT")
        print(f"   总交易数: {stats['total_trades']}")
        print(f"   总盈亏: ${stats['total_pnl']:+.2f} USDT")
        print(f"   收益率: {stats['return_percent']:+.2f}%")
        
    else:
        print("\n❌ 开仓失败!")
    
    print("\n" + "=" * 70)
    print("测试案例完成!")
    print("=" * 70)
