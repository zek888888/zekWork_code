#!/usr/bin/env python3
"""
AI 知识库管理系统
- 交易策略知识库
- 市场规律知识库
- 回测经验知识库
- 自学习更新
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

# 配置
DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"
KNOWLEDGE_DIR = Path.home() / ".openclaw/workspace/quant-trading/ai_models/knowledge_base"
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


class KnowledgeType(Enum):
    STRATEGY = "策略知识"
    MARKET_PATTERN = "市场规律"
    TRADING_EXPERIENCE = "交易经验"
    RISK_MANAGEMENT = "风控规则"
    FACTOR_INSIGHT = "因子洞察"


@dataclass
class KnowledgeEntry:
    """知识条目"""
    id: str
    type: str
    title: str
    content: str
    tags: List[str]
    source: str  # 来源: 回测/实盘/研报/经验
    confidence: float  # 置信度 0-1
    performance_score: float  # 表现评分
    usage_count: int  # 使用次数
    created_at: datetime
    updated_at: datetime
    metadata: Dict  # 额外元数据


class KnowledgeBaseManager:
    """知识库管理器"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()
        self._load_builtin_knowledge()
    
    def init_database(self):
        """初始化知识库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 知识条目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,  -- JSON array
                source TEXT,
                confidence REAL DEFAULT 0.5,
                performance_score REAL DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT  -- JSON
            )
        ''')
        
        # 知识使用记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_id TEXT,
                usage_context TEXT,
                result_score REAL,
                used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (knowledge_id) REFERENCES knowledge_entries(id)
            )
        ''')
        
        # 策略库表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_library (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,  -- trend/mean_reversion/breakout/etc
                description TEXT,
                params TEXT,  -- JSON 默认参数
                rules TEXT,   -- JSON 交易规则
                performance TEXT,  -- JSON 历史表现
                suitable_markets TEXT,  -- JSON 适用市场
                risk_level INTEGER,  -- 1-5
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_builtin_knowledge(self):
        """加载内置知识库"""
        builtin_strategies = [
            {
                "id": "trend_following_ma",
                "name": "均线趋势跟踪",
                "type": "trend",
                "description": "基于移动平均线交叉的趋势跟踪策略",
                "params": json.dumps({
                    "fast_ma": 5,
                    "slow_ma": 20,
                    "position_size": 0.2,
                    "stop_loss": 0.05,
                    "take_profit": 0.10
                }),
                "rules": json.dumps({
                    "entry": "fast_ma > slow_ma 且 前一周期 fast_ma <= slow_ma",
                    "exit": "fast_ma < slow_ma 或 止损 或 止盈",
                    "filter": "成交量 > 20日均量"
                }),
                "performance": json.dumps({
                    "expected_return": 0.15,
                    "max_drawdown": 0.10,
                    "win_rate": 0.45,
                    "avg_trade": 0.02
                }),
                "suitable_markets": json.dumps(["crypto", "stock", "future"]),
                "risk_level": 3
            },
            {
                "id": "mean_reversion_rsi",
                "name": "RSI均值回归",
                "type": "mean_reversion",
                "description": "基于RSI超买超卖的均值回归策略",
                "params": json.dumps({
                    "rsi_period": 14,
                    "oversold": 30,
                    "overbought": 70,
                    "position_size": 0.15,
                    "stop_loss": 0.03,
                    "take_profit": 0.08
                }),
                "rules": json.dumps({
                    "entry": "RSI < 30 且 开始回升",
                    "exit": "RSI > 50 或 止损 或 止盈",
                    "filter": "趋势为震荡市（ADX < 25）"
                }),
                "performance": json.dumps({
                    "expected_return": 0.12,
                    "max_drawdown": 0.08,
                    "win_rate": 0.55,
                    "avg_trade": 0.015
                }),
                "suitable_markets": json.dumps(["crypto", "stock"]),
                "risk_level": 2
            },
            {
                "id": "breakout_volatility",
                "name": "波动率突破",
                "type": "breakout",
                "description": "基于波动率收缩后的突破策略",
                "params": json.dumps({
                    "lookback": 20,
                    "volatility_threshold": 0.5,
                    "position_size": 0.25,
                    "stop_loss": 0.04,
                    "take_profit": 0.12
                }),
                "rules": json.dumps({
                    "entry": "价格突破前20日高点 且 波动率压缩",
                    "exit": "价格跌破前10日低点 或 止损 或 止盈",
                    "filter": "成交量放大 (>2倍均量)"
                }),
                "performance": json.dumps({
                    "expected_return": 0.20,
                    "max_drawdown": 0.12,
                    "win_rate": 0.40,
                    "avg_trade": 0.03
                }),
                "suitable_markets": json.dumps(["crypto", "stock", "future"]),
                "risk_level": 4
            },
            {
                "id": "meme_coin_momentum",
                "name": "冲狗动量策略",
                "type": "momentum",
                "description": "针对Meme币的动量突破策略，结合聪明钱包信号",
                "params": json.dumps({
                    "volume_threshold": 3.0,
                    "momentum_period": 3,
                    "position_size": 0.10,
                    "stop_loss": 0.08,
                    "take_profit": 0.20,
                    "max_holding_hours": 72
                }),
                "rules": json.dumps({
                    "entry": "成交量 > 3倍均量 且 3小时涨幅 > 15% 且 聪明钱包买入",
                    "exit": "持仓 > 72小时 或 涨幅 > 50% 或 止损",
                    "filter": "市值 < 1亿 且 流动性 > 100k"
                }),
                "performance": json.dumps({
                    "expected_return": 0.50,
                    "max_drawdown": 0.25,
                    "win_rate": 0.35,
                    "avg_trade": 0.08
                }),
                "suitable_markets": json.dumps(["crypto_meme"]),
                "risk_level": 5
            },
            {
                "id": "event_driven_earnings",
                "name": "财报事件驱动",
                "type": "event_driven",
                "description": "基于财报发布前后的事件驱动策略",
                "params": json.dumps({
                    "entry_before_days": 1,
                    "exit_after_days": 3,
                    "position_size": 0.20,
                    "stop_loss": 0.05,
                    "take_profit": 0.15
                }),
                "rules": json.dumps({
                    "entry": "财报发布前1天 且 预期利好",
                    "exit": "财报发布后3天 或 止损 或 止盈",
                    "filter": "历史财报超预期率 > 70%"
                }),
                "performance": json.dumps({
                    "expected_return": 0.08,
                    "max_drawdown": 0.06,
                    "win_rate": 0.60,
                    "avg_trade": 0.025
                }),
                "suitable_markets": json.dumps(["stock_us"]),
                "risk_level": 3
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for strategy in builtin_strategies:
            cursor.execute('''
                INSERT OR IGNORE INTO strategy_library 
                (id, name, type, description, params, rules, performance, suitable_markets, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                strategy['id'], strategy['name'], strategy['type'], strategy['description'],
                strategy['params'], strategy['rules'], strategy['performance'],
                strategy['suitable_markets'], strategy['risk_level']
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 已加载 {len(builtin_strategies)} 个内置策略")
    
    def add_knowledge(self, entry: KnowledgeEntry) -> str:
        """添加知识条目"""
        entry.id = hashlib.md5(f"{entry.title}{entry.content}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO knowledge_entries 
            (id, type, title, content, tags, source, confidence, performance_score, usage_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.id, entry.type, entry.title, entry.content,
            json.dumps(entry.tags), entry.source, entry.confidence,
            entry.performance_score, entry.usage_count, json.dumps(entry.metadata)
        ))
        
        conn.commit()
        conn.close()
        
        return entry.id
    
    def query_knowledge(self, query_type: Optional[str] = None, 
                       tags: Optional[List[str]] = None,
                       min_confidence: float = 0.5,
                       limit: int = 10) -> List[KnowledgeEntry]:
        """查询知识库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = "SELECT * FROM knowledge_entries WHERE confidence >= ?"
        params = [min_confidence]
        
        if query_type:
            sql += " AND type = ?"
            params.append(query_type)
        
        if tags:
            # 简化处理：检查tags字段包含任一标签
            tag_conditions = " OR ".join(["tags LIKE ?" for _ in tags])
            sql += f" AND ({tag_conditions})"
            params.extend([f'%{tag}%' for tag in tags])
        
        sql += " ORDER BY performance_score DESC, usage_count DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        entries = []
        for row in rows:
            entries.append(KnowledgeEntry(
                id=row[0],
                type=row[1],
                title=row[2],
                content=row[3],
                tags=json.loads(row[4]) if row[4] else [],
                source=row[5],
                confidence=row[6],
                performance_score=row[7],
                usage_count=row[8],
                created_at=datetime.fromisoformat(row[9]),
                updated_at=datetime.fromisoformat(row[10]),
                metadata=json.loads(row[11]) if row[11] else {}
            ))
        
        return entries
    
    def get_strategy(self, strategy_id: str) -> Optional[Dict]:
        """获取策略详情"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM strategy_library WHERE id = ? AND is_active = 1
        ''', (strategy_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'description': row[3],
            'params': json.loads(row[4]) if row[4] else {},
            'rules': json.loads(row[5]) if row[5] else {},
            'performance': json.loads(row[6]) if row[6] else {},
            'suitable_markets': json.loads(row[7]) if row[7] else [],
            'risk_level': row[8],
            'is_active': row[9],
            'created_at': row[10],
            'updated_at': row[11]
        }
    
    def get_strategies(self, market_type: Optional[str] = None, 
                      max_risk: int = 5) -> List[Dict]:
        """获取策略列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = "SELECT * FROM strategy_library WHERE is_active = 1 AND risk_level <= ?"
        params = [max_risk]
        
        if market_type:
            sql += " AND suitable_markets LIKE ?"
            params.append(f'%{market_type}%')
        
        sql += " ORDER BY risk_level ASC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        strategies = []
        for row in rows:
            strategies.append({
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'description': row[3],
                'params': json.loads(row[4]) if row[4] else {},
                'risk_level': row[8]
            })
        
        return strategies
    
    def update_strategy_performance(self, strategy_id: str, 
                                   actual_return: float,
                                   win_rate: float,
                                   max_drawdown: float):
        """更新策略表现（从回测或实盘）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取当前表现数据
        cursor.execute('SELECT performance FROM strategy_library WHERE id = ?', (strategy_id,))
        row = cursor.fetchone()
        
        if row and row[0]:
            performance = json.loads(row[0])
            
            # 更新滚动平均值
            n = performance.get('update_count', 0) + 1
            performance['expected_return'] = (performance.get('expected_return', 0) * (n-1) + actual_return) / n
            performance['win_rate'] = (performance.get('win_rate', 0) * (n-1) + win_rate) / n
            performance['max_drawdown'] = max(performance.get('max_drawdown', 0), max_drawdown)
            performance['update_count'] = n
            performance['last_updated'] = datetime.now().isoformat()
            
            cursor.execute('''
                UPDATE strategy_library 
                SET performance = ?, updated_at = ?
                WHERE id = ?
            ''', (json.dumps(performance), datetime.now(), strategy_id))
            
            conn.commit()
        
        conn.close()
    
    def recommend_strategy(self, market_type: str, risk_tolerance: int = 3,
                          market_condition: str = 'neutral') -> List[Dict]:
        """
        根据市场条件推荐策略
        
        Args:
            market_type: 市场类型 (crypto/stock/future)
            risk_tolerance: 风险承受度 1-5
            market_condition: 市场状态 (bull/bear/neutral/volatile)
        """
        strategies = self.get_strategies(market_type, risk_tolerance)
        
        # 根据市场状态过滤
        condition_strategy_map = {
            'bull': ['trend', 'momentum', 'breakout'],
            'bear': ['mean_reversion', 'short', 'hedge'],
            'neutral': ['mean_reversion', 'range', 'arbitrage'],
            'volatile': ['breakout', 'momentum', 'short']
        }
        
        suitable_types = condition_strategy_map.get(market_condition, [])
        
        # 排序：匹配当前市场状态的优先
        def sort_key(s):
            type_match = 1 if s['type'] in suitable_types else 0
            return (type_match, s['risk_level'])
        
        strategies.sort(key=sort_key, reverse=True)
        
        return strategies[:5]  # 返回前5个推荐
    
    def learn_from_backtest(self, backtest_result: Dict):
        """从回测结果中学习"""
        # 生成知识条目
        strategy_name = backtest_result.get('strategy_name', 'Unknown')
        symbol = backtest_result.get('symbol', 'Unknown')
        
        # 如果策略表现好，记录经验
        if backtest_result.get('total_return', 0) > 10 and backtest_result.get('sharpe_ratio', 0) > 1:
            entry = KnowledgeEntry(
                id="",
                type=KnowledgeType.STRATEGY.value,
                title=f"{strategy_name} 在 {symbol} 上的成功经验",
                content=f"""
