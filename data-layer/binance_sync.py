#!/usr/bin/env python3
"""
币安K线数据同步服务
支持多时间维度数据获取和存储
"""

import requests
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading'))

BINANCE_API_BASE = 'https://api.binance.com'
DB_PATH = os.path.expanduser('~/.openclaw/workspace/quant-trading/data/market_data.db')

# 时间维度映射
INTERVAL_MAP = {
    '5m': '5m',
    '15m': '15m',
    '30m': '30m',
    '1h': '1h',
    '4h': '4h',
    '12h': '12h',
    '1d': '1d',
    '1w': '1w',
    '1M': '1M'
}

# 每个时间维度的毫秒数
INTERVAL_MS = {
    '5m': 5 * 60 * 1000,
    '15m': 15 * 60 * 1000,
    '30m': 30 * 60 * 1000,
    '1h': 60 * 60 * 1000,
    '4h': 4 * 60 * 60 * 1000,
    '12h': 12 * 60 * 60 * 1000,
    '1d': 24 * 60 * 60 * 1000,
    '1w': 7 * 24 * 60 * 60 * 1000,
    '1M': 30 * 24 * 60 * 60 * 1000
}


class BinanceSyncService:
    """币安数据同步服务"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._init_tables()
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_tables(self):
        """初始化数据表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # K线数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kline_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                interval TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                quote_volume REAL,
                trades INTEGER,
                macd REAL,
                macd_signal REAL,
                macd_hist REAL,
                kdj_k REAL,
                kdj_d REAL,
                kdj_j REAL,
                source TEXT DEFAULT 'binance',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, interval, timestamp)
            )
        ''')
        
        # 数据同步状态表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_sync_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                interval TEXT NOT NULL,
                last_sync_time DATETIME,
                last_candle_time DATETIME,
                records_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                error_msg TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, interval)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def fetch_klines(self, symbol: str, interval: str, start_time: int = None, 
                     end_time: int = None, limit: int = 1000) -> List[Dict]:
        """
        从币安API获取K线数据
        
        Args:
            symbol: 交易对，如 BTCUSDT
            interval: 时间维度，如 15m, 1h, 1d
            start_time: 开始时间（毫秒戳）
            end_time: 结束时间（毫秒戳）
            limit: 返回条数限制，最大1000
        """
        url = f'{BINANCE_API_BASE}/api/v3/klines'
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            klines = []
            for item in data:
                klines.append({
                    'timestamp': datetime.fromtimestamp(item[0] / 1000),
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5]),
                    'quote_volume': float(item[7]),
                    'trades': int(item[8])
                })
            
            return klines
            
        except Exception as e:
            print(f"[错误] 获取K线数据失败: {e}")
            return []
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        计算MACD指标
        """
        df = df.copy()
        
        # 计算EMA
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        # MACD线
        df['macd'] = ema_fast - ema_slow
        # 信号线
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        # MACD柱状图
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def calculate_kdj(self, df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """
        计算KDJ指标
        """
        df = df.copy()
        
        # 计算N日内的最高价、最低价、收盘价
        low_list = df['low'].rolling(window=n, min_periods=n).min()
        high_list = df['high'].rolling(window=n, min_periods=n).max()
        rsv = (df['close'] - low_list) / (high_list - low_list) * 100
        
        # 计算K、D、J值
        df['kdj_k'] = rsv.ewm(com=m1-1, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(com=m2-1, adjust=False).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算所有技术指标"""
        df = self.calculate_macd(df)
        df = self.calculate_kdj(df)
        return df
    
    def save_klines(self, symbol: str, interval: str, klines: List[Dict]):
        """
        保存K线数据到数据库
        """
        if not klines:
            return 0
        
        # 转换为DataFrame计算指标
        df = pd.DataFrame(klines)
        df = self.calculate_indicators(df)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        inserted = 0
        for _, row in df.iterrows():
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO kline_data
                    (symbol, interval, timestamp, open, high, low, close, volume,
                     quote_volume, trades, macd, macd_signal, macd_hist,
                     kdj_k, kdj_d, kdj_j, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, interval, row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    row['open'], row['high'], row['low'], row['close'], row['volume'],
                    row.get('quote_volume', 0), row.get('trades', 0),
                    row.get('macd'), row.get('macd_signal'), row.get('macd_hist'),
                    row.get('kdj_k'), row.get('kdj_d'), row.get('kdj_j'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                inserted += 1
            except Exception as e:
                print(f"[错误] 保存数据失败: {e}")
        
        conn.commit()
        conn.close()
        
        return inserted
    
    def update_sync_status(self, symbol: str, interval: str, status: str, 
                          last_candle_time: datetime = None, records: int = 0, error: str = None):
        """更新同步状态"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO data_sync_status
            (symbol, interval, last_sync_time, last_candle_time, records_count, status, error_msg, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol, interval,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            last_candle_time.strftime('%Y-%m-%d %H:%M:%S') if last_candle_time else None,
            records, status, error,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        conn.commit()
        conn.close()
    
    def sync_historical_data(self, symbol: str, interval: str, 
                            start_date: datetime = None, end_date: datetime = None):
        """
        同步历史数据
        
        Args:
            symbol: 交易对
            interval: 时间维度
            start_date: 开始日期，默认2026-01-01
            end_date: 结束日期，默认当前时间
        """
        if start_date is None:
            start_date = datetime(2026, 1, 1)
        if end_date is None:
            end_date = datetime.now()
        
        print(f"[同步] {symbol} {interval} 历史数据: {start_date} 至 {end_date}")
        
        self.update_sync_status(symbol, interval, 'syncing')
        
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)
        
        total_inserted = 0
        current_start = start_ms
        
        # 币安API每次最多返回1000条数据
        while current_start < end_ms:
            klines = self.fetch_klines(
                symbol, interval,
                start_time=current_start,
                limit=1000
            )
            
            if not klines:
                break
            
            inserted = self.save_klines(symbol, interval, klines)
            total_inserted += inserted
            
            print(f"[进度] 已保存 {inserted} 条数据，共 {total_inserted} 条")
            
            # 更新下一次起始时间
            last_timestamp = int(klines[-1]['timestamp'].timestamp() * 1000)
            if last_timestamp <= current_start:
                break
            current_start = last_timestamp + INTERVAL_MS.get(interval, 60000)
            
            # 防止请求过快
            time.sleep(0.1)
        
        self.update_sync_status(
            symbol, interval, 'completed',
            last_candle_time=klines[-1]['timestamp'] if klines else None,
            records=total_inserted
        )
        
        print(f"[完成] {symbol} {interval} 共同步 {total_inserted} 条数据")
        return total_inserted
    
    def sync_realtime_data(self, symbol: str, interval: str):
        """
        同步实时数据（最近的几根K线）
        """
        print(f"[实时同步] {symbol} {interval}")
        
        # 获取最近的200根K线
        klines = self.fetch_klines(symbol, interval, limit=200)
        
        if klines:
            inserted = self.save_klines(symbol, interval, klines)
            self.update_sync_status(
                symbol, interval, 'completed',
                last_candle_time=klines[-1]['timestamp'],
                records=inserted
            )
            print(f"[完成] 更新 {inserted} 条数据")
            return inserted
        
        return 0
    
    def sync_all_intervals(self, symbol: str = 'BTCUSDT', intervals: List[str] = None):
        """
        同步所有时间维度的数据
        """
        if intervals is None:
            intervals = ['5m', '15m', '30m', '1h', '4h', '12h', '1d', '1w', '1M']
        
        print(f"=" * 60)
        print(f"[开始全量同步] {symbol}")
        print(f"=" * 60)
        
        for interval in intervals:
            print()
            try:
                # 对于大周期数据，同步更长的历史
                if interval in ['1w', '1M']:
                    start_date = datetime(2020, 1, 1)
                elif interval in ['1d', '12h']:
                    start_date = datetime(2025, 1, 1)
                else:
                    start_date = datetime(2026, 1, 1)
                
                self.sync_historical_data(symbol, interval, start_date)
                
            except Exception as e:
                print(f"[错误] {interval} 同步失败: {e}")
                self.update_sync_status(symbol, interval, 'error', error=str(e))
        
        print()
        print(f"=" * 60)
        print(f"[全量同步完成] {symbol}")
        print(f"=" * 60)


def main():
    """主函数"""
    service = BinanceSyncService()
    
    # 同步BTC所有时间维度的历史数据
    service.sync_all_intervals('BTCUSDT')


if __name__ == '__main__':
    main()
