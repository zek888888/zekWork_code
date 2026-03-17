#!/usr/bin/env python3
"""
模式存储
管理预测模式和知识库
"""

import os
import sys
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger('PatternStore')


class PatternStore:
    """
    模式存储类
    管理所有学习到的预测模式
    """
    
    def __init__(self, db_path: str = None, max_patterns: int = 1000):
        self.db_path = db_path or str(PROJECT_ROOT / "data" / "market_data.db")
        self.max_patterns = max_patterns
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def add_pattern(self, pattern: Dict) -> int:
        """
        添加新的模式到知识库
        
        Args:
            pattern: 模式字典
            
        Returns:
            int: 模式ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查是否已存在相似模式
            existing_id = self._find_similar_pattern(cursor, pattern)
            
            if existing_id:
                # 更新现有模式
                cursor.execute("""
                    UPDATE knowledge_base_patterns SET
                        total_occurrences = total_occurrences + ?,
                        correct_predictions = correct_predictions + ?,
                        accuracy_rate = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    pattern.get('occurrence_count', 1),
                    pattern.get('correct_count', 0),
                    pattern.get('accuracy_rate', 0.5),
                    existing_id
                ))
                pattern_id = existing_id
                logger.debug(f"[模式更新] ID={existing_id}")
            else:
                # 添加新模式
                cursor.execute("""
                    INSERT INTO knowledge_base_patterns (
                        pattern_type, pattern_name, pattern_description,
                        indicator_conditions, time_features,
                        total_occurrences, correct_predictions, accuracy_rate,
                        status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    pattern.get('type', 'general'),
                    pattern.get('name', 'Unknown Pattern'),
                    pattern.get('description', ''),
                    json.dumps(pattern.get('conditions', {})),
                    json.dumps(pattern.get('time_features', {})),
                    pattern.get('occurrence_count', 1),
                    pattern.get('correct_count', 0),
                    pattern.get('accuracy_rate', 0.5),
                    'active'
                ))
                pattern_id = cursor.lastrowid
                logger.info(f"[模式添加] ID={pattern_id}, {pattern.get('name')}")
            
            conn.commit()
            
            # 清理旧模式
            self._cleanup_old_patterns(cursor)
            conn.commit()
            
            return pattern_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[模式添加失败] {e}")
            raise
        finally:
            conn.close()
    
    def find_matching_patterns(
        self,
        symbol: str,
        interval: str,
        market_conditions: Dict
    ) -> List[Dict]:
        """
        查找匹配当前市场条件的模式
        
        Args:
            symbol: 交易对
            interval: 时间维度
            market_conditions: 市场条件
            
        Returns:
            List[Dict]: 匹配的模式列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取所有活跃模式
            cursor.execute("""
                SELECT * FROM knowledge_base_patterns
                WHERE status = 'active'
                AND (best_interval IS NULL OR best_interval = ?)
                ORDER BY accuracy_rate DESC, total_occurrences DESC
                LIMIT 50
            """, (interval,))
            
            patterns = [dict(row) for row in cursor.fetchall()]
            
            # 过滤匹配的模式
            matched = []
            for pattern in patterns:
                if self._check_pattern_match(pattern, market_conditions):
                    matched.append(pattern)
            
            # 只返回最相关的前5个
            return matched[:5]
            
        finally:
            conn.close()
    
    def _find_similar_pattern(self, cursor, pattern: Dict) -> Optional[int]:
        """查找相似的现有模式"""
        pattern_type = pattern.get('type')
        conditions = json.dumps(pattern.get('conditions', {}), sort_keys=True)
        
        cursor.execute("""
            SELECT id, indicator_conditions FROM knowledge_base_patterns
            WHERE pattern_type = ?
            AND status = 'active'
        """, (pattern_type,))
        
        for row in cursor.fetchall():
            existing_conditions = row['indicator_conditions']
            if existing_conditions:
                try:
                    existing = json.loads(existing_conditions)
                    current = pattern.get('conditions', {})
                    
                    # 简单的相似度检查
                    if self._conditions_similar(existing, current):
                        return row['id']
                except:
                    pass
        
        return None
    
    def _conditions_similar(self, cond1: Dict, cond2: Dict) -> bool:
        """检查两个条件是否相似"""
        # 如果关键字匹配率超过80%，认为相似
        keys1 = set(cond1.keys())
        keys2 = set(cond2.keys())
        
        if not keys1 or not keys2:
            return False
        
        intersection = keys1 & keys2
        union = keys1 | keys2
        
        similarity = len(intersection) / len(union)
        
        # 更进一步检查值的相似性
        value_matches = 0
        for key in intersection:
            if cond1[key] == cond2[key]:
                value_matches += 1
        
        value_similarity = value_matches / len(intersection) if intersection else 0
        
        return similarity > 0.7 and value_similarity > 0.7
    
    def _check_pattern_match(self, pattern: Dict, market_conditions: Dict) -> bool:
        """检查模式是否匹配当前市场条件"""
        try:
            conditions = json.loads(pattern.get('indicator_conditions', '{}'))
            
            # 检查MACD范围
            if 'macd_range' in conditions:
                macd = market_conditions.get('macd_hist', 0)
                macd_range = conditions['macd_range']
                if not (macd_range[0] <= macd <= macd_range[1]):
                    return False
            
            # 检查KDJ范围
            if 'kdj_range' in conditions:
                kdj = market_conditions.get('kdj_j', 50)
                kdj_range = conditions['kdj_range']
                if not (kdj_range[0] <= kdj <= kdj_range[1]):
                    return False
            
            # 检查预测方向（如果模式有特定方向）
            if 'prediction' in conditions:
                # 这里不检查，因为我们想要所有相关模式
                pass
            
            return True
            
        except Exception as e:
            logger.warning(f"[模式匹配失败] {e}")
            return False
    
    def _cleanup_old_patterns(self, cursor):
        """清理旧的、准确率低的模式"""
        # 检查当前模式数量
        cursor.execute("SELECT COUNT(*) FROM knowledge_base_patterns WHERE status = 'active'")
        count = cursor.fetchone()[0]
        
        if count > self.max_patterns:
            # 标记最老的、准确率低的模式为已弃用
            to_remove = count - self.max_patterns
            cursor.execute("""
                UPDATE knowledge_base_patterns
                SET status = 'deprecated'
                WHERE id IN (
                    SELECT id FROM knowledge_base_patterns
                    WHERE status = 'active'
                    ORDER BY accuracy_rate ASC, updated_at ASC
                    LIMIT ?
                )
            """, (to_remove,))
            logger.info(f"[模式清理] 标记 {to_remove} 个旧模式为已弃用")
    
    def get_pattern_stats(self) -> Dict:
        """获取模式统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                AVG(accuracy_rate) as avg_accuracy,
                SUM(total_occurrences) as total_occurrences
            FROM knowledge_base_patterns
        """)
        
        stats = dict(cursor.fetchone())
        conn.close()
        
        return stats


if __name__ == '__main__':
    store = PatternStore()
    
    # 测试添加
    pattern = {
        'type': 'indicator_failure',
        'name': 'MACD正值时看跌失败',
        'description': '当MACD为正但预测看跌时容易失败',
        'conditions': {
            'macd_range': [0, 100],
            'prediction': 'down'
        },
        'occurrence_count': 5,
        'correct_count': 1,
        'accuracy_rate': 0.2
    }
    
    pid = store.add_pattern(pattern)
    print(f"\u6dfb加模式 ID: {pid}")
    
    # 查看统计
    stats = store.get_pattern_stats()
    print(f"\u7edf计: {stats}")
