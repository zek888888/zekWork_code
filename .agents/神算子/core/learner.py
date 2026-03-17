#!/usr/bin/env python3
"""
学习引擎
负责分析历史预测结果，提取模式，优化策略
"""

import os
import sys
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "data-layer"))

logger = logging.getLogger('LearningEngine')


class LearningEngine:
    """
    学习引擎
    通过分析历史预测结果，不断改进预测策略
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(PROJECT_ROOT / "data" / "market_data.db")
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_learning_samples(
        self,
        min_samples: int = 10,
        max_age_days: int = 30
    ) -> List[Dict]:
        """
        获取待学习的预测样本
        
        Args:
            min_samples: 最小样本数
            max_age_days: 最大日期范围
            
        Returns:
            List[Dict]: 预测记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        cursor.execute("""
            SELECT r.*, GROUP_CONCAT(json_object(
                'ai_name', ai.ai_name,
                'prediction', ai.prediction,
                'is_correct', ai.is_correct,
                'confidence', ai.confidence
            )) as ai_details
            FROM ai_prediction_records r
            LEFT JOIN ai_individual_predictions ai ON r.id = ai.record_id
            WHERE r.verified_at IS NOT NULL
            AND r.predict_initiated_at >= ?
            GROUP BY r.id
            ORDER BY r.predict_initiated_at DESC
            LIMIT ?
        """, (cutoff_date, min_samples * 3))  # 多取一些以保证质量
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # 解析AI详情
        for record in records:
            if record.get('ai_details'):
                try:
                    record['ai_details'] = json.loads(f"[{record['ai_details']}]")
                except:
                    record['ai_details'] = []
        
        return records
    
    def analyze_failures(self, records: List[Dict]) -> List[Dict]:
        """
        分析失败模式
        
        Args:
            records: 预测记录列表
            
        Returns:
            List[Dict]: 失败模式列表
        """
        failure_records = [r for r in records if r.get('is_correct') == 0]
        
        if not failure_records:
            return []
        
        patterns = []
        
        # 1. 指标组合失败模式
        indicator_patterns = self._analyze_indicator_failures(failure_records)
        patterns.extend(indicator_patterns)
        
        # 2. 时间段失败模式
        time_patterns = self._analyze_time_patterns(failure_records)
        patterns.extend(time_patterns)
        
        # 3. AI偏好失败模式
        ai_patterns = self._analyze_ai_bias(failure_records)
        patterns.extend(ai_patterns)
        
        logger.info(f"[失败分析] 发现 {len(patterns)} 个失败模式")
        
        return patterns
    
    def analyze_successes(self, records: List[Dict]) -> List[Dict]:
        """
        分析成功模式
        
        Args:
            records: 预测记录列表
            
        Returns:
            List[Dict]: 成功模式列表
        """
        success_records = [r for r in records if r.get('is_correct') == 1]
        
        if not success_records:
            return []
        
        patterns = []
        
        # 1. 指标组合成功模式
        indicator_patterns = self._analyze_indicator_successes(success_records)
        patterns.extend(indicator_patterns)
        
        # 2. 高置信度成功模式
        confidence_patterns = self._analyze_confidence_successes(success_records)
        patterns.extend(confidence_patterns)
        
        logger.info(f"[成功分析] 发现 {len(patterns)} 个成功模式")
        
        return patterns
    
    def _analyze_indicator_failures(self, failures: List[Dict]) -> List[Dict]:
        """分析指标相关的失败模式"""
        patterns = []
        
        # 按MACD和KDJ分组
        macd_ranges = defaultdict(list)
        for record in failures:
            macd = record.get('macd_at_predict', 0)
            kdj = record.get('kdj_j_at_predict', 50)
            prediction = record.get('consensus_prediction')
            
            # MACD区间: <-50, -50~0, 0~50, >50
            if macd < -50:
                macd_range = 'strong_negative'
            elif macd < 0:
                macd_range = 'weak_negative'
            elif macd < 50:
                macd_range = 'weak_positive'
            else:
                macd_range = 'strong_positive'
            
            # KDJ区间: <20, 20~80, >80
            if kdj < 20:
                kdj_range = 'oversold'
            elif kdj > 80:
                kdj_range = 'overbought'
            else:
                kdj_range = 'neutral'
            
            key = f"{macd_range}_{kdj_range}_{prediction}"
            macd_ranges[key].append(record)
        
        # 发现高频失败模式
        for key, records in macd_ranges.items():
            if len(records) >= 3:  # 至少3次失败才算模式
                parts = key.split('_')
                patterns.append({
                    'type': 'indicator_failure',
                    'name': f"{parts[2]}预测失败 - MACD:{parts[0]}, KDJ:{parts[1]}",
                    'description': f"在MACD为{parts[0]}且KDJ为{parts[1]}时，{parts[2]}预测失败率较高",
                    'conditions': {
                        'macd_range': parts[0],
                        'kdj_range': parts[1],
                        'prediction': parts[2]
                    },
                    'occurrence_count': len(records),
                    'sample_records': [r['id'] for r in records[:5]],
                    'lesson': f"在此指标组合下，需要更谨慎地进行{parts[2]}预测"
                })
        
        return patterns
    
    def _analyze_time_patterns(self, failures: List[Dict]) -> List[Dict]:
        """分析时间段相关的失败模式"""
        patterns = []
        
        # 按小时分组
        hour_distribution = defaultdict(list)
        for record in failures:
            dt = datetime.fromisoformat(record['predict_initiated_at'])
            hour_distribution[dt.hour].append(record)
        
        # 找到失败高发时段
        for hour, records in hour_distribution.items():
            if len(records) >= 5:  # 该小时失败超过5次
                patterns.append({
                    'type': 'time_pattern',
                    'name': f"高失败时段 - {hour}:00",
                    'description': f"在{hour}:00-{hour+1}:00时段预测失败率较高",
                    'conditions': {'hour': hour},
                    'occurrence_count': len(records),
                    'sample_records': [r['id'] for r in records[:5]],
                    'lesson': f"该时段可能存在特殊市场规律，需要降低置信度或增加其他指标参考"
                })
        
        return patterns
    
    def _analyze_ai_bias(self, failures: List[Dict]) -> List[Dict]:
        """分析AI偏好相关的失败模式"""
        patterns = []
        
        ai_failures = defaultdict(list)
        for record in failures:
            if record.get('ai_details'):
                for ai in record['ai_details']:
                    if ai.get('is_correct') == 0:
                        ai_failures[ai['ai_name']].append(record)
        
        for ai_name, records in ai_failures.items():
            if len(records) >= 5:
                patterns.append({
                    'type': 'ai_bias',
                    'name': f"{ai_name} 失败偏好",
                    'description': f"{ai_name}在某些条件下失败率较高",
                    'conditions': {'ai_name': ai_name},
                    'occurrence_count': len(records),
                    'sample_records': [r['id'] for r in records[:5]],
                    'lesson': f"需要调整{ai_name}的权重或优化其Prompt"
                })
        
        return patterns
    
    def _analyze_indicator_successes(self, successes: List[Dict]) -> List[Dict]:
        """分析指标组合成功模式"""
        patterns = []
        
        # 类似失败分析，但关注成功情况
        # 实现略...
        
        return patterns
    
    def _analyze_confidence_successes(self, successes: List[Dict]) -> List[Dict]:
        """分析高置信度成功模式"""
        patterns = []
        
        high_conf_successes = [
            r for r in successes 
            if r.get('consensus_confidence', 0) > 0.8
        ]
        
        if len(high_conf_successes) >= 5:
            patterns.append({
                'type': 'confidence_success',
                'name': '高置信度预测成功',
                'description': '置信度>0.8的预测有较高成功率',
                'conditions': {'min_confidence': 0.8},
                'occurrence_count': len(high_conf_successes),
                'sample_records': [r['id'] for r in high_conf_successes[:5]],
                'lesson': '应优先采用高置信度预测，对低置信度预测需要额外验证'
            })
        
        return patterns
    
    def calculate_accuracy_trend(self, records: List[Dict]) -> Dict:
        """计算准确率趋势
        
        Args:
            records: 预测记录列表
            
        Returns:
            Dict: 趋势分析结果
        """
        if not records:
            return {'trend': 'unknown', 'change': 0}
        
        # 按时间分组
        mid = len(records) // 2
        early_records = records[mid:]
        recent_records = records[:mid]
        
        early_correct = sum(1 for r in early_records if r.get('is_correct') == 1)
        recent_correct = sum(1 for r in recent_records if r.get('is_correct') == 1)
        
        early_acc = early_correct / len(early_records) if early_records else 0
        recent_acc = recent_correct / len(recent_records) if recent_records else 0
        
        change = recent_acc - early_acc
        
        if change > 0.1:
            trend = 'improving'
        elif change < -0.1:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change': round(change, 3),
            'early_accuracy': round(early_acc, 3),
            'recent_accuracy': round(recent_acc, 3)
        }
    
    def generate_performance_report(self, days: int = 7) -> Dict:
        """生成性能报告
        
        Args:
            days: 统计天数
            
        Returns:
            Dict: 性能报告
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 总体统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                AVG(consensus_confidence) as avg_confidence,
                AVG(accuracy_score) as avg_score
            FROM ai_prediction_records
            WHERE verified_at IS NOT NULL
            AND predict_initiated_at >= ?
        """, (cutoff_date,))
        
        overall = dict(cursor.fetchone())
        
        # AI统计
        cursor.execute("""
            SELECT 
                ai.ai_name,
                COUNT(*) as total,
                SUM(CASE WHEN ai.is_correct = 1 THEN 1 ELSE 0 END) as correct,
                AVG(ai.confidence) as avg_confidence
            FROM ai_individual_predictions ai
            JOIN ai_prediction_records r ON ai.record_id = r.id
            WHERE ai.is_correct IS NOT NULL
            AND r.predict_initiated_at >= ?
            GROUP BY ai.ai_name
        """, (cutoff_date,))
        
        ai_stats = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'period_days': days,
            'overall': overall,
            'ai_performance': ai_stats,
            'generated_at': datetime.now().isoformat()
        }


if __name__ == '__main__':
    # 测试
    engine = LearningEngine()
    
    samples = engine.get_learning_samples(min_samples=5)
    print(f"获取了 {len(samples)} 个学习样本")
    
    if samples:
        failures = engine.analyze_failures(samples)
        print(f"\u53d1现 {len(failures)} 个失败模式")
        
        successes = engine.analyze_successes(samples)
        print(f"\u53d1现 {len(successes)} 个成功模式")
