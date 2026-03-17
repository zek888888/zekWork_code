#!/usr/bin/env python3
"""
数据获取器
负责获取市场数据和K线数据
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "config-layer"))

from ai_config_manager import AIConfigManager

logger = logging.getLogger('DataFetcher')


class DataFetcher:
    """
    数据获取器
    从数据库获取预测所需的市场数据
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(PROJECT_ROOT / "data" / "market_data.db")
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_latest_data(
        self,
        symbol: str,
        interval: str,
        limit: int = 20
    ) -> Optional[Dict]:
        """
        获取最新的市场数据
        
        Args:
            symbol: 交易对符号
            interval: 时间维度
            limit: 获取K线数量
            
        Returns:
            Dict: 包含最新价格和指标的字典
        """
        klines = self.get_klines(symbol, interval, limit)
        
        if not klines or len(klines) < 5:
            logger.warning(f"[数据不足] {symbol} {interval}, 只有 {len(klines) if klines else 0} 条")
            return None
        
        latest = klines[-1]
        
        # 计算额外指标
        price_change_24h = self._calculate_price_change(symbol, interval, hours=24)
        volume_avg = sum(k['volume'] for k in klines[-5:]) / 5
        
        return {
            'symbol': symbol,
            'interval': interval,
            'timestamp': latest['timestamp'],
            'open': latest['open'],
            'high': latest['high'],
            'low': latest['low'],
            'close': latest['close'],
            'volume': latest['volume'],
            'price_change_24h': price_change_24h,
            'volume_avg': volume_avg,
            'macd': latest['macd'],
            'macd_signal': latest['macd_signal'],
            'macd_hist': latest['macd_hist'],
            'kdj_k': latest['kdj_k'],
            'kdj_d': latest['kdj_d'],
            'kdj_j': latest['kdj_j'],
            'klines': klines  # 返回完整K线数据供分析
        }
    
    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号
            interval: 时间维度
            limit: 数量限制
            
        Returns:
            List[Dict]: K线数据列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    timestamp,
                    open, high, low, close, volume,
                    macd, macd_signal, macd_hist,
                    kdj_k, kdj_d, kdj_j
                FROM kline_data
                WHERE symbol = ? AND interval = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (symbol, interval, limit))
            
            rows = cursor.fetchall()
            
            # 转换为列表（从旧到新）
            klines = []
            for row in reversed(rows):
                klines.append({
                    'timestamp': row['timestamp'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']),
                    'macd': float(row['macd']) if row['macd'] else 0,
                    'macd_signal': float(row['macd_signal']) if row['macd_signal'] else 0,
                    'macd_hist': float(row['macd_hist']) if row['macd_hist'] else 0,
                    'kdj_k': float(row['kdj_k']) if row['kdj_k'] else 50,
                    'kdj_d': float(row['kdj_d']) if row['kdj_d'] else 50,
                    'kdj_j': float(row['kdj_j']) if row['kdj_j'] else 50
                })
            
            return klines
            
        except Exception as e:
            logger.error(f"[获取K线失败] {e}")
            return []
        finally:
            conn.close()
    
    def get_price_at_time(
        self,
        symbol: str,
        interval: str,
        target_time: datetime
    ) -> Optional[float]:
        """
        获取指定时间点的价格
        
        Args:
            symbol: 交易对
            interval: 时间维度
            target_time: 目标时间
            
        Returns:
            float: 价格
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT close FROM kline_data
                WHERE symbol = ? AND interval = ?
                AND timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (symbol, interval, target_time))
            
            row = cursor.fetchone()
            return float(row['close']) if row else None
            
        except Exception as e:
            logger.error(f"[获取历史价格失败] {e}")
            return None
        finally:
            conn.close()
    
    def get_price_range(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        获取时间范围内的价格统计
        
        Args:
            symbol: 交易对
            interval: 时间维度
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            Tuple: (开盘价, 收盘价, 最大涨跌幅)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    MIN(low) as min_price,
                    MAX(high) as max_price,
                    open as first_open,
                    close as last_close
                FROM kline_data
                WHERE symbol = ? AND interval = ?
                AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, (symbol, interval, start_time, end_time))
            
            row = cursor.fetchone()
            
            if row and row['first_open']:
                open_price = float(row['first_open'])
                close_price = float(row['last_close'])
                max_change = ((float(row['max_price']) - float(row['min_price'])) / float(row['min_price'])) * 100
                
                return open_price, close_price, max_change
            
            return None, None, None
            
        except Exception as e:
            logger.error(f"[获取价格区间失败] {e}")
            return None, None, None
        finally:
            conn.close()
    
    def _calculate_price_change(
        self,
        symbol: str,
        interval: str,
        hours: int = 24
    ) -> Optional[float]:
        """计算指定时间内的价格变化"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT close FROM kline_data
                WHERE symbol = ? AND interval = ?
                AND timestamp >= ?
                ORDER BY timestamp ASC
                LIMIT 1
            """, (symbol, interval, cutoff_time))
            
            old_row = cursor.fetchone()
            
            cursor.execute("""
                SELECT close FROM kline_data
                WHERE symbol = ? AND interval = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (symbol, interval))
            
            new_row = cursor.fetchone()
            
            if old_row and new_row:
                old_price = float(old_row['close'])
                new_price = float(new_row['close'])
                return ((new_price - old_price) / old_price) * 100
            
            return None
            
        except Exception as e:
            logger.error(f"[计算价格变化失败] {e}")
            return None
        finally:
            conn.close()
    
    def check_data_freshness(
        self,
        symbol: str,
        interval: str,
        max_delay_minutes: int = 10
    ) -> Tuple[bool, Optional[datetime]]:
        """
        检查数据新鲜度
        
        Args:
            symbol: 交易对
            interval: 时间维度
            max_delay_minutes: 最大容忍延迟（分钟）
            
        Returns:
            Tuple[bool, datetime]: (是否新鲜, 最新数据时间)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT MAX(timestamp) as latest
                FROM kline_data
                WHERE symbol = ? AND interval = ?
            """, (symbol, interval))
            
            row = cursor.fetchone()
            
            if not row or not row['latest']:
                return False, None
            
            latest_time = datetime.fromisoformat(row['latest'])
            delay = datetime.now() - latest_time
            
            is_fresh = delay <= timedelta(minutes=max_delay_minutes)
            
            if not is_fresh:
                logger.warning(f"[数据过期] {symbol} {interval} 延迟 {delay.total_seconds()/60:.1f} 分钟")
            
            return is_fresh, latest_time
            
        except Exception as e:
            logger.error(f"[检查数据新鲜度失败] {e}")
            return False, None
        finally:
            conn.close()
    
    def get_available_symbols(self) -> List[str]:
        """获取可用的交易对列表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT symbol FROM kline_data
                ORDER BY symbol
            """)
            
            return [row['symbol'] for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"[获取交易对列表失败] {e}")
            return []
        finally:
            conn.close()
    
    def get_available_intervals(self, symbol: str) -> List[str]:
        """获取指定交易对的可用时间维度"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT interval FROM kline_data
                WHERE symbol = ?
                ORDER BY interval
            """, (symbol,))
            
            return [row['interval'] for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"[获取时间维度失败] {e}")
            return []
        finally:
            conn.close()


if __name__ == '__main__':
    # 测试
    fetcher = DataFetcher()
    
    # 获取最新数据
    data = fetcher.get_latest_data('BTCUSDT', '15m')
    if data:
        print(f"\u6700新价格: ${data['close']:,.2f}")
        print(f"MACD: {data['macd_hist']:.2f}")
        print(f"KDJ J: {data['kdj_j']:.2f}")
        print(f"24h涨跌: {data['price_change_24h']:.2f}%")
    
    # 检查数据新鲜度
    is_fresh, latest = fetcher.check_data_freshness('BTCUSDT', '15m')
    print(f"\u6570据新鲜: {is_fresh}, 最新时间: {latest}")
