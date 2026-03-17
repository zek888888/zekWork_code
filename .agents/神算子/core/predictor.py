#!/usr/bin/env python3
"""
AI预测引擎
负责调用多个AI进行并行预测
"""

import os
import sys
import json
import re
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "config-layer"))

from ai_config_manager import AIConfigManager

logger = logging.getLogger('AIPredictor')


class AIPredictor:
    """
    AI预测引擎
    管理多个AI模型的预测调用和结果处理
    """
    
    # 默认的预测Prompt模板
    DEFAULT_PROMPT_TEMPLATE = """你是专业量化分析师。请基于以下{symbol}的{interval}数据，预测下一个{interval}的走势。

【当前市场状态】
- 最新价格: ${close:,.2f}
- MACD柱状图: {macd_hist:.2f}
- KDJ J值: {kdj_j:.2f}
- 24h涨跌: {price_change_24h:+.2f}%
- 平均成交量: {volume_avg:,.0f}

【最近10根K线数据】
{klines_summary}

【分析要求】
1. 综合分析MACD趋势、KDJ位置和价格动能
2. 判断下一根{interval}K线涨(>0.1%)还是跌(<-0.1%)
3. 给出涨的概率(0-100)和跌的概率
4. 给出置信度(0.0-1.0)
5. 简要说明理由(30字内，关键指标分析)

【返回格式】
严格按以下JSON格式返回，不要其他文字:
{{"prediction": "up" 或 "down", "up_probability": 65, "down_probability": 35, "confidence": 0.75, "reason": "理由说明"}}"""

    def __init__(
        self,
        db_path: str = None,
        timeout: int = 30,
        max_retries: int = 2
    ):
        """
        初始化预测引擎
        
        Args:
            db_path: 数据库路径
            timeout: AI调用超时时间（秒）
            max_retries: 最大重试次数
        """
        self.db_path = db_path or str(PROJECT_ROOT / "data" / "market_data.db")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 初始化AI配置管理器
        self.config_manager = AIConfigManager(self.db_path)
        
        logger.info(f"[预测引擎初始化] 超时={timeout}s, 重试={max_retries}")
    
    def get_default_prompt(self) -> str:
        """获取默认Prompt模板"""
        return self.DEFAULT_PROMPT_TEMPLATE
    
    def predict(
        self,
        symbol: str,
        interval: str,
        market_data: Dict,
        custom_prompt: Optional[str] = None,
        parallel: bool = True
    ) -> List[Dict]:
        """
        执行AI预测
        
        Args:
            symbol: 交易对
            interval: 时间维度
            market_data: 市场数据
            custom_prompt: 自定义Prompt（可选）
            parallel: 是否并行调用
            
        Returns:
            List[Dict]: 各AI的预测结果
        """
        # 获取所有活跃的AI配置
        active_configs = self.config_manager.get_active_configs()
        
        if not active_configs:
            logger.error("[预测失败] 没有活跃的AI配置")
            return []
        
        logger.info(f"[预测开始] 使用 {len(active_configs)} 个AI: {[c.name for c in active_configs]}")
        
        # 构建Prompt
        prompt = custom_prompt or self._build_prompt(symbol, interval, market_data)
        
        # 执行预测
        if parallel and len(active_configs) > 1:
            results = self._predict_parallel(active_configs, prompt)
        else:
            results = self._predict_sequential(active_configs, prompt)
        
        # 过滤失败结果
        successful = [r for r in results if r.get('success')]
        
        logger.info(f"[预测完成] 成功 {len(successful)}/{len(active_configs)}")
        
        return successful
    
    def _build_prompt(
        self,
        symbol: str,
        interval: str,
        market_data: Dict
    ) -> str:
        """构建预测Prompt"""
        klines = market_data.get('klines', [])
        
        # 格式化K线概要
        klines_summary = []
        for i, k in enumerate(klines[-10:]):
            klines_summary.append(
                f"{i+1:2d}. {k['timestamp']} | C:{k['close']:>10.2f} | "
                f"MACD:{k['macd_hist']:>8.2f} | KDJ_J:{k['kdj_j']:>6.2f}"
            )
        
        return self.DEFAULT_PROMPT_TEMPLATE.format(
            symbol=symbol,
            interval=interval,
            close=market_data['close'],
            macd_hist=market_data['macd_hist'],
            kdj_j=market_data['kdj_j'],
            price_change_24h=market_data.get('price_change_24h', 0),
            volume_avg=market_data.get('volume_avg', 0),
            klines_summary="\n".join(klines_summary)
        )
    
    def _predict_parallel(
        self,
        configs: List[Any],
        prompt: str
    ) -> List[Dict]:
        """并行预测"""
        results = []
        
        with ThreadPoolExecutor(max_workers=len(configs)) as executor:
            future_to_config = {
                executor.submit(self._call_single_ai, config, prompt): config
                for config in configs
            }
            
            for future in as_completed(future_to_config):
                config = future_to_config[future]
                try:
                    result = future.result(timeout=self.timeout + 5)
                    results.append(result)
                    
                    if result.get('success'):
                        logger.debug(f"  ✅ {config.name}: {result['prediction'].upper()}")
                    else:
                        logger.warning(f"  ❌ {config.name}: {result.get('error', '未知错误')}")
                        
                except Exception as e:
                    logger.error(f"  ❌ {config.name}: 异常 - {e}")
                    results.append({
                        'success': False,
                        'ai_name': config.name,
                        'ai_provider': config.provider,
                        'ai_model': config.model,
                        'error': str(e),
                        'source': 'error'
                    })
        
        return results
    
    def _predict_sequential(
        self,
        configs: List[Any],
        prompt: str
    ) -> List[Dict]:
        """串行预测"""
        results = []
        
        for config in configs:
            result = self._call_single_ai(config, prompt)
            results.append(result)
            
            if result.get('success'):
                logger.debug(f"  ✅ {config.name}: {result['prediction'].upper()}")
            else:
                logger.warning(f"  ❌ {config.name}: {result.get('error', '未知错误')}")
        
        return results
    
    def _call_single_ai(self, config, prompt: str) -> Dict:
        """调用单个AI
        
        Args:
            config: AI配置
            prompt: 预测Prompt
            
        Returns:
            Dict: 预测结果
        """
        start_time = time.time()
        
        headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': config.model,
            'messages': [
                {
                    'role': 'system',
                    'content': '你是专业量化分析师，严格按JSON格式返回结果，不要包含任何其他文字。'
                },
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 400
        }
        
        last_error = None
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f'{config.base_url}/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # 解析响应
                parsed = self._parse_response(content)
                
                if parsed:
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    return {
                        'success': True,
                        'ai_name': config.name,
                        'ai_provider': config.provider,
                        'ai_model': config.model,
                        'prediction': parsed['prediction'],
                        'up_probability': parsed['up_probability'],
                        'down_probability': parsed['down_probability'],
                        'confidence': parsed['confidence'],
                        'reason': parsed['reason'],
                        'raw_response': content,
                        'response_time_ms': elapsed_ms,
                        'source': 'ai'
                    }
                else:
                    last_error = '响应解析失败'
                    logger.warning(f"  [解析失败] {config.name}: {content[:100]}...")
                    
            except requests.exceptions.Timeout:
                last_error = '请求超时'
                logger.warning(f"  [超时] {config.name} 第{attempt+1}次尝试")
                
            except requests.exceptions.RequestException as e:
                last_error = f'请求异常: {str(e)}'
                logger.warning(f"  [请求异常] {config.name}: {e}")
                
            except Exception as e:
                last_error = f'未知异常: {str(e)}'
                logger.error(f"  [未知异常] {config.name}: {e}")
        
        # 所有重试失败
        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            'success': False,
            'ai_name': config.name,
            'ai_provider': config.provider,
            'ai_model': config.model,
            'error': last_error,
            'response_time_ms': elapsed_ms,
            'source': 'error'
        }
    
    def _parse_response(self, content: str) -> Optional[Dict]:
        """
        解析AI响应
        
        Args:
            content: AI返回的原始内容
            
        Returns:
            Dict: 解析后的预测结果，失败返回None
        """
        try:
            content = content.strip()
            
            # 尝试直接解析整个内容
            try:
                data = json.loads(content)
                return self._extract_prediction(data)
            except json.JSONDecodeError:
                pass
            
            # 处理Markdown代码块 ```json ... ```
            code_block_match = re.search(
                r'```(?:json)?\s*\n?([\s\S]*?)\n?```',
                content
            )
            if code_block_match:
                json_content = code_block_match.group(1).strip()
                data = json.loads(json_content)
                return self._extract_prediction(data)
            
            # 尝试提取JSON块
            json_match = re.search(r'\{[\s\S]*?"prediction"[\s\S]*?\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return self._extract_prediction(data)
            
            return None
            
        except Exception as e:
            logger.debug(f"[解析失败] {e}: {content[:100]}...")
            return None
    
    def _extract_prediction(self, data: Dict) -> Optional[Dict]:
        """从解析的数据中提取预测结果"""
        prediction = data.get('prediction', '').lower()
        
        # 验证prediction值
        if prediction not in ['up', 'down']:
            return None
        
        # 提取并验证其他字段
        up_prob = data.get('up_probability')
        down_prob = data.get('down_probability')
        confidence = data.get('confidence')
        reason = data.get('reason', '')
        
        # 如果缺少概率字段，使用默认值
        if up_prob is None and down_prob is not None:
            up_prob = 100 - down_prob
        elif down_prob is None and up_prob is not None:
            down_prob = 100 - up_prob
        elif up_prob is None and down_prob is None:
            up_prob = 70 if prediction == 'up' else 30
            down_prob = 100 - up_prob
        
        # 限制范围
        up_prob = max(0, min(100, int(up_prob)))
        down_prob = max(0, min(100, int(down_prob)))
        confidence = max(0.0, min(1.0, float(confidence or 0.5)))
        
        return {
            'prediction': prediction,
            'up_probability': up_prob,
            'down_probability': down_prob,
            'confidence': round(confidence, 2),
            'reason': str(reason)[:200]  # 限制长度
        }


if __name__ == '__main__':
    # 测试
    predictor = AIPredictor()
    
    # 模拟市场数据
    market_data = {
        'close': 73815.48,
        'macd_hist': -36.42,
        'kdj_j': 12.18,
        'price_change_24h': 2.5,
        'volume_avg': 150000000,
        'klines': [
            {'timestamp': '2026-03-16 14:45:00', 'close': 74000, 'macd_hist': -30, 'kdj_j': 15},
            {'timestamp': '2026-03-16 15:00:00', 'close': 73815, 'macd_hist': -36, 'kdj_j': 12},
        ]
    }
    
    results = predictor.predict('BTCUSDT', '15m', market_data)
    
    print(f"\u9884测结果: {len(results)} 个AI成功")
    for r in results:
        if r.get('success'):
            print(f"  {r['ai_name']}: {r['prediction'].upper()} {r['up_probability']}%/{r['down_probability']}%")
