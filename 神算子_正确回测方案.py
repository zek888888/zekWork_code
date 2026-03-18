#!/usr/bin/env python3
"""
神算子正确回测方案
使用真实历史数据，调用AI模型进行预测，然后与实际结果比对
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
DB_PATH = f"{PROJECT_ROOT}/data/market_data.db"

class 神算子正确回测:
    """
    正确的回测逻辑：
    1. 获取历史N根K线（真实发生过）
    2. 构建prompt，调用AI模型进行预测
    3. 等待预测时段结束后，与实际价格对比
    4. 统计准确率
    """
    
    def __init__(self):
        self.results = []
        self.ai_models = ['MiniMAX', 'DeepSeek-Reasoner', 'Kimi']
        
    def 获取历史K线(self, symbol: str, interval: str, 
                   end_time: datetime, 
                   lookback_bars: int = 50) -> pd.DataFrame:
        """
        获取历史K线数据
        例如：获取2026-03-10 14:00:00之前的50根15分钟K线
        """
        conn = sqlite3.connect(DB_PATH)
        
        # 转换时间为毫秒时间戳
        end_timestamp = int(end_time.timestamp() * 1000)
        
        query = '''
            SELECT 
                datetime(timestamp/1000, 'unixepoch') as datetime,
                open, high, low, close, volume,
                macd, macd_signal, macd_hist,
                kdj_k, kdj_d, kdj_j
            FROM kline_data
            WHERE symbol = ? AND interval = ?
                AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(
            query, 
            conn, 
            params=(symbol, interval, end_timestamp, lookback_bars)
        )
        conn.close()
        
        # 按时间正序排列（从早到晚）
        df = df.sort_values('datetime')
        
        return df
    
    def 获取实际结果(self, symbol: str, interval: str,
                    start_time: datetime,
                    end_time: datetime) -> Dict:
        """
        获取预测时段的实际价格变化
        """
        conn = sqlite3.connect(DB_PATH)
        
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)
        
        query = '''
            SELECT close, datetime(timestamp/1000, 'unixepoch') as dt
            FROM kline_data
            WHERE symbol = ? AND interval = ?
                AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
        '''
        
        df = pd.read_sql_query(
            query,
            conn,
            params=(symbol, interval, start_ts, end_ts)
        )
        conn.close()
        
        if len(df) >= 2:
            start_price = df['close'].iloc[0]
            end_price = df['close'].iloc[-1]
            change_pct = (end_price - start_price) / start_price * 100
            
            if change_pct > 0.1:
                result = 'up'
            elif change_pct < -0.1:
                result = 'down'
            else:
                result = 'flat'
            
            return {
                'start_price': start_price,
                'end_price': end_price,
                'change_pct': change_pct,
                'result': result
            }
        
        return None
    
    def 构建预测Prompt(self, df: pd.DataFrame) -> str:
        """
        构建给AI的预测prompt，包含历史K线数据
        """
        # 构建K线数据描述
        klines_desc = []
        for _, row in df.iterrows():
            klines_desc.append(
                f"{row['datetime']}: 开{row['open']:.2f} 高{row['high']:.2f} "
                f"低{row['low']:.2f} 收{row['close']:.2f} "
                f"量{row['volume']:.2f} "
                f"MACD{row['macd']:.2f} KDJ_K{row['kdj_k']:.2f}"
            )
        
        klines_text = '\n'.join(klines_desc[-10:])  # 只展示最近10根，避免过长
        
        prompt = f"""你是一位专业的加密货币交易分析师。

请基于以下BTC/USDT最近{len(df)}根15分钟K线数据，预测未来15分钟的价格走势。

最近10根K线数据：
{klines_text}

技术指标汇总：
- MACD: {df['macd'].iloc[-1]:.2f} (信号线: {df['macd_signal'].iloc[-1]:.2f})
- KDJ: K={df['kdj_k'].iloc[-1]:.2f}, D={df['kdj_d'].iloc[-1]:.2f}, J={df['kdj_j'].iloc[-1]:.2f}
- 当前价格: {df['close'].iloc[-1]:.2f}
- 短期趋势: {'上涨' if df['close'].iloc[-1] > df['close'].iloc[-5] else '下跌'}

请分析并给出预测：
1. 预测方向 (up/down/flat)
2. 上涨概率 (0-100%)
3. 下跌概率 (0-100%)
4. 置信度 (0-100%)
5. 分析理由

