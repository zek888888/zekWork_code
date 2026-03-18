#!/usr/bin/env python3
"""
神算子真实AI回测 - 80%阈值
调用MiniMAX和DeepSeek真实API，全程记录成本
"""

import os
import sys
import sqlite3
import json
import time
import requests
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('/Users/mac/.openclaw/workspace/quant-trading/.env')

DB_PATH = '/Users/mac/.openclaw/workspace/quant-trading/data/market_data.db'

# API成本记录
API_COST_LOG = {
    'MiniMAX': {'calls': 0, 'cost_cny': 0, 'cost_per_call': 0.015},
    'DeepSeek': {'calls': 0, 'cost_cny': 0, 'cost_per_call': 0.008},
    'total': 0
}

# 配置
CONFIDENCE_THRESHOLD = 0.8  # 80%阈值
TEST_POINTS = 20  # 测试20个时间点
LOOKBACKS = [40, 80, 100]  # 三种K线数量

def log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {msg}")

def get_klines(end_time, lookback):
    """获取历史K线"""
    conn = sqlite3.connect(DB_PATH)
    query = '''SELECT datetime(timestamp) as dt, open, high, low, close, volume,
               macd, macd_signal, macd_hist, kdj_k, kdj_d, kdj_j
        FROM kline_data WHERE symbol = 'BTCUSDT' AND interval = '15m'
        AND timestamp <= ? ORDER BY timestamp DESC LIMIT ?'''
    df = pd.read_sql_query(query, conn, params=(end_time.strftime('%Y-%m-%d %H:%M:%S'), lookback))
    conn.close()
    return df.sort_values('dt')

def get_actual(start_time, end_time):
    """获取实际结果"""
    conn = sqlite3.connect(DB_PATH)
    query = '''SELECT close FROM kline_data WHERE symbol = 'BTCUSDT' AND interval = '15m'
        AND timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC'''
    df = pd.read_sql_query(query, conn, params=(
        start_time.strftime('%Y-%m-%d %H:%M:%S'),
        end_time.strftime('%Y-%m-%d %H:%M:%S')))
    conn.close()
    if len(df) >= 2:
        start_p, end_p = df['close'].iloc[0], df['close'].iloc[-1]
        change = (end_p - start_p) / start_p * 100
        result = 'up' if change > 0.1 else ('down' if change < -0.1 else 'flat')
        return {'start': start_p, 'end': end_p, 'change': change, 'result': result}
    return None

def build_prompt(df, lookback):
    """构建预测Prompt"""
    recent = df.tail(8)
    lines = []
    for _, r in recent.iterrows():
        lines.append(f"{r['dt'][-8:]} 收{r['close']:.2f} MACD{r['macd']:.1f} KDJ_K{r['kdj_k']:.1f}")
    
    lines_str = '\n'.join(lines)
    change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
    
    return f"""作为加密货币分析师，基于BTC最近{lookback}根15分钟K线预测未来15分钟走势。

最近8根K线：
{lines_str}

整体趋势: {'上涨' if change > 0 else '下跌'} {change:.2f}%
当前价格: {df['close'].iloc[-1]:.2f}
MACD: {df['macd'].iloc[-1]:.2f}
KDJ: K={df['kdj_k'].iloc[-1]:.2f}, D={df['kdj_d'].iloc[-1]:.2f}

请分析并给出预测，必须按JSON格式输出：
{{"prediction": "up/down/flat", "up_probability": <0-100>, "down_probability": <0-100>, "confidence": <0-100>, "reasoning": "分析理由"}}"""

