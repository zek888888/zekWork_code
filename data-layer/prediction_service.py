#!/usr/bin/env python3
"""
预测统计报告服务
管理AI预测记录、验证和知识库学习
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# 添加项目路径
PROJECT_PATH = Path(os.path.expanduser("~/.openclaw/workspace/quant-trading"))
sys.path.insert(0, str(PROJECT_PATH))
sys.path.insert(0, str(PROJECT_PATH / "config-layer"))

DB_PATH = PROJECT_PATH / "data" / "market_data.db"


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


class PredictionService:
    """预测服务类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self._ensure_tables()
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_tables(self):
        """确保表存在"""
        sql_path = PROJECT_PATH / "data-layer" / "prediction_tables.sql"
        if sql_path.exists():
            with open(sql_path, 'r') as f:
                sql = f.read()
            conn = self._get_connection()
            conn.executescript(sql)
            conn.commit()
            conn.close()
    
    def create_prediction_record(
        self,
        symbol: str,
        interval: str,
        price_at_predict: float,
        macd_at_predict: float,
        kdj_j_at_predict: float,
        consensus_prediction: str,
        consensus_up_probability: int,
        consensus_down_probability: int,
        consensus_confidence: float,
        consensus_reason: str,
        ai_predictions: List[Dict]
    ) -> int:
        """
        创建新的预测记录
        
        执行时间规则：
        - 14:50 -> 预测 15:00-15:15
        - 29:50 -> 预测 15:15-15:30
        - 44:50 -> 预测 15:30-15:45
        - 59:50 -> 预测 15:45-16:00
        """
        now = datetime.now()
        
        # 计算目标时间段
        target_period_start, target_period_end = self._calculate_target_period(now, interval)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查是否已存在相同记录
            cursor.execute("""
                SELECT id FROM ai_prediction_records
                WHERE symbol = ? AND interval = ? AND target_period_start = ?
            """, (symbol, interval, target_period_start))
            
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有记录
                record_id = existing['id']
                cursor.execute("""
                    UPDATE ai_prediction_records SET
                        predict_initiated_at = ?,
                        price_at_predict = ?,
                        macd_at_predict = ?,
                        kdj_j_at_predict = ?,
                        consensus_prediction = ?,
                        consensus_up_probability = ?,
                        consensus_down_probability = ?,
                        consensus_confidence = ?,
                        consensus_reason = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    now, price_at_predict, macd_at_predict, kdj_j_at_predict,
                    consensus_prediction, consensus_up_probability,
                    consensus_down_probability, consensus_confidence, consensus_reason,
                    record_id
                ))
                
                # 删除旧的AI预测详情
                cursor.execute("DELETE FROM ai_individual_predictions WHERE record_id = ?", (record_id,))
            else:
                # 插入新记录
                cursor.execute("""
                    INSERT INTO ai_prediction_records (
                        symbol, interval, predict_initiated_at,
                        target_period_start, target_period_end,
                        price_at_predict, macd_at_predict, kdj_j_at_predict,
                        consensus_prediction, consensus_up_probability,
                        consensus_down_probability, consensus_confidence, consensus_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, interval, now,
                    target_period_start, target_period_end,
                    price_at_predict, macd_at_predict, kdj_j_at_predict,
                    consensus_prediction, consensus_up_probability,
                    consensus_down_probability, consensus_confidence, consensus_reason
                ))
                
                record_id = cursor.lastrowid
            
            # 插入各AI详细预测
            for ai_pred in ai_predictions:
                cursor.execute("""
                    INSERT INTO ai_individual_predictions (
                        record_id, ai_name, ai_provider, ai_model,
                        prediction, up_probability, down_probability,
                        confidence, reason, raw_response,
                        response_time_ms, status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record_id,
                    ai_pred.get('ai_name'),
                    ai_pred.get('ai_provider'),
                    ai_pred.get('ai_model'),
                    ai_pred.get('prediction'),
                    ai_pred.get('up_probability', 50),
                    ai_pred.get('down_probability', 50),
                    ai_pred.get('confidence', 0.5),
                    ai_pred.get('reason', ''),
                    ai_pred.get('raw_response'),
                    ai_pred.get('response_time_ms'),
                    ai_pred.get('source', 'success'),
                    ai_pred.get('error_message')
                ))
            
            conn.commit()
            return record_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _calculate_target_period(self, predict_time: datetime, interval: str) -> Tuple[datetime, datetime]:
        """计算预测的目标时间段"""
        if interval == '15m':
            # 找到下一个15分钟整点
            minute = predict_time.minute
            if minute < 15:
                target_start = predict_time.replace(minute=15, second=0, microsecond=0)
            elif minute < 30:
                target_start = predict_time.replace(minute=30, second=0, microsecond=0)
            elif minute < 45:
                target_start = predict_time.replace(minute=45, second=0, microsecond=0)
            else:
                # 下一小时的00分
                target_start = (predict_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            
            target_end = target_start + timedelta(minutes=15)
            return target_start, target_end
        
        # 其他interval的默认处理
        minutes_map = {'5m': 5, '30m': 30, '1h': 60}
        delta = timedelta(minutes=minutes_map.get(interval, 15))
        
        # 找到下一个整点
        target_start = predict_time + delta
        target_start = target_start.replace(second=0, microsecond=0)
        target_end = target_start + delta
        
        return target_start, target_end
    
    def verify_prediction(self, record_id: int) -> bool:
        """验证预测结果，查询实际价格走势"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取预测记录
            cursor.execute("""
                SELECT * FROM ai_prediction_records WHERE id = ?
            """, (record_id,))
            record = cursor.fetchone()
            
            if not record:
                return False
            
            target_start = record['target_period_start']
            target_end = record['target_period_end']
            consensus_pred = record['consensus_prediction']
            symbol = record['symbol']
            
            # 查询实际价格数据
            cursor.execute("""
                SELECT timestamp, close FROM kline_data
                WHERE symbol = ? AND interval = '15m'
                AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            """, (symbol, target_start, target_end))
            
            rows = cursor.fetchall()
            
            if len(rows) < 2:
                # 数据不足，无法验证
                return False
            
            price_start = rows[0]['close']
            price_end = rows[-1]['close']
            price_change = ((price_end - price_start) / price_start) * 100
            
            # 判断实际结果
            if price_change > 0.1:  # 涨超过0.1%
                actual_result = 'up'
            elif price_change < -0.1:  # 跌超过0.1%
                actual_result = 'down'
            else:
                actual_result = 'flat'
            
            # 计算准确性
            is_correct = (consensus_pred == actual_result) if actual_result != 'flat' else None
            
            # 准确性得分
            if actual_result == 'flat':
                accuracy_score = 0.5
            elif is_correct:
                # 预测准确，根据概率计算得分
                if consensus_pred == 'up':
                    accuracy_score = record['consensus_up_probability'] / 100.0
                else:
                    accuracy_score = record['consensus_down_probability'] / 100.0
            else:
                accuracy_score = 0.0
            
            # 更新记录
            cursor.execute("""
                UPDATE ai_prediction_records SET
                    actual_result = ?,
                    price_at_target_start = ?,
                    price_at_target_end = ?,
                    actual_price_change_percent = ?,
                    is_correct = ?,
                    accuracy_score = ?,
                    verified_at = ?
                WHERE id = ?
            """, (
                actual_result, price_start, price_end,
                price_change, is_correct, accuracy_score,
                datetime.now(), record_id
            ))
            
            # 更新各AI的准确性
            cursor.execute("""
                SELECT * FROM ai_individual_predictions WHERE record_id = ?
            """, (record_id,))
            
            for ai_pred in cursor.fetchall():
                ai_is_correct = (ai_pred['prediction'] == actual_result) if actual_result != 'flat' else None
                cursor.execute("""
                    UPDATE ai_individual_predictions
                    SET is_correct = ?
                    WHERE id = ?
                """, (ai_is_correct, ai_pred['id']))
            
            conn.commit()
            
            # 创建复盘分析
            self._create_prediction_review(record_id, is_correct, price_change)
            
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"验证预测失败: {e}")
            return False
        finally:
            conn.close()
    
    def _create_prediction_review(self, record_id: int, is_correct: bool, price_change: float):
        """创建预测复盘分析"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取预测详情
            cursor.execute("""
                SELECT * FROM ai_prediction_records WHERE id = ?
            """, (record_id,))
            record = cursor.fetchone()
            
            if not record:
                return
            
            # 分析原因
            if is_correct:
                review_type = 'success_analysis'
                primary_reason = self._analyze_success_reason(record)
            else:
                review_type = 'failure_analysis'
                primary_reason = self._analyze_failure_reason(record, price_change)
            
            # 检查是否需要更新知识库
            should_update_kb = self._should_update_knowledge_base(record)
            
            cursor.execute("""
                INSERT INTO prediction_reviews (
                    record_id, review_type, primary_reason,
                    should_update_kb, reviewed_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (record_id, review_type, primary_reason, should_update_kb, datetime.now()))
            
            conn.commit()
            
        except Exception as e:
            print(f"创建复盘分析失败: {e}")
        finally:
            conn.close()
    
    def _analyze_success_reason(self, record) -> str:
        """分析预测成功的原因"""
        reasons = []
        
        macd = record['macd_at_predict']
        kdj = record['kdj_j_at_predict']
        prediction = record['consensus_prediction']
        
        if prediction == 'up':
            if macd > 0:
                reasons.append("MACD正值支持上涨判断")
            if kdj < 30:
                reasons.append("KDJ超卖区反弹")
        else:
            if macd < 0:
                reasons.append("MACD负值支持下跌判断")
            if kdj > 70:
                reasons.append("KDJ超买区回调")
        
        return "; ".join(reasons) if reasons else "技术指标综合判断准确"
    
    def _analyze_failure_reason(self, record, actual_change: float) -> str:
        """分析预测失败的原因"""
        reasons = []
        
        macd = record['macd_at_predict']
        kdj = record['kdj_j_at_predict']
        prediction = record['consensus_prediction']
        
        # 检查是否有背离
        if prediction == 'up' and actual_change < 0:
            if macd < 0:
                reasons.append("MACD负值时判断上涨，信号冲突")
            if abs(actual_change) > 1:
                reasons.append("出现突发性下跌，超出技术预期")
        
        elif prediction == 'down' and actual_change > 0:
            if macd > 0:
                reasons.append("MACD正值时判断下跌，信号冲突")
            if actual_change > 1:
                reasons.append("出现突发性上涨，超出技术预期")
        
        # KDJ极端情况
        if kdj < 10 or kdj > 90:
            reasons.append("KDJ处于极端区域，可能产生假信号")
        
        return "; ".join(reasons) if reasons else "市场出现不可预测波动"
    
    def _should_update_knowledge_base(self, record) -> bool:
        """判断是否需要更新知识库"""
        # 特殊情况才更新知识库
        confidence = record['consensus_confidence']
        
        # 高置信度但失败，或低置信度但成功，都值得学习
        if (confidence > 0.8 and record['is_correct'] == False) or \
           (confidence < 0.5 and record['is_correct'] == True):
            return True
        
        return False
    
    def get_prediction_report(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        symbol: str = 'BTCUSDT',
        interval: str = '15m'
    ) -> List[Dict]:
        """获取预测统计报告"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
                SELECT 
                    r.*,
                    GROUP_CONCAT(
                        json_object(
                            'ai_name', ai.ai_name,
                            'ai_provider', ai.ai_provider,
                            'prediction', ai.prediction,
                            'up_probability', ai.up_probability,
                            'down_probability', ai.down_probability,
                            'confidence', ai.confidence,
                            'reason', ai.reason,
                            'is_correct', ai.is_correct,
                            'status', ai.status
                        )
                    ) as ai_details
                FROM ai_prediction_records r
                LEFT JOIN ai_individual_predictions ai ON r.id = ai.record_id
                WHERE r.symbol = ? AND r.interval = ?
            """
            params = [symbol, interval]
            
            if start_date:
                sql += " AND r.predict_initiated_at >= ?"
                params.append(start_date)
            
            if end_date:
                sql += " AND r.predict_initiated_at <= ?"
                params.append(end_date)
            
            sql += " GROUP BY r.id ORDER BY r.predict_initiated_at DESC"
            
            cursor.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                record = dict(row)
                # 解析AI详情
                if record.get('ai_details'):
                    try:
                        record['ai_details'] = json.loads(f"[{record['ai_details']}]")
                    except:
                        record['ai_details'] = []
                results.append(record)
            
            return results
            
        finally:
            conn.close()
    
    def get_accuracy_stats(self, days: int = 7) -> Dict:
        """获取准确率统计"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 总体统计
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                    ROUND(AVG(consensus_confidence), 2) as avg_confidence,
                    ROUND(AVG(accuracy_score), 2) as avg_accuracy_score
                FROM ai_prediction_records
                WHERE is_correct IS NOT NULL
                AND predict_initiated_at >= ?
            """, (start_date,))
            
            overall = dict(cursor.fetchone())
            
            # 各AI统计
            cursor.execute("""
                SELECT 
                    ai_name,
                    ai_provider,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                    ROUND(
                        SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
                        2
                    ) as accuracy_rate
                FROM ai_individual_predictions
                WHERE is_correct IS NOT NULL
                AND created_at >= ?
                GROUP BY ai_name, ai_provider
            """, (start_date,))
            
            ai_stats = [dict(row) for row in cursor.fetchall()]
            
            return {
                'overall': overall,
                'ai_stats': ai_stats,
                'period_days': days
            }
            
        finally:
            conn.close()
    
    def verify_pending_predictions(self):
        """验证所有待验证的预测"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取所有已过期但尚未验证的预测
            cursor.execute("""
                SELECT id FROM ai_prediction_records
                WHERE verified_at IS NULL
                AND target_period_end < datetime('now', '-15 minutes')
            """)
            
            pending_ids = [row['id'] for row in cursor.fetchall()]
            
            verified_count = 0
            for record_id in pending_ids:
                if self.verify_prediction(record_id):
                    verified_count += 1
            
            return verified_count
            
        finally:
            conn.close()


# 单例模式
_prediction_service = None

def get_prediction_service() -> PredictionService:
    """获取预测服务单例"""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service


if __name__ == '__main__':
    # 测试
    service = get_prediction_service()
    print("预测服务初始化成功")
    
    # 测试验证待处理的预测
    count = service.verify_pending_predictions()
    print(f"验证了 {count} 条待处理预测")
