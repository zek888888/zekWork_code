#!/usr/bin/env python3
"""
千手财童 (Thousand Hands Treasurer)
数据收集智能体 - 从2021年开始获取BTC历史数据

支持多时间框架:
- 5m, 15m, 30m - 短期交易
- 1h, 2h, 4h, 12h - 中期趋势
- 1d, 1w, 1M, 1q - 长期分析

使用 ccxt 从 Binance 获取数据
"""

import os
import sys
import ccxt
import sqlite3
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# 配置
PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
DB_PATH = f"{PROJECT_ROOT}/data/market_data.db"
START_DATE = "2021-01-01"

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('千手财童')


class 千手财童:
    """
    千手财童 - 数据收集智能体
    负责收集BTC历史数据和实时数据
    """
    
    def __init__(self):
        self.logger = logging.getLogger('千手财童')
        self.logger.info("🙏 千手财童初始化...")
        
        # 初始化交易所
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        
        # 时间框架配置
        self.timeframes = {
            '5m': {'minutes': 5, 'limit': 1000, 'description': '超短期'},
            '15m': {'minutes': 15, 'limit': 500, 'description': '短期交易'},
            '30m': {'minutes': 30, 'limit': 500, 'description': '短期趋势'},
            '1h': {'minutes': 60, 'limit': 500, 'description': '小时趋势'},
            '2h': {'minutes': 120, 'limit': 500, 'description': '双时趋势'},
            '4h': {'minutes': 240, 'limit': 500, 'description': '四时趋势'},
            '12h': {'minutes': 720, 'limit': 500, 'description': '半日趋势'},
            '1d': {'minutes': 1440, 'limit': 500, 'description': '日线趋势'},
            '1w': {'minutes': 10080, 'limit': 200, 'description': '周线趋势'},
            '1M': {'minutes': 43200, 'limit': 100, 'description': '月线趋势'},
        }
        
        self._初始化数据库()
        self.logger.info("✅ 千手财童初始化完成")
    
    def _初始化数据库(self):
        """初始化数据库表"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # K线数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kline_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                interval TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                quote_volume REAL,
                macd REAL,
                macd_signal REAL,
                macd_hist REAL,
                kdj_k REAL,
                kdj_d REAL,
                kdj_j REAL,
                boll_up REAL,
                boll_mid REAL,
                boll_down REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, interval, timestamp)
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_kline_symbol_tf_time 
            ON kline_data(symbol, interval, timestamp)
        ''')
        
        # 数据收集进度表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_collection_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                interval TEXT NOT NULL,
                last_timestamp INTEGER,
                record_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, interval)
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("[✓] 数据库表初始化完成")
    
    def 获取历史数据(self, symbol: str = 'BTC/USDT', 
                   timeframe: str = '5m',
                   since: str = START_DATE) -> pd.DataFrame:
        """
        获取历史K线数据
        
        Args:
            symbol: 交易对
            timeframe: 时间框架
            since: 开始日期 (YYYY-MM-DD)
        
        Returns:
            DataFrame with OHLCV + indicators
        """
        self.logger.info(f"📊 获取 {symbol} {timeframe} 历史数据 (从 {since})...")
        
        # 转换开始时间为毫秒时间戳
        since_dt = datetime.strptime(since, '%Y-%m-%d')
        since_ms = int(since_dt.timestamp() * 1000)
        
        all_data = []
        current_since = since_ms
        
        while True:
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, 
                    timeframe, 
                    since=current_since,
                    limit=1000
                )
                
                if not ohlcv or len(ohlcv) == 0:
                    break
                
                all_data.extend(ohlcv)
                
                # 更新since为最后一条数据的时间 + 1个时间单位
                last_timestamp = ohlcv[-1][0]
                current_since = last_timestamp + 1
                
                # 检查是否已到达当前时间
                if last_timestamp > datetime.now().timestamp() * 1000:
                    break
                
                # 防止请求过快
                self.exchange.sleep(100)
                
                if len(all_data) % 5000 == 0:
                    self.logger.info(f"   已获取 {len(all_data)} 条数据...")
                    
            except Exception as e:
                self.logger.error(f"获取数据失败: {e}")
                break
        
        if not all_data:
            self.logger.warning(f"未获取到 {symbol} {timeframe} 的历史数据")
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ])
        
        # 添加时间列
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        self.logger.info(f"✅ 成功获取 {len(df)} 条 {timeframe} 历史数据")
        
        return df
    
    def 计算技术指标(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        - MACD: 趋势指标
        - KDJ: 动量指标
        - Bollinger Bands: 波动性指标
        """
        self.logger.info("🔧 计算技术指标...")
        
        df = df.copy()
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # KDJ
        low_list = df['low'].rolling(window=9, min_periods=9).min()
        high_list = df['high'].rolling(window=9, min_periods=9).max()
        rsv = (df['close'] - low_list) / (high_list - low_list) * 100
        df['kdj_k'] = rsv.ewm(com=2, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(com=2, adjust=False).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        # Bollinger Bands
        df['boll_mid'] = df['close'].rolling(window=20, min_periods=20).mean()
        df['boll_std'] = df['close'].rolling(window=20, min_periods=20).std()
        df['boll_up'] = df['boll_mid'] + 2 * df['boll_std']
        df['boll_down'] = df['boll_mid'] - 2 * df['boll_std']
        
        self.logger.info("[✓] 技术指标计算完成")
        
        return df
    
    def 保存到数据库(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """保存数据到数据库"""
        if df.empty:
            return
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 准备数据
        records = []
        for _, row in df.iterrows():
            records.append((
                symbol, timeframe, int(row['timestamp']),
                float(row['open']), float(row['high']), 
                float(row['low']), float(row['close']), 
                float(row['volume']),
                float(row.get('macd', 0)) if pd.notna(row.get('macd')) else None,
                float(row.get('macd_signal', 0)) if pd.notna(row.get('macd_signal')) else None,
                float(row.get('macd_hist', 0)) if pd.notna(row.get('macd_hist')) else None,
                float(row.get('kdj_k', 0)) if pd.notna(row.get('kdj_k')) else None,
                float(row.get('kdj_d', 0)) if pd.notna(row.get('kdj_d')) else None,
                float(row.get('kdj_j', 0)) if pd.notna(row.get('kdj_j')) else None,
                float(row.get('boll_up', 0)) if pd.notna(row.get('boll_up')) else None,
                float(row.get('boll_mid', 0)) if pd.notna(row.get('boll_mid')) else None,
                float(row.get('boll_down', 0)) if pd.notna(row.get('boll_down')) else None,
            ))
        
        # 批量插入 (使用INSERT OR REPLACE处理重复)
        cursor.executemany('''
            INSERT OR REPLACE INTO kline_data 
            (symbol, interval, timestamp, open, high, low, close, volume,
             macd, macd_signal, macd_hist,
             kdj_k, kdj_d, kdj_j,
             boll_up, boll_mid, boll_down)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', records)
        
        # 更新进度
        last_timestamp = int(df['timestamp'].max())
        cursor.execute('''
            INSERT OR REPLACE INTO data_collection_progress 
            (symbol, interval, last_timestamp, record_count, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, timeframe, last_timestamp, len(records), datetime.now()))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"[✓] 保存 {len(records)} 条记录到数据库")
    
    def 收集完整历史数据(self, symbol: str = 'BTC/USDT'):
        """收集所有时间框架的完整历史数据"""
        self.logger.info("=" * 60)
        self.logger.info(f"🚀 开始收集 {symbol} 完整历史数据")
        self.logger.info("=" * 60)
        
        for timeframe, config in self.timeframes.items():
            self.logger.info(f"\n{'='*40}")
            self.logger.info(f"时间框架: {timeframe} ({config['description']})")
            self.logger.info(f"{'='*40}")
            
            # 获取历史数据
            df = self.获取历史数据(symbol, timeframe, START_DATE)
            
            if not df.empty:
                # 计算指标
                df = self.计算技术指标(df)
                
                # 保存到数据库
                self.保存到数据库(df, symbol, timeframe)
                
                self.logger.info(f"✅ {timeframe} 数据收集完成: {len(df)} 条记录")
            else:
                self.logger.warning(f"⚠️ {timeframe} 数据获取失败")
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🎉 所有历史数据收集完成!")
        self.logger.info("=" * 60)
    
    def 获取实时数据(self, symbol: str = 'BTC/USDT', 
                   timeframe: str = '5m') -> Optional[pd.DataFrame]:
        """获取最新K线数据"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=10)
            df = pd.DataFrame(ohlcv, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume'
            ])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            self.logger.error(f"获取实时数据失败: {e}")
            return None
    
    def 从数据库读取(self, symbol: str = 'BTC/USDT',
                    timeframe: str = '5m',
                    limit: int = 1000) -> pd.DataFrame:
        """从数据库读取历史数据"""
        conn = sqlite3.connect(DB_PATH)
        
        query = f'''
            SELECT * FROM kline_data
            WHERE symbol = ? AND interval = ?
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(symbol, timeframe, limit))
        conn.close()
        
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('timestamp')
        
        return df
    
    def 获取数据摘要(self) -> Dict:
        """获取数据收集摘要"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        summary = {}
        
        for timeframe in self.timeframes.keys():
            cursor.execute('''
                SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
                FROM kline_data
                WHERE symbol = 'BTC/USDT' AND interval = ?
            ''', (timeframe,))
            
            row = cursor.fetchone()
            if row and row[0] > 0:
                summary[timeframe] = {
                    'count': row[0],
                    'start': datetime.fromtimestamp(row[1]/1000).strftime('%Y-%m-%d'),
                    'end': datetime.fromtimestamp(row[2]/1000).strftime('%Y-%m-%d')
                }
        
        conn.close()
        return summary


if __name__ == "__main__":
    print("=" * 60)
    print("🙏 千手财童 - BTC历史数据收集器")
    print("=" * 60)
    print(f"\n数据范围: 2021-01-01 至今")
    print("时间框架: 5m, 15m, 30m, 1h, 2h, 4h, 12h, 1d, 1w, 1M")
    print("技术指标: MACD, KDJ, Bollinger Bands")
    print("\n" + "=" * 60)
    
    # 创建实例
    财童 = 千手财童()
    
    # 收集完整历史数据
    财童.收集完整历史数据('BTC/USDT')
    
    # 显示数据摘要
    print("\n📊 数据收集摘要:")
    summary = 财童.获取数据摘要()
    for tf, info in summary.items():
        print(f"  {tf:4s}: {info['count']:6d} 条 | {info['start']} ~ {info['end']}")
    
    print("\n" + "=" * 60)
    print("数据收集完成!")
    print("=" * 60)
