"""RSI策略"""
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class RSIStrategy(BaseStrategy):
    """
    RSI相对强弱指标策略
    RSI > overbought 卖出，RSI < oversold 买入
    """
    
    def __init__(
        self,
        period: int = 14,
        oversold: int = 30,
        overbought: int = 70
    ):
        super().__init__("RSIStrategy")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.set_parameters(
            period=period,
            oversold=oversold,
            overbought=overbought
        )
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = data.copy()
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        df['signal'] = 0
        
        # 超卖区买入（RSI从下向上突破oversold）
        buy_signal = (df['rsi'] > self.oversold) & (df['rsi'].shift(1) <= self.oversold)
        
        # 超买区卖出（RSI从上向下突破overbought）
        sell_signal = (df['rsi'] < self.overbought) & (df['rsi'].shift(1) >= self.overbought)
        
        df.loc[buy_signal, 'signal'] = 1
        df.loc[sell_signal, 'signal'] = -1
        
        return df
    
    def on_bar(self, timestamp: pd.Timestamp, data: pd.Series) -> Signal:
        """检查RSI信号"""
        if 'signal' not in data or pd.isna(data['signal']):
            return Signal.HOLD
        
        if data['signal'] == 1:
            return Signal.BUY
        elif data['signal'] == -1:
            return Signal.SELL
        return Signal.HOLD


class RSIWithMA(BaseStrategy):
    """
    RSI + 移动平均线组合策略
    结合趋势和动量指标
    """
    
    def __init__(
        self,
        rsi_period: int = 14,
        ma_period: int = 50,
        oversold: int = 30,
        overbought: int = 70
    ):
        super().__init__("RSIWithMA")
        self.rsi_period = rsi_period
        self.ma_period = ma_period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = data.copy()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 移动平均线
        df['ma'] = df['close'].rolling(window=self.ma_period).mean()
        
        df['signal'] = 0
        
        # 多头趋势 + RSI超卖 = 买入
        bullish = (df['close'] > df['ma']) & (df['rsi'] < self.oversold)
        bullish_exit = (df['rsi'] > self.overbought)
        
        # 空头趋势 + RSI超买 = 卖出
        bearish = (df['close'] < df['ma']) & (df['rsi'] > self.overbought)
        bearish_exit = (df['rsi'] < self.oversold)
        
        df.loc[bullish, 'signal'] = 1
        df.loc[bearish, 'signal'] = -1
        
        return df
