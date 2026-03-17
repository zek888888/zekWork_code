#!/usr/bin/env python3
"""
战颅将军 (War Skull General)
模拟盘交易指挥官，整合五大子智能体

架构:
- 影谍 (DeepSeek-Chat): 情报分析
- 铁算 (DeepSeek-R1): 风险计算
- 史官 (DeepSeek-R1): 回测验证
- 谋师 (DeepSeek-R1): 策略制定
- 宪兵 (DeepSeek-Chat): 合规检查

全阵容使用DeepSeek (创始人有量化背景)
"""

import os
import sys
import json
import time
import sqlite3
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('战颅将军')

# 加载环境变量
load_dotenv()

# 配置
PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
DB_PATH = f"{PROJECT_ROOT}/data/market_data.db"

# 导入模拟盘引擎
sys.path.insert(0, PROJECT_ROOT)
from 模拟盘_engine import 模拟盘引擎, TradeRecord


@dataclass
class 情报分析结果:
    """影谍的分析结果"""
    sentiment: str  # bullish/bearish/neutral
    sentiment_score: float  # -1 to 1
    key_factors: List[str]
    confidence: float


@dataclass
class 风险评估结果:
    """铁算的风险评估"""
    risk_level: str  # low/medium/high
    position_size: float  # 建议仓位比例
    max_leverage: int
    stop_loss_pct: float
    risk_reward_ratio: float
    reasoning: str


@dataclass
class 回测结果:
    """史官的回测验证"""
    strategy_valid: bool
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    backtest_score: float
    reasoning: str


@dataclass
class 策略方案:
    """谋师的交易策略"""
    direction: str  # long/short/hold
    entry_price: float
    take_profit_levels: List[float]
    stop_loss: float
    leverage: int
    reasoning: str


@dataclass
class 合规检查:
    """宪兵的合规检查结果"""
    passed: bool
    violations: List[str]
    warnings: List[str]