策略: {strategy_name}
标的: {symbol}
回测表现:
- 总收益率: {backtest_result.get('total_return', 0):.2f}%
- 夏普比率: {backtest_result.get('sharpe_ratio', 0):.2f}
- 胜率: {backtest_result.get('win_rate', 0):.1f}%
- 最大回撤: {backtest_result.get('max_drawdown_pct', 0):.2f}%

结论: 该策略在这个标的上表现优秀，建议实盘测试。
                """,
                tags=[strategy_name, symbol, 'backtest', 'success'],
                source='backtest',
                confidence=min(backtest_result.get('sharpe_ratio', 0) / 3, 1.0),
                performance_score=backtest_result.get('total_return', 0),
                usage_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={
                    'backtest_id': backtest_result.get('id'),
                    'symbol': symbol,
                    'strategy': strategy_name
                }
            )
            
            self.add_knowledge(entry)
            print(f"✅ 从回测中学习: {strategy_name} - {symbol}")
    
    def generate_trading_plan(self, symbol: str, market_type: str,
                             current_signals: Dict) -> Dict:
        """
        基于知识库生成交易计划
        
        Args:
            symbol: 交易标的
            market_type: 市场类型
            current_signals: 当前信号数据
        
        Returns:
            交易计划
        """
        # 获取推荐策略
        market_condition = current_signals.get('market_condition', 'neutral')
        recommended = self.recommend_strategy(market_type, risk_tolerance=3, 
                                            market_condition=market_condition)
        
        if not recommended:
            return {"error": "无可用策略"}
        
        # 选择最佳策略
        best_strategy = recommended[0]
        strategy_detail = self.get_strategy(best_strategy['id'])
        
        # 生成交易计划
        plan = {
            'symbol': symbol,
            'strategy_id': best_strategy['id'],
            'strategy_name': best_strategy['name'],
            'confidence': self._calculate_plan_confidence(best_strategy, current_signals),
            'entry_conditions': strategy_detail['rules'].get('entry', ''),
            'exit_conditions': strategy_detail['rules'].get('exit', ''),
            'position_size': strategy_detail['params'].get('position_size', 0.2),
            'stop_loss': strategy_detail['params'].get('stop_loss', 0.05),
            'take_profit': strategy_detail['params'].get('take_profit', 0.10),
            'risk_level': best_strategy['risk_level'],
            'expected_performance': strategy_detail['performance'],
            'reasoning': f"基于当前{market_condition}市场环境，选择{best_strategy['name']}策略"
        }
        
        return plan
    
    def _calculate_plan_confidence(self, strategy: Dict, signals: Dict) -> float:
        """计算交易计划的置信度"""
        confidence = 0.5
        
        # 策略历史表现
        confidence += min(strategy.get('performance_score', 0) / 100, 0.2)
        
        # 信号强度
        if 'signal_strength' in signals:
            confidence += signals['signal_strength'] * 0.2
        
        # 因子评分
        if 'factor_score' in signals:
            confidence += (signals['factor_score'] / 100) * 0.1
        
        return min(confidence, 1.0)


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI 知识库管理')
    parser.add_argument('--init', action='store_true', help='初始化知识库')
    parser.add_argument('--list-strategies', action='store_true', help='列出所有策略')
    parser.add_argument('--strategy-id', help='查看策略详情')
    parser.add_argument('--recommend', action='store_true', help='推荐策略')
    parser.add_argument('--market', default='crypto', help='市场类型')
    parser.add_argument('--condition', default='neutral', 
                       choices=['bull', 'bear', 'neutral', 'volatile'],
                       help='市场状态')
    parser.add_argument('--risk', type=int, default=3, help='风险承受度 1-5')
    
    args = parser.parse_args()
    
    kb = KnowledgeBaseManager()
    
    if args.init:
        print("✅ 知识库已初始化")
        return
    
    if args.list_strategies:
        strategies = kb.get_strategies(args.market, args.risk)
        print(f"\n📚 可用策略列表 ({len(strategies)} 个):")
        print(f"{'ID':<25} {'名称':<20} {'类型':<15} {'风险':<6}")
        print("-" * 70)
        for s in strategies:
            print(f"{s['id']:<25} {s['name']:<20} {s['type']:<15} {s['risk_level']:<6}")
    
    elif args.strategy_id:
        strategy = kb.get_strategy(args.strategy_id)
        if strategy:
            print(f"\n📖 策略详情: {strategy['name']}")
            print(f"{'='*60}")
            print(f"ID: {strategy['id']}")
            print(f"类型: {strategy['type']}")
            print(f"描述: {strategy['description']}")
            print(f"风险等级: {strategy['risk_level']}/5")
            print(f"\n参数:")
            for k, v in strategy['params'].items():
                print(f"  {k}: {v}")
            print(f"\n规则:")
            for k, v in strategy['rules'].items():
                print(f"  {k}: {v}")
            print(f"\n历史表现:")
            for k, v in strategy['performance'].items():
                print(f"  {k}: {v}")
        else:
            print(f"❌ 策略不存在: {args.strategy_id}")
    
    elif args.recommend:
        recommendations = kb.recommend_strategy(args.market, args.risk, args.condition)
        print(f"\n🎯 针对 {args.market} 市场 ({args.condition} 状态) 的策略推荐:")
        print(f"{'='*70}")
        for i, s in enumerate(recommendations, 1):
            print(f"\n{i}. {s['name']} (ID: {s['id']})")
            print(f"   类型: {s['type']} | 风险: {s['risk_level']}/5")
            print(f"   {s['description']}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
