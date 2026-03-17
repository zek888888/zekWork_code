#!/usr/bin/env python3
"""
启动战颅将军模拟盘交易系统
一键启动: 数据收集 → Web展示
"""

import os
import sys
import subprocess
import time
import signal
import sqlite3
from datetime import datetime

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
DB_PATH = f"{PROJECT_ROOT}/data/market_data.db"
PID_FILE = f"{PROJECT_ROOT}/.web_server.pid"

sys.path.insert(0, PROJECT_ROOT)


def print_banner():
    print("=" * 70)
    print("⚔️  战颅将军 - 模拟盘交易系统")
    print("=" * 70)
    print("""
    🙏 千手财童  →  📊 数据收集 (2021-至今)
       ↓
    🔮 神算子    →  📈 预测分析 (15m级别)
       ↓
    ⚔️  战颅将军  →  💰 模拟交易 (5m级别)
       ↓
    🌐 Web展示   →  📊 交易记录 (http://localhost:5000/trade)
    
    🤖 AI配置 (全DeepSeek阵容):
       战颅将军/铁算/史官/谋师: DeepSeek-R1 (量化背景)
       影谍/宪兵: DeepSeek-Chat (快速响应)
    
    💰 交易配置:
       启动资金: 10,000 USDT
       交易级别: 5分钟
       数据范围: 2021-01-01 至今
       技术指标: MACD, KDJ, Bollinger Bands
    """)
    print("=" * 70)


def check_database():
    """检查数据库状态"""
    print("\n📦 检查数据库...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = ['kline_data', 'simulated_trades', 'equity_curve']
    
    for table in required_tables:
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table}: {count} 条记录")
        else:
            print(f"  ✗ {table}: 表不存在，正在创建...")
            if table == 'simulated_trades':
                cursor.execute('''
                    CREATE TABLE simulated_trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trade_id TEXT UNIQUE NOT NULL,
                        symbol TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        entry_time TIMESTAMP NOT NULL,
                        entry_price REAL NOT NULL,
                        position_size REAL NOT NULL,
                        leverage INTEGER NOT NULL,
                        margin REAL NOT NULL,
                        stop_loss REAL NOT NULL,
                        take_profit TEXT NOT NULL,
                        exit_time TIMESTAMP,
                        exit_price REAL,
                        exit_reason TEXT,
                        pnl REAL DEFAULT 0,
                        pnl_percent REAL DEFAULT 0,
                        confidence REAL,
                        reasoning TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            elif table == 'equity_curve':
                cursor.execute('''
                    CREATE TABLE equity_curve (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        balance REAL NOT NULL DEFAULT 10000,
                        total_trades INTEGER DEFAULT 0,
                        win_trades INTEGER DEFAULT 0,
                        loss_trades INTEGER DEFAULT 0,
                        total_pnl REAL DEFAULT 0
                    )
                ''')
                # 初始化资金曲线
                cursor.execute('''
                    INSERT INTO equity_curve (balance) VALUES (10000)
                ''')
            print(f"  ✓ {table}: 表已创建")
    
    # 检查K线数据摘要
    if 'kline_data' in tables:
        print("\n  📊 K线数据摘要:")
        # 使用正确的列名 'interval' 而不是 'timeframe'
        cursor.execute('''
            SELECT interval, COUNT(*) as cnt, 
                   MIN(datetime(timestamp/1000, 'unixepoch')) as start,
                   MAX(datetime(timestamp/1000, 'unixepoch')) as end
            FROM kline_data 
            WHERE symbol = 'BTC/USDT'
            GROUP BY interval
            ORDER BY cnt DESC
        ''')
        for row in cursor.fetchall():
            print(f"    {row[0]:4s}: {row[1]:6,} 条 | {row[2][:10]} ~ {row[3][:10]}")
    
    conn.commit()
    conn.close()


def start_web_server():
    """启动Web展示服务"""
    print("\n🌐 启动Web展示服务...")
    
    # 检查是否已在运行
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            old_pid = f.read().strip()
        try:
            os.kill(int(old_pid), 0)
            print(f"  ⚠️  Web服务已在运行 (PID: {old_pid})")
            return True
        except:
            os.remove(PID_FILE)
    
    # 启动新进程
    web_script = f"{PROJECT_ROOT}/web_trade.py"
    
    proc = subprocess.Popen(
        [sys.executable, web_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=PROJECT_ROOT
    )
    
    # 保存PID
    with open(PID_FILE, 'w') as f:
        f.write(str(proc.pid))
    
    # 等待服务启动
    time.sleep(2)
    
    print(f"  ✓ Web服务已启动 (PID: {proc.pid})")
    print(f"  📍 访问地址: http://localhost:5000/trade")
    
    return True


def check_data_collection():
    """检查是否需要数据收集"""
    print("\n📊 检查历史数据...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查是否有数据
    cursor.execute("SELECT COUNT(*) FROM kline_data WHERE symbol = 'BTC/USDT'")
    count = cursor.fetchone()[0]
    
    conn.close()
    
    if count == 0:
        print("  ⚠️  未检测到BTC历史数据")
        print("\n  是否需要启动数据收集? (这将从2021-01-01开始下载，耗时约10-20分钟)")
        response = input("  启动数据收集? [y/N]: ").strip().lower()
        
        if response == 'y':
            print("\n  🚀 启动千手财童数据收集...")
            collector_script = f"{PROJECT_ROOT}/千手财童_data_collector.py"
            subprocess.run([sys.executable, collector_script], cwd=PROJECT_ROOT)
        else:
            print("  ⏭️  跳过数据收集")
    else:
        print(f"  ✓ 已有 {count:,} 条历史数据")


def stop_web_server():
    """停止Web服务"""
    print("\n🛑 停止Web服务...")
    
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = f.read().strip()
        try:
            os.kill(int(pid), signal.SIGTERM)
            print(f"  ✓ 已停止Web服务 (PID: {pid})")
        except ProcessLookupError:
            print("  ⚠️  进程已不存在")
        os.remove(PID_FILE)
    else:
        print("  ℹ️  Web服务未运行")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='战颅将军模拟盘交易系统')
    parser.add_argument('command', choices=['start', 'stop', 'status'], 
                       nargs='?', default='start',
                       help='命令: start/stop/status')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        print_banner()
        
        # 检查数据库
        check_database()
        
        # 检查数据收集
        check_data_collection()
        
        # 启动Web服务
        start_web_server()
        
        print("\n" + "=" * 70)
        print("✅ 系统启动完成!")
        print("=" * 70)
        print("\n可用操作:")
        print("  • 查看交易记录: http://localhost:5000/trade")
        print("  • 停止服务: python 启动模拟盘系统.py stop")
        print("\n按 Ctrl+C 停止")
        print("=" * 70)
        
        # 保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_web_server()
    
    elif args.command == 'stop':
        stop_web_server()
    
    elif args.command == 'status':
        print_banner()
        check_database()
        
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                pid = f.read().strip()
            try:
                os.kill(int(pid), 0)
                print(f"\n🟢 Web服务运行中 (PID: {pid})")
            except:
                print("\n🔴 Web服务未运行")
        else:
            print("\n🔴 Web服务未运行")


if __name__ == "__main__":
    main()
