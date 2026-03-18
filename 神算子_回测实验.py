#!/usr/bin/env python3
"""
神算子回测实验
测试不同参数对预测准确率的影响
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
DB_PATH = f"{PROJECT_ROOT}/data/market_data.db"

class 神算子回测实验:
    """神算子回测实验框架"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.results = []
        
    def _setup_logger(self):
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - 神算子回测 - %(levelname)s - %(message)s'
        )
        return logging.getLogger('神算子回测')
    
    def 获取历史数据(self, symbol: str = 'BTCUSDT', 
                   interval: str = '15m',
                   lookback_bars: int = 100) -> pd.DataFrame:
        """获取历史K线数据"""
        conn = sqlite3.connect(DB_PATH)
        
        query = f'''
            SELECT timestamp, open, high, low, close, volume,
                   macd, macd_signal, kdj_k, kdj_d
            FROM kline_data
            WHERE symbol = ? AND interval = ?
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(symbol, interval, lookback_bars))
        conn.close()
        
        if not df.empty:
            df = df.sort_values('timestamp')
            df['returns'] = df['close'].pct_change()
            df['volatility'] = df['returns'].rolling(window=20).std()
        
        return df
    
    def 模拟预测(self, df: pd.DataFrame, 
                lookback: int,
                confidence_threshold: float) -> List[Dict]:
        """
        模拟预测过程
        基于历史数据模拟不同参数的效果
        """
        predictions = []
        
        # 使用历史数据中的技术指标模拟预测
        for i in range(lookback, len(df) - 1):
            window = df.iloc[i-lookback:i]
            current = df.iloc[i]
            next_bar = df.iloc[i+1]
            
            # 计算技术指标信号
            macd_signal = 1 if current['macd'] > current['macd_signal'] else -1
            kdj_signal = 1 if current['kdj_k'] > current['kdj_d'] else -1
            trend_signal = 1 if window['close'].iloc[-1] > window['close'].iloc[0] else -1
            
            # 综合信号 (模拟AI投票)
            signals = [macd_signal, kdj_signal, trend_signal]
            up_votes = sum(1 for s in signals if s > 0)
            down_votes = 3 - up_votes
            
            # 预测方向
            if up_votes > down_votes:
                prediction = 'up'
                confidence = up_votes / 3
            elif down_votes > up_votes:
                prediction = 'down'
                confidence = down_votes / 3
            else:
                prediction = 'flat'
                confidence = 0.5
            
            # 实际结果
            actual_return = (next_bar['close'] - current['close']) / current['close']
            if actual_return > 0.001:
                actual = 'up'
            elif actual_return < -0.001:
                actual = 'down'
            else:
                actual = 'flat'
            
            # 记录结果
            predictions.append({
                'timestamp': current['timestamp'],
                'lookback': lookback,
                'prediction': prediction,
                'confidence': confidence,
                'confidence_threshold': confidence_threshold,
                'actual': actual,
                'is_correct': prediction == actual and prediction != 'flat',
                'return_pct': actual_return * 100
            })
        
        return predictions
    
    def 运行实验(self):
        """运行完整实验"""
        print("=" * 70)
        print("🔬 神算子回测实验")
        print("=" * 70)
        print(f"实验时间: {datetime.now()}")
        print("=" * 70)
        
        # 实验参数
        lookback_options = [40, 50, 60, 80, 100]
        confidence_thresholds = [0.5, 0.6, 0.7, 0.8]
        
        all_results = []
        
        # 获取足够的历史数据
        df = self.获取历史数据(lookback_bars=500)
        
        if df.empty or len(df) < 150:
            print("❌ 历史数据不足")
            return
        
        print(f"\n📊 使用 {len(df)} 条历史数据进行回测")
        print(f"数据范围: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
        
        # 运行所有组合
        total_experiments = len(lookback_options) * len(confidence_thresholds)
        current = 0
        
        for lookback in lookback_options:
            for threshold in confidence_thresholds:
                current += 1
                print(f"\n[{current}/{total_experiments}] 测试: lookback={lookback}, threshold={threshold}")
                
                predictions = self.模拟预测(df, lookback, threshold)
                
                # 过滤低置信度
                high_conf = [p for p in predictions if p['confidence'] >= threshold]
                
                if not high_conf:
                    continue
                
                # 计算指标
                correct = sum(1 for p in high_conf if p['is_correct'])
                total = len(high_conf)
                accuracy = correct / total if total > 0 else 0
                
                # 计算收益率
                returns = [p['return_pct'] for p in high_conf if p['is_correct']]
                losses = [p['return_pct'] for p in high_conf if not p['is_correct'] and p['prediction'] != 'flat']
                
                avg_return = np.mean(returns) if returns else 0
                avg_loss = np.mean(losses) if losses else 0
                
                result = {
                    'lookback': lookback,
                    'threshold': threshold,
                    'total_signals': total,
                    'correct': correct,
                    'accuracy': accuracy,
                    'avg_return': avg_return,
                    'avg_loss': avg_loss,
                    'profit_factor': abs(avg_return / avg_loss) if avg_loss != 0 else 0
                }
                
                all_results.append(result)
                
                print(f"  信号数: {total}, 正确: {correct}, 胜率: {accuracy:.1%}")
        
        self.results = all_results
        return all_results
    
    def 分析报告(self):
        """生成分析报告"""
        if not self.results:
            print("❌ 没有实验结果")
            return
        
        df = pd.DataFrame(self.results)
        
        print("\n" + "=" * 70)
        print("📊 实验结果分析")
        print("=" * 70)
        
        # 1. 最佳lookback
        print("\n📈 不同历史数据量对比:")
        print("-" * 70)
        lookback_summary = df.groupby('lookback').agg({
            'accuracy': 'mean',
            'total_signals': 'mean',
            'profit_factor': 'mean'
        }).round(3)
        print(lookback_summary)
        
        best_lookback = lookback_summary['accuracy'].idxmax()
        print(f"\n✅ 最佳历史数据量: {best_lookback} 根K线 (平均胜率: {lookback_summary.loc[best_lookback, 'accuracy']:.1%})")
        
        # 2. 最佳置信度阈值
        print("\n📈 不同置信度阈值对比:")
        print("-" * 70)
        threshold_summary = df.groupby('threshold').agg({
            'accuracy': 'mean',
            'total_signals': 'mean',
            'profit_factor': 'mean'
        }).round(3)
        print(threshold_summary)
        
        best_threshold = threshold_summary['accuracy'].idxmax()
        print(f"\n✅ 最佳置信度阈值: {best_threshold} (平均胜率: {threshold_summary.loc[best_threshold, 'accuracy']:.1%})")
        
        # 3. 最佳组合
        print("\n📈 最佳参数组合 (TOP 5):")
        print("-" * 70)
        best_combos = df.nlargest(5, 'accuracy')[['lookback', 'threshold', 'accuracy', 'total_signals', 'profit_factor']]
        print(best_combos.to_string(index=False))
        
        # 4. 当前神算子参数对比
        print("\n📈 当前神算子参数分析:")
        print("-" * 70)
        
        # 假设当前使用50根，80%阈值
        current_params = df[(df['lookback'] == 50) & (df['threshold'] == 0.8)]
        if not current_params.empty:
            print(f"当前参数 (50根K线, 80%阈值):")
            print(f"  胜率: {current_params['accuracy'].values[0]:.1%}")
            print(f"  信号数: {current_params['total_signals'].values[0]:.0f}")
        
        # 推荐参数 (60%阈值)
        recommended = df[(df['lookback'] == best_lookback) & (df['threshold'] == 0.6)]
        if not recommended.empty:
            print(f"\n推荐参数 ({best_lookback}根K线, 60%阈值):")
            print(f"  胜率: {recommended['accuracy'].values[0]:.1%}")
            print(f"  信号数: {recommended['total_signals'].values[0]:.0f}")
        
        return {
            'best_lookback': best_lookback,
            'best_threshold': best_threshold,
            'best_combos': best_combos.to_dict('records')
        }

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 神算子回测实验")
    print("=" * 70)
    print("\n实验目标:")
    print("  1. 测试不同历史K线数据量 (40-100根) 对准确率的影响")
    print("  2. 测试不同置信度阈值 (50%-80%) 对交易机会和胜率的影响")
    print("  3. 找出最佳参数组合")
    print("=" * 70)
    
    实验 = 神算子回测实验()
    实验.运行实验()
    结论 = 实验.分析报告()
    
    print("\n" + "=" * 70)
    print("✅ 实验完成!")
    print("=" * 70)
