#!/usr/bin/env python3
"""
预测Agent 主类
具备自学习能力的AI预测Agent
"""

import os
import sys
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "config-layer"))
sys.path.insert(0, str(PROJECT_ROOT / "data-layer"))

from core.fetcher import DataFetcher
from core.predictor import AIPredictor
from core.validator import PredictionValidator
from core.learner import LearningEngine
from knowledge.pattern_store import PatternStore
from knowledge.prompt_optimizer import PromptOptimizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PredictionAgent')


@dataclass
class AgentConfig:
    """Agent配置"""
    learning_enabled: bool = True
    min_samples_for_learning: int = 10
    learning_interval: int = 3600  # 秒
    prediction_timeout: int = 30
    min_confidence: float = 0.6
    max_patterns: int = 1000
    parallel_prediction: bool = True


@dataclass
class PredictionResult:
    """预测结果"""
    record_id: Optional[int]
    symbol: str
    interval: str
    initiated_at: datetime
    target_period: Tuple[datetime, datetime]
    consensus_prediction: str
    up_probability: int
    down_probability: int
    confidence: float
    ai_predictions: List[Dict]
    market_data: Dict
    knowledge_applied: List[str]  # 应用的知识库条目


class PredictionAgent:
    """
    预测Agent主类
    具备自学习能力的AI预测系统
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化Agent
        
        Args:
            config_path: 配置文件路径，默认使用内置配置
        """
        self.config = self._load_config(config_path)
        
        # 初始化各组件
        self.fetcher = DataFetcher()
        self.predictor = AIPredictor(timeout=self.config.prediction_timeout)
        self.validator = PredictionValidator()
        self.learner = LearningEngine()
        
        # 初始化知识库
        self.pattern_store = PatternStore(max_patterns=self.config.max_patterns)
        self.prompt_optimizer = PromptOptimizer()
        
        # 学习状态
        self.last_learning_time = None
        
        logger.info("预测Agent初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> AgentConfig:
        """加载配置"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            return AgentConfig(**config_dict.get('agent', {}))
        return AgentConfig()
    
    def predict(
        self,
        symbol: str = 'BTCUSDT',
        interval: str = '15m',
        use_knowledge: bool = True
    ) -> PredictionResult:
        """
        执行预测
        
        Args:
            symbol: 交易对
            interval: 时间维度
            use_knowledge: 是否使用知识库优化
            
        Returns:
            PredictionResult: 预测结果
        """
        logger.info(f"[预测开始] {symbol} {interval}")
        
        # 1. 获取市场数据
        market_data = self.fetcher.get_latest_data(symbol, interval)
        if not market_data:
            raise ValueError(f"无法获取 {symbol} 的市场数据")
        
        # 2. 查询知识库获取历史模式
        knowledge_patterns = []
        if use_knowledge:
            knowledge_patterns = self.pattern_store.find_matching_patterns(
                symbol=symbol,
                interval=interval,
                market_conditions=market_data
            )
            logger.info(f"[知识库] 找到 {len(knowledge_patterns)} 个匹配模式")
        
        # 3. 优化Prompt（如果有知识）
        custom_prompt = None
        if knowledge_patterns:
            custom_prompt = self.prompt_optimizer.optimize_prompt(
                base_prompt=self.predictor.get_default_prompt(),
                patterns=knowledge_patterns,
                market_data=market_data
            )
        
        # 4. 执行AI预测
        ai_results = self.predictor.predict(
            symbol=symbol,
            interval=interval,
            market_data=market_data,
            custom_prompt=custom_prompt,
            parallel=self.config.parallel_prediction
        )
        
        # 5. 计算综合结果
        consensus = self._calculate_consensus(ai_results, knowledge_patterns)
        
        # 6. 保存预测记录
        record_id = self._save_prediction(
            symbol=symbol,
            interval=interval,
            market_data=market_data,
            consensus=consensus,
            ai_results=ai_results,
            knowledge_patterns=knowledge_patterns
        )
        
        # 7. 检查是否需要学习
        self._check_learning_trigger()
        
        result = PredictionResult(
            record_id=record_id,
            symbol=symbol,
            interval=interval,
            initiated_at=datetime.now(),
            target_period=self._calculate_target_period(interval),
            consensus_prediction=consensus['prediction'],
            up_probability=consensus['up_probability'],
            down_probability=consensus['down_probability'],
            confidence=consensus['confidence'],
            ai_predictions=ai_results,
            market_data=market_data,
            knowledge_applied=[p['id'] for p in knowledge_patterns]
        )
        
        logger.info(f"[预测完成] {consensus['prediction'].upper()} {consensus['up_probability']}%/{consensus['down_probability']}%")
        
        return result
    
    def _calculate_consensus(
        self,
        ai_results: List[Dict],
        knowledge_patterns: List[Dict]
    ) -> Dict:
        """计算综合预测结果，考虑知识库加权"""
        if not ai_results:
            return {
                'prediction': 'unknown',
                'up_probability': 50,
                'down_probability': 50,
                'confidence': 0.0,
                'reason': '无AI预测结果'
            }
        
        # 基础权重
        base_weights = {r['ai_name']: 1.0 for r in ai_results}
        
        # 根据知识库调整权重
        if knowledge_patterns:
            for pattern in knowledge_patterns:
                if 'preferred_ai' in pattern:
                    preferred = pattern['preferred_ai']
                    for ai_name in base_weights:
                        if ai_name == preferred:
                            base_weights[ai_name] *= 1.2  # 提升推荐AI的权重
        
        # 计算加权平均
        total_weight = 0
        weighted_up = 0
        weighted_confidence = 0
        
        for result in ai_results:
            weight = base_weights.get(result['ai_name'], 1.0)
            total_weight += weight
            weighted_up += result['up_probability'] * weight
            weighted_confidence += result['confidence'] * weight
        
        avg_up_prob = int(weighted_up / total_weight)
        avg_confidence = weighted_confidence / total_weight
        
        # 确定预测方向
        prediction = 'up' if avg_up_prob > 50 else 'down'
        
        # 收集理由
        reasons = [r['reason'] for r in ai_results if r.get('reason')]
        primary_reason = reasons[0] if reasons else '基于AI综合分析'
        
        return {
            'prediction': prediction,
            'up_probability': avg_up_prob,
            'down_probability': 100 - avg_up_prob,
            'confidence': round(avg_confidence, 2),
            'reason': primary_reason
        }
    
    def verify_pending(self) -> int:
        """
        验证所有待处理的预测
        
        Returns:
            int: 验证的记录数
        """
        count = self.validator.verify_all_pending()
        logger.info(f"[验证完成] {count} 条预测已验证")
        return count
    
    def learn(self, force: bool = False) -> Dict:
        """
        执行学习循环
        
        Args:
            force: 是否强制学习（忽略时间间隔）
            
        Returns:
            Dict: 学习结果统计
        """
        # 检查学习间隔
        if not force and self.last_learning_time:
            elapsed = (datetime.now() - self.last_learning_time).total_seconds()
            if elapsed < self.config.learning_interval:
                logger.info(f"[学习跳过] 距离上次学习仅 {elapsed:.0f}秒")
                return {'skipped': True, 'reason': 'interval_not_met'}
        
        logger.info("[学习开始] 分析历史预测结果...")
        
        # 1. 获取待学习的预测记录
        records = self.learner.get_learning_samples(
            min_samples=self.config.min_samples_for_learning
        )
        
        if len(records) < self.config.min_samples_for_learning:
            logger.info(f"[学习跳过] 样本不足: {len(records)} < {self.config.min_samples_for_learning}")
            return {'skipped': True, 'reason': 'insufficient_samples'}
        
        # 2. 分析失败模式
        failure_patterns = self.learner.analyze_failures(records)
        
        # 3. 识别成功模式
        success_patterns = self.learner.analyze_successes(records)
        
        # 4. 更新知识库
        pattern_count = 0
        for pattern in failure_patterns + success_patterns:
            self.pattern_store.add_pattern(pattern)
            pattern_count += 1
        
        # 5. 优化Prompt
        prompt_improvements = self.prompt_optimizer.analyze_and_improve(
            records=records,
            failure_patterns=failure_patterns
        )
        
        # 6. 更新学习状态
        self.last_learning_time = datetime.now()
        
        # 7. 生成学习报告
        result = {
            'skipped': False,
            'timestamp': self.last_learning_time.isoformat(),
            'samples_analyzed': len(records),
            'patterns_discovered': pattern_count,
            'failure_patterns': len(failure_patterns),
            'success_patterns': len(success_patterns),
            'prompt_improvements': len(prompt_improvements),
            'accuracy_trend': self.learner.calculate_accuracy_trend(records)
        }
        
        logger.info(f"[学习完成] 发现 {pattern_count} 个模式, {len(prompt_improvements)} 处Prompt优化")
        
        return result
    
    def get_performance_report(self, days: int = 7) -> Dict:
        """
        获取Agent性能报告
        
        Args:
            days: 统计天数
            
        Returns:
            Dict: 性能报告
        """
        return self.learner.generate_performance_report(days)
    
    def _calculate_target_period(self, interval: str) -> Tuple[datetime, datetime]:
        """计算预测目标时间段"""
        now = datetime.now()
        
        if interval == '15m':
            # 找到下一个15分钟整点
            minute = now.minute
            if minute < 15:
                start = now.replace(minute=15, second=0, microsecond=0)
            elif minute < 30:
                start = now.replace(minute=30, second=0, microsecond=0)
            elif minute < 45:
                start = now.replace(minute=45, second=0, microsecond=0)
            else:
                start = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(minutes=15)
        else:
            # 默认处理
            delta = timedelta(minutes=int(interval.replace('m', '')))
            start = now + delta
            start = start.replace(second=0, microsecond=0)
            end = start + delta
        
        return start, end
    
    def _save_prediction(
        self,
        symbol: str,
        interval: str,
        market_data: Dict,
        consensus: Dict,
        ai_results: List[Dict],
        knowledge_patterns: List[Dict]
    ) -> int:
        """保存预测记录到数据库"""
        # 这里使用原有的 prediction_service 保存
        from prediction_service import PredictionService
        
        service = PredictionService()
        
        target_start, target_end = self._calculate_target_period(interval)
        
        record_id = service.create_prediction_record(
            symbol=symbol,
            interval=interval,
            price_at_predict=market_data['close'],
            macd_at_predict=market_data['macd_hist'],
            kdj_j_at_predict=market_data['kdj_j'],
            consensus_prediction=consensus['prediction'],
            consensus_up_probability=consensus['up_probability'],
            consensus_down_probability=consensus['down_probability'],
            consensus_confidence=consensus['confidence'],
            consensus_reason=consensus['reason'],
            ai_predictions=ai_results
        )
        
        return record_id
    
    def _check_learning_trigger(self):
        """检查是否触发学习"""
        if not self.config.learning_enabled:
            return
        
        if self.last_learning_time is None:
            # 首次运行，记录时间
            self.last_learning_time = datetime.now()
            return
        
        elapsed = (datetime.now() - self.last_learning_time).total_seconds()
        
        if elapsed >= self.config.learning_interval:
            # 触发学习
            self.learn()


if __name__ == '__main__':
    # 测试Agent
    agent = PredictionAgent()
    
    # 执行预测
    result = agent.predict(symbol='BTCUSDT', interval='15m')
    print(f"\n预测结果: {result}")
    
    # 验证待处理预测
    verified = agent.verify_pending()
    print(f"\n验证了 {verified} 条预测")
    
    # 执行学习
    learn_result = agent.learn(force=True)
    print(f"\n学习结果: {learn_result}")
