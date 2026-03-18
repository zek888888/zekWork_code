#!/usr/bin/env python3
"""
战颅将军 - 测试交易执行（模拟强上涨信号）
"""

import os
import sys

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
DB_PATH = f"{PROJECT_ROOT}/data/market_data.db"

sys.path.insert(0, PROJECT_ROOT)

from 战颅将军_core import 战颅将军

if __name__ == "__main__":
    print("=" * 60)
    print("⚔️  战颅将军 - 测试交易执行")
    print("=" * 60)
    
    # 模拟强上涨市场信号
    market_data = {
        'current_price': 73700,
        'price_change_24h': 5.2,
        'volume_24h': 45000000000,
        'prediction_15m': 'up',  # 强上涨预测
        'support': 72000,
        'resistance': 76000,
        'volatility': 0.025,
        'macd': 150,
        'macd_signal': 50,
        'kdj_k': 75,
        'kdj_d': 55,
        'historical': []
    }
    
    print("\n📊 模拟市场数据:")
    print(f"   当前价格: ${market_data['current_price']:,.2f}")
    print(f"   24h涨跌: +{market_data['price_change_24h']}%")
    print(f"   15m预测: {market_data['prediction_15m']} 📈")
    print(f"   MACD: {market_data['macd']} (金叉)")
    
    # 创建战颅将军
    print("\n⚔️  初始化战颅将军...")
    将军 = 战颅将军(initial_balance=10000.0)
    
    # 执行交易
    print("\n🎯 开始交易决策...")
    trade = 将军.执行交易周期(market_data)
    
    if trade:
        print("\n" + "=" * 60)
        print("✅ 交易执行成功!")
        print("=" * 60)
        print(f"交易ID: {trade.trade_id}")
        print(f"交易对: {trade.symbol}")
        print(f"方向: {trade.direction.upper()}")
        print(f"入场价: ${trade.entry_price:,.2f}")
        print(f"杠杆: {trade.leverage}x")
        print(f"仓位: {trade.position_size*100:.1f}%")
        print(f"保证金: ${trade.margin:.2f} USDT")
        print(f"止损: ${trade.stop_loss:,.2f}")
        print(f"止盈: {trade.take_profit}")
        print("=" * 60)
    else:
        print("\n⏸️  未执行交易")
    
    # 显示统计
    print("\n📊 当前交易统计:")
    stats = 将军.获取统计()
    print(f"   当前资金: ${stats['current_balance']:.2f} USDT")
    print(f"   总交易数: {stats['total_trades']}")
    print(f"   胜率: {stats.get('win_rate', 0)*100:.1f}%")
    print(f"   总盈亏: {stats['total_pnl']:+.2f} USDT")
