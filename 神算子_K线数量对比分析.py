#!/usr/bin/env python3
"""
神算子 K线数量对比分析
使用历史数据验证不同K线数量的效果，无需API调用
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DB_PATH = '/Users/mac/.openclaw/workspace/quant-trading/data/market_data.db'

def analyze_kline_effectiveness():
    """
    分析不同K线数量的预测效果
    基于技术指标的回测，无需API成本
    """
    print("="*70)
    print("📊 神算子 K线数量对比分析")
    print("="*70)
    print(f"分析时间: {datetime.now()}")
    print("对比方案: 40根 vs 80根 vs 100根K线")
    print("方法: 基于技术指标的信号准确率回测")
    print("="*70)
    
    conn = sqlite3.connect(DB_PATH)
    
    # 获取大量历史数据用于回测
    query = """
        SELECT datetime(timestamp) as dt, open, high, low, close, volume,
               macd, macd_signal, macd_hist, kdj_k, kdj_d, kdj_j
        FROM kline_data
        WHERE symbol = 'BTCUSDT' AND interval = '15m'
          AND timestamp >= '2026-01-15' AND timestamp <= '2026-03-10'
        ORDER BY timestamp
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"\n✅ 获取历史数据: {len(df)} 根K线")
    print(f"   时间范围: {df['dt'].min()} ~ {df['dt'].max()}")
    
    # 测试不同K线数量
    lookbacks = [40, 80, 100]
    results = {}
    
    for lookback in lookbacks:
        print(f"\n{'='*70}")
        print(f"测试 {lookback} 根K线的效果")
        print(f"{'='*70}")
        
        predictions = []
        
        # 从第lookback根开始测试
        for i in range(lookback, len(df) - 1):
            window = df.iloc[i-lookback:i]
            current = df.iloc[i]
            next_bar = df.iloc[i+1]
            
            # 计算技术指标信号（模拟神算子的分析逻辑）
            # 1. MACD信号
            macd_bull = current['macd'] > current['macd_signal']
            
            # 2. KDJ信号
            kdj_bull = current['kdj_k'] > current['kdj_d']
            
            # 3. 趋势信号
            trend_bull = window['close'].iloc[-1] > window['close'].iloc[0]
            
            # 4. 成交量信号
            vol_avg = window['volume'].mean()
            vol_bull = current['volume'] > vol_avg
            
            # 综合信号（模拟AI投票）
            bull_signals = sum([macd_bull, kdj_bull, trend_bull])
            
            if bull_signals >= 2:
                prediction = 'up'
            elif bull_signals <= 1:
                prediction = 'down'
            else:
                prediction = 'flat'
            
            # 实际结果
            actual_return = (next_bar['close'] - current['close']) / current['close']
            if actual_return > 0.0005:  # 0.05%
                actual = 'up'
            elif actual_return < -0.0005:
                actual = 'down'
            else:
                actual = 'flat'
            
            predictions.append({
                'prediction': prediction,
                'actual': actual,
                'correct': prediction == actual and prediction != 'flat',
                'return': actual_return * 100,
                'confidence': 60 + bull_signals * 10  # 模拟置信度
            })
        
        # 统计结果
        total = len(predictions)
        correct = sum(1 for p in predictions if p['correct'])
        accuracy = correct / total if total > 0 else 0
        
        up_predictions = [p for p in predictions if p['prediction'] == 'up']
        down_predictions = [p for p in predictions if p['prediction'] == 'down']
        
        up_accuracy = sum(1 for p in up_predictions if p['correct']) / len(up_predictions) if up_predictions else 0
        down_accuracy = sum(1 for p in down_predictions if p['correct']) / len(down_predictions) if down_predictions else 0
        
        avg_return_correct = np.mean([p['return'] for p in predictions if p['correct']]) if correct > 0 else 0
        avg_return_wrong = np.mean([p['return'] for p in predictions if not p['correct'] and p['prediction'] != 'flat']) if predictions else 0
        
        results[lookback] = {
            'total': total,
            'correct': correct,
            'accuracy': accuracy,
            'up_accuracy': up_accuracy,
            'down_accuracy': down_accuracy,
            'up_signals': len(up_predictions),
            'down_signals': len(down_predictions),
            'avg_return_correct': avg_return_correct,
            'avg_return_wrong': avg_return_wrong
        }
        
        print(f"\n统计结果:")
        print(f"  总测试次数: {total}")
        print(f"  正确次数: {correct}")
        print(f"  准确率: {accuracy:.2%}")
        print(f"\n  做多信号:")
        print(f"    次数: {len(up_predictions)}")
        print(f"    准确率: {up_accuracy:.2%}")
        print(f"\n  做空信号:")
        print(f"    次数: {len(down_predictions)}")
        print(f"    准确率: {down_accuracy:.2%}")
        print(f"\n  收益率:")
        print(f"    正确时平均: {avg_return_correct:+.3f}%")
        print(f"    错误时平均: {avg_return_wrong:+.3f}%")
    
    # 最终对比
    print("\n" + "="*70)
    print("📊 最终对比分析")
    print("="*70)
    print(f"{'K线数量':<10} {'总准确率':<12} {'做多准确率':<12} {'做空准确率':<12} {'信号数量':<10}")
    print("-"*70)
    
    for lb in lookbacks:
        r = results[lb]
        total_signals = r['up_signals'] + r['down_signals']
        print(f"{lb:<10} {r['accuracy']:<12.2%} {r['up_accuracy']:<12.2%} {r['down_accuracy']:<12.2%} {total_signals:<10}")
    
    # 找出最佳
    best = max(results.items(), key=lambda x: x[1]['accuracy'])
    print(f"\n✅ 最佳配置: {best[0]}根K线 (准确率 {best[1]['accuracy']:.2%})")
    
    # 分析结论
    print("\n" + "="*70)
    print("💡 分析结论")
    print("="*70)
    
    # 计算准确率提升
    acc_40 = results[40]['accuracy']
    acc_100 = results[100]['accuracy']
    improvement = acc_100 - acc_40
    
    print(f"\n1. K线数量影响:")
    print(f"   40根 → 100根，准确率变化: {acc_40:.2%} → {acc_100:.2%} ({improvement:+.2%})")
    
    if improvement > 0.02:
        print(f"   ✅ 增加K线数量有明显提升")
    elif improvement > -0.02:
        print(f"   ⚠️  K线数量影响不显著")
    else:
        print(f"   ❌ 增加K线数量反而降低准确率")
    
    print(f"\n2. 信号分布:")
    for lb in lookbacks:
        r = results[lb]
        total = r['up_signals'] + r['down_signals']
        up_pct = r['up_signals'] / total * 100 if total > 0 else 0
        print(f"   {lb}根: 做多{r['up_signals']}次({up_pct:.0f}%), 做空{r['down_signals']}次({100-up_pct:.0f}%)")
    
    print(f"\n3. 收益特征:")
    for lb in lookbacks:
        r = results[lb]
        print(f"   {lb}根: 正确时{r['avg_return_correct']:+.3f}%, 错误时{r['avg_return_wrong']:+.3f}%")
    
    # 建议
    print("\n" + "="*70)
    print("🎯 优化建议")
    print("="*70)
    
    best_lb = best[0]
    print(f"\n推荐配置:")
    print(f"  历史K线数量: {best_lb}根")
    print(f"  预期准确率: {results[best_lb]['accuracy']:.2%}")
    
    if results[best_lb]['up_accuracy'] > results[best_lb]['down_accuracy']:
        print(f"  优势方向: 做多 (准确率 {results[best_lb]['up_accuracy']:.2%})")
    else:
        print(f"  优势方向: 做空 (准确率 {results[best_lb]['down_accuracy']:.2%})")
    
    # 保存结果
    import json
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'/Users/mac/.openclaw/workspace/quant-trading/logs/K线数量对比分析_{timestamp_str}.json', 'w') as f:
        json.dump({
            'results': {str(k): v for k, v in results.items()},
            'analysis_time': str(datetime.now()),
            'data_range': {'start': df['dt'].min(), 'end': df['dt'].max(), 'count': len(df)}
        }, f, indent=2)
    
    print(f"\n📄 详细结果已保存到 logs/ 目录")

if __name__ == "__main__":
    analyze_kline_effectiveness()
