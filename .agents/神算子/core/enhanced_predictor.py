#!/usr/bin/env python3
"""
神算子增强版预测引擎 - 提高命中率
多策略融合 + 动态权重 + 市场状态识别
"""

import os
import sys
import json
import time
import logging
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger('EnhancedPredictor')


@dataclass
class PredictionResult:
    """预测结果"""
    direction: str  # up/down
    confidence: float  # 0-1
    probability: float  # 0-100
    reasoning: str
    ai_consensus: Dict[str, any]
    market_state: str  # trend/range/volatile
    suggested_action: str  # strong_buy/buy/hold/sell/strong_sell


class MarketStateAnalyzer:
    """市场状态分析器 - 识别趋势/震荡/波动"""
    
    def analyze(self, klines: List[Dict]) -> Dict[str, any]:
        """分析市场状态"""
        if len(klines) < 20:
            return {'state': 'unknown', 'trend_strength': 0}
        
        closes = [k['close'] for k in klines[-20:]]
        highs = [k['high'] for k in klines[-20:]]
        lows = [k['low'] for k in klines[-20:]]
        
        # 计算趋势强度 (ADX简化版)
        trend_strength = self._calculate_trend_strength(closes)
        
        # 计算波动率
        volatility = self._calculate_volatility(closes)
        
        # 计算震荡指标
        ranging = self._detect_ranging(highs, lows, closes)
        
        # 判断市场状态
        if trend_strength > 0.6 and volatility < 0.03:
            state = 'strong_trend'
        elif trend_strength > 0.4:
            state = 'trend'
        elif ranging and volatility < 0.02:
            state = 'range'
        elif volatility > 0.05:
            state = 'volatile'
        else:
            state = 'uncertain'
        
        return {
            'state': state,
            'trend_strength': trend_strength,
            'volatility': volatility,
            'is_ranging': ranging
        }
    
    def _calculate_trend_strength(self, closes: List[float]) -> float:
        """计算趋势强度"""
        if len(closes) < 10:
            return 0
        
        # 使用线性回归斜率
        x = np.arange(len(closes))
        slope = np.polyfit(x, closes, 1)[0]
        
        # 标准化斜率
        normalized_slope = abs(slope) / (np.mean(closes) * 0.01)
        return min(normalized_slope, 1.0)
    
    def _calculate_volatility(self, closes: List[float]) -> float:
        """计算波动率"""
        if len(closes) < 2:
            return 0
        
        returns = np.diff(closes) / closes[:-1]
        return np.std(returns)
    
    def _detect_ranging(self, highs: List[float], lows: List[float], closes: List[float]) -> bool:
        """检测是否处于震荡区间"""
        if len(highs) < 10:
            return False
        
        # 计算近期高低点范围
        recent_highs = highs[-10:]
        recent_lows = lows[-10:]
        
        max_high = max(recent_highs)
        min_low = min(recent_lows)
        
        range_pct = (max_high - min_low) / np.mean(closes[-10:])
        
        # 如果波动范围小，认为是震荡
        return range_pct < 0.05


class DynamicWeightAdjuster:
    """动态权重调整器 - 根据历史表现调整AI权重"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_adjusted_weights(self, ai_names: List[str]) -> Dict[str, float]:
        """获取调整后的权重"""
        # 查询各AI最近的表现
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        weights = {}
        
        for ai_name in ai_names:
            # 查询最近50次预测的准确率
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN prediction_correct = 1 THEN 1 ELSE 0 END) as correct
                FROM ai_individual_predictions
                WHERE ai_name = ? AND created_at > datetime('now', '-7 days')
            """, (ai_name,))
            
            row = cursor.fetchone()
            
            if row and row[0] > 10:  # 至少有10次记录
                accuracy = row[1] / row[0] if row[0] > 0 else 0.5
                # 基础权重1.0，根据准确率调整
                weights[ai_name] = 0.5 + accuracy  # 范围0.5-1.5
            else:
                weights[ai_name] = 1.0  # 默认权重
        
        conn.close()
        
        # 归一化权重
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}
        
        return weights


