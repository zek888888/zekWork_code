#!/usr/bin/env python3
"""
Factor Score Engine - 多因子评分引擎
"""

import sys
import json
import sqlite3
import argparse
import math
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request

DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"

def init_factor_tables():
    """初始化因子表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS factor_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            market TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            total_score REAL,
            technical_score REAL,
            capital_flow_score REAL,
            sentiment_score REAL,
            rating TEXT,
            signal TEXT,
            confidence REAL,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def calculate_rsi(prices, period=14):
    """计算RSI"""
    if len(prices) < period + 1:
        return 50
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return 50
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_ma(prices, period):
    """计算移动平均线"""
    if len(prices) < period:
        return prices[-1] if prices else 0
    return sum(prices[-period:]) / period

def calculate_technical_score(symbol, market):
    """计算技术面评分"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取最近100条K线
    cursor.execute('''
        SELECT close, high, low, volume FROM price_data 
        WHERE symbol = ? AND market = ?
        ORDER BY timestamp DESC LIMIT 100
    ''', (symbol, market))
    
    rows = cursor.fetchall()
    conn.close()
    
    if len(rows) < 20:
        return 50, {"error": "数据不足"}
    
    closes = [r[0] for r in reversed(rows)]
    highs = [r[1] for r in reversed(rows)]
    lows = [r[2] for r in reversed(rows)]
    volumes = [r[3] for r in reversed(rows)]
    
    # RSI评分 (0-100 -> 0-25分)
    rsi = calculate_rsi(closes)
    rsi_score = 25 - abs(rsi - 50) / 2  # RSI越接近50，分数越高
    
    # 均线趋势评分 (0-25分)
    ma5 = calculate_ma(closes, 5)
    ma20 = calculate_ma(closes, 20)
    ma_score = 25 if ma5 > ma20 else 10
    
    # 成交量评分 (0-25分)
    avg_volume = sum(volumes[-20:]) / 20
    recent_volume = sum(volumes[-5:]) / 5
    volume_score = min(25, recent_volume / avg_volume * 15) if avg_volume > 0 else 12.5
    
    # 价格波动评分 (0-25分)
    price_range = (max(highs[-20:]) - min(lows[-20:])) / closes[-1] * 100
    volatility_score = 25 if 5 < price_range < 20 else 15
    
    total = rsi_score + ma_score + volume_score + volatility_score
    
    return total, {
        "rsi": round(rsi, 2),
        "rsi_score": round(rsi_score, 2),
        "ma_trend": "up" if ma5 > ma20 else "down",
        "ma_score": round(ma_score, 2),
        "volume_ratio": round(recent_volume / avg_volume, 2) if avg_volume > 0 else 0,
        "volume_score": round(volume_score, 2),
        "volatility_score": round(volatility_score, 2)
    }

def calculate_capital_flow_score(symbol, market):
    """计算资金面评分"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT change_24h, volume_24h FROM realtime_price 
        WHERE symbol = ?
    ''', (symbol,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return 50, {"error": "无实时数据"}
    
    change_24h, volume_24h = row
    
    # 涨跌幅评分 (-10% ~ +10% -> 0-40分)
    change_score = min(40, max(0, (change_24h + 10) * 2))
    
    # 成交量评分 (0-30分)
    volume_score = 30  # 简化处理
    
    # 资金流入评分 (0-30分)
    flow_score = 30 if change_24h > 0 else 15
    
    total = change_score + volume_score + flow_score
    
    return total, {
        "change_24h": change_24h,
        "change_score": round(change_score, 2),
        "volume_score": volume_score,
        "flow_score": flow_score
    }

def calculate_sentiment_score(symbol):
    """计算情绪面评分"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    cursor.execute('''
        SELECT AVG(sentiment_score) FROM news 
        WHERE content LIKE ? AND published_at > ?
    ''', (f'%{symbol}%', since))
    
    row = cursor.fetchone()
    conn.close()
    
    avg_sentiment = row[0] or 0
    
    # 情绪分 (-1 ~ 1 -> 0-100)
    score = (avg_sentiment + 1) * 50
    
    return score, {
        "avg_sentiment": round(avg_sentiment, 3),
        "news_count": 0  # 简化
    }

def calculate_factor_score(symbol, market):
    """计算综合因子评分"""
    technical_score, tech_details = calculate_technical_score(symbol, market)
    capital_score, capital_details = calculate_capital_flow_score(symbol, market)
    sentiment_score, sentiment_details = calculate_sentiment_score(symbol)
    
    # 权重: 技术面40% + 资金面35% + 情绪面25%
    total_score = technical_score * 0.4 + capital_score * 0.35 + sentiment_score * 0.25
    
    # 评级
    if total_score >= 80:
        rating = "A"
        signal = "买入"
    elif total_score >= 65:
        rating = "B"
        signal = "观望/轻仓"
    elif total_score >= 50:
        rating = "C"
        signal = "观望"
    else:
        rating = "D"
        signal = "回避"
    
    result = {
        "symbol": symbol,
        "market": market,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_score": round(total_score, 2),
        "rating": rating,
        "signal": signal,
        "confidence": round(min(1.0, total_score / 100 + 0.3), 2),
        "factors": {
            "technical": {
                "score": round(technical_score, 2),
                "weight": 0.4,
                "details": tech_details
            },
            "capital_flow": {
                "score": round(capital_score, 2),
                "weight": 0.35,
                "details": capital_details
            },
            "sentiment": {
                "score": round(sentiment_score, 2),
                "weight": 0.25,
                "details": sentiment_details
            }
        }
    }
    
    # 保存到数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO factor_scores 
        (symbol, market, timestamp, total_score, technical_score, capital_flow_score, sentiment_score, rating, signal, confidence, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        symbol, market, result["timestamp"], result["total_score"],
        technical_score, capital_score, sentiment_score,
        rating, signal, result["confidence"],
        json.dumps(result["factors"])
    ))
    conn.commit()
    conn.close()
    
    return result

def get_watchlist():
    """获取监控列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT symbol, market FROM watchlist')
    items = cursor.fetchall()
    conn.close()
    return items

def main():
    parser = argparse.ArgumentParser(description="Factor Score Engine")
    parser.add_argument("--init", action="store_true", help="初始化数据库")
    parser.add_argument("--symbol", help="交易对/股票代码")
    parser.add_argument("--market", choices=["crypto", "stock"], help="市场类型")
    parser.add_argument("--watchlist", action="store_true", help="评分监控列表")
    parser.add_argument("--filter", action="store_true", help="筛选高分标的")
    parser.add_argument("--min-score", type=float, default=70, help="最低分数")
    
    args = parser.parse_args()
    
    if args.init:
        init_factor_tables()
        print("✅ 因子表初始化完成")
        return
    
    if args.watchlist:
        items = get_watchlist()
        print(f"🎯 对 {len(items)} 个标的进行评分...\n")
        for symbol, market in items:
            result = calculate_factor_score(symbol, market)
            print(f"{symbol}: {result['total_score']}分 [{result['rating']}] - {result['signal']}")
        return
    
    if args.symbol and args.market:
        result = calculate_factor_score(args.symbol, args.market)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    parser.print_help()

if __name__ == "__main__":
    main()
