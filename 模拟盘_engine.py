#!/usr/bin/env python3
"""
模拟盘交易引擎
启动资金10000U，5分钟级别交易，记录所有交易
"""

import os
import sys
import json
import time
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('模拟盘')

DB_PATH = "/Users/mac/.openclaw/workspace/quant-trading/data/market_data.db"


@dataclass
class TradeRecord:
    """交易记录"""
    trade_id: str
    symbol: str
    direction: str  # long/short
    entry_time: datetime
    entry_price: float
    position_size: float  # 仓位比例
    leverage: int
    margin: float  # 保证金
    stop_loss: float
    take_profit: List[float]
    
    # 平仓信息（平仓后填充）
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None  # stop_loss/take_profit/timeout/manual
    
    # 盈亏计算
    pnl: float = 0  # 盈亏金额
    pnl_percent: float = 0  # 盈亏百分比
    
    # 决策信息
    confidence: float = 0
    reasoning: str = ""


class 模拟盘引擎:
    """模拟盘交易引擎"""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions: List[TradeRecord] = []  # 当前持仓
        self.trade_history: List[TradeRecord] = []  # 历史交易
        self.trade_counter = 0
        
        self._init_database()
        logger.info(f"[模拟盘] 初始化完成，启动资金: {initial_balance} USDT")
    
    def _init_database(self):
        """初始化交易记录表"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulated_trades (
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
                take_profit TEXT NOT NULL,  -- JSON array
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
        
        # 资金曲线表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equity_curve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                balance REAL NOT NULL,
                total_trades INTEGER DEFAULT 0,
                win_trades INTEGER DEFAULT 0,
                loss_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("[模拟盘] 数据库表初始化完成")
    
    def 开仓(self, symbol: str, direction: str, entry_price: float,
            position_size: float, leverage: int, stop_loss: float,
            take_profit: List[float], confidence: float, reasoning: str) -> Optional[TradeRecord]:
        """开仓"""
        
        # 检查是否有足够资金
        margin = self.current_balance * position_size / leverage
        if margin > self.current_balance * 0.95:  # 保留5%缓冲
            logger.error(f"[模拟盘] 资金不足，无法开仓")
            return None
        
        # 生成交易ID
        self.trade_counter += 1
        trade_id = f"TRADE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.trade_counter}"
        
        trade = TradeRecord(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            entry_time=datetime.now(),
            entry_price=entry_price,
            position_size=position_size,
            leverage=leverage,
            margin=margin,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            reasoning=reasoning
        )
        
        # 冻结保证金
        self.current_balance -= margin
        
        # 保存到持仓列表
        self.positions.append(trade)
        
        # 保存到数据库
        self._保存交易记录(trade)
        
        logger.info("=" * 60)
        logger.info(f"[模拟盘] 🟢 开仓成功")
        logger.info(f"交易ID: {trade_id}")
        logger.info(f"方向: {direction.upper()}")
        logger.info(f"入场价: {entry_price}")
        logger.info(f"仓位: {position_size*100:.1f}%")
        logger.info(f"杠杆: {leverage}x")
        logger.info(f"保证金: {margin:.2f} USDT")
        logger.info(f"剩余资金: {self.current_balance:.2f} USDT")
        logger.info("=" * 60)
        
        return trade
    
    def 平仓(self, trade_id: str, exit_price: float, exit_reason: str) -> Optional[TradeRecord]:
        """平仓"""
        # 查找持仓
        trade = None
        for i, t in enumerate(self.positions):
            if t.trade_id == trade_id:
                trade = t
                del self.positions[i]
                break
        
        if not trade:
            logger.error(f"[模拟盘] 未找到持仓: {trade_id}")
            return None
        
        # 计算盈亏
        if trade.direction == 'long':
            pnl_percent = (exit_price - trade.entry_price) / trade.entry_price
        else:  # short
            pnl_percent = (trade.entry_price - exit_price) / trade.entry_price
        
        # 杠杆放大盈亏
        pnl_percent *= trade.leverage
        
        # 计算盈亏金额
        pnl = trade.margin * pnl_percent
        
        # 更新交易记录
        trade.exit_time = datetime.now()
        trade.exit_price = exit_price
        trade.exit_reason = exit_reason
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        
        # 返还保证金和盈亏
        self.current_balance += trade.margin + pnl
        
        # 保存到历史记录
        self.trade_history.append(trade)
        
        # 更新数据库
        self._更新平仓记录(trade)
        
        # 记录资金曲线
        self._记录资金曲线()
        
        # 显示结果
        result_emoji = "✅" if pnl > 0 else "❌"
        logger.info("=" * 60)
        logger.info(f"[模拟盘] {result_emoji} 平仓成功")
        logger.info(f"交易ID: {trade_id}")
        logger.info(f"出场价: {exit_price}")
        logger.info(f"出场原因: {exit_reason}")
        logger.info(f"盈亏: {pnl:+.2f} USDT ({pnl_percent*100:+.2f}%)")
        logger.info(f"当前资金: {self.current_balance:.2f} USDT")
        logger.info("=" * 60)
        
        return trade
    
    def 检查持仓(self, current_price: float):
        """检查所有持仓是否触发止盈止损"""
        closed_positions = []
        
        for trade in self.positions[:]:  # 复制列表避免修改时出错
            # 检查止损
            if trade.direction == 'long':
                if current_price <= trade.stop_loss:
                    self.平仓(trade.trade_id, current_price, 'stop_loss')
                    closed_positions.append((trade.trade_id, '止损'))
                elif current_price >= trade.take_profit[0]:
                    self.平仓(trade.trade_id, current_price, 'take_profit_1')
                    closed_positions.append((trade.trade_id, '止盈1'))
            else:  # short
                if current_price >= trade.stop_loss:
                    self.平仓(trade.trade_id, current_price, 'stop_loss')
                    closed_positions.append((trade.trade_id, '止损'))
                elif current_price <= trade.take_profit[0]:
                    self.平仓(trade.trade_id, current_price, 'take_profit_1')
                    closed_positions.append((trade.trade_id, '止盈1'))
            
            # 检查持仓时间（超过8小时强制平仓）
            hold_time = datetime.now() - trade.entry_time
            if hold_time > timedelta(hours=8):
                self.平仓(trade.trade_id, current_price, 'timeout')
                closed_positions.append((trade.trade_id, '超时平仓'))
        
        return closed_positions
    
    def _保存交易记录(self, trade: TradeRecord):
        """保存交易记录到数据库"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO simulated_trades 
            (trade_id, symbol, direction, entry_time, entry_price, 
             position_size, leverage, margin, stop_loss, take_profit,
             confidence, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.trade_id, trade.symbol, trade.direction,
            trade.entry_time, trade.entry_price,
            trade.position_size, trade.leverage, trade.margin,
            trade.stop_loss, json.dumps(trade.take_profit),
            trade.confidence, trade.reasoning
        ))
        
        conn.commit()
        conn.close()
    
    def _更新平仓记录(self, trade: TradeRecord):
        """更新平仓信息"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE simulated_trades 
            SET exit_time = ?, exit_price = ?, exit_reason = ?,
                pnl = ?, pnl_percent = ?
            WHERE trade_id = ?
        ''', (
            trade.exit_time, trade.exit_price, trade.exit_reason,
            trade.pnl, trade.pnl_percent, trade.trade_id
        ))
        
        conn.commit()
        conn.close()
    
    def _记录资金曲线(self):
        """记录资金曲线"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        total_pnl = sum(t.pnl for t in self.trade_history)
        win_trades = len([t for t in self.trade_history if t.pnl > 0])
        loss_trades = len([t for t in self.trade_history if t.pnl < 0])
        
        cursor.execute('''
            INSERT INTO equity_curve 
            (balance, total_trades, win_trades, loss_trades, total_pnl)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            self.current_balance,
            len(self.trade_history),
            win_trades,
            loss_trades,
            total_pnl
        ))
        
        conn.commit()
        conn.close()
    
    def 获取统计(self) -> Dict:
        """获取交易统计"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'current_balance': self.current_balance
            }
        
        total = len(self.trade_history)
        wins = len([t for t in self.trade_history if t.pnl > 0])
        losses = len([t for t in self.trade_history if t.pnl < 0])
        total_pnl = sum(t.pnl for t in self.trade_history)
        
        return {
            'total_trades': total,
            'win_trades': wins,
            'loss_trades': losses,
            'win_rate': wins / total if total > 0 else 0,
            'total_pnl': total_pnl,
            'current_balance': self.current_balance,
            'return_percent': (self.current_balance - self.initial_balance) / self.initial_balance * 100
        }


if __name__ == "__main__":
    print("=" * 60)
    print("💰 模拟盘引擎测试")
    print("=" * 60)
    
    引擎 = 模拟盘引擎(initial_balance=10000)
    
    # 模拟开仓
    trade = 引擎.开仓(
        symbol='BTCUSDT',
        direction='long',
        entry_price=65000,
        position_size=0.1,
        leverage=5,
        stop_loss=64000,
        take_profit=[66500, 68000],
        confidence=0.75,
        reasoning='测试开仓'
    )
    
    if trade:
        # 模拟平仓
        time.sleep(1)
        引擎.平仓(trade.trade_id, 66000, 'take_profit')
    
    # 查看统计
    stats = 引擎.获取统计()
    print("\n📊 交易统计:")
    print(f"总交易: {stats['total_trades']}")
    print(f"胜率: {stats['win_rate']*100:.1f}%")
    print(f"总盈亏: {stats['total_pnl']:+.2f} USDT")
    print(f"当前资金: {stats['current_balance']:.2f} USDT")
    print(f"收益率: {stats['return_percent']:+.2f}%")
