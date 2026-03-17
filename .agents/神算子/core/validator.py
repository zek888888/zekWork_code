#!/usr/bin/env python3
"""
验证器
负责验证预测结果，对比预测与实际价格走势
"""

import os
import sys
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "data-layer"))

from prediction_service import PredictionService

logger = logging.getLogger('PredictionValidator')


class PredictionValidator:
    """
    预测验证器
    将预测结果与实际价格走势进行对比，计算准确性
    """
    
    # 涨跌阈值（超过此值才算涨或跌）
    CHANGE_THRESHOLD = 0.1  # 0.1%
    
    def __init__(self, db_path: str = None):
        """
        初始化验证器
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path or str(PROJECT_ROOT / "data" / "market_data.db")
        self.prediction_service = PredictionService(self.db_path)
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def verify_all_pending(self, max_age_hours: int = 2) -> int:
        """
        验证所有待处理的预测
        
        Args:
            max_age_hours: 最大等待时间，超过此时间才验证
            
        Returns:
            int: 验证的记录数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 查找已过期但尚未验证的预测
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            cursor.execute("""
                SELECT id, symbol, interval, target_period_start, target_period_end,
                       consensus_prediction, price_at_predict
                FROM ai_prediction_records
                WHERE verified_at IS NULL
                AND target_period_end < ?
                ORDER BY target_period_end ASC
            """, (cutoff_time,))
            
            pending_records = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"[验证待处理] 发现 {len(pending_records)} 条待验证记录")
            
            verified_count = 0
            for record in pending_records:
                if self.verify_single(record):
                    verified_count += 1
            
            return verified_count
            
        except Exception as e:
            logger.error(f"[验证失败] {e}")
            return 0
        finally:
            conn.close()
    
    def verify_single(self, record: Dict) -> bool:
        """
        验证单条预测记录
        
        Args:
            record: 预测记录字典
            
        Returns:
            bool: 验证是否成功
        """
        record_id = record['id']
        symbol = record['symbol']
        interval = record['interval']
        target_start = record['target_period_start']
        target_end = record['target_period_end']
        consensus_pred = record['consensus_prediction']
        
        try:
            # 获取实际价格数据
            price_start, price_end, actual_result = self._get_actual_prices(
                symbol, interval, target_start, target_end
            )
            
            if price_start is None or price_end is None:
                logger.warning(f"[验证跳过] 记录 {record_id}: 缺少价格数据")
                return False
            
            # 计算价格变化
            price_change = ((price_end - price_start) / price_start) * 100
            
            # 判断实际结果
            actual_direction = self._determine_direction(price_change)
            
            # 计算是否正确
            is_correct = self._calculate_accuracy(
                consensus_pred, actual_direction, price_change
            )
            
            # 计算准确性得分
            accuracy_score = self._calculate_accuracy_score(
                consensus_pred, actual_direction, price_change,
                record.get('consensus_up_probability', 50),
                record.get('consensus_down_probability', 50)
            )
            
            # 更新记录
            self._update_verification_result(
                record_id=record_id,
                actual_result=actual_direction,
                price_start=price_start,
                price_end=price_end,
                price_change=price_change,
                is_correct=is_correct,
                accuracy_score=accuracy_score
            )
            
            # 更新各AI的准确性
            self._update_ai_accuracy(record_id, actual_direction)
            
            # 创建复盘分析
            self._create_review(record_id, is_correct, price_change)
            
            logger.info(
                f"[验证完成] 记录 {record_id}: "
                f"预测={consensus_pred}, 实际={actual_direction}, "
                f"变化={price_change:+.2f}%, 正确={is_correct}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"[验证失败] 记录 {record_id}: {e}")
            return False
    
    def _get_actual_prices(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime
    ) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """
        获取实际价格数据
        
        Returns:
            Tuple: (开盘价, 收盘价, 方向)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取时间段内的所有K线
            cursor.execute("""
                SELECT timestamp, open, close, high, low
                FROM kline_data
                WHERE symbol = ? AND interval = ?
                AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            """, (symbol, interval, start_time, end_time))
            
            rows = cursor.fetchall()
            
            if not rows:
                return None, None, None
            
            # 开盘价是第一根K线的开盘价
            price_start = float(rows[0]['open'])
            
            # 收盘价是最后一根K线的收盘价
            price_end = float(rows[-1]['close'])
            
            return price_start, price_end, None
            
        except Exception as e:
            logger.error(f"[获取实际价格失败] {e}")
            return None, None, None
        finally:
            conn.close()
    
    def _determine_direction(self, price_change: float) -> str:
        """
        根据价格变化判断方向
        
        Args:
            price_change: 价格变化百分比
            
        Returns:
            str: 'up', 'down', 或 'flat'
        """
        if price_change > self.CHANGE_THRESHOLD:
            return 'up'
        elif price_change < -self.CHANGE_THRESHOLD:
            return 'down'
        else:
            return 'flat'
    
    def _calculate_accuracy(
        self,
        prediction: str,
        actual: str,
        price_change: float
    ) -> Optional[bool]:
        """
        计算预测是否正确
        
        Args:
            prediction: 预测方向
            actual: 实际方向
            price_change: 价格变化
            
        Returns:
            bool: 是否正确，flat返回None
        """
        if actual == 'flat':
            return None  # 平盘不计算准确性
        
        return prediction == actual
    
    def _calculate_accuracy_score(
        self,
        prediction: str,
        actual: str,
        price_change: float,
        up_probability: int,
        down_probability: int
    ) -> float:
        """
        计算准确性得分 (0-1)
        
        算法:
        - 完全正确且高置信度: 1.0
        - 正确但置信度一般: 0.6-0.8
        - 错误: 0.0
        - 平盘: 0.5
        """
        if actual == 'flat':
            return 0.5
        
        if prediction != actual:
            return 0.0
        
        # 预测正确
        if prediction == 'up':
            confidence = up_probability / 100.0
        else:
            confidence = down_probability / 100.0
        
        # 基于置信度和实际涨跌幅计算得分
        magnitude_bonus = min(abs(price_change) / 1.0, 1.0) * 0.2  # 最多0.2加成
        
        score = confidence * 0.8 + magnitude_bonus
        return round(min(score, 1.0), 2)
    
    def _update_verification_result(
        self,
        record_id: int,
        actual_result: str,
        price_start: float,
        price_end: float,
        price_change: float,
        is_correct: Optional[bool],
        accuracy_score: float
    ):
        """更新验证结果到数据库"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE ai_prediction_records SET
                    actual_result = ?,
                    price_at_target_start = ?,
                    price_at_target_end = ?,
                    actual_price_change_percent = ?,
                    is_correct = ?,
                    accuracy_score = ?,
                    verified_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                actual_result,
                price_start,
                price_end,
                price_change,
                is_correct,
                accuracy_score,
                record_id
            ))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[更新验证结果失败] {e}")
            raise
        finally:
            conn.close()
    
    def _update_ai_accuracy(self, record_id: int, actual_result: str):
        """更新各AI的准确性"""
        if actual_result == 'flat':
            return  # 平盘不更新AI准确性
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取该记录的所有AI预测
            cursor.execute("""
                SELECT id, prediction FROM ai_individual_predictions
                WHERE record_id = ?
            """, (record_id,))
            
            for row in cursor.fetchall():
                ai_pred = row['prediction']
                ai_is_correct = (ai_pred == actual_result) if ai_pred in ['up', 'down'] else None
                
                cursor.execute("""
                    UPDATE ai_individual_predictions
                    SET is_correct = ?
                    WHERE id = ?
                """, (ai_is_correct, row['id']))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[更新AI准确性失败] {e}")
        finally:
            conn.close()
    
    def _create_review(self, record_id: int, is_correct: Optional[bool], price_change: float):
        """创建复盘分析记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if is_correct:
                review_type = 'success_analysis'
                primary_reason = self._analyze_success_reason(record_id)
            else:
                review_type = 'failure_analysis'
                primary_reason = self._analyze_failure_reason(record_id, price_change)
            
            # 检查是否需要更新知识库
            should_update_kb = self._should_update_kb(is_correct, price_change)
            
            cursor.execute("""
                INSERT INTO prediction_reviews (
                    record_id, review_type, primary_reason,
                    should_update_kb, reviewed_at
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (record_id, review_type, primary_reason, should_update_kb))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[创建复盘失败] {e}")
        finally:
            conn.close()
    
    def _analyze_success_reason(self, record_id: int) -> str:
        """分析成功原因"""
        # 这里可以根据记录的具体指标分析
        return "技术指标综合判断准确"
    
    def _analyze_failure_reason(self, record_id: int, price_change: float) -> str:
        """分析失败原因"""
        # 可以根据涨跌幅和预测方向分析
        if abs(price_change) > 2.0:
            return "市场出现突发性大幅波动，超出技术分析范畴"
        else:
            return "指标信号不明确或出现虚假信号"
    
    def _should_update_kb(self, is_correct: Optional[bool], price_change: float) -> bool:
        """判断是否需要更新知识库"""
        # 以下情况值得学习：
        # 1. 失败但是市场波动很大（可能是新模式）
        # 2. 成功且涨跌幅很大（强趋势确认）
        if is_correct is False and abs(price_change) > 1.5:
            return True
        if is_correct is True and abs(price_change) > 1.0:
            return True
        return False
    
    def get_verification_stats(self, days: int = 7) -> Dict:
        """获取验证统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_verified,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                    SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as wrong,
                    SUM(CASE WHEN is_correct IS NULL THEN 1 ELSE 0 END) as flat,
                    AVG(accuracy_score) as avg_score,
                    AVG(actual_price_change_percent) as avg_change
                FROM ai_prediction_records
                WHERE verified_at IS NOT NULL
                AND verified_at >= ?
            """, (cutoff_date,))
            
            stats = dict(cursor.fetchone())
            
            return {
                'period_days': days,
                'total_verified': stats.get('total_verified', 0),
                'correct': stats.get('correct', 0),
                'wrong': stats.get('wrong', 0),
                'flat': stats.get('flat', 0),
                'accuracy_rate': round((stats.get('correct', 0) / stats.get('total_verified', 1)) * 100, 2) if stats.get('total_verified') else 0,
                'avg_score': round(stats.get('avg_score', 0), 2),
                'avg_price_change': round(stats.get('avg_change', 0), 2)
            }
            
        except Exception as e:
            logger.error(f"[获取验证统计失败] {e}")
            return {}
        finally:
            conn.close()


if __name__ == '__main__':
    # 测试
    validator = PredictionValidator()
    
    # 验证待处理的预测
    count = validator.verify_all_pending()
    print(f"\u9a8c\u8bc1\u4e86 {count} \u6761\u8bb0\u5f55")
    
    # 获取验证统计
    stats = validator.get_verification_stats(7)
    print(f"\u7edf\u8ba1: {stats}")
