#!/usr/bin/env python3
"""
预测相关数据模型
"""

from datetime import datetime
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field


@dataclass
class PredictionRecord:
    """预测记录数据类"""
    id: Optional[int]
    symbol: str
    interval: str
    predict_initiated_at: datetime
    target_period_start: datetime
    target_period_end: datetime
    price_at_predict: float
    macd_at_predict: float
    kdj_j_at_predict: float
    consensus_prediction: str
    consensus_up_probability: int
    consensus_down_probability: int
    consensus_confidence: float
    consensus_reason: str
    actual_result: Optional[str] = None
    price_at_target_start: Optional[float] = None
    price_at_target_end: Optional[float] = None
    actual_price_change_percent: Optional[float] = None
    is_correct: Optional[bool] = None
    accuracy_score: Optional[float] = None
    verified_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'interval': self.interval,
            'predict_initiated_at': self.predict_initiated_at.isoformat() if self.predict_initiated_at else None,
            'target_period_start': self.target_period_start.isoformat() if self.target_period_start else None,
            'target_period_end': self.target_period_end.isoformat() if self.target_period_end else None,
            'price_at_predict': self.price_at_predict,
            'macd_at_predict': self.macd_at_predict,
            'kdj_j_at_predict': self.kdj_j_at_predict,
            'consensus_prediction': self.consensus_prediction,
            'consensus_up_probability': self.consensus_up_probability,
            'consensus_down_probability': self.consensus_down_probability,
            'consensus_confidence': self.consensus_confidence,
            'consensus_reason': self.consensus_reason,
            'actual_result': self.actual_result,
            'price_at_target_start': self.price_at_target_start,
            'price_at_target_end': self.price_at_target_end,
            'actual_price_change_percent': self.actual_price_change_percent,
            'is_correct': self.is_correct,
            'accuracy_score': self.accuracy_score,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None
        }


@dataclass
class IndividualAIPrediction:
    """单个AI预测结果"""
    id: Optional[int]
    record_id: int
    ai_name: str
    ai_provider: str
    ai_model: str
    prediction: str
    up_probability: int
    down_probability: int
    confidence: float
    reason: str
    raw_response: Optional[str] = None
    is_correct: Optional[bool] = None
    response_time_ms: Optional[int] = None
    status: str = 'success'
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'record_id': self.record_id,
            'ai_name': self.ai_name,
            'ai_provider': self.ai_provider,
            'ai_model': self.ai_model,
            'prediction': self.prediction,
            'up_probability': self.up_probability,
            'down_probability': self.down_probability,
            'confidence': self.confidence,
            'reason': self.reason,
            'is_correct': self.is_correct,
            'response_time_ms': self.response_time_ms,
            'status': self.status,
            'error_message': self.error_message
        }


@dataclass
class LearningResult:
    """学习结果"""
    timestamp: datetime
    samples_analyzed: int
    patterns_discovered: int
    failure_patterns: int
    success_patterns: int
    prompt_improvements: int
    accuracy_trend: Dict
    applied_changes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'samples_analyzed': self.samples_analyzed,
            'patterns_discovered': self.patterns_discovered,
            'failure_patterns': self.failure_patterns,
            'success_patterns': self.success_patterns,
            'prompt_improvements': self.prompt_improvements,
            'accuracy_trend': self.accuracy_trend,
            'applied_changes': self.applied_changes
        }


@dataclass
class Pattern:
    """模式定义"""
    id: Optional[int]
    pattern_type: str
    name: str
    description: str
    conditions: Dict
    occurrence_count: int
    correct_predictions: int
    accuracy_rate: float
    lesson: str
    sample_records: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'pattern_type': self.pattern_type,
            'name': self.name,
            'description': self.description,
            'conditions': self.conditions,
            'occurrence_count': self.occurrence_count,
            'correct_predictions': self.correct_predictions,
            'accuracy_rate': self.accuracy_rate,
            'lesson': self.lesson,
            'sample_records': self.sample_records
        }