def call_minimax(prompt):
    """调用MiniMAX API"""
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        return {'model': 'MiniMAX', 'prediction': 'error', 'confidence': 0, 'reasoning': 'no key'}
    
    try:
        r = requests.post(
            'https://api.minimaxi.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={
                'model': 'MiniMax-Text-01',
                'messages': [
                    {'role': 'system', 'content': '你是专业的加密货币交易分析师，只输出JSON格式的预测结果。'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 300
            },
            timeout=60
        )
        
        API_COST_LOG['MiniMAX']['calls'] += 1
        API_COST_LOG['MiniMAX']['cost_cny'] += API_COST_LOG['MiniMAX']['cost_per_call']
        API_COST_LOG['total'] += API_COST_LOG['MiniMAX']['cost_per_call']
        
        if r.status_code == 200:
            content = r.json()['choices'][0]['message']['content']
            try:
                j_start, j_end = content.find('{'), content.rfind('}') + 1
                if j_start >= 0 and j_end > j_start:
                    result = json.loads(content[j_start:j_end])
                    result['model'] = 'MiniMAX'
                    return result
            except:
                pass
            return {'model': 'MiniMAX', 'prediction': 'error', 'confidence': 0, 'reasoning': 'parse error'}
        return {'model': 'MiniMAX', 'prediction': 'error', 'confidence': 0, 'reasoning': f'http {r.status_code}'}
    except Exception as e:
        return {'model': 'MiniMAX', 'prediction': 'error', 'confidence': 0, 'reasoning': str(e)[:50]}

def call_deepseek(prompt):
    """调用DeepSeek API"""
    key = os.getenv('DEEPSEEK_API_KEY')
    if not key:
        return {'model': 'DeepSeek', 'prediction': 'error', 'confidence': 0, 'reasoning': 'no key'}
    
    try:
        r = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={
                'model': 'deepseek-reasoner',
                'messages': [
                    {'role': 'system', 'content': '你是专业的加密货币交易分析师，只输出JSON格式的预测结果。'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 300
            },
            timeout=60
        )
        
        API_COST_LOG['DeepSeek']['calls'] += 1
        API_COST_LOG['DeepSeek']['cost_cny'] += API_COST_LOG['DeepSeek']['cost_per_call']
        API_COST_LOG['total'] += API_COST_LOG['DeepSeek']['cost_per_call']
        
        if r.status_code == 200:
            content = r.json()['choices'][0]['message']['content']
            try:
                j_start, j_end = content.find('{'), content.rfind('}') + 1
                if j_start >= 0 and j_end > j_start:
                    result = json.loads(content[j_start:j_end])
                    result['model'] = 'DeepSeek'
                    return result
            except:
                pass
            return {'model': 'DeepSeek', 'prediction': 'error', 'confidence': 0, 'reasoning': 'parse error'}
        return {'model': 'DeepSeek', 'prediction': 'error', 'confidence': 0, 'reasoning': f'http {r.status_code}'}
    except Exception as e:
        return {'model': 'DeepSeek', 'prediction': 'error', 'confidence': 0, 'reasoning': str(e)[:50]}

def calculate_consensus(minimax_result, deepseek_result):
    """计算共识预测"""
    results = [r for r in [minimax_result, deepseek_result] if r.get('prediction') in ['up', 'down']]
    
    if len(results) < 2:
        return {'consensus': 'flat', 'confidence': 0, 'up_prob': 0, 'down_prob': 0}
    
    up_votes = sum(1 for r in results if r['prediction'] == 'up')
    down_votes = 2 - up_votes
    
    up_prob = sum(r.get('up_probability', 0) for r in results) / 2
    down_prob = sum(r.get('down_probability', 0) for r in results) / 2
    avg_conf = sum(r.get('confidence', 0) for r in results) / 2
    
    if up_votes > down_votes:
        consensus = 'up'
    elif down_votes > up_votes:
        consensus = 'down'
    else:
        consensus = 'flat'
    
    return {
        'consensus': consensus,
        'confidence': avg_conf,
        'up_prob': up_prob,
        'down_prob': down_prob
    }

def run_backtest():
    """执行回测"""
    print("="*70)
    print("🚀 神算子真实AI回测 - 80%阈值")
    print("="*70)
    print(f"开始时间: {datetime.now()}")
    print(f"对比方案: 40根 vs 80根 vs 100根K线")
    print(f"置信度阈值: {CONFIDENCE_THRESHOLD*100}%")
    print(f"AI模型: MiniMAX + DeepSeek")
    print("="*70)
    
    # 检查API配置
    minimax_key = os.getenv('OPENAI_API_KEY')
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    
    print(f"\nAPI配置检查:")
    print(f"  MiniMAX: {'✅ 已配置' if minimax_key else '❌ 未配置'}")
    print(f"  DeepSeek: {'✅ 已配置' if deepseek_key else '❌ 未配置'}")
    
    if not minimax_key or not deepseek_key:
        print("\n❌ API配置不完整")
        return
    
    # 生成测试时间点
    start_date = datetime(2026, 2, 1, 0, 0, 0)
    test_times = []
    for i in range(TEST_POINTS):
        test_times.append(start_date + timedelta(hours=i*12))
    
    total_tests = len(LOOKBACKS) * len(test_times)
    estimated_cost = total_tests * 2 * 0.012
    
    print(f"\n测试计划:")
    print(f"  测试点数量: {len(test_times)}个时间点")
    print(f"  K线数量: {LOOKBACKS}")
    print(f"  总测试次数: {total_tests}")
    print(f"  API调用: {total_tests * 2}次")
    print(f"  预计成本: ¥{estimated_cost:.2f}")
    
    print(f"\n⚠️  即将开始回测，将产生API调用费用")
    print(f"   按回车键继续...")
    # 实际执行时不需要input
    
    all_results = []
    test_idx = 0
    
    for lookback in LOOKBACKS:
        print(f"\n{'='*70}")
        print(f"测试 {lookback}根K线")
        print(f"{'='*70}")
        
        lookback_results = []
        
        for test_time in test_times:
            test_idx += 1
            log(f"\n测试点 {test_idx}/{total_tests}: {test_time}")
            
            # 1. 获取历史数据
            df = get_klines(test_time, lookback)
            if len(df) < lookback:
                log(f"  ⚠️ 数据不足: {len(df)}/{lookback}")
                continue
            
            log(f"  ✅ 历史数据: {len(df)}根, 价格{df['close'].iloc[-1]:.2f}")
            
            # 2. 调用AI
            prompt = build_prompt(df, lookback)
            
            log(f"  🤖 调用MiniMAX...")
            minimax_r = call_minimax(prompt)
            time.sleep(1)
            
            log(f"  🤖 调用DeepSeek...")
            deepseek_r = call_deepseek(prompt)
            time.sleep(1)
            
            log(f"     MiniMAX: {minimax_r.get('prediction', 'error')} (置信度{minimax_r.get('confidence', 0)}%)")
            log(f"     DeepSeek: {deepseek_r.get('prediction', 'error')} (置信度{deepseek_r.get('confidence', 0)}%)")
            
            # 3. 计算共识
            consensus = calculate_consensus(minimax_r, deepseek_r)
            log(f"  📊 共识: {consensus['consensus'].upper()}, 置信度{consensus['confidence']:.0f}%")
            
            # 4. 检查是否达到阈值
            if consensus['confidence'] < CONFIDENCE_THRESHOLD * 100:
                log(f"  ⏭️  置信度{consensus['confidence']:.0f}% < {CONFIDENCE_THRESHOLD*100}%, 跳过")
                lookback_results.append({
                    'lookback': lookback,
                    'test_time': str(test_time),
                    'skipped': True,
                    'reason': 'low_confidence'
                })
                continue
            
            # 5. 获取实际结果
            actual = get_actual(test_time, test_time + timedelta(minutes=15))
            if not actual:
                log(f"  ⚠️ 无法获取实际结果")
                continue
            
            log(f"  📈 实际: {actual['result'].upper()}, 变化{actual['change']:+.2f}%")
            
            # 6. 对比
            is_correct = consensus['consensus'] == actual['result']
            log(f"  {'✅ 正确' if is_correct else '❌ 错误'}")
            
            lookback_results.append({
                'lookback': lookback,
                'test_time': str(test_time),
                'prediction': consensus['consensus'],
                'confidence': consensus['confidence'],
                'actual': actual['result'],
                'correct': is_correct,
                'price_change': actual['change'],
                'skipped': False
            })
            
            all_results.append(lookback_results[-1])
            
            # 显示累计成本
            log(f"  💰 累计成本: ¥{API_COST_LOG['total']:.3f}")
        
        # 统计该lookback
        valid_results = [r for r in lookback_results if not r.get('skipped')]
        if valid_results:
            correct = sum(1 for r in valid_results if r['correct'])
            accuracy = correct / len(valid_results)
            log(f"\n  {lookback}根总结: {len(valid_results)}次交易, 正确{correct}次, 胜率{accuracy:.1%}")
    
    # 生成最终报告
    generate_report(all_results)

def generate_report(results):
    """生成报告"""
    print("\n" + "="*70)
    print("📊 最终回测报告")
    print("="*70)
    
    for lookback in LOOKBACKS:
        lb_results = [r for r in results if r.get('lookback') == lookback and not r.get('skipped')]
        skipped = len([r for r in results if r.get('lookback') == lookback and r.get('skipped')])
        
        if lb_results:
            correct = sum(1 for r in lb_results if r['correct'])
            accuracy = correct / len(lb_results)
            avg_conf = sum(r['confidence'] for r in lb_results) / len(lb_results)
            
            print(f"\n{lookback}根K线:")
            print(f"  总测试: {len(lb_results) + skipped}次")
            print(f"  达到80%阈值: {len(lb_results)}次")
            print(f"  因低置信度跳过: {skipped}次")
            print(f"  正确: {correct}, 错误: {len(lb_results) - correct}")
            print(f"  胜率: {accuracy:.1%}")
            print(f"  平均置信度: {avg_conf:.1f}%")
    
    # 成本
    print(f"\n💰 API成本明细:")
    print(f"  MiniMAX: {API_COST_LOG['MiniMAX']['calls']}次 × ¥{API_COST_LOG['MiniMAX']['cost_per_call']:.3f} = ¥{API_COST_LOG['MiniMAX']['cost_cny']:.3f}")
    print(f"  DeepSeek: {API_COST_LOG['DeepSeek']['calls']}次 × ¥{API_COST_LOG['DeepSeek']['cost_per_call']:.3f} = ¥{API_COST_LOG['DeepSeek']['cost_cny']:.3f}")
    print(f"  总成本: ¥{API_COST_LOG['total']:.3f}")
    
    # 保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'/Users/mac/.openclaw/workspace/quant-trading/logs/真实AI回测_80阈值_{timestamp}.json'
    with open(report_file, 'w') as f:
        json.dump({
            'results': results,
            'cost': API_COST_LOG,
            'config': {'threshold': CONFIDENCE_THRESHOLD, 'test_points': TEST_POINTS},
            'timestamp': str(datetime.now())
        }, f, indent=2, default=str)
    
    print(f"\n📄 详细报告: {report_file}")
    log("回测完成!")

if __name__ == "__main__":
    run_backtest()
