"""布林带策略"""
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class BollingerBandsStrategy(BaseStrategy):
    """
    布林带策略
    价格触及下轨买入，触及上轨卖出
    """
    
    def __init__(
        self,
        period: int = 20,
        std_dev: float = 2.0
    ):
        super().__init__("BollingerBandsStrategy")
        self.period = period
        self.std_dev = std_dev
        self.set_parameters(period=period, std_dev=std_dev)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = data.copy()
        
        # 计算布林带
        df['middle'] = df['close'].rolling(window=self.period).mean()
        df['std'] = df['close'].rolling(window=self.period).std()
        df['upper'] = df['middle'] + (df['std'] * self.std_dev)
        df['lower'] = df['middle'] - (df['std'] * self.std_dev)
        
        # %B指标
        df['percent_b'] = (df['close'] - df['lower']) / (df['upper'] - df['lower'])
        
        df['signal'] = 0
        
        # 价格跌破下轨买入
        buy_signal = (df['close'] < df['lower']) & (df['close'].shift(1) >= df['lower'].shift(1))
        
        # 价格突破上轨卖出
        sell_signal = (df['close'] > df['upper']) & (df['close'].shift(1) <= df['upper'].shift(1))
        
        df.loc[buy_signal, 'signal'] = 1
        df.loc[sell_signal, 'signal'] = -1
        
        return df
    
    def on_bar(self, timestamp: pd.Timestamp, data: pd.Series) -> Signal:
        """检查布林带信号"""
        if 'signal' not in data or pd.isna(data['signal']):
            return Signal.HOLD
        
        if data['signal'] == 1:
            return Signal.BUY
        elif data['signal'] == -1:
            return Signal.SELL
        return Signal.HOLD


class BollingerSqueeze(BaseStrategy):
    """
    布林带挤压策略
    布林带收窄后突破
    """
    
    def __init__(
        self,
        period: int = 20,
        std_dev: float = 2.0,
        squeeze_threshold: float = 0.05
    ):
        super().__init__("BollingerSqueeze")
        self.period = period
        self.std_dev = std_dev
        self.squeeze_threshold = squeeze_threshold
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = data.copy()
        
        # 布林带
        df['middle'] = df['close'].rolling(window=self.period).mean()
        df['std'] = df['close'].rolling(window=self.period).std()
        df['upper'] = df['middle'] + (df['std'] * self.std_dev)
        df['lower'] = df['middle'] - (df['std'] * self.std_dev)
        df['bandwidth'] = (df['upper'] - df['lower']) / df['middle']
        
        # 挤压检测
        df['squeeze'] = df['bandwidth'] < df['bandwidth'].rolling(window=self.period).min() * (1 + self.squeeze_threshold)
        
        df['signal'] = 0
        
        # 挤压后向上突破
        breakout_up = df['squeeze'].shift(1) & (df['close'] > df['upper'])
        
        # 挤压后向下突破
        breakout_down = df['squeeze'].shift(1) & (df['close'] < df['lower'])
        
        df.loc[breakout_up, 'signal'] = 1
        df.loc[breakout_down, 'signal'] = -1
        
        return df
