"""策略基类"""
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class Signal(Enum):
    """交易信号"""
    BUY = 1
    SELL = -1
    HOLD = 0


@dataclass
class Trade:
    """交易记录"""
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp = None
    entry_price: float = 0.0
    exit_price: float = 0.0
    side: str = "long"  # long or short
    size: float = 1.0
    pnl: float = 0.0
    return_pct: float = 0.0


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str = "BaseStrategy"):
        self.name = name
        self.signals: List[Tuple[pd.Timestamp, Signal]] = []
        self.trades: List[Trade] = []
        self.current_position = 0
        self.parameters = {}
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: OHLCV数据
        
        Returns:
            包含信号列的DataFrame
        """
        pass
    
    def set_parameters(self, **kwargs):
        """设置策略参数"""
        self.parameters.update(kwargs)
    
    def get_parameters(self) -> Dict:
        """获取策略参数"""
        return self.parameters.copy()
    
    def on_bar(self, timestamp: pd.Timestamp, data: pd.Series) -> Signal:
        """
        每根K线触发的回调
        
        子类可以重写此方法实现更复杂的逻辑
        """
        return Signal.HOLD
    
    def calculate_position_size(self, capital: float, price: float, risk_pct: float = 0.02) -> float:
        """计算仓位大小"""
        risk_amount = capital * risk_pct
        return risk_amount / price if price > 0 else 0
    
    def reset(self):
        """重置策略状态"""
        self.signals = []
        self.trades = []
        self.current_position = 0
