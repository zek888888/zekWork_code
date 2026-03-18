#!/usr/bin/env python3
"""
神算子正式回测执行
对比40/80/100根K线的效果，全程记录API成本
"""

import os
import sys
import sqlite3
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('/Users/mac/.openclaw/workspace/quant-trading/.env')

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
DB_PATH = f"{PROJECT_ROOT}/data/market_data.db"

# 成本记录
API_COST_LOG = {
    'MiniMAX': {'calls': 0, 'cost_cny': 0, 'cost_per_call': 0.015},  # 约0.015元/次
    'DeepSeek': {'calls': 0, 'cost_cny': 0, 'cost_per_call': 0.008},  # 约0.008元/次  
    'Kimi': {'calls': 0, 'cost_cny': 0, 'cost_per_call': 0.012},  # 约0.012元/次
    'total': 0
}

class 神算子正式回测:
    """正式回测执行器"""
    
    def __init__(self):
        self.results = []
        self.test_count = 0
        self.ai_configs = self._加载AI配置()
        
    def _加载AI配置(self) -> Dict:
        """加载AI配置"""
        return {
            'MiniMAX': {
                'api_key': os.getenv('OPENAI_API_KEY', ''),
                'base_url': 'https://api.minimaxi.com/v1',
                'model': 'MiniMax-Text-01'
            },
            'DeepSeek': {
                'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
                'base_url': 'https://api.deepseek.com/v1',
                'model': 'deepseek-reasoner'
            },
            'Kimi': {
                'api_key': os.getenv('KIMI_API_KEY', ''),
                'base_url': 'https://api.moonshot.cn/v1',
                'model': 'moonshot-v1-8k'
            }
        }
    
    def 获取历史K线(self, end_time: datetime, lookback_bars: int) -> pd.DataFrame:
        """获取历史K线数据"""
        conn = sqlite3.connect(DB_PATH)
        
        query = '''
            SELECT 
                datetime(timestamp) as datetime,
                open, high, low, close, volume,
                macd, macd_signal, macd_hist,
                kdj_k, kdj_d, kdj_j
            FROM kline_data
            WHERE symbol = 'BTCUSDT' 
                AND interval = '15m'
                AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(
            query, 
            conn, 
            params=(end_time.strftime('%Y-%m-%d %H:%M:%S'), lookback_bars)
        )
        conn.close()
        
        df = df.sort_values('datetime')
        return df
    
    def 获取实际结果(self, start_time: datetime, end_time: datetime) -> Dict:
        """获取预测时段的实际结果"""
        conn = sqlite3.connect(DB_PATH)
        
        query = '''
            SELECT close, datetime(timestamp) as dt
            FROM kline_data
            WHERE symbol = 'BTCUSDT' 
                AND interval = '15m'
                AND timestamp >= ? 
                AND timestamp <= ?
            ORDER BY timestamp ASC
        '''
        
        df = pd.read_sql_query(
            query,
            conn,
            params=(
                start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_time.strftime('%Y-%m-%d %H:%M:%S')
            )
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
    
    def 构建预测Prompt(self, df: pd.DataFrame, lookback: int) -> str:
        """构建预测Prompt"""
        # 只取最近10根用于展示，避免过长
        recent = df.tail(10)
        
        klines_text = []
        for _, row in recent.iterrows():
            klines_text.append(
                f"{row['datetime']}: 开{row['open']:.2f} 高{row['high']:.2f} "
                f"低{row['low']:.2f} 收{row['close']:.2f} "
                f"MACD{row['macd']:.2f} KDJ_K{row['kdj_k']:.2f}"
            )
        
        klines_str = '\n'.join(klines_text)
        
        # 计算趋势
        price_change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
        
        prompt = f"""作为专业加密货币分析师，基于以下BTC/USDT 15分钟K线数据预测未来15分钟走势。

历史数据（最近10根，共{lookback}根）：
{klines_str}

技术指标汇总：
- 当前价格: {df['close'].iloc[-1]:.2f}
- 整体趋势: {'上涨' if price_change > 0 else '下跌'} {price_change:.2f}%
- MACD: {df['macd'].iloc[-1]:.2f} (信号线: {df['macd_signal'].iloc[-1]:.2f})
- KDJ: K={df['kdj_k'].iloc[-1]:.2f}, D={df['kdj_d'].iloc[-1]:.2f}, J={df['kdj_j'].iloc[-1]:.2f}

请严格按JSON格式输出预测结果：
{{
    "prediction": "up/down/flat",
    "up_probability": <0-100>,
    "down_probability": <0-100>,
    "confidence": <0-100>,
    "reasoning": "简要分析理由"
}}"""
        
        return prompt
    
    def 调用AI预测(self, prompt: str, model_name: str) -> Dict:
        """调用AI模型进行预测"""
        config = self.ai_configs.get(model_name)
        if not config or not config['api_key']:
            return {
                'model': model_name,
                'prediction': 'error',
                'up_probability': 0,
                'down_probability': 0,
                'confidence': 0,
                'reasoning': 'API未配置'
            }
        
        try:
            response = requests.post(
                f"{config['base_url']}/chat/completions",
                headers={
                    'Authorization': f"Bearer {config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config['model'],
                    'messages': [
                        {'role': 'system', 'content': '你是专业的加密货币交易分析师，只输出JSON格式的预测结果。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 500
                },
                timeout=60
            )
            
            # 记录API调用
            API_COST_LOG[model_name]['calls'] += 1
            API_COST_LOG[model_name]['cost_cny'] += API_COST_LOG[model_name]['cost_per_call']
            API_COST_LOG['total'] += API_COST_LOG[model_name]['cost_per_call']
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                
                # 解析JSON
                try:
                    # 尝试提取JSON
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        result = json.loads(content[json_start:json_end])
                        result['model'] = model_name
                        return result
                except:
                    pass
                
                # 解析失败返回错误
                return {
                    'model': model_name,
                    'prediction': 'error',
                    'up_probability': 0,
                    'down_probability': 0,
                    'confidence': 0,
                    'reasoning': f'解析失败: {content[:100]}'
                }
            else:
                return {
                    'model': model_name,
                    'prediction': 'error',
                    'up_probability': 0,
                    'down_probability': 0,
                    'confidence': 0,
                    'reasoning': f'API错误: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'model': model_name,
                'prediction': 'error',
                'up_probability': 0,
                'down_probability': 0,
                'confidence': 0,
                'reasoning': f'异常: {str(e)[:100]}'
            }
    
    def 计算共识预测(self, ai_results: List[Dict]) -> Dict:
        """计算共识预测"""
        valid_results = [r for r in ai_results if r['prediction'] not in ['error', 'flat']]
        
        if not valid_results:
            return {
                'consensus': 'flat',
                'up_probability': 33,
                'down_probability': 33,
                'confidence': 0
            }
        
        # 统计
        up_votes = sum(1 for r in valid_results if r['prediction'] == 'up')
        down_votes = sum(1 for r in valid_results if r['prediction'] == 'down')
        
        # 平均概率
        avg_up = sum(r['up_probability'] for r in valid_results) / len(valid_results)
        avg_down = sum(r['down_probability'] for r in valid_results) / len(valid_results)
        avg_conf = sum(r['confidence'] for r in valid_results) / len(valid_results)
        
        # 共识方向
        if up_votes > down_votes:
            consensus = 'up'
        elif down_votes > up_votes:
            consensus = 'down'
        else:
            consensus = 'flat'
        
        return {
            'consensus': consensus,
            'up_probability': avg_up,
            'down_probability': avg_down,
            'confidence': avg_conf,
            'ai_details': valid_results
        }
    
    def 运行单点测试(self, test_time: datetime, lookback: int, test_id: str) -> Dict:
        """运行单个测试点"""
        print(f"\n{'='*70}")
        print(f"测试点 #{test_id} | 回测时间: {test_time} | K线数量: {lookback}")
        print(f"{'='*70}")
        
        # 1. 获取历史数据
        print(f"\n[1/4] 获取历史数据...")
        df = self.获取历史K线(test_time, lookback)
        
        if len(df) < lookback:
            print(f"  ❌ 历史数据不足: {len(df)}/{lookback}")
            return None
        
        print(f"  ✅ 获取 {len(df)} 根K线")
        print(f"     时间: {df['datetime'].min()} ~ {df['datetime'].max()}")
        print(f"     价格: {df['close'].iloc[0]:.2f} -> {df['close'].iloc[-1]:.2f}")
        
        # 2. 构建Prompt并调用AI
        print(f"\n[2/4] 调用AI模型预测...")
        prompt = self.构建预测Prompt(df, lookback)
        
        ai_results = []
        for model in ['MiniMAX', 'DeepSeek', 'Kimi']:
            print(f"     调用 {model}...", end=' ', flush=True)
            result = self.调用AI预测(prompt, model)
            ai_results.append(result)
            print(f"{result['prediction']} (置信度{result['confidence']}%)")
            time.sleep(1)  # 避免请求过快
        
        # 3. 计算共识
        print(f"\n[3/4] 计算共识预测...")
        consensus = self.计算共识预测(ai_results)
        print(f"     共识: {consensus['consensus'].upper()}")
        print(f"     涨/跌概率: {consensus['up_probability']:.0f}%/{consensus['down_probability']:.0f}%")
        print(f"     置信度: {consensus['confidence']:.0f}%")
        
        # 4. 获取实际结果
        print(f"\n[4/4] 获取实际结果...")
        prediction_end = test_time + timedelta(minutes=15)
        actual = self.获取实际结果(test_time, prediction_end)
        
        if not actual:
            print(f"  ❌ 无法获取实际结果")
            return None
        
        print(f"     实际: {actual['result'].upper()}")
        print(f"     价格: {actual['start_price']:.2f} -> {actual['end_price']:.2f}")
        print(f"     变化: {actual['change_pct']:+.2f}%")
        
        # 5. 对比结果
        is_correct = consensus['consensus'] == actual['result']
        
        print(f"\n[结果]")
        if is_correct:
            print(f"  ✅ 预测正确!")
        else:
            print(f"  ❌ 预测错误")
        
        # 累计成本
        print(f"\n[成本累计]")
        print(f"  本次调用: ¥{API_COST_LOG['total']:.3f} (累计)")
        
        return {
            'test_id': test_id,
            'test_time': test_time,
            'lookback': lookback,
            'prediction': consensus['consensus'],
            'confidence': consensus['confidence'],
            'actual': actual['result'],
            'is_correct': is_correct,
            'price_change': actual['change_pct'],
            'ai_details': ai_results
        }
    
    def 执行完整回测(self, lookback_options: List[int] = [40, 80, 100]):
        """执行完整回测"""
        print("="*70)
        print("🚀 神算子正式回测执行")
        print("="*70)
        print(f"开始时间: {datetime.now()}")
        print(f"测试K线数量: {lookback_options}")
        print(f"对比方案: 40根 vs 80根 vs 100根")
        print("="*70)
        
        # 选择测试时间点（2026-01-15到2026-03-01，每2小时一个点）
        start_date = datetime(2026, 1, 15, 0, 0, 0)
        end_date = datetime(2026, 3, 1, 0, 0, 0)
        
        # 生成测试点（每4小时一个，避免过多API调用）
        test_times = []
        current = start_date
        while current < end_date:
            test_times.append(current)
            current += timedelta(hours=4)
        
        # 每个lookback测试3个点（共9个测试点，27次API调用）
        samples_per_lookback = 3
        total_tests = len(lookback_options) * samples_per_lookback
        
        print(f"\n计划测试: {len(lookback_options)}种K线数量 × {samples_per_lookback}个时间点 = {total_tests}次测试")
        print(f"预计API调用: {total_tests * 3}次 (3个AI)")
        print(f"预计成本: ¥{total_tests * 3 * 0.012:.2f}")
        print("")
        
        input("确认开始回测？按回车继续...")
        
        all_results = []
        test_idx = 0
        
        for lookback in lookback_options:
            print(f"\n{'='*70}")
            print(f"测试K线数量: {lookback}根")
            print(f"{'='*70}")
            
            lookback_results = []
            
            # 选择该lookback的测试点
            for i in range(samples_per_lookback):
                test_idx += 1
                # 均匀分布测试点
                time_idx = i * (len(test_times) // len(lookback_options) // samples_per_lookback + 1)
                test_time = test_times[min(time_idx, len(test_times)-1)]
                
                result = self.运行单点测试(test_time, lookback, f"{test_idx}/{total_tests}")
                if result:
                    lookback_results.append(result)
                    all_results.append(result)
                
                time.sleep(2)  # 避免请求过快
            
            # 统计该lookback的结果
            if lookback_results:
                correct = sum(1 for r in lookback_results if r['is_correct'])
                accuracy = correct / len(lookback_results)
                avg_conf = sum(r['confidence'] for r in lookback_results) / len(lookback_results)
                
                print(f"\n{'='*70}")
                print(f"{lookback}根K线 测试完成:")
                print(f"  测试次数: {len(lookback_results)}")
                print(f"  正确次数: {correct}")
                print(f"  准确率: {accuracy:.1%}")
                print(f"  平均置信度: {avg_conf:.1f}%")
                print(f"{'='*70}")
        
        # 生成最终报告
        self.生成最终报告(all_results, lookback_options)
        
        return all_results
    
    def 生成最终报告(self, results: List[Dict], lookback_options: List[int]):
        """生成最终回测报告"""
        print("\n" + "="*70)
        print("📊 最终回测报告")
        print("="*70)
        
        # 按lookback分组统计
        for lookback in lookback_options:
            lookback_results = [r for r in results if r['lookback'] == lookback]
            if lookback_results:
                correct = sum(1 for r in lookback_results if r['is_correct'])
                accuracy = correct / len(lookback_results)
                avg_conf = sum(r['confidence'] for r in lookback_results) / len(lookback_results)
                
                print(f"\n{lookback}根K线:")
                print(f"  测试次数: {len(lookback_results)}")
                print(f"  正确: {correct} | 错误: {len(lookback_results) - correct}")
                print(f"  准确率: {accuracy:.1%}")
                print(f"  平均置信度: {avg_conf:.1f}%")
        
        # API成本
        print(f"\n💰 API成本明细:")
        for model in ['MiniMAX', 'DeepSeek', 'Kimi']:
            log = API_COST_LOG[model]
            print(f"  {model}: {log['calls']}次 × ¥{log['cost_per_call']:.3f} = ¥{log['cost_cny']:.3f}")
        print(f"  总计: ¥{API_COST_LOG['total']:.3f}")
        
        # 保存结果
        report_file = f"{PROJECT_ROOT}/logs/回测报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'results': results,
                'cost': API_COST_LOG,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        print(f"\n📄 详细报告已保存: {report_file}")

if __name__ == "__main__":
    回测 = 神算子正式回测()
    回测.执行完整回测()
