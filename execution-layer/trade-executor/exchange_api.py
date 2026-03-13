#!/usr/bin/env python3
"""
交易所API接口
支持币安(Binance)真实交易和模拟交易
"""

import os
import hmac
import hashlib
import time
import json
import urllib.request
import urllib.parse
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class OrderResult:
    """订单结果"""
    order_id: str
    symbol: str
    side: str
    order_type: str
    status: str
    price: float
    quantity: float
    executed_qty: float
    created_time: int
    is_test: bool = False


class BinanceAPI:
    """币安API封装"""
    
    def __init__(self, api_key: Optional[str] = None, 
                 secret_key: Optional[str] = None,
                 testnet: bool = True):
        """
        初始化币安API
        
        Args:
            api_key: API Key
            secret_key: API Secret
            testnet: 是否使用测试网
        """
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.secret_key = secret_key or os.getenv('BINANCE_SECRET_KEY')
        self.testnet = testnet
        
        # API端点
        if testnet:
            self.base_url = "https://testnet.binance.vision"
        else:
            self.base_url = "https://api.binance.com"
        
        self.recv_window = 5000  # 接收窗口
        
    def _generate_signature(self, query_string: str) -> str:
        """生成签名"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_timestamp(self) -> int:
        """获取时间戳"""
        return int(time.time() * 1000)
    
    def _request(self, method: str, endpoint: str, 
                params: Optional[Dict] = None,
                signed: bool = False) -> Dict:
        """
        发送HTTP请求
        
        Args:
            method: GET/POST/DELETE
            endpoint: API端点
            params: 请求参数
            signed: 是否需要签名
        
        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = self._get_timestamp()
            params['recvWindow'] = self.recv_window
            
            query_string = urllib.parse.urlencode(params)
            params['signature'] = self._generate_signature(query_string)
        
        query_string = urllib.parse.urlencode(params)
        
        if method == 'GET':
            url = f"{url}?{query_string}"
            data = None
        else:
            data = query_string.encode('utf-8')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            try:
                error_json = json.loads(error_body)
                raise Exception(f"API错误: {error_json.get('msg', error_body)}")
            except json.JSONDecodeError:
                raise Exception(f"HTTP错误 {e.code}: {error_body}")
        except Exception as e:
            raise Exception(f"请求失败: {e}")
    
    def test_connectivity(self) -> bool:
        """测试连接"""
        try:
            result = self._request('GET', '/api/v3/ping')
            return result == {}
        except:
            return False
    
    def get_server_time(self) -> int:
        """获取服务器时间"""
        result = self._request('GET', '/api/v3/time')
        return result.get('serverTime', 0)
    
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        return self._request('GET', '/api/v3/account', signed=True)
    
    def get_balance(self, asset: str) -> float:
        """获取指定资产余额"""
        account = self.get_account_info()
        for balance in account.get('balances', []):
            if balance['asset'] == asset:
                return float(balance['free']) + float(balance['locked'])
        return 0.0
    
    def get_symbol_price(self, symbol: str) -> float:
        """获取币种价格"""
        result = self._request('GET', '/api/v3/ticker/price', {'symbol': symbol})
        return float(result.get('price', 0))
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """获取交易对信息"""
        exchange_info = self._request('GET', '/api/v3/exchangeInfo')
        for s in exchange_info.get('symbols', []):
            if s['symbol'] == symbol:
                return s
        return None
    
    def place_order(self, symbol: str, side: OrderSide, order_type: OrderType,
                   quantity: float, price: Optional[float] = None,
                   stop_price: Optional[float] = None,
                   test: bool = False) -> OrderResult:
        """
        下单
        
        Args:
            symbol: 交易对
            side: BUY/SELL
            order_type: 订单类型
            quantity: 数量
            price: 价格(限价单需要)
            stop_price: 触发价(止损单需要)
            test: 是否测试订单
        
        Returns:
            订单结果
        """
        endpoint = '/api/v3/order/test' if test else '/api/v3/order'
        
        params = {
            'symbol': symbol,
            'side': side.value,
            'type': order_type.value,
            'quantity': quantity
        }
        
        if order_type in [OrderType.LIMIT, OrderType.STOP_LOSS_LIMIT, OrderType.TAKE_PROFIT_LIMIT]:
            if price is None:
                raise ValueError("限价单需要提供价格")
            params['price'] = price
            params['timeInForce'] = 'GTC'  # Good Till Cancel
        
        if order_type in [OrderType.STOP_LOSS, OrderType.STOP_LOSS_LIMIT, 
                         OrderType.TAKE_PROFIT, OrderType.TAKE_PROFIT_LIMIT]:
            if stop_price is None:
                raise ValueError("止损/止盈单需要提供触发价")
            params['stopPrice'] = stop_price
        
        result = self._request('POST', endpoint, params, signed=True)
        
        return OrderResult(
            order_id=str(result.get('orderId', '')),
            symbol=result.get('symbol', symbol),
            side=side.value,
            order_type=order_type.value,
            status=result.get('status', 'UNKNOWN'),
            price=float(result.get('price', price or 0)),
            quantity=float(result.get('origQty', quantity)),
            executed_qty=float(result.get('executedQty', 0)),
            created_time=result.get('transactTime', int(time.time() * 1000)),
            is_test=test
        )
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """撤销订单"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._request('DELETE', '/api/v3/order', params, signed=True)
    
    def get_order_status(self, symbol: str, order_id: str) -> Dict:
        """查询订单状态"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._request('GET', '/api/v3/order', params, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """获取未成交订单"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/api/v3/openOrders', params, signed=True)
    
    def get_order_history(self, symbol: str, limit: int = 50) -> List[Dict]:
        """获取历史订单"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._request('GET', '/api/v3/allOrders', params, signed=True)
    
    def get_my_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """获取成交记录"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._request('GET', '/api/v3/myTrades', params, signed=True)


