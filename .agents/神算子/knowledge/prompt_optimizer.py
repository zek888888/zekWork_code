#!/usr/bin/env python3
"""
Prompt优化器
基于历史表现优化AI预测Prompt
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger('PromptOptimizer')


class PromptOptimizer:
    """
    Prompt优化器
    根据知识库中的模式和历史表现，优化AI预测Prompt
    """
    
    # 基础Prompt模板
    BASE_PROMPT = """你是专业量化分析师。请基于以下{symbol}的{interval}数据，预测下一个{interval}的走势。

【当前市场状态】
- 最新价格: ${close:,.2f}
- MACD柱状图: {macd_hist:.2f}
- KDJ J值: {kdj_j:.2f}
- 24h涨跌: {price_change_24h:+.2f}%
- 平均成交量: {volume_avg:,.0f}

【最近10根K线数据】
{klines_summary}

{pattern_warnings}

【分析要求】
1. 综合分析MACD趋势、KDJ位置和价格动能
2. 判断下一根{interval}K线涨(>0.1%)还是跌(<-0.1%)
3. 给出涨的概率(0-100)和跌的概率
4. 给出置信度(0.0-1.0)
5. 简要说明理由(30字内，关键指标分析)

【返回格式】
严格按以下JSON格式返回，不要其他文字:
{{"prediction": "up" 或 "down", "up_probability": 65, "down_probability": 35, "confidence": 0.75, "reason": "理由说明"}}"""
    
    def __init__(self, db_path: str = None):
        """
        初始化Prompt优化器
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path or str(PROJECT_ROOT / "data" / "market_data.db")
        self.optimization_history = []
    
    def optimize_prompt(
        self,
        base_prompt: str,
        patterns: List[Dict],
        market_data: Dict
    ) -> str:
        """
        根据知识库模式优化Prompt
        
        Args:
            base_prompt: 基础Prompt
            patterns: 匹配的知识库模式
            market_data: 市场数据
            
        Returns:
            str: 优化后的Prompt
        """
        if not patterns:
            return base_prompt
        
        # 构建模式警告插入
        pattern_warnings = self._build_pattern_warnings(patterns)
        
        # 替换或添加到基础Prompt
        if '{pattern_warnings}' in base_prompt:
            optimized = base_prompt.format(
                pattern_warnings=pattern_warnings
            )
        else:
            # 插入到分析要求之前
            optimized = base_prompt.replace(
                "【分析要求】",
                f"{pattern_warnings}\n\n【分析要求】"
            )
        
        logger.info(f"[Prompt优化] 应用了 {len(patterns)} 个模式警告")
        
        return optimized
    
    def _build_pattern_warnings(self, patterns: List[Dict]) -> str:
        """构建模式警告部分"""
        warnings = ["【历史模式提示】"]
        
        for i, pattern in enumerate(patterns[:3], 1):  # 最多3个提示
            lesson = pattern.get('lesson', '')
            pattern_type = pattern.get('type', '')
            
            if pattern_type == 'indicator_failure':
                warnings.append(f"{i}. ⚠️ {lesson}")
            elif pattern_type == 'time_pattern':
                warnings.append(f"{i}. ⏰ {lesson}")
            elif pattern_type == 'success_pattern':
                warnings.append(f"{i}. ✅ {lesson}")
            else:
                warnings.append(f"{i}. 💡 {lesson}")
        
        return "\n".join(warnings)
    
    def analyze_and_improve(
        self,
        records: List[Dict],
        failure_patterns: List[Dict]
    ) -> List[Dict]:
        """
        分析历史记录并提出Prompt改进建议
        
        Args:
            records: 历史预测记录
            failure_patterns: 失败模式
            
        Returns:
            List[Dict]: 改进建议列表
        """
        improvements = []
        
        # 分析高失败率的指标组合
        indicator_failures = [
            p for p in failure_patterns 
            if p.get('type') == 'indicator_failure'
        ]
        
        if indicator_failures:
            # 提示需要更仔细地分析这些指标组合
            improvements.append({
                'type': 'indicator_emphasis',
                'priority': 'high',
                'description': '在Prompt中强调特定指标组合的分析',
                'affected_patterns': [p['name'] for p in indicator_failures[:3]]
            })
        
        # 分析时间段模式
        time_patterns = [
            p for p in failure_patterns
            if p.get('type') == 'time_pattern'
        ]
        
        if time_patterns:
            improvements.append({
                'type': 'time_awareness',
                'priority': 'medium',
                'description': '在Prompt中添加时间因素考量',
                'affected_hours': [p['conditions'].get('hour') for p in time_patterns if p.get('conditions')]
            })
        
        # 分析高置信度失败
        high_conf_failures = [
            r for r in records
            if r.get('is_correct') == 0 
            and r.get('consensus_confidence', 0) > 0.8
        ]
        
        if len(high_conf_failures) >= 3:
            improvements.append({
                'type': 'confidence_calibration',
                'priority': 'high',
                'description': '高置信度预测失败较多，需要校准置信度评估标准',
                'failure_count': len(high_conf_failures)
            })
        
        # 记录改进历史
        self.optimization_history.append({
            'timestamp': datetime.now().isoformat(),
            'improvements': improvements,
            'records_analyzed': len(records)
        })
        
        return improvements
    
    def get_default_prompt_template(self) -> str:
        """获取默认Prompt模板"""
        return self.BASE_PROMPT
    
    def generate_improved_prompt(
        self,
        improvements: List[Dict],
        original_prompt: str
    ) -> str:
        """
        基于改进建议生成优化后的Prompt
        
        Args:
            improvements: 改进建议列表
            original_prompt: 原始Prompt
            
        Returns:
            str: 改进后的Prompt
        """
        improved = original_prompt
        
        # 根据改进建议调整Prompt
        for imp in improvements:
            if imp['type'] == 'indicator_emphasis':
                # 强调指标分析
                improved = improved.replace(
                    "1. 综合分析MACD趋势、KDJ位置和价格动能",
                    "1. 综合分析MACD趋势、KDJ位置和价格动能 (特别注意历史表现较差的指标组合)"
                )
            
            elif imp['type'] == 'time_awareness':
                # 添加时间考量
                if "当前时间段" not in improved:
                    improved = improved.replace(
                        "- 24h涨跌: {price_change_24h:+.2f}%",
                        "- 24h涨跌: {price_change_24h:+.2f}%\n- 当前时间段: 请考虑当前时段的历史表现特征"
                    )
            
            elif imp['type'] == 'confidence_calibration':
                # 校准置信度
                improved = improved.replace(
                    "4. 给出置信度(0.0-1.0)",
                    "4. 给出置信度(0.0-1.0)，请保持保守，避免过高估计"
                )
        
        return improved


if __name__ == '__main__':
    # 测试
    optimizer = PromptOptimizer()
    
    # 测试模式警告
    patterns = [
        {
            'type': 'indicator_failure',
            'name': 'MACD正值看跌失败',
            'lesson': 'MACD为正时判断下跌需要更谨慎'
        },
        {
            'type': 'time_pattern',
            'name': '高失败时段',
            'lesson': '目前时段历史上预测较难'
        }
    ]
    
    optimized = optimizer.optimize_prompt(
        optimizer.get_default_prompt_template(),
        patterns,
        {}
    )
    
    print("优化后的Prompt:\n")
    print(optimized[:500] + "...")
