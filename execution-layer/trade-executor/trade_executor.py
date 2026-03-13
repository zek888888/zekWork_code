#!/usr/bin/env python3
"""
Trade Executor - 交易执行器
支持模拟交易和真实交易(币安API)
"""

import sys
import json
import sqlite3
import argparse
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
import urllib.request
import urllib.error

# 配置
DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass
class Order:
    """订单数据类"""
    id: str
    symbol: str
    side: str
    order_type: str
    amount: float
    price: Optional[float]
    status: str
    timestamp: str
    filled_price: Optional[float] = None
    filled_time: Optional[str] = None
    is_paper: bool = True
    
@dataclass
class Position:
    """持仓数据类"""
    symbol: str
    quantity: float
    avg_price: float
    unrealized_pnl: float
    realized_pnl: float
    last_update: str

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_tables(self):
        """初始化交易相关表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 订单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                order_type TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                filled_price REAL,
                filled_time TEXT,
                is_paper INTEGER DEFAULT 1
            )
        ''')
        
        # 持仓表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                unrealized_pnl REAL DEFAULT 0,
                realized_pnl REAL DEFAULT 0,
                last_update TEXT NOT NULL
            )
        ''')
        
        # 交易历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total_value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                is_paper INTEGER DEFAULT 1
            )
        ''')
        
        # 账户表 (模拟交易)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paper_account (
                id INTEGER PRIMARY KEY,
                balance REAL DEFAULT 100000.0,
                total_equity REAL DEFAULT 100000.0,
                updated_at TEXT
            )
        ''')
        
        # 初始化模拟账户
        cursor.execute('''
            INSERT OR IGNORE INTO paper_account (id, balance, total_equity, updated_at)
            VALUES (1, 100000.0, 100000.0, ?)
        ''', (datetime.utcnow().isoformat(),))
        
        conn.commit()
        conn.close()
        print("✅ 交易数据库表初始化完成")

class TradeExecutor:
    """交易执行器"""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None, testnet: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.db = DatabaseManager(DB_PATH)
        self.base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
        
    def generate_order_id(self) -> str:
        """生成订单ID"""
        timestamp = str(int(time.time() * 1000))
        random_str = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"ORD{timestamp}{random_str}"
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                return float(data['price'])
        except Exception as e:
            print(f"❌ 获取价格失败: {e}")
            return None
    
    def place_paper_order(self, symbol: str, side: OrderSide, order_type: OrderType, 
                         amount: float, price: Optional[float] = None) -> Optional[Order]:
        """下单 (模拟交易)"""
        current_price = self.get_current_price(symbol)
        if not current_price:
            return None
        
        # 确定成交价格
        if order_type == OrderType.MARKET:
            filled_price = current_price
        else:
            filled_price = price if price else current_price
        
        order_id = self.generate_order_id()
        timestamp = datetime.utcnow().isoformat()
        
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side.value,
            order_type=order_type.value,
            amount=amount,
            price=price,
            status=OrderStatus.FILLED.value,
            timestamp=timestamp,
            filled_price=filled_price,
            filled_time=timestamp,
            is_paper=True
        )
        
        # 保存订单
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (id, symbol, side, order_type, amount, price, status, 
                              timestamp, filled_price, filled_time, is_paper)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order.id, order.symbol, order.side, order.order_type, order.amount,
              order.price, order.status, order.timestamp, order.filled_price,
              order.filled_time, 1))
        
        # 保存交易历史
        total_value = amount * filled_price
        cursor.execute('''
            INSERT INTO trade_history (order_id, symbol, side, quantity, price, total_value, timestamp, is_paper)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order.id, symbol, side.value, amount, filled_price, total_value, timestamp, 1))
        
        # 更新持仓
        self._update_position(cursor, symbol, side, amount, filled_price)
        
        # 更新模拟账户余额
        if side == OrderSide.BUY:
            cursor.execute('UPDATE paper_account SET balance = balance - ?, updated_at = ? WHERE id = 1',
                         (total_value, timestamp))
        else:
            cursor.execute('UPDATE paper_account SET balance = balance + ?, updated_at = ? WHERE id = 1',
                         (total_value, timestamp))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 模拟订单已执行: {side.value} {amount} {symbol} @ {filled_price}")
        return order
    
    def _update_position(self, cursor, symbol: str, side: OrderSide, quantity: float, price: float):
        """更新持仓"""
        cursor.execute('SELECT quantity, avg_price FROM positions WHERE symbol = ?', (symbol,))
        row = cursor.fetchone()
        
        timestamp = datetime.utcnow().isoformat()
        
        if row:
            current_qty, current_avg = row
            if side == OrderSide.BUY:
                new_qty = current_qty + quantity
                new_avg = (current_qty * current_avg + quantity * price) / new_qty
            else:
                new_qty = current_qty - quantity
                new_avg = current_avg if new_qty > 0 else 0
            
            if new_qty > 0:
                cursor.execute('''
                    UPDATE positions SET quantity = ?, avg_price = ?, last_update = ?
                    WHERE symbol = ?
                ''', (new_qty, new_avg, timestamp, symbol))
            else:
                cursor.execute('DELETE FROM positions WHERE symbol = ?', (symbol,))
        else:
            if side == OrderSide.BUY:
                cursor.execute('''
                    INSERT INTO positions (symbol, quantity, avg_price, last_update)
                    VALUES (?, ?, ?, ?)
                ''', (symbol, quantity, price, timestamp))
    
    def get_positions(self, is_paper: bool = True) -> List[Position]:
        """获取持仓"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM positions')
        rows = cursor.fetchall()
        conn.close()
        
        positions = []
        for row in rows:
            # 获取当前价格计算未实现盈亏
            current_price = self.get_current_price(row[0]) or row[2]
            unrealized = (current_price - row[2]) * row[1]
            
            positions.append(Position(
                symbol=row[0],
                quantity=row[1],
                avg_price=row[2],
                unrealized_pnl=unrealized,
                realized_pnl=row[4] or 0,
                last_update=row[5]
            ))
        
        return positions
    
    def get_orders(self, status: Optional[str] = None, is_paper: bool = True) -> List[Dict]:
        """获取订单列表"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM orders WHERE status = ? AND is_paper = ? ORDER BY timestamp DESC',
                         (status, 1 if is_paper else 0))
        else:
            cursor.execute('SELECT * FROM orders WHERE is_paper = ? ORDER BY timestamp DESC',
                         (1 if is_paper else 0,))
        
        rows = cursor.fetchall()
        conn.close()
        
        orders = []
        for row in rows:
            orders.append({
                'id': row[0],
                'symbol': row[1],
                'side': row[2],
                'order_type': row[3],
                'amount': row[4],
                'price': row[5],
                'status': row[6],
                'timestamp': row[7],
                'filled_price': row[8],
                'is_paper': bool(row[10])
            })
        
        return orders
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE orders SET status = ? WHERE id = ? AND status = ?',
                     (OrderStatus.CANCELLED.value, order_id, OrderStatus.PENDING.value))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            print(f"✅ 订单 {order_id} 已撤销")
        else:
            print(f"❌ 订单 {order_id} 无法撤销")
        
        return success
    
    def get_trade_history(self, limit: int = 50, is_paper: bool = True) -> List[Dict]:
        """获取交易历史"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trade_history 
            WHERE is_paper = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (1 if is_paper else 0, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'order_id': row[1],
                'symbol': row[2],
                'side': row[3],
                'quantity': row[4],
                'price': row[5],
                'total_value': row[6],
                'timestamp': row[7]
            })
        
        return history
    
    def get_paper_account(self) -> Dict:
        """获取模拟账户信息"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT balance, total_equity FROM paper_account WHERE id = 1')
        row = cursor.fetchone()
        
        # 计算持仓市值
        positions = self.get_positions(is_paper=True)
        position_value = sum(p.quantity * self.get_current_price(p.symbol) or p.avg_price 
                           for p in positions)
        
        conn.close()
        
        return {
            'balance': row[0] if row else 100000,
            'position_value': position_value,
            'total_equity': (row[0] if row else 100000) + position_value,
            'positions_count': len(positions)
        }

def main():
    parser = argparse.ArgumentParser(description="Trade Executor - 交易执行器")
    parser.add_argument("--paper", action="store_true", help="模拟交易模式")
    parser.add_argument("--buy", help="买入标的")
    parser.add_argument("--sell", help="卖出标的")
    parser.add_argument("--amount", type=float, help="数量")
    parser.add_argument("--price", type=float, help="价格(限价单)")
    parser.add_argument("--positions", action="store_true", help="查看持仓")
    parser.add_argument("--orders", action="store_true", help="查看订单")
    parser.add_argument("--history", action="store_true", help="查看交易历史")
    parser.add_argument("--cancel", help="撤销订单ID")
    parser.add_argument("--account", action="store_true", help="查看账户信息")
    
    args = parser.parse_args()
    
    executor = TradeExecutor()
    
    if args.account:
        account = executor.get_paper_account()
        print("\n📊 模拟账户:")
        print(f"  可用余额: ${account['balance']:,.2f}")
        print(f"  持仓市值: ${account['position_value']:,.2f}")
        print(f"  总资产: ${account['total_equity']:,.2f}")
        print(f"  持仓数量: {account['positions_count']}")
    
    elif args.positions:
        positions = executor.get_positions()
        print("\n📈 当前持仓:")
        for p in positions:
            print(f"  {p.symbol}: {p.quantity} @ ${p.avg_price:,.2f} (浮动盈亏: ${p.unrealized_pnl:,.2f})")
    
    elif args.orders:
        orders = executor.get_orders()
        print("\n📋 订单列表:")
        for o in orders[:10]:
            print(f"  {o['id'][:20]}... | {o['side']} {o['amount']} {o['symbol']} | {o['status']}")
    
    elif args.history:
        history = executor.get_trade_history()
        print("\n📜 交易历史:")
        for h in history[:10]:
            print(f"  {h['timestamp'][:16]} | {h['side']} {h['quantity']} {h['symbol']} @ ${h['price']:,.2f}")
    
    elif args.cancel:
        executor.cancel_order(args.cancel)
    
    elif args.buy and args.amount:
        order_type = OrderType.LIMIT if args.price else OrderType.MARKET
        order = executor.place_paper_order(args.buy, OrderSide.BUY, order_type, args.amount, args.price)
        if order:
            print(f"\n✅ 订单详情:")
            print(json.dumps(asdict(order), indent=2, ensure_ascii=False))
    
    elif args.sell and args.amount:
        order_type = OrderType.LIMIT if args.price else OrderType.MARKET
        order = executor.place_paper_order(args.sell, OrderSide.SELL, order_type, args.amount, args.price)
        if order:
            print(f"\n✅ 订单详情:")
            print(json.dumps(asdict(order), indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
