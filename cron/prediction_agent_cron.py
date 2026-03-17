#!/usr/bin/env python3
"""
Prediction Agent 定时预测任务
执行时间: 每小时的 14:50, 29:50, 44:50, 59:50
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
PROJECT_PATH = Path(os.path.expanduser("~/.openclaw/workspace/quant-trading"))
sys.path.insert(0, str(PROJECT_PATH))
sys.path.insert(0, str(PROJECT_PATH / ".agents/神算子"))

from agent import PredictionAgent

def run_scheduled_prediction():
    """执行定时预测任务"""
    now = datetime.now()
    print(f"\n{'='*70}")
    print(f"[Prediction Agent] 定时预测任务 | {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*70)
    
    try:
        # 初始化Agent
        agent = PredictionAgent()
        
        # 首先验证待处理的预测
        print("\n[1/3] 验证待处理的预测...")
        verified = agent.verify_pending()
        if verified > 0:
            print(f"  ✓ 验证了 {verified} 条历史预测")
        
        # 执行新的预测
        print("\n[2/3] 执行 BTC/USDT 15分钟预测...")
        result = agent.predict(
            symbol='BTCUSDT',
            interval='15m',
            use_knowledge=True
        )
        
        # 计算目标时间段
        target_start = result.target_period[0]
        target_end = result.target_period[1]
        
        print(f"  ✓ 预测完成")
        print(f"  预测发起: {result.initiated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  预测时段: {target_start.strftime('%H:%M')} - {target_end.strftime('%H:%M')}")
        print(f"  综合结果: {result.consensus_prediction.upper()} | 涨{result.up_probability}%/跌{result.down_probability}%")
        print(f"  置信度: {result.confidence*100:.0f}%")
        print(f"  参与AI: {len(result.ai_predictions)}个")
        
        for ai in result.ai_predictions:
            icon = "📈" if ai['prediction'] == 'up' else "📉"
            print(f"    - {ai['ai_name']}: {icon} {ai['up_probability']}% 涨 | {ai['reason'][:40]}...")
        
        # 学习优化
        print("\n[3/3] 检查是否需要学习优化...")
        learn_result = agent.learn()
        if not learn_result.get('skipped'):
            print(f"  ✓ 学习完成: 发现 {learn_result.get('patterns_discovered', 0)} 个新模式")
        else:
            print(f"  - {learn_result.get('reason', '暂无需要')}")
        
        print(f"\n{'='*70}")
        print("✓ 任务完成")
        print('='*70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    run_scheduled_prediction()