class ConfidenceFilter:
    """置信度过滤器 - 低置信度预测不交易"""
    
    def __init__(self):
        self.min_confidence = 0.65  # 最低置信度阈值
        self.strong_confidence = 0.80  # 强置信度阈值
    
    def filter_prediction(self, confidence: float, consensus_ratio: float) -> Tuple[bool, str]:
        """
        过滤预测结果
        返回: (是否可信, 建议动作)
        """
        if confidence >= self.strong_confidence and consensus_ratio >= 0.7:
            return True, "strong_trade"
        elif confidence >= self.min_confidence and consensus_ratio >= 0.6:
            return True, "trade"
        elif confidence >= 0.55:
            return True, "weak_trade"
        else:
            return False, "skip"


class EnhancedConsensusCalculator:
    """增强版共识计算器"""
    
    def calculate(self, ai_results: List[Dict], weights: Dict[str, float]) -> Dict:
        """计算加权共识"""
        if not ai_results:
            return {'direction': 'unknown', 'confidence': 0, 'consensus_ratio': 0}
        
        # 统计方向和概率
        up_votes = []
        down_votes = []
        
        for result in ai_results:
            ai_name = result.get('ai_name', 'unknown')
            weight = weights.get(ai_name, 1.0)
            
            if result.get('prediction') == 'up':
                up_votes.append({
                    'weight': weight,
                    'probability': result.get('up_probability', 50),
                    'confidence': result.get('confidence', 0.5)
                })
            else:
                down_votes.append({
                    'weight': weight,
                    'probability': result.get('down_probability', 50),
                    'confidence': result.get('confidence', 0.5)
                })
        
        # 计算加权票数
        up_weight = sum(v['weight'] * v['confidence'] for v in up_votes)
        down_weight = sum(v['weight'] * v['confidence'] for v in down_votes)
        
        total_weight = up_weight + down_weight
        
        if total_weight == 0:
            return {'direction': 'unknown', 'confidence': 0, 'consensus_ratio': 0}
        
        # 计算共识比例
        if up_weight > down_weight:
            direction = 'up'
            consensus_ratio = up_weight / total_weight
            avg_probability = np.mean([v['probability'] for v in up_votes]) if up_votes else 50
        else:
            direction = 'down'
            consensus_ratio = down_weight / total_weight
            avg_probability = np.mean([v['probability'] for v in down_votes]) if down_votes else 50
        
        # 综合置信度 = 共识比例 * 平均概率归一化
        confidence = consensus_ratio * (avg_probability / 100)
        
        return {
            'direction': direction,
            'confidence': round(confidence, 2),
            'consensus_ratio': round(consensus_ratio, 2),
            'up_votes': len(up_votes),
            'down_votes': len(down_votes),
            'probability': round(avg_probability, 1)
        }