请严格按以下JSON格式输出：
{{
    "prediction": "up/down/flat",
    "up_probability": 45,
    "down_probability": 55,
    "confidence": 70,
    "reasoning": "分析理由..."
}}"""
        
        return prompt
    
    def 调用AI预测(self, prompt: str, model: str) -> Dict:
        """
        调用AI模型进行预测
        这里应该调用实际的AI API
        """
        # 实际实现时需要调用MiniMAX/DeepSeek/Kimi的API
        # 现在返回模拟数据用于框架展示
        
        # 模拟不同AI的预测风格
        if model == 'MiniMAX':
            return {
                'prediction': 'down',
                'up_probability': 35,
                'down_probability': 65,
                'confidence': 72,
                'reasoning': 'MACD持续下降，KDJ高位回落，价格动能减弱'
            }
        elif model == 'DeepSeek-Reasoner':
            return {
                'prediction': 'down',
                'up_probability': 30,
                'down_probability': 70,
                'confidence': 75,
                'reasoning': 'MACD柱状图持续走弱，KDJ J值进入超卖区，价格动能偏弱'
            }
        else:  # Kimi
            return {
                'prediction': 'down',
                'up_probability': 40,
                'down_probability': 60,
                'confidence': 68,
                'reasoning': 'MACD和KDJ均处于超卖区域，短期可能反弹'
            }
    
    def 计算共识预测(self, ai_results: List[Dict]) -> Dict:
        """
        计算AI共识预测结果
        """
        # 统计投票
        up_votes = sum(1 for r in ai_results if r['prediction'] == 'up')
        down_votes = sum(1 for r in ai_results if r['prediction'] == 'down')
        flat_votes = sum(1 for r in ai_results if r['prediction'] == 'flat')
        
        # 平均概率
        avg_up_prob = sum(r['up_probability'] for r in ai_results) / len(ai_results)
        avg_down_prob = sum(r['down_probability'] for r in ai_results) / len(ai_results)
        avg_confidence = sum(r['confidence'] for r in ai_results) / len(ai_results)
        
        # 共识方向
        if up_votes > down_votes and up_votes > flat_votes:
            consensus = 'up'
        elif down_votes > up_votes and down_votes > flat_votes:
            consensus = 'down'
        else:
            consensus = 'flat'
        
        return {
            'consensus': consensus,
            'up_probability': avg_up_prob,
            'down_probability': avg_down_prob,
            'confidence': avg_confidence,
            'ai_results': ai_results
        }
    
    def 运行单点回测(self, 
                    test_time: datetime,
                    lookback_bars: int = 50) -> Dict:
        """
        运行单个时间点的回测
        
        流程：
        1. 获取test_time之前lookback_bars根K线
        2. 调用AI预测接下来15分钟
        3. 获取test_time+15min到test_time+30min的实际价格
        4. 对比预测和实际结果
        """
        print(f"\n回测时间点: {test_time}")
        print(f"使用历史数据: {lookback_bars}根15分钟K线")
        
        # 1. 获取历史数据
        df = self.获取历史K线('BTCUSDT', '15m', test_time, lookback_bars)
        
        if len(df) < lookback_bars:
            print(f"  ⚠️ 历史数据不足: {len(df)}/{lookback_bars}")
            return None
        
        print(f"  ✅ 获取历史数据: {len(df)}根K线")
        print(f"     时间范围: {df['datetime'].min()} ~ {df['datetime'].max()}")
        
        # 2. 构建prompt并调用AI
        prompt = self.构建预测Prompt(df)
        
        ai_results = []
        for model in self.ai_models:
            result = self.调用AI预测(prompt, model)
            result['model'] = model
            ai_results.append(result)
            print(f"     {model}: {result['prediction']} (置信度{result['confidence']}%)")
        
        # 3. 计算共识
        consensus = self.计算共识预测(ai_results)
        print(f"  📊 共识预测: {consensus['consensus']} "
              f"(涨{consensus['up_probability']:.0f}%/跌{consensus['down_probability']:.0f}%, "
              f"置信度{consensus['confidence']:.0f}%)")
        
        # 4. 获取实际结果
        prediction_start = test_time
        prediction_end = test_time + timedelta(minutes=15)
        
        actual = self.获取实际结果('BTCUSDT', '15m', prediction_start, prediction_end)
        
        if actual:
            print(f"  📈 实际结果: {actual['result']} "
                  f"({actual['start_price']:.2f} -> {actual['end_price']:.2f}, "
                  f"{actual['change_pct']:+.2f}%)")
            
            # 5. 判断是否正确
            is_correct = consensus['consensus'] == actual['result']
            
            result = {
                'test_time': test_time,
                'lookback_bars': lookback_bars,
                'prediction': consensus['consensus'],
                'confidence': consensus['confidence'],
                'actual': actual['result'],
                'is_correct': is_correct,
                'change_pct': actual['change_pct']
            }
            
            if is_correct:
                print(f"  ✅ 预测正确!")
            else:
                print(f"  ❌ 预测错误")
            
            return result
        else:
            print(f"  ⚠️ 无法获取实际结果")
            return None
    
    def 运行完整回测(self, 
                   start_date: datetime,
                   end_date: datetime,
                   lookback_options: List[int] = [40, 50, 60, 80, 100]):
        """
        运行完整回测
        测试不同历史数据量对准确率的影响
        """
        print("=" * 70)
        print("🧪 神算子正确回测方案")
        print("=" * 70)
        print(f"回测区间: {start_date} ~ {end_date}")
        print(f"测试K线数量: {lookback_options}")
        print("=" * 70)
        
        all_results = []
        
        # 生成测试时间点（每30分钟一个）
        current_time = start_date
        test_times = []
        while current_time < end_date:
            test_times.append(current_time)
            current_time += timedelta(minutes=30)
        
        print(f"\n共生成 {len(test_times)} 个测试时间点")
        
        # 对每个lookback进行测试
        for lookback in lookback_options:
            print(f"\n{'='*70}")
            print(f"测试历史数据量: {lookback}根K线")
            print(f"{'='*70}")
            
            results = []
            
            # 只测试前5个点用于演示
            for i, test_time in enumerate(test_times[:5]):
                print(f"\n[{i+1}/5] ")
                result = self.运行单点回测(test_time, lookback)
                if result:
                    results.append(result)
            
            if results:
                accuracy = sum(1 for r in results if r['is_correct']) / len(results)
                avg_confidence = sum(r['confidence'] for r in results) / len(results)
                
                print(f"\n{'='*70}")
                print(f"{lookback}根K线 回测结果:")
                print(f"  测试次数: {len(results)}")
                print(f"  正确次数: {sum(1 for r in results if r['is_correct'])}")
                print(f"  准确率: {accuracy:.1%}")
                print(f"  平均置信度: {avg_confidence:.1f}%")
                print(f"{'='*70}")
                
                all_results.append({
                    'lookback': lookback,
                    'accuracy': accuracy,
                    'total_tests': len(results),
                    'avg_confidence': avg_confidence
                })
        
        # 输出最终对比
        print("\n" + "=" * 70)
        print("📊 不同历史数据量对比")
        print("=" * 70)
        print(f"{'K线数量':<10} {'准确率':<12} {'测试次数':<10} {'平均置信度':<12}")
        print("-" * 70)
        for r in all_results:
            print(f"{r['lookback']:<10} {r['accuracy']:<12.1%} {r['total_tests']:<10} {r['avg_confidence']:<12.1f}%")
        
        return all_results

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 神算子正确回测方案")
    print("=" * 70)
    print("\n本方案流程:")
    print("  1. 获取历史N根真实K线数据")
    print("  2. 构建Prompt，调用AI模型预测")
    print("  3. 获取预测时段的实际价格")
    print("  4. 对比预测与实际，统计准确率")
    print("\n" + "=" * 70)
    
    # 创建回测实例
    回测 = 神算子正确回测()
    
    # 运行完整回测（使用2026-03-10的数据）
    start_date = datetime(2026, 3, 10, 0, 0, 0)
    end_date = datetime(2026, 3, 11, 0, 0, 0)
    
    # 先运行单点测试演示
    test_time = datetime(2026, 3, 10, 12, 0, 0)
    result = 回测.运行单点回测(test_time, lookback_bars=50)
    
    print("\n" + "=" * 70)
    print("✅ 演示完成!")
    print("=" * 70)
    print("\n这是正确的回测框架，实际运行时需要:")
    print("  1. 替换 调用AI预测() 方法，接入真实AI API")
    print("  2. 增加更多测试时间点")
    print("  3. 保存结果到数据库")
