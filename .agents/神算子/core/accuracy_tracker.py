#!/usr/bin/env python3
"""
神算子命中率追踪系统
持续追踪预测准确率，自动优化策略
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class AccuracyTracker:
    """命中率追踪器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(PROJECT_ROOT / "data" / "market_data.db")
        self._init_tables()
    
    def _init_tables(self):
        """初始化命中率追踪表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 预测准确率统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_accuracy_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                interval TEXT NOT NULL,
                total_predictions INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                wrong_predictions INTEGER DEFAULT 0,
                accuracy_rate REAL DEFAULT 0,
                avg_confidence REAL DEFAULT 0,
                high_conf_accuracy REAL DEFAULT 0,  -- 高置信度准确率
                low_conf_accuracy REAL DEFAULT 0,   -- 低置信度准确率
                market_state TEXT,
                UNIQUE(date, symbol, interval, market_state)
            )
        """)
        
        # AI个体准确率表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_individual_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ai_name TEXT NOT NULL,
                date TEXT NOT NULL,
                total INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0,
                accuracy_rate REAL DEFAULT 0,
                avg_response_time_ms INTEGER DEFAULT 0,
                UNIQUE(ai_name, date)
            )
        """)
        
        # 优化建议表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                category TEXT NOT NULL,  -- 'threshold', 'weight', 'filter', 'other'
                suggestion TEXT NOT NULL,
                current_value TEXT,
                suggested_value TEXT,
                expected_improvement REAL,
                applied BOOLEAN DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_prediction_result(self, prediction_id: str, symbol: str, 
                                 interval: str, predicted_direction: str,
                                 actual_direction: str, confidence: float,
                                 market_state: str = 'unknown'):
        """记录预测结果"""
        is_correct = (predicted_direction == actual_direction)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        date = datetime.now().strftime('%Y-%m-%d')
        
        # 更新或插入统计
        cursor.execute("""
            INSERT INTO prediction_accuracy_stats 
            (date, symbol, interval, market_state, total_predictions, correct_predictions, wrong_predictions)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(date, symbol, interval, market_state) DO UPDATE SET
                total_predictions = total_predictions + 1,
                correct_predictions = correct_predictions + ?,
                wrong_predictions = wrong_predictions + ?,
                accuracy_rate = (correct_predictions + ?) * 100.0 / (total_predictions + 1)
        """, (date, symbol, interval, market_state, 
              1 if is_correct else 0, 0 if is_correct else 1,
              1 if is_correct else 0, 0 if is_correct else 1,
              1 if is_correct else 0))
        
        conn.commit()
        conn.close()
        
        return is_correct
    
    def get_accuracy_report(self, days: int = 7) -> Dict:
        """获取命中率报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 总体命中率
        cursor.execute("""
            SELECT 
                SUM(total_predictions) as total,
                SUM(correct_predictions) as correct,
                AVG(accuracy_rate) as avg_rate
            FROM prediction_accuracy_stats
            WHERE date >= ?
        """, (start_date,))
        
        row = cursor.fetchone()
        total = row[0] or 0
        correct = row[1] or 0
        overall_rate = (correct / total * 100) if total > 0 else 0
        
        # 分市场状态的命中率
        cursor.execute("""
            SELECT market_state, 
                   SUM(total_predictions) as total,
                   SUM(correct_predictions) as correct,
                   AVG(accuracy_rate) as rate
            FROM prediction_accuracy_stats
            WHERE date >= ?
            GROUP BY market_state
        """, (start_date,))
        
        by_market_state = {}
        for row in cursor.fetchall():
            by_market_state[row[0]] = {
                'total': row[1],
                'correct': row[2],
                'rate': round(row[3], 2) if row[3] else 0
            }
        
        # 各AI命中率
        cursor.execute("""
            SELECT ai_name,
                   SUM(total) as total,
                   SUM(correct) as correct,
                   AVG(accuracy_rate) as rate
            FROM ai_individual_accuracy
            WHERE date >= ?
            GROUP BY ai_name
        """, (start_date,))
        
        by_ai = {}
        for row in cursor.fetchall():
            by_ai[row[0]] = {
                'total': row[1],
                'correct': row[2],
                'rate': round(row[3], 2) if row[3] else 0
            }
        
        # 最近7天趋势
        cursor.execute("""
            SELECT date, accuracy_rate
            FROM prediction_accuracy_stats
            WHERE date >= ?
            GROUP BY date
            ORDER BY date
        """, (start_date,))
        
        trend = [{'date': row[0], 'rate': round(row[1], 2)} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'period_days': days,
            'total_predictions': total,
            'correct_predictions': correct,
            'overall_accuracy': round(overall_rate, 2),
            'by_market_state': by_market_state,
            'by_ai': by_ai,
            'trend': trend
        }
    
    def analyze_and_suggest(self) -> List[Dict]:
        """分析数据并生成优化建议"""
        suggestions = []
        
        report = self.get_accuracy_report(days=14)
        
        # 1. 置信度阈值优化建议
        overall_acc = report['overall_accuracy']
        
        if overall_acc < 55:
            suggestions.append({
                'category': 'threshold',
                'suggestion': '整体命中率偏低，建议提高置信度阈值至0.70',
                'current_value': '0.65',
                'suggested_value': '0.70',
                'expected_improvement': 0.05
            })
        elif overall_acc > 70:
            suggestions.append({
                'category': 'threshold',
                'suggestion': '整体命中率较高，可适当降低置信度阈值至0.60以增加交易机会',
                'current_value': '0.65',
                'suggested_value': '0.60',
                'expected_improvement': 0.02
            })
        
        # 2. AI权重优化建议
        by_ai = report['by_ai']
        if by_ai:
            best_ai = max(by_ai.items(), key=lambda x: x[1]['rate'])
            worst_ai = min(by_ai.items(), key=lambda x: x[1]['rate'])
            
            if best_ai[1]['rate'] - worst_ai[1]['rate'] > 15:
                suggestions.append({
                    'category': 'weight',
                    'suggestion': f'{best_ai[0]}表现优异({best_ai[1]["rate"]}%)，建议增加其权重；{worst_ai[0]}表现较差({worst_ai[1]["rate"]}%)，建议降低权重或暂时停用',
                    'current_value': 'equal_weights',
                    'suggested_value': f'{best_ai[0]}:1.5, {worst_ai[0]}:0.5',
                    'expected_improvement': 0.03
                })
        
        # 3. 市场状态过滤建议
        by_state = report['by_market_state']
        if by_state:
            for state, data in by_state.items():
                if data['rate'] < 45 and data['total'] > 10:
                    suggestions.append({
                        'category': 'filter',
                        'suggestion': f'{state}市场状态命中率仅{data["rate"]}%，建议在此状态下减少交易或暂停',
                        'current_value': 'trade_all_states',
                        'suggested_value': f'skip_{state}',
                        'expected_improvement': 0.04
                    })
        
        # 保存建议到数据库
        self._save_suggestions(suggestions)
        
        return suggestions
    
    def _save_suggestions(self, suggestions: List[Dict]):
        """保存优化建议"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for sug in suggestions:
            cursor.execute("""
                INSERT INTO optimization_suggestions
                (category, suggestion, current_value, suggested_value, expected_improvement)
                VALUES (?, ?, ?, ?, ?)
            """, (sug['category'], sug['suggestion'], sug['current_value'], 
                  sug['suggested_value'], sug['expected_improvement']))
        
        conn.commit()
        conn.close()
    
    def get_hit_rate_by_confidence(self, confidence_threshold: float = 0.65) -> Dict:
        """获取不同置信度区间的命中率"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 这里需要从原始预测记录表查询
        # 假设表中有confidence字段
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN confidence >= 0.80 THEN 'high'
                    WHEN confidence >= 0.65 THEN 'medium'
                    ELSE 'low'
                END as conf_level,
                COUNT(*) as total,
                SUM(CASE WHEN prediction_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM ai_prediction_records
            WHERE created_at > datetime('now', '-7 days')
            GROUP BY conf_level
        """)
        
        result = {}
        for row in cursor.fetchall():
            level = row[0]
            total = row[1]
            correct = row[2]
            rate = (correct / total * 100) if total > 0 else 0
            result[level] = {
                'total': total,
                'correct': correct,
                'rate': round(rate, 2)
            }
        
        conn.close()
        return result


if __name__ == "__main__":
    tracker = AccuracyTracker()
    
    print("=" * 60)
    print("🎯 神算子命中率追踪报告")
    print("=" * 60)
    
    report = tracker.get_accuracy_report(days=7)
    
    print(f"\n📊 总体表现 (最近7天)")
    print(f"   总预测: {report['total_predictions']} 次")
    print(f"   命中: {report['correct_predictions']} 次")
    print(f"   命中率: {report['overall_accuracy']}%")
    
    print(f"\n📈 分市场状态命中率:")
    for state, data in report['by_market_state'].items():
        print(f"   {state}: {data['rate']}% ({data['correct']}/{data['total']})")
    
    print(f"\n🤖 各AI命中率:")
    for ai, data in report['by_ai'].items():
        print(f"   {ai}: {data['rate']}% ({data['correct']}/{data['total']})")
    
    print("\n💡 优化建议:")
    suggestions = tracker.analyze_and_suggest()
    for i, sug in enumerate(suggestions, 1):
        print(f"   {i}. [{sug['category']}] {sug['suggestion']}")
        print(f"      建议值: {sug['suggested_value']}")
