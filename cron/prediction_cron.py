#!/usr/bin/env python3
"""
定时AI预测任务
执行时间: 每小时的14:50, 29:50, 44:50, 59:50
预测BTC/USDT 15分钟走势
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
PROJECT_PATH = Path(os.path.expanduser("~/.openclaw/workspace/quant-trading"))
sys.path.insert(0, str(PROJECT_PATH))
sys.path.insert(0, str(PROJECT_PATH / "config-layer"))
sys.path.insert(0, str(PROJECT_PATH / "data-layer"))

import requests
import json
import sqlite3
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai_config_manager import AIConfigManager
from prediction_service import get_prediction_service

DB_PATH = PROJECT_PATH / "data" / "market_data.db"


def get_klines_for_prediction(symbol: str, interval: str, limit: int = 20):
    """获取K线数据用于预测"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, open, high, low, close, volume,
               macd, macd_signal, macd_hist, kdj_k, kdj_d, kdj_j
        FROM kline_data 
        WHERE symbol = ? AND interval = ?
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (symbol, interval, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows or len(rows) < 10:
        return None
    
    klines_data = []
    for row in reversed(rows):
        klines_data.append({
            'timestamp': row['timestamp'],
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
            'volume': float(row['volume']),
            'macd_hist': float(row['macd_hist']) if row['macd_hist'] else 0,
            'kdj_j': float(row['kdj_j']) if row['kdj_j'] else 50
        })
    
    return klines_data


def build_prediction_prompt(klines_data: list, interval: str, symbol: str) -> str:
    """构建预测prompt"""
    latest = klines_data[-1]
    
    interval_cn = {'15m': '15分钟', '30m': '30分钟', '1h': '1小时'}.get(interval, interval)
    
    # 格式化K线数据
    klines_table = []
    for i, k in enumerate(klines_data[-10:]):
        klines_table.append(
            f"{i+1:2d}. {k['timestamp']} | C:{k['close']:>10.2f} | "
            f"MACD:{k['macd_hist']:>8.2f} | KDJ_J:{k['kdj_j']:>6.2f}"
        )
    
    prompt = f"""你是专业量化分析师。基于以下{symbol}的{interval_cn}K线数据，预测下一个{interval_cn}的涨跌。

【当前市场状态】
- 最新价格: ${latest['close']:,.2f}
- MACD柱状图: {latest['macd_hist']:.2f}
- KDJ J值: {latest['kdj_j']:.2f}

【最近10根{interval_cn}K线】
{chr(10).join(klines_table)}

【预测要求】
1. 分析MACD趋势、KDJ位置和价格动能
2. 判断下一根{interval_cn}K线涨(>0.1%)还是跌(<-0.1%)
3. 给出涨的概率(0-100)和跌的概率
4. 给出置信度(0.0-1.0)
5. 说明理由(30字内，包含关键指标分析)

【返回格式】
严格按以下JSON格式返回，不要其他文字:
{{"prediction": "up"/"down", "up_probability": 65, "down_probability": 35, "confidence": 0.75, "reason": "理由"}}"""
    
    return prompt


def parse_ai_response(content: str) -> dict:
    """解析AI响应"""
    try:
        content = content.strip()
        # 处理markdown代码块
        code_block_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', content)
        if code_block_match:
            content = code_block_match.group(1).strip()
        # 提取JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            data = json.loads(json_match.group())
            return {
                'prediction': data.get('prediction', 'unknown'),
                'up_probability': data.get('up_probability', 50),
                'down_probability': data.get('down_probability', 50),
                'confidence': data.get('confidence', 0.5),
                'reason': data.get('reason', '暂无分析')
            }
    except Exception as e:
        print(f"  解析失败: {e}")
    return None


def call_single_ai(config, prompt: str) -> dict:
    """调用单个AI"""
    import time
    start_time = time.time()
    
    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': config.model,
        'messages': [
            {'role': 'system', 'content': '你是专业量化分析师，严格按JSON格式返回结果。'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.3,
        'max_tokens': 400
    }
    
    try:
        resp = requests.post(
            f'{config.base_url}/chat/completions',
            headers=headers,
            json=data,
            timeout=45
        )
        resp.raise_for_status()
        result = resp.json()
        content = result['choices'][0]['message']['content']
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        parsed = parse_ai_response(content)
        
        if parsed:
            return {
                'success': True,
                'ai_name': config.name,
                'ai_provider': config.provider,
                'ai_model': config.model,
                **parsed,
                'raw_response': content,
                'response_time_ms': elapsed_ms,
                'source': 'success'
            }
        else:
            return {
                'success': False,
                'ai_name': config.name,
                'error': '解析失败',
                'raw_response': content,
                'response_time_ms': elapsed_ms,
                'source': 'error'
            }
            
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            'success': False,
            'ai_name': config.name,
            'error': str(e),
            'response_time_ms': elapsed_ms,
            'source': 'error'
        }


def execute_prediction():
    """执行预测任务"""
    now = datetime.now()
    print(f"\n{'='*70}")
    print(f"[定时预测任务] {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*70)
    
    # 计算目标时间段
    minute = now.minute
    if minute < 15:
        target_label = f"{now.strftime('%H')}:00-{now.strftime('%H')}:15"
    elif minute < 30:
        target_label = f"{now.strftime('%H')}:15-{now.strftime('%H')}:30"
    elif minute < 45:
        target_label = f"{now.strftime('%H')}:30-{now.strftime('%H')}:45"
    else:
        next_hour = (now + __import__('datetime').timedelta(hours=1)).strftime('%H')
        target_label = f"{now.strftime('%H')}:45-{next_hour}:00"
    
    print(f"[预测目标] BTC/USDT 15分钟走势 ({target_label})")
    
    # 获取K线数据
    klines = get_klines_for_prediction('BTCUSDT', '15m', 20)
    if not klines:
        print("❌ 错误: 无法获取K线数据")
        return False
    
    latest = klines[-1]
    print(f"[当前数据] 价格: ${latest['close']:,.2f}, MACD: {latest['macd_hist']:.2f}, KDJ: {latest['kdj_j']:.2f}")
    
    # 获取AI配置
    manager = AIConfigManager(str(DB_PATH))
    active_configs = manager.get_active_configs()
    
    if not active_configs:
        print("❌ 错误: 没有活跃的AI配置")
        return False
    
    print(f"[调用AI] 共{len(active_configs)}个AI: {', '.join(c.name for c in active_configs)}")
    
    # 构建prompt
    prompt = build_prediction_prompt(klines, '15m', 'BTCUSDT')
    
    # 并行调用所有AI
    ai_results = []
    with ThreadPoolExecutor(max_workers=len(active_configs)) as executor:
        future_to_config = {
            executor.submit(call_single_ai, config, prompt): config 
            for config in active_configs
        }
        
        for future in as_completed(future_to_config):
            config = future_to_config[future]
            try:
                result = future.result()
                if result.get('success'):
                    ai_results.append(result)
                    print(f"  ✅ {result['ai_name']}: {'看涨' if result['prediction'] == 'up' else '看跌'} {result['up_probability']}%/{result['down_probability']}% (耗时{result['response_time_ms']}ms)")
                else:
                    print(f"  ❌ {config.name}: 失败 - {result.get('error', '未知错误')}")
            except Exception as e:
                print(f"  ❌ {config.name}: 异常 - {e}")
    
    if not ai_results:
        print("❌ 错误: 所有AI调用失败")
        return False
    
    # 计算综合预测
    avg_up_prob = sum(r['up_probability'] for r in ai_results) / len(ai_results)
    avg_confidence = sum(r['confidence'] for r in ai_results) / len(ai_results)
    up_count = sum(1 for r in ai_results if r['prediction'] == 'up')
    down_count = len(ai_results) - up_count
    consensus = 'up' if up_count > down_count else 'down'
    
    print(f"\n[综合预测] {'📈 看涨' if consensus == 'up' else '📉 看跌'} {round(avg_up_prob)}%/{round(100-avg_up_prob)}% (置信度{avg_confidence:.2f})")
    
    # 保存到数据库
    try:
        service = get_prediction_service()
        record_id = service.create_prediction_record(
            symbol='BTCUSDT',
            interval='15m',
            price_at_predict=latest['close'],
            macd_at_predict=latest['macd_hist'],
            kdj_j_at_predict=latest['kdj_j'],
            consensus_prediction=consensus,
            consensus_up_probability=round(avg_up_prob),
            consensus_down_probability=round(100 - avg_up_prob),
            consensus_confidence=round(avg_confidence, 2),
            consensus_reason=f"{up_count}看涨,{down_count}看跌 | {ai_results[0]['reason'][:30]}",
            ai_predictions=ai_results
        )
        print(f"[保存成功] 记录ID: {record_id}")
        
        # 验证历史预测
        verified = service.verify_pending_predictions()
        if verified > 0:
            print(f"[验证完成] 验证了 {verified} 条历史预测")
        
        return True
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    execute_prediction()


if __name__ == '__main__':
    main()
