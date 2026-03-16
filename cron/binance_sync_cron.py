#!/usr/bin/env python3
"""
币安数据定时同步任务
每5分钟执行一次，同步所有时间维度的数据
"""

import sys
import os
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading'))
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/data-layer'))

from binance_sync import BinanceSyncService
from datetime import datetime
import time


def sync_all_intervals():
    """同步所有时间维度的数据"""
    service = BinanceSyncService()
    
    # 需要实时更新的时间维度
    intervals = ['5m', '15m', '30m', '1h', '4h', '12h', '1d', '1w', '1M']
    symbol = 'BTCUSDT'
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始同步币安数据...")
    
    for interval in intervals:
        try:
            print(f"  同步 {interval}...")
            service.sync_realtime_data(symbol, interval)
            time.sleep(0.5)  # 避免请求过快
        except Exception as e:
            print(f"  {interval} 同步失败: {e}")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 同步完成")


def sync_historical_if_needed():
    """检查并补全历史数据（每天执行一次）"""
    service = BinanceSyncService()
    
    # 检查是否需要全量同步
    intervals_to_check = ['5m', '15m', '30m', '1h', '4h']
    
    for interval in intervals_to_check:
        try:
            # 检查数据库中的数据量
            import sqlite3
            conn = sqlite3.connect(service.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM kline_data 
                WHERE symbol = 'BTCUSDT' AND interval = ?
            ''', (interval,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            # 如果数据量不足，执行历史同步
            expected_min = {
                '5m': 1000,
                '15m': 500,
                '30m': 300,
                '1h': 200,
                '4h': 100
            }
            
            if count < expected_min.get(interval, 100):
                print(f"[{interval}] 数据量不足({count})，执行历史同步...")
                from datetime import datetime
                start_date = datetime(2026, 1, 1)
                service.sync_historical_data('BTCUSDT', interval, start_date)
            else:
                print(f"[{interval}] 数据量正常({count})")
                
        except Exception as e:
            print(f"  {interval} 检查失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='币安数据同步任务')
    parser.add_argument('--full', action='store_true', help='执行全量历史数据同步')
    parser.add_argument('--check', action='store_true', help='检查并补全缺失数据')
    
    args = parser.parse_args()
    
    if args.full:
        # 全量同步
        service = BinanceSyncService()
        service.sync_all_intervals('BTCUSDT')
    elif args.check:
        # 检查并补全
        sync_historical_if_needed()
    else:
        # 实时同步
        sync_all_intervals()


if __name__ == '__main__':
    main()