class RiskManager:
    """风险管理系统"""
    
    def __init__(self, max_position_pct: float = 0.2,
                 max_daily_loss_pct: float = 0.05,
                 max_total_loss_pct: float = 0.15,
                 max_positions: int = 10,
                 stop_loss_pct: float = 0.05,
                 take_profit_pct: float = 0.10):
        """
        初始化风险管理器
        
        Args:
            max_position_pct: 单标的最大仓位比例
            max_daily_loss_pct: 单日最大亏损比例
            max_total_loss_pct: 总最大亏损比例
            max_positions: 最大持仓数量
            stop_loss_pct: 默认止损比例
            take_profit_pct: 默认止盈比例
        """
        self.max_position_pct = max_position_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_total_loss_pct = max_total_loss_pct
        self.max_positions = max_positions
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        self.daily_pnl = 0
        self.total_pnl = 0
        self.last_reset_date = datetime.now().date()
        
    def reset_daily_limits(self):
        """重置每日限制"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0
            self.last_reset_date = today
    
    def check_order_risk(self, symbol: str, side: str, quantity: float,
                        price: float, available_balance: float,
                        current_positions: List[Dict]) -> Dict:
        """
        检查订单风险
        
        Returns:
            {'allowed': bool, 'reason': str, 'warnings': List[str]}
        """
        self.reset_daily_limits()
        
        warnings = []
        order_value = quantity * price
        
        # 1. 检查仓位限制
        if order_value > available_balance * self.max_position_pct:
            return {
                'allowed': False,
                'reason': f'超出仓位限制: ${order_value:.2f} > ${available_balance * self.max_position_pct:.2f}',
                'warnings': warnings
            }
        
        # 2. 检查持仓数量
        if side == 'BUY' and len(current_positions) >= self.max_positions:
            return {
                'allowed': False,
                'reason': f'超出最大持仓数量: {len(current_positions)}/{self.max_positions}',
                'warnings': warnings
            }
        
        # 3. 检查是否有重复持仓
        existing_position = next((p for p in current_positions if p['symbol'] == symbol), None)
        if existing_position and side == 'BUY':
            warnings.append(f'已持有 {symbol}，建议先平仓再开新仓')
        
        # 4. 检查市场波动
        volatility_warning = self._check_volatility(symbol)
        if volatility_warning:
            warnings.append(volatility_warning)
        
        # 5. 检查流动性
        liquidity_warning = self._check_liquidity(symbol, order_value)
        if liquidity_warning:
            warnings.append(liquidity_warning)
        
        return {
            'allowed': True,
            'reason': '通过风险检查',
            'warnings': warnings
        }
    
    def _check_volatility(self, symbol: str) -> Optional[str]:
        """检查市场波动"""
        # 这里可以从数据库获取波动率数据
        # 简化实现
        return None
    
    def _check_liquidity(self, symbol: str, order_value: float) -> Optional[str]:
        """检查流动性"""
        # 如果订单金额过大，提示流动性风险
        if order_value > 100000:  # $100k
            return f'订单金额 ${order_value:,.2f} 较大，注意滑点风险'
        return None
    
    def calculate_position_size(self, available_balance: float,
                               entry_price: float,
                               stop_loss_price: float,
                               risk_pct: Optional[float] = None) -> float:
        """
        计算仓位大小
        
        基于风险金额计算仓位：
        position_size = risk_amount / (entry_price - stop_loss_price)
        
        Args:
            available_balance: 可用资金
            entry_price: 入场价格
            stop_loss_price: 止损价格
            risk_pct: 单笔风险比例 (默认使用 max_position_pct)
        
        Returns:
            建议的仓位数量
        """
        risk_pct = risk_pct or self.max_position_pct
        risk_amount = available_balance * risk_pct
        
        price_diff = abs(entry_price - stop_loss_price)
        if price_diff == 0:
            return 0
        
        position_size = risk_amount / price_diff
        max_position_value = available_balance * self.max_position_pct
        max_size = max_position_value / entry_price
        
        return min(position_size, max_size)
    
    def update_pnl(self, pnl: float):
        """更新盈亏统计"""
        self.daily_pnl += pnl
        self.total_pnl += pnl
    
    def check_trading_allowed(self, total_equity: float) -> Dict:
        """
        检查是否允许继续交易
        
        Returns:
            {'allowed': bool, 'reason': str}
        """
        self.reset_daily_limits()
        
        # 检查日亏损限制
        daily_loss_pct = abs(self.daily_pnl) / total_equity if total_equity > 0 else 0
        if daily_loss_pct >= self.max_daily_loss_pct:
            return {
                'allowed': False,
                'reason': f'单日亏损超限: {daily_loss_pct*100:.2f}% >= {self.max_daily_loss_pct*100:.2f}%'
            }
        
        # 检查总亏损限制
        total_loss_pct = abs(self.total_pnl) / total_equity if total_equity > 0 else 0
        if total_loss_pct >= self.max_total_loss_pct:
            return {
                'allowed': False,
                'reason': f'总亏损超限: {total_loss_pct*100:.2f}% >= {self.max_total_loss_pct*100:.2f}%'
            }
        
        return {'allowed': True, 'reason': '允许交易'}
    
    def get_stop_loss_price(self, entry_price: float, side: str) -> float:
        """获取止损价格"""
        if side == 'BUY':
            return entry_price * (1 - self.stop_loss_pct)
        else:
            return entry_price * (1 + self.stop_loss_pct)
    
    def get_take_profit_price(self, entry_price: float, side: str) -> float:
        """获取止盈价格"""
        if side == 'BUY':
            return entry_price * (1 + self.take_profit_pct)
        else:
            return entry_price * (1 - self.take_profit_pct)


def test_api():
    """测试API连接"""
    print("🔧 币安API测试")
    print("=" * 50)
    
    # 使用测试网（无需真实API Key）
    api = BinanceAPI(testnet=True)
    
    # 测试连接
    print("\n1. 测试连接...")
    if api.test_connectivity():
        print("✅ 连接成功")
    else:
        print("❌ 连接失败")
        return
    
    # 获取服务器时间
    print("\n2. 获取服务器时间...")
    server_time = api.get_server_time()
    local_time = int(time.time() * 1000)
    print(f"   服务器时间: {server_time}")
    print(f"   本地时间: {local_time}")
    print(f"   时间差: {abs(server_time - local_time)}ms")
    
    # 获取价格
    print("\n3. 获取BTC价格...")
    price = api.get_symbol_price('BTCUSDT')
    print(f"   BTC/USDT: ${price:,.2f}")
    
    # 获取ETH价格
    print("\n4. 获取ETH价格...")
    price = api.get_symbol_price('ETHUSDT')
    print(f"   ETH/USDT: ${price:,.2f}")
    
    print("\n✅ API测试完成")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='交易所API接口')
    parser.add_argument('--test', action='store_true', help='测试API连接')
    parser.add_argument('--price', help='获取币种价格')
    parser.add_argument('--testnet', action='store_true', default=True, help='使用测试网')
    
    args = parser.parse_args()
    
    if args.test:
        test_api()
    elif args.price:
        api = BinanceAPI(testnet=args.testnet)
        price = api.get_symbol_price(args.price.upper())
        print(f"{args.price.upper()}: ${price:,.2f}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
