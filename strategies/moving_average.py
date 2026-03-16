"""移动平均线策略"""
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class MovingAverageCrossover(BaseStrategy):
    """
    双均线交叉策略
    当短期均线上穿长期均线时买入，下穿时卖出
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50):
        super().__init__("MovingAverageCrossover")
        self.short_window = short_window
        self.long_window = long_window
        self.set_parameters(short_window=short_window, long_window=long_window)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = data.copy()
        
        # 计算移动平均线
        df['short_ma'] = df['close'].rolling(window=self.short_window).mean()
        df['long_ma'] = df['close'].rolling(window=self.long_window).mean()
        
        # 生成信号
        df['signal'] = 0
        df['position'] = 0
        
        # 金叉买入
        golden_cross = (df['short_ma'] > df['long_ma']) & (df['short_ma'].shift(1) <= df['long_ma'].shift(1))
        df.loc[golden_cross, 'signal'] = 1
        
        # 死叉卖出
        death_cross = (df['short_ma'] < df['long_ma']) & (df['short_ma'].shift(1) >= df['long_ma'].shift(1))
        df.loc[death_cross, 'signal'] = -1
        
        # 持仓状态
        df['position'] = np.where(df['short_ma'] > df['long_ma'], 1, 0)
        
        return df
    
    def on_bar(self, timestamp: pd.Timestamp, data: pd.Series) -> Signal:
        """每根K线检查信号"""
        if 'signal' not in data:
            return Signal.HOLD
        
        signal_value = data['signal']
        if signal_value == 1:
            return Signal.BUY
        elif signal_value == -1:
            return Signal.SELL
        return Signal.HOLD


class TripleMACrossover(BaseStrategy):
    """
    三均线策略
    结合短期、中期、长期均线
    """
    
    def __init__(self, fast: int = 5, medium: int = 20, slow: int = 50):
        super().__init__("TripleMACrossover")
        self.fast = fast
        self.medium = medium
        self.slow = slow
        self.set_parameters(fast=fast, medium=medium, slow=slow)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = data.copy()
        
        df['fast_ma'] = df['close'].rolling(window=self.fast).mean()
        df['medium_ma'] = df['close'].rolling(window=self.medium).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow).mean()
        
        df['signal'] = 0
        
        # 多头排列买入
        bullish = (df['fast_ma'] > df['medium_ma']) & (df['medium_ma'] > df['slow_ma'])
        bullish_prev = (df['fast_ma'].shift(1) <= df['medium_ma'].shift(1)) | (df['medium_ma'].shift(1) <= df['slow_ma'].shift(1))
        
        # 空头排列卖出
        bearish = (df['fast_ma'] < df['medium_ma']) & (df['medium_ma'] < df['slow_ma'])
        bearish_prev = (df['fast_ma'].shift(1) >= df['medium_ma'].shift(1)) | (df['medium_ma'].shift(1) >= df['slow_ma'].shift(1))
        
        df.loc[bullish & bullish_prev, 'signal'] = 1
        df.loc[bearish & bearish_prev, 'signal'] = -1
        
        return df
