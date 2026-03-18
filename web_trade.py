#!/usr/bin/env python3
"""
交易展示页面
http://localhost:5050/trade
展示战颅将军的交易记录和绩效
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request

# 配置Flask
app = Flask(__name__, 
    template_folder='/Users/mac/.openclaw/workspace/quant-trading/templates',
    static_folder='/Users/mac/.openclaw/workspace/quant-trading/static'
)

DB_PATH = "/Users/mac/.openclaw/workspace/quant-trading/data/market_data.db"


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/trade')
def trade_dashboard():
    """交易展示页面"""
    return render_template('trade.html')


@app.route('/api/trade/stats')
def api_trade_stats():
    """API: 获取交易统计"""
    try:
        conn = get_db_connection()
        
        # 总体统计
        cursor = conn.execute('''
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as win_trades,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as loss_trades,
                SUM(CASE WHEN pnl = 0 THEN 1 ELSE 0 END) as break_even,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl,
                AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss
            FROM simulated_trades
            WHERE exit_time IS NOT NULL
        ''')
        
        row = cursor.fetchone()
        
        stats = {
            'total_trades': row['total_trades'] or 0,
            'win_trades': row['win_trades'] or 0,
            'loss_trades': row['loss_trades'] or 0,
            'break_even': row['break_even'] or 0,
            'total_pnl': round(row['total_pnl'] or 0, 2),
            'avg_pnl': round(row['avg_pnl'] or 0, 2),
            'avg_win': round(row['avg_win'] or 0, 2),
            'avg_loss': round(row['avg_loss'] or 0, 2),
            'win_rate': round((row['win_trades'] or 0) / row['total_trades'] * 100, 2) if row['total_trades'] else 0
        }
        
        # 当前持仓
        cursor = conn.execute('''
            SELECT COUNT(*) as count
            FROM simulated_trades
            WHERE exit_time IS NULL
        ''')
        stats['open_positions'] = cursor.fetchone()['count']
        
        # 当前资金
        cursor = conn.execute('''
            SELECT balance FROM equity_curve
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        stats['current_balance'] = round(row['balance'], 2) if row else 10000
        
        conn.close()
        
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/trade/history')
def api_trade_history():
    """API: 获取交易历史"""
    try:
        conn = get_db_connection()
        
        limit = request.args.get('limit', 50, type=int)
        status = request.args.get('status', 'all')  # all/open/closed
        
        query = '''
            SELECT * FROM simulated_trades
        '''
        
        if status == 'open':
            query += ' WHERE exit_time IS NULL'
        elif status == 'closed':
            query += ' WHERE exit_time IS NOT NULL'
        
        query += ' ORDER BY entry_time DESC LIMIT ?'
        
        cursor = conn.execute(query, (limit,))
        
        trades = []
        for row in cursor.fetchall():
            trade = {
                'trade_id': row['trade_id'],
                'symbol': row['symbol'],
                'direction': row['direction'],
                'entry_time': row['entry_time'],
                'entry_price': row['entry_price'],
                'position_size': row['position_size'],
                'leverage': row['leverage'],
                'margin': row['margin'],
                'stop_loss': row['stop_loss'],
                'take_profit': json.loads(row['take_profit']),
                'exit_time': row['exit_time'],
                'exit_price': row['exit_price'],
                'exit_reason': row['exit_reason'],
                'pnl': round(row['pnl'], 2) if row['pnl'] else None,
                'pnl_percent': round(row['pnl_percent'] * 100, 2) if row['pnl_percent'] else None,
                'confidence': row['confidence'],
                'reasoning': row['reasoning']
            }
            trades.append(trade)
        
        conn.close()
        
        return jsonify({'success': True, 'data': trades})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/trade/equity')
def api_equity_curve():
    """API: 获取资金曲线"""
    try:
        conn = get_db_connection()
        
        cursor = conn.execute('''
            SELECT timestamp, balance, total_pnl
            FROM equity_curve
            ORDER BY timestamp
        ''')
        
        equity = []
        for row in cursor.fetchall():
            equity.append({
                'timestamp': row['timestamp'],
                'balance': round(row['balance'], 2),
                'total_pnl': round(row['total_pnl'], 2)
            })
        
        conn.close()
        
        return jsonify({'success': True, 'data': equity})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print("=" * 60)
    print("🌐 战颅将军交易展示页面")
    print("=" * 60)
    print("访问地址: http://localhost:5050/trade")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5050, debug=True)