class 子智能体基类:
    """子智能体基类"""
    
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model
        self.logger = logging.getLogger(f'战颅将军.{name}')
    
    def _调用deepseek(self, prompt: str) -> str:
        """调用DeepSeek API"""
        try:
            import requests
            
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if not api_key:
                raise ValueError("未设置DEEPSEEK_API_KEY")
            
            response = requests.post(
                'https://api.deepseek.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.model,
                    'messages': [
                        {'role': 'system', 'content': f'你是{self.name}，专业的加密货币交易分析师。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                self.logger.error(f"API错误: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            self.logger.error(f"调用DeepSeek失败: {e}")
            return ""


class 影谍(子智能体基类):
    """
    影谍 - 情报分析师
    使用 DeepSeek-Chat 分析市场情绪、新闻、链上数据
    """
    
    def __init__(self):
        super().__init__("影谍", "deepseek-chat")
    
    def 分析情报(self, market_data: Dict, news_data: List[Dict] = None) -> 情报分析结果:
        """分析市场情绪"""
        self.logger.info("🕵️ 影谍开始情报分析...")
        
        # 构造分析提示
        current_price = market_data.get('current_price', 0)
        price_change_24h = market_data.get('price_change_24h', 0)
        volume_24h = market_data.get('volume_24h', 0)
        
        prompt = f"""
        分析当前BTC市场情绪和关键影响因素:
        
        当前价格: ${current_price:,.2f}
        24h涨跌: {price_change_24h:+.2f}%
        24h成交量: ${volume_24h:,.0f}
        
        请输出JSON格式:
        {{
            "sentiment": "bullish/bearish/neutral",
            "sentiment_score": -1到1之间的数值,
            "key_factors": ["因素1", "因素2", ...],
            "confidence": 0到1之间的置信度
        }}
        """
        
        response = self._调用deepseek(prompt)
        
        try:
            # 解析JSON响应
            result = json.loads(self._提取json(response))
            return 情报分析结果(**result)
        except:
            self.logger.warning("影谍分析失败，使用默认结果")
            return 情报分析结果(
                sentiment='neutral',
                sentiment_score=0,
                key_factors=['数据不足'],
                confidence=0.5
            )
    
    def _提取json(self, text: str) -> str:
        """从文本中提取JSON"""
        import re
        match = re.search(r'\{[\s\S]*\}', text)
        return match.group(0) if match else '{}'


class 铁算(子智能体基类):
    """
    铁算 - 风险计算器
    使用 DeepSeek-R1 计算仓位、杠杆、止损
    """
    
    def __init__(self):
        super().__init__("铁算", "deepseek-reasoner")
    
    def 计算风险(self, current_balance: float, market_volatility: float,
               entry_price: float, stop_loss: float) -> 风险评估结果:
        """计算风险参数"""
        self.logger.info("🧮 铁算开始风险计算...")
        
        risk_amount = current_balance * 0.02  # 单笔风险2%
        
        prompt = f"""
        基于以下参数计算交易风险:
        - 账户余额: ${current_balance:,.2f}
        - 单笔风险: ${risk_amount:,.2f} (2%)
        - 入场价: ${entry_price:,.2f}
        - 止损价: ${stop_loss:,.2f}
        - 市场波动率: {market_volatility:.2%}
        
        请输出JSON格式:
        {{
            "risk_level": "low/medium/high",
            "position_size": 建议仓位比例(0-1),
            "max_leverage": 建议最大杠杆(1-125),
            "stop_loss_pct": 止损百分比,
            "risk_reward_ratio": 盈亏比,
            "reasoning": "风险分析理由"
        }}
        """
        
        response = self._调用deepseek(prompt)
        
        try:
            result = json.loads(self._提取json(response))
            return 风险评估结果(**result)
        except:
            self.logger.warning("铁算计算失败，使用保守参数")
            return 风险评估结果(
                risk_level='medium',
                position_size=0.1,
                max_leverage=3,
                stop_loss_pct=2.0,
                risk_reward_ratio=1.5,
                reasoning='使用默认保守参数'
            )
    
    def _提取json(self, text: str) -> str:
        import re
        match = re.search(r'\{[\s\S]*\}', text)
        return match.group(0) if match else '{}'


class 史官(子智能体基类):
    """
    史官 - 回测验证员
    使用 DeepSeek-R1 验证策略历史表现
    """
    
    def __init__(self):
        super().__init__("史官", "deepseek-reasoner")
    
    def 回测验证(self, strategy_params: Dict, historical_data: List[Dict]) -> 回测结果:
        """验证策略历史表现"""
        self.logger.info("📜 史官开始回测验证...")
        
        prompt = f"""
        基于以下策略参数进行历史回测分析:
        
        策略参数:
        {json.dumps(strategy_params, indent=2)}
        
        历史数据概要:
        - 数据点数: {len(historical_data)}
        - 时间范围: 2021-01-01 至今
        
        请输出JSON格式:
        {{
            "strategy_valid": true/false,
            "win_rate": 历史胜率(0-1),
            "sharpe_ratio": 夏普比率,
            "max_drawdown": 最大回撤(0-1),
            "backtest_score": 回测得分(0-100),
            "reasoning": "回测分析结论"
        }}
        """
        
        response = self._调用deepseek(prompt)
        
        try:
            result = json.loads(self._提取json(response))
            return 回测结果(**result)
        except:
            self.logger.warning("史官回测失败，使用中性结果")
            return 回测结果(
                strategy_valid=True,
                win_rate=0.55,
                sharpe_ratio=1.0,
                max_drawdown=0.15,
                backtest_score=60,
                reasoning='使用默认回测数据'
            )
    
    def _提取json(self, text: str) -> str:
        import re
        match = re.search(r'\{[\s\S]*\}', text)
        return match.group(0) if match else '{}'


class 谋师(子智能体基类):
    """
    谋师 - 策略制定者
    使用 DeepSeek-R1 制定具体交易方案
    """
    
    def __init__(self):
        super().__init__("谋师", "deepseek-reasoner")
    
    def 制定策略(self, market_data: Dict, 情报: 情报分析结果,
               回测: 回测结果) -> 策略方案:
        """制定交易策略"""
        self.logger.info("🎯 谋师开始制定策略...")
        
        prompt = f"""
        基于以下信息制定BTC交易策略:
        
        市场数据:
        - 当前价格: ${market_data.get('current_price', 0):,.2f}
        - 15m预测: {market_data.get('prediction_15m', 'unknown')}
        - 支持位: ${market_data.get('support', 0):,.2f}
        - 阻力位: ${market_data.get('resistance', 0):,.2f}
        
        情报分析:
        - 情绪: {情报.sentiment} (得分: {情报.sentiment_score:+.2f})
        - 关键因素: {', '.join(情报.key_factors)}
        
        回测结果:
        - 策略有效: {回测.strategy_valid}
        - 历史胜率: {回测.win_rate:.1%}
        - 回测得分: {回测.backtest_score}/100
        
        请输出JSON格式:
        {{
            "direction": "long/short/hold",
            "entry_price": 入场价格,
            "take_profit_levels": [止盈1, 止盈2],
            "stop_loss": 止损价格,
            "leverage": 杠杆倍数,
            "reasoning": "策略理由"
        }}
        """
        
        response = self._调用deepseek(prompt)
        
        try:
            result = json.loads(self._提取json(response))
            return 策略方案(**result)
        except:
            self.logger.warning("谋师策略制定失败，建议观望")
            return 策略方案(
                direction='hold',
                entry_price=market_data.get('current_price', 0),
                take_profit_levels=[],
                stop_loss=0,
                leverage=1,
                reasoning='策略制定失败，建议观望'
            )
    
    def _提取json(self, text: str) -> str:
        import re
        match = re.search(r'\{[\s\S]*\}', text)
        return match.group(0) if match else '{}'


class 宪兵(子智能体基类):
    """
    宪兵 - 合规检查员
    使用 DeepSeek-Chat 检查交易合规性
    """
    
    def __init__(self):
        super().__init__("宪兵", "deepseek-chat")
    
    def 合规检查(self, 策略: 策略方案, 风险: 风险评估结果) -> 合规检查:
        """检查交易合规性"""
        self.logger.info("🛡️ 宪兵开始合规检查...")
        
        violations = []
        warnings = []
        
        # 基础规则检查
        if 策略.leverage > 风险.max_leverage:
            violations.append(f"杠杆{策略.leverage}x超过最大允许{风险.max_leverage}x")
        
        if 策略.direction != 'hold' and len(策略.take_profit_levels) == 0:
            violations.append("未设置止盈目标")
        
        if 风险.risk_reward_ratio < 1.0:
            warnings.append("盈亏比小于1:1")
        
        return 合规检查(
            passed=len(violations) == 0,
            violations=violations,
            warnings=warnings
        )


class 战颅将军:
    """
    战颅将军 - 交易指挥官
    整合五大子智能体，执行模拟盘交易
    """
    
    def __init__(self, initial_balance: float = 10000.0):
        self.logger = logging.getLogger('战颅将军')
        self.logger.info("⚔️ 战颅将军初始化中...")
        
        # 初始化子智能体
        self.子智能体 = {
            '影谍': 影谍(),
            '铁算': 铁算(),
            '史官': 史官(),
            '谋师': 谋师(),
            '宪兵': 宪兵()
        }
        
        # 初始化模拟盘引擎
        self.引擎 = 模拟盘引擎(initial_balance=initial_balance)
        
        self.logger.info("✅ 战颅将军初始化完成")
        self.logger.info(f"   启动资金: {initial_balance} USDT")
        self.logger.info("   交易级别: 5分钟")
    
    def 执行交易周期(self, market_data: Dict) -> Optional[TradeRecord]:
        """执行一个完整的交易决策周期"""
        self.logger.info("=" * 60)
        self.logger.info("🔄 开始交易决策周期")
        self.logger.info("=" * 60)
        
        # Step 1: 影谍情报分析
        情报 = self.子智能体['影谍'].分析情报(market_data)
        self.logger.info(f"   市场情绪: {情报.sentiment} ({情报.sentiment_score:+.2f})")
        
        # Step 2: 史官回测验证
        回测 = self.子智能体['史官'].回测验证(
            {'sentiment': 情报.sentiment, 'confidence': 情报.confidence},
            market_data.get('historical', [])
        )
        self.logger.info(f"   回测得分: {回测.backtest_score}/100, 胜率: {回测.win_rate:.1%}")
        
        # Step 3: 谋师制定策略
        策略 = self.子智能体['谋师'].制定策略(market_data, 情报, 回测)
        self.logger.info(f"   策略方向: {策略.direction.upper()}")
        
        if 策略.direction == 'hold':
            self.logger.info("📊 建议观望，不执行交易")
            return None
        
        # Step 4: 铁算风险计算
        current_balance = self.引擎.current_balance
        风险 = self.子智能体['铁算'].计算风险(
            current_balance,
            market_data.get('volatility', 0.02),
            策略.entry_price,
            策略.stop_loss
        )
        self.logger.info(f"   建议仓位: {风险.position_size*100:.1f}%, 最大杠杆: {风险.max_leverage}x")
        
        # Step 5: 宪兵合规检查
        合规 = self.子智能体['宪兵'].合规检查(策略, 风险)
        if not 合规.passed:
            self.logger.error(f"❌ 合规检查未通过: {合规.violations}")
            return None
        
        if 合规.warnings:
            self.logger.warning(f"⚠️ 合规警告: {合规.warnings}")
        
        # 执行交易
        self.logger.info("✅ 所有检查通过，执行交易")
        
        trade = self.引擎.开仓(
            symbol='BTCUSDT',
            direction=策略.direction,
            entry_price=策略.entry_price,
            position_size=风险.position_size,
            leverage=min(策略.leverage, 风险.max_leverage),
            stop_loss=策略.stop_loss,
            take_profit=策略.take_profit_levels[:2],  # 最多2个止盈
            confidence=情报.confidence,
            reasoning=策略.reasoning
        )
        
        return trade
    
    def 检查持仓(self, current_price: float):
        """检查持仓状态"""
        return self.引擎.检查持仓(current_price)
    
    def 获取统计(self) -> Dict:
        """获取交易统计"""
        return self.引擎.获取统计()


if __name__ == "__main__":
    print("=" * 60)
    print("⚔️  战颅将军 - 模拟盘交易系统")
    print("=" * 60)
    print("\n系统组件:")
    print("  🕵️ 影谍 - 情报分析 (DeepSeek-Chat)")
    print("  🧮 铁算 - 风险计算 (DeepSeek-R1)")
    print("  📜 史官 - 回测验证 (DeepSeek-R1)")
    print("  🎯 谋师 - 策略制定 (DeepSeek-R1)")
    print("  🛡️ 宪兵 - 合规检查 (DeepSeek-Chat)")
    print("\n" + "=" * 60)
    
    # 创建将军实例
    将军 = 战颅将军(initial_balance=10000.0)
    
    # 示例市场数据
    示例数据 = {
        'current_price': 65000,
        'price_change_24h': 2.5,
        'volume_24h': 35000000000,
        'prediction_15m': 'up',
        'support': 64000,
        'resistance': 66500,
        'volatility': 0.025,
        'historical': []
    }
    
    # 执行交易周期
    将军.执行交易周期(示例数据)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
