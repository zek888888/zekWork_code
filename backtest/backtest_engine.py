#!/usr/bin/env python3
"""
策略回测引擎
支持多种策略的回测和绩效分析
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor

# 配置
DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"
RESULTS_DIR = DATA_DIR / "backtest_results"
RESULTS_DIR.mkdir(exist_ok=True)


class StrategyType(Enum):
    TREND_FOLLOWING = "趋势跟踪"
    MEAN_REVERSION = "均值回归"
    BREAKOUT = "突破策略"
    EVENT_DRIVEN = "事件驱动"
    MEME_COIN = "冲狗策略"


@dataclass
class Trade:
    """交易记录"""
    entry_time: datetime
    exit_time: Optional[datetime] = None
    symbol: str = ""
    side: str = "long"  # long/short
    entry_price: float = 0
    exit_price: float = 0
    quantity: float = 0
    pnl: float = 0
    pnl_pct: float = 0
    status: str = "open"  # open/closed
    exit_reason: str = ""


@dataclass
class BacktestResult:
    """回测结果"""
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission  # 手续费率
        self.current_capital = initial_capital
        self.positions = {}  # 当前持仓
        self.trades = []  # 交易记录
        self.equity_curve = []  # 权益曲线
        self.db_path = DB_PATH
        
    def get_historical_data(self, symbol: str, start_date: datetime, 
                           end_date: datetime, interval: str = '1h') -> pd.DataFrame:
        """获取历史数据"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT timestamp, open, high, low, close, volume
            FROM price_data
            WHERE symbol = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
        '''
        
        df = pd.read_sql_query(query, conn, 
                              params=(symbol, start_date.isoformat(), end_date.isoformat()))
        conn.close()
        
        if df.empty:
            # 生成模拟数据用于演示
            df = self._generate_mock_data(symbol, start_date, end_date)
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # 计算技术指标
        df = self._calculate_indicators(df)
        
        return df
    
    def _generate_mock_data(self, symbol: str, start_date: datetime, 
                           end_date: datetime) -> pd.DataFrame:
        """生成模拟数据"""
        np.random.seed(42)
        
        # 生成小时级数据
        hours = int((end_date - start_date).total_seconds() / 3600)
        timestamps = [start_date + timedelta(hours=i) for i in range(hours)]
        
        # 生成随机价格序列 (随机游走)
        base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100
        returns = np.random.normal(0.0001, 0.02, hours)  # 均值0.01%, 标准差2%
        prices = base_price * np.exp(np.cumsum(returns))
        
        # 生成OHLCV
        data = []
        for i, ts in enumerate(timestamps):
            price = prices[i]
            volatility = price * 0.005  # 0.5%波动
            
            open_p = price + np.random.normal(0, volatility * 0.3)
            close_p = price
            high_p = max(open_p, close_p) + np.random.uniform(0, volatility)
            low_p = min(open_p, close_p) - np.random.uniform(0, volatility)
            volume = np.random.uniform(100, 10000)
            
            data.append({
                'timestamp': ts.isoformat(),
                'open': open_p,
                'high': high_p,
                'low': low_p,
                'close': close_p,
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        # 移动平均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # ATR (平均真实波幅)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        # 波动率
        df['volatility'] = df['close'].pct_change().rolling(window=20).std() * np.sqrt(365 * 24)
        
        return df
    
    def trend_following_strategy(self, df: pd.DataFrame, 
                                 fast_ma: int = 5, slow_ma: int = 20) -> pd.DataFrame:
        """趋势跟踪策略 - 均线突破"""
        df = df.copy()
        
        # 计算均线
        df['fast_ma'] = df['close'].rolling(window=fast_ma).mean()
        df['slow_ma'] = df['close'].rolling(window=slow_ma).mean()
        
        # 信号生成
        df['signal'] = 0
        df.loc[df['fast_ma'] > df['slow_ma'], 'signal'] = 1  # 多头
        df.loc[df['fast_ma'] < df['slow_ma'], 'signal'] = -1  # 空头
        
        # 信号变化点
        df['position'] = df['signal'].diff()
        
        return df
    
    def mean_reversion_strategy(self, df: pd.DataFrame, 
                                rsi_low: int = 30, rsi_high: int = 70) -> pd.DataFrame:
        """均值回归策略 - RSI超买超卖"""
        df = df.copy()
        
        df['signal'] = 0
        df.loc[df['rsi'] < rsi_low, 'signal'] = 1  # 超卖，买入
        df.loc[df['rsi'] > rsi_high, 'signal'] = -1  # 超买，卖出
        
        # 保持持仓直到反向信号
        df['position'] = 0
        position = 0
        for i in range(len(df)):
            if df['signal'].iloc[i] == 1:
                position = 1
            elif df['signal'].iloc[i] == -1:
                position = 0
            df.loc[df.index[i], 'position'] = position
        
        return df
    
    def breakout_strategy(self, df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
        """突破策略 - 突破前高/前低"""
        df = df.copy()
        
        df['highest'] = df['high'].rolling(window=lookback).max()
        df['lowest'] = df['low'].rolling(window=lookback).min()
        
        df['signal'] = 0
        df.loc[df['close'] > df['highest'].shift(1), 'signal'] = 1  # 突破前高
        df.loc[df['close'] < df['lowest'].shift(1), 'signal'] = -1  # 突破前低
        
        df['position'] = df['signal'].diff()
        
        return df
    
    def meme_coin_strategy(self, df: pd.DataFrame, 
                          volume_threshold: float = 2.0,
                          momentum_period: int = 3) -> pd.DataFrame:
        """冲狗策略 - 成交量突破 + 动量"""
        df = df.copy()
        
        # 成交量均值
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        # 动量 (短期涨幅)
        df['momentum'] = df['close'].pct_change(periods=momentum_period)
        
        # 信号
        df['signal'] = 0
        volume_spike = df['volume'] > (df['volume_ma'] * volume_threshold)
        positive_momentum = df['momentum'] > 0.05  # 5%涨幅
        
        df.loc[volume_spike & positive_momentum, 'signal'] = 1  # 买入信号
        
        # 止盈条件 (10%收益) 或 持仓3天
        df['position'] = 0
        in_position = False
        entry_price = 0
        
        for i in range(len(df)):
            if not in_position and df['signal'].iloc[i] == 1:
                in_position = True
                entry_price = df['close'].iloc[i]
                df.loc[df.index[i], 'position'] = 1
            elif in_position:
                current_price = df['close'].iloc[i]
                pnl_pct = (current_price - entry_price) / entry_price
                
                # 止盈10% 或 止损-5%
                if pnl_pct >= 0.10 or pnl_pct <= -0.05:
                    in_position = False
                    df.loc[df.index[i], 'position'] = -1
                else:
                    df.loc[df.index[i], 'position'] = 1
        
        return df
    
    def run_backtest(self, symbol: str, strategy_func: Callable, 
                     start_date: datetime, end_date: datetime,
                     strategy_name: str = "Unknown",
                     position_size: float = 0.2,  # 单笔仓位20%
                     stop_loss: float = 0.05,    # 止损5%
                     take_profit: float = 0.10,  # 止盈10%
                     **strategy_params) -> BacktestResult:
        """
        执行回测
        
        Args:
            symbol: 交易标的
            strategy_func: 策略函数
            start_date: 开始日期
            end_date: 结束日期
            strategy_name: 策略名称
            position_size: 仓位比例
            stop_loss: 止损比例
            take_profit: 止盈比例
        
        Returns:
            BacktestResult: 回测结果
        """
        # 获取数据
        df = self.get_historical_data(symbol, start_date, end_date)
        
        # 应用策略
        df = strategy_func(df, **strategy_params)
        
        # 初始化
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
        current_position = None
        entry_price = 0
        entry_time = None
        
        # 遍历数据
        for i, (timestamp, row) in enumerate(df.iterrows()):
            if i < 60:  # 跳过前60条（技术指标需要预热）
                continue
            
            price = row['close']
            signal = row.get('position', 0)
            
            # 更新权益曲线
            current_equity = self.current_capital
            if current_position:
                unrealized = (price - entry_price) / entry_price * current_position['value']
                current_equity += unrealized
            self.equity_curve.append((timestamp, current_equity))
            
            # 开仓信号
            if signal == 1 and not current_position:
                position_value = self.current_capital * position_size
                quantity = position_value / price
                
                current_position = {
                    'symbol': symbol,
                    'side': 'long',
                    'quantity': quantity,
                    'entry_price': price,
                    'entry_time': timestamp,
                    'value': position_value
                }
                
                entry_price = price
                entry_time = timestamp
                
                # 扣除手续费
                self.current_capital -= position_value * self.commission
            
            # 平仓信号或止损止盈
            elif current_position:
                pnl_pct = (price - entry_price) / entry_price
                
                should_exit = (
                    signal == -1 or  # 策略信号
                    pnl_pct <= -stop_loss or  # 止损
                    pnl_pct >= take_profit    # 止盈
                )
                
                if should_exit:
                    # 计算收益
                    exit_value = current_position['quantity'] * price
                    pnl = exit_value - current_position['value']
                    
                    # 扣除手续费
                    self.current_capital += exit_value * (1 - self.commission)
                    
                    # 记录交易
                    trade = Trade(
                        entry_time=entry_time,
                        exit_time=timestamp,
                        symbol=symbol,
                        side='long',
                        entry_price=entry_price,
                        exit_price=price,
                        quantity=current_position['quantity'],
                        pnl=pnl,
                        pnl_pct=pnl_pct * 100,
                        status='closed',
                        exit_reason='signal' if signal == -1 else 'stop_loss' if pnl_pct <= -stop_loss else 'take_profit'
                    )
                    self.trades.append(trade)
                    
                    current_position = None
        
        # 计算绩效指标
        return self._calculate_performance(symbol, strategy_name, start_date, end_date)
    
    def _calculate_performance(self, symbol: str, strategy_name: str,
                              start_date: datetime, end_date: datetime) -> BacktestResult:
        """计算绩效指标"""
        
        # 基础统计
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.pnl > 0)
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 盈亏
        profits = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl < 0]
        
        avg_profit = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 0
        profit_factor = abs(sum(profits) / sum(losses)) if losses else float('inf')
        
        # 收益
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital
        
        # 计算日收益率和夏普比率
        equity_values = [e[1] for e in self.equity_curve]
        daily_returns = []
        for i in range(1, len(equity_values)):
            daily_return = (equity_values[i] - equity_values[i-1]) / equity_values[i-1]
            daily_returns.append(daily_return)
        
        sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(365) if daily_returns and np.std(daily_returns) > 0 else 0
        
        # 最大回撤
        max_drawdown = 0
        max_drawdown_pct = 0
        peak = equity_values[0] if equity_values else self.initial_capital
        
        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = peak - value
            drawdown_pct = drawdown / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct
        
        return BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.current_capital,
            total_return=total_return * 100,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate * 100,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct * 100,
            trades=self.trades,
            equity_curve=self.equity_curve,
            daily_returns=daily_returns
        )
    
    def plot_results(self, result: BacktestResult, save_path: Optional[Path] = None):
        """绘制回测结果"""
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        
        # 权益曲线
        times = [e[0] for e in result.equity_curve]
        values = [e[1] for e in result.equity_curve]
        axes[0].plot(times, values, label='Equity Curve', color='blue')
        axes[0].axhline(y=result.initial_capital, color='gray', linestyle='--', alpha=0.5)
        axes[0].set_title(f'{result.strategy_name} - {result.symbol} Equity Curve')
        axes[0].set_ylabel('Capital ($)')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # 回撤
        drawdowns = []
        peak = values[0]
        for v in values:
            if v > peak:
                peak = v
            drawdowns.append((peak - v) / peak * 100)
        axes[1].fill_between(times, drawdowns, 0, color='red', alpha=0.3)
        axes[1].set_title('Drawdown (%)')
        axes[1].set_ylabel('Drawdown (%)')
        axes[1].grid(True, alpha=0.3)
        
        # 收益分布
        pnls = [t.pnl_pct for t in result.trades]
        axes[2].hist(pnls, bins=30, color='green', alpha=0.7, edgecolor='black')
        axes[2].axvline(x=0, color='red', linestyle='--')
        axes[2].set_title('Trade PnL Distribution (%)')
        axes[2].set_xlabel('Return (%)')
        axes[2].set_ylabel('Frequency')
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✅ 图表已保存: {save_path}")
        else:
            plt.show()
    
    def save_result(self, result: BacktestResult):
        """保存回测结果到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建回测结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT,
                symbol TEXT,
                start_date DATETIME,
                end_date DATETIME,
                initial_capital REAL,
                final_capital REAL,
                total_return REAL,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                win_rate REAL,
                avg_profit REAL,
                avg_loss REAL,
                profit_factor REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                max_drawdown_pct REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO backtest_results 
            (strategy_name, symbol, start_date, end_date, initial_capital, final_capital,
             total_return, total_trades, winning_trades, losing_trades, win_rate,
             avg_profit, avg_loss, profit_factor, sharpe_ratio, max_drawdown, max_drawdown_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.strategy_name, result.symbol, result.start_date, result.end_date,
            result.initial_capital, result.final_capital, result.total_return,
            result.total_trades, result.winning_trades, result.losing_trades,
            result.win_rate, result.avg_profit, result.avg_loss, result.profit_factor,
            result.sharpe_ratio, result.max_drawdown, result.max_drawdown_pct
        ))
        
        conn.commit()
        conn.close()
    
    def print_report(self, result: BacktestResult):
        """打印回测报告"""
        print(f"\n{'='*60}")
        print(f"📊 回测报告: {result.strategy_name} - {result.symbol}")
        print(f"{'='*60}")
        print(f"回测周期: {result.start_date.strftime('%Y-%m-%d')} ~ {result.end_date.strftime('%Y-%m-%d')}")
        print(f"初始资金: ${result.initial_capital:,.2f}")
        print(f"最终资金: ${result.final_capital:,.2f}")
        print(f"总收益率: {result.total_return:+.2f}%")
        print(f"\n📈 交易统计:")
        print(f"  总交易次数: {result.total_trades}")
        print(f"  盈利次数: {result.winning_trades}")
        print(f"  亏损次数: {result.losing_trades}")
        print(f"  胜率: {result.win_rate:.1f}%")
        print(f"\n💰 盈亏分析:")
        print(f"  平均盈利: ${result.avg_profit:,.2f}")
        print(f"  平均亏损: ${result.avg_loss:,.2f}")
        print(f"  盈亏比: {result.profit_factor:.2f}")
        print(f"\n📉 风险指标:")
        print(f"  夏普比率: {result.sharpe_ratio:.2f}")
        print(f"  最大回撤: ${result.max_drawdown:,.2f} ({result.max_drawdown_pct:.2f}%)")
        print(f"{'='*60}\n")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='策略回测引擎')
    parser.add_argument('--symbol', default='BTCUSDT', help='交易标的')
    parser.add_argument('--strategy', choices=['trend', 'mean_reversion', 'breakout', 'meme'], 
                       default='trend', help='策略类型')
    parser.add_argument('--days', type=int, default=90, help='回测天数')
    parser.add_argument('--capital', type=float, default=100000, help='初始资金')
    parser.add_argument('--position-size', type=float, default=0.2, help='仓位比例')
    parser.add_argument('--stop-loss', type=float, default=0.05, help='止损比例')
    parser.add_argument('--take-profit', type=float, default=0.10, help='止盈比例')
    parser.add_argument('--plot', action='store_true', help='绘制图表')
    parser.add_argument('--save-db', action='store_true', help='保存到数据库')
    
    args = parser.parse_args()
    
    # 创建引擎
    engine = BacktestEngine(initial_capital=args.capital)
    
    # 设置回测区间
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    # 选择策略
    strategies = {
        'trend': (engine.trend_following_strategy, '趋势跟踪'),
        'mean_reversion': (engine.mean_reversion_strategy, '均值回归'),
        'breakout': (engine.breakout_strategy, '突破策略'),
        'meme': (engine.meme_coin_strategy, '冲狗策略')
    }
    
    strategy_func, strategy_name = strategies[args.strategy]
    
    print(f"🚀 开始回测: {strategy_name} - {args.symbol}")
    print(f"   回测区间: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    
    # 执行回测
    result = engine.run_backtest(
        symbol=args.symbol,
        strategy_func=strategy_func,
        start_date=start_date,
        end_date=end_date,
        strategy_name=strategy_name,
        position_size=args.position_size,
        stop_loss=args.stop_loss,
        take_profit=args.take_profit
    )
    
    # 打印报告
    engine.print_report(result)
    
    # 保存结果
    if args.save_db:
        engine.save_result(result)
        print("✅ 结果已保存到数据库")
    
    # 绘制图表
    if args.plot:
        save_path = RESULTS_DIR / f"backtest_{args.strategy}_{args.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        engine.plot_results(result, save_path)


if __name__ == "__main__":
    main()