class EnhancedAIPredictor:
    """神算子增强版预测引擎"""
    
    def __init__(self, db_path: str = None, timeout: int = 30):
        self.db_path = db_path or str(PROJECT_ROOT / "data" / "market_data.db")
        self.timeout = timeout
        
        # 初始化各模块
        self.market_analyzer = MarketStateAnalyzer()
        self.weight_adjuster = DynamicWeightAdjuster(self.db_path)
        self.confidence_filter = ConfidenceFilter()
        self.consensus_calculator = EnhancedConsensusCalculator()
        
        # 导入原预测器
        from predictor import AIPredictor
        self.base_predictor = AIPredictor(db_path=self.db_path, timeout=timeout)
        
        logger.info("[神算子增强版] 初始化完成")
    
    def predict(self, symbol: str, interval: str, market_data: Dict) -> Optional[PredictionResult]:
        """
        执行增强版预测
        
        流程:
        1. 分析市场状态
        2. 调用多个AI预测
        3. 动态权重调整
        4. 计算加权共识
        5. 置信度过滤
        6. 生成交易建议
        """
        try:
            # 1. 分析市场状态
            klines = market_data.get('klines', [])
            market_state = self.market_analyzer.analyze(klines)
            
            logger.info(f"[市场状态] {market_state['state']}, 趋势强度: {market_state['trend_strength']:.2f}")
            
            # 2. 调用基础预测器获取各AI结果
            ai_results = self.base_predictor.predict(symbol, interval, market_data)
            
            if not ai_results:
                logger.warning("[神算子] 没有获得AI预测结果")
                return None
            
            # 3. 获取动态权重
            ai_names = [r.get('ai_name') for r in ai_results if r.get('success')]
            weights = self.weight_adjuster.get_adjusted_weights(ai_names)
            
            logger.info(f"[动态权重] {weights}")
            
            # 4. 计算加权共识
            consensus = self.consensus_calculator.calculate(ai_results, weights)
            
            logger.info(f"[加权共识] 方向: {consensus['direction']}, 置信度: {consensus['confidence']}, 共识度: {consensus['consensus_ratio']}")
            
            # 5. 置信度过滤
            is_tradable, action = self.confidence_filter.filter_prediction(
                consensus['confidence'], 
                consensus['consensus_ratio']
            )
            
            # 6. 根据市场状态调整建议
            final_action = self._adjust_action_by_market_state(
                action, market_state['state'], consensus['direction']
            )
            
            # 构建结果
            result = PredictionResult(
                direction=consensus['direction'],
                confidence=consensus['confidence'],
                probability=consensus['probability'],
                reasoning=self._generate_reasoning(ai_results, consensus, market_state),
                ai_consensus=consensus,
                market_state=market_state['state'],
                suggested_action=final_action
            )
            
            logger.info(f"[神算子预测] 方向: {result.direction}, 置信度: {result.confidence}, 建议: {result.suggested_action}")
            
            return result
            
        except Exception as e:
            logger.error(f"[神算子增强预测失败] {e}")
            return None
    
    def _adjust_action_by_market_state(self, action: str, market_state: str, direction: str) -> str:
        """根据市场状态调整交易建议"""
        # 强趋势市场 - 顺势交易
        if market_state == 'strong_trend':
            if action == 'strong_trade':
                return 'strong_' + direction
            elif action == 'trade':
                return direction
        
        # 震荡市场 - 降低仓位或观望
        elif market_state == 'range':
            if action in ['strong_trade', 'trade']:
                return 'weak_trade'
            else:
                return 'hold'
        
        # 高波动市场 - 谨慎交易
        elif market_state == 'volatile':
            if action == 'strong_trade':
                return 'trade'
            else:
                return 'hold'
        
        # 不确定市场 - 观望
        elif market_state == 'uncertain':
            return 'hold'
        
        return action
    
    def _generate_reasoning(self, ai_results: List[Dict], consensus: Dict, market_state: Dict) -> str:
        """生成综合理由"""
        reasons = []
        
        # 添加市场状态
        state_desc = {
            'strong_trend': '强趋势',
            'trend': '趋势行情',
            'range': '震荡整理',
            'volatile': '高波动',
            'uncertain': '方向不明'
        }
        reasons.append(f"市场状态: {state_desc.get(market_state['state'], '未知')}")
        
        # 添加AI共识
        reasons.append(f"AI共识: {consensus['up_votes']}涨/{consensus['down_votes']}跌, 共识度{consensus['consensus_ratio']*100:.0f}%")
        
        # 添加主要AI的理由
        for result in ai_results[:2]:  # 取前2个AI的理由
            if result.get('success'):
                ai_name = result.get('ai_name', 'AI')
                ai_reason = result.get('reason', '')
                if ai_reason:
                    reasons.append(f"{ai_name}: {ai_reason[:20]}...")
        
        return " | ".join(reasons)


if __name__ == "__main__":
    # 测试增强版预测器
    predictor = EnhancedAIPredictor()
    
    # 模拟市场数据
    test_data = {
        'klines': [
            {'close': 65000, 'high': 65500, 'low': 64800, 'macd_hist': 10, 'kdj_j': 60},
            {'close': 65200, 'high': 65800, 'low': 65100, 'macd_hist': 15, 'kdj_j': 65},
            # ... 更多K线
        ],
        'close': 65200,
        'macd_hist': 15,
        'kdj_j': 65
    }
    
    result = predictor.predict('BTCUSDT', '15m', test_data)
    if result:
        print(f"预测方向: {result.direction}")
        print(f"置信度: {result.confidence}")
        print(f"建议: {result.suggested_action}")
        print(f"理由: {result.reasoning}")
