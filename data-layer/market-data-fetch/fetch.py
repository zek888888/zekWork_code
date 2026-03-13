#!/usr/bin/env python3
"""
Market Data Fetcher - 行情数据抓取脚本
支持: 股票(美股/港股/A股) + 虚拟货币(BTC/ETH/SOL等)
"""

import sys
import json
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error

# 配置
DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"

# 确保数据目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

def init_database():
    """初始化SQLite数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 价格数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            market TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            source TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 实时价格表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS realtime_price (
            symbol TEXT PRIMARY KEY,
            price REAL NOT NULL,
            change_24h REAL,
            volume_24h REAL,
            timestamp DATETIME NOT NULL,
            source TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 监控列表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            market TEXT NOT NULL,
            name TEXT,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {DB_PATH}")

def fetch_binance_price(symbol):
    """从Binance获取虚拟货币价格"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                "symbol": data["symbol"],
                "price": float(data["lastPrice"]),
                "change_24h": float(data["priceChangePercent"]),
                "volume_24h": float(data["volume"]),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "binance"
            }
    except Exception as e:
        print(f"❌ 获取 {symbol} 价格失败: {e}")
        return None

def fetch_binance_klines(symbol, interval="1h", limit=100):
    """从Binance获取K线数据"""
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            klines = []
            for item in data:
                klines.append({
                    "timestamp": datetime.fromtimestamp(item[0]/1000).isoformat() + "Z",
                    "open": float(item[1]),
                    "high": float(item[2]),
                    "low": float(item[3]),
                    "close": float(item[4]),
                    "volume": float(item[5])
                })
            return {
                "symbol": symbol,
                "interval": interval,
                "data": klines,
                "source": "binance"
            }
    except Exception as e:
        print(f"❌ 获取 {symbol} K线失败: {e}")
        return None

def fetch_yahoo_price(symbol):
    """从Yahoo Finance获取股票价格"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            result = data["chart"]["result"][0]
            meta = result["meta"]
            
            return {
                "symbol": symbol,
                "price": meta.get("regularMarketPrice", 0),
                "change_24h": meta.get("regularMarketChangePercent", 0),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "yahoo"
            }
    except Exception as e:
        print(f"❌ 获取 {symbol} 价格失败: {e}")
        return None

def save_realtime_price(data):
    """保存实时价格到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO realtime_price 
        (symbol, price, change_24h, volume_24h, timestamp, source)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data["symbol"],
        data["price"],
        data.get("change_24h", 0),
        data.get("volume_24h", 0),
        data["timestamp"],
        data["source"]
    ))
    conn.commit()
    conn.close()

def save_klines(symbol, market, klines_data):
    """保存K线数据到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for item in klines_data["data"]:
        cursor.execute('''
            INSERT OR IGNORE INTO price_data 
            (symbol, market, timestamp, open, high, low, close, volume, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            market,
            item["timestamp"],
            item["open"],
            item["high"],
            item["low"],
            item["close"],
            item["volume"],
            klines_data["source"]
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ 已保存 {len(klines_data['data'])} 条K线数据")

def get_realtime_price(symbol, market):
    """获取并保存实时价格"""
    if market == "crypto":
        data = fetch_binance_price(symbol)
    else:
        data = fetch_yahoo_price(symbol)
    
    if data:
        save_realtime_price(data)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    return data

def get_klines(symbol, market, interval="1h", limit=100):
    """获取并保存K线数据"""
    if market == "crypto":
        data = fetch_binance_klines(symbol, interval, limit)
    else:
        # 股票K线需要额外实现
        print("⚠️ 股票K线数据暂未实现")
        return None
    
    if data:
        save_klines(symbol, market, data)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    return data

def add_to_watchlist(symbol, market, name=None):
    """添加到监控列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO watchlist (symbol, market, name)
            VALUES (?, ?, ?)
        ''', (symbol, market, name or symbol))
        conn.commit()
        print(f"✅ 已添加 {symbol} 到监控列表")
    except sqlite3.IntegrityError:
        print(f"⚠️ {symbol} 已在监控列表中")
    conn.close()

def list_watchlist():
    """列出监控列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT symbol, market, name FROM watchlist ORDER BY added_at')
    items = cursor.fetchall()
    conn.close()
    
    print("\n📋 监控列表:")
    print("-" * 40)
    for item in items:
        print(f"  {item[0]:<15} | {item[1]:<10} | {item[2]}")
    return items

def fetch_watchlist():
    """获取监控列表中所有数据"""
    items = list_watchlist()
    print(f"\n🔄 开始获取 {len(items)} 个标的的数据...")
    
    for symbol, market, _ in items:
        print(f"\n📊 获取 {symbol}...")
        get_realtime_price(symbol, market)

def main():
    parser = argparse.ArgumentParser(description="Market Data Fetcher")
    parser.add_argument("--init", action="store_true", help="初始化数据库")
    parser.add_argument("--symbol", help="交易对/股票代码")
    parser.add_argument("--symbols", help="多个交易对，逗号分隔")
    parser.add_argument("--market", choices=["crypto", "stock"], help="市场类型")
    parser.add_argument("--type", choices=["realtime", "klines"], default="realtime", help="数据类型")
    parser.add_argument("--interval", default="1h", help="K线周期 (1m, 5m, 15m, 1h, 4h, 1d)")
    parser.add_argument("--limit", type=int, default=100, help="获取数量")
    parser.add_argument("--watchlist", action="store_true", help="使用监控列表")
    parser.add_argument("--add", action="store_true", help="添加到监控列表")
    parser.add_argument("--list", action="store_true", help="列出监控列表")
    
    args = parser.parse_args()
    
    if args.init:
        init_database()
        return
    
    if args.list:
        list_watchlist()
        return
    
    if args.add and args.symbol and args.market:
        add_to_watchlist(args.symbol, args.market)
        return
    
    if args.watchlist:
        fetch_watchlist()
        return
    
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
        for symbol in symbols:
            if args.type == "realtime":
                get_realtime_price(symbol, args.market)
            else:
                get_klines(symbol, args.market, args.interval, args.limit)
        return
    
    if args.symbol and args.market:
        if args.type == "realtime":
            get_realtime_price(args.symbol, args.market)
        else:
            get_klines(args.symbol, args.market, args.interval, args.limit)
        return
    
    parser.print_help()

if __name__ == "__main__":
    main()
