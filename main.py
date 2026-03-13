#!/usr/bin/env python3
"""
Quant Trading System v1.0 - 主控程序
整合所有模块，实现全自动量化交易
"""

import os
import sys
import time
import schedule
import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目路径
PROJECT_DIR = Path.home() / ".openclaw/workspace/quant-trading"
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "data-layer" / "market-data-fetch"))
sys.path.insert(0, str(PROJECT_DIR / "data-layer" / "gmgn-fetch"))
sys.path.insert(0, str(PROJECT_DIR / "research-layer" / "factor-score-engine"))
sys.path.insert(0, str(PROJECT_DIR / "execution-layer" / "trade-executor"))
sys.path.insert(0, str(PROJECT_DIR / "backtest"))
sys.path.insert(0, str(PROJECT_DIR / "ai_models" / "knowledge_base"))
sys.path.insert(0, str(PROJECT_DIR / "utils"))

# 导入模块
from fetch import init_database as init_market_db, get_realtime_price
from gmgn_fetch import GMGNFetcher
from score import calculate_factor_score, init_factor_tables
from backtest_engine import BacktestEngine
from knowledge_manager import KnowledgeBaseManager
from exchange_api import BinanceAPI, RiskManager
from notification import NotificationManager

# 配置
DATA_DIR = Path.home() / ".openclaw/workspace/quant-trading/data"
DB_PATH = DATA_DIR / "market_data.db"
VERSION = "1.0.0"


class QuantTradingSystem:
    """量化交易系统主控"""
    
    def __init__(self):
        self.version = VERSION
        self.db_path = DB_PATH
        self.running = False
        
        # 初始化各模块
        print("🚀 初始化量化交易系统 v{}...".format(self.version))
        
        # 数据模块
        self.gmgn = GMGNFetcher()
        
        # AI模块
        self.kb = KnowledgeBaseManager()
        
        # 通知模块
        self.notifier = NotificationManager()
        
        # 交易模块
        self.risk_manager = RiskManager(
            max_position_pct=0.2,
            max_daily_loss_pct=0.05,
            max_total_loss_pct=0.15
        )
        
        # API（模拟模式，需要设置环境变量才能启用真实交易）
        self.use_real_trading = os.getenv('ENABLE_REAL_TRADING', 'false').lower() == 'true'
        if self.use_real_trading:
            self.exchange = BinanceAPI(testnet=False)
            print("⚠️  真实交易模式已启用！")
        else:
            print("ℹ️  当前为模拟交易模式")
        
        print("✅ 系统初始化完成")
    
    def init_system(self):
        """初始化系统数据库"""
        print("\n🔧 初始化系统...")
        
        # 初始化市场数据表
        init_market_db()
        
        # 初始化因子评分表
        init_factor_tables()
        
        # GMGN表已在初始化时创建
        
        print("✅ 系统初始化完成\n")
    
    def add_watchlist(self, symbol: str, market: str, name: str = None):
        """添加监控标的"""
        from fetch import add_to_watchlist
        add_to_watchlist(symbol, market, name)
    
    def scan_market(self):
        """扫描市场 - 获取实时数据并生成信号"""
        print(f"\n[{datetime.now()}] 🔍 开始市场扫描...")
        
        # 1. 获取监控列表
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT symbol, market FROM watchlist')
        watchlist = cursor.fetchall()
        conn.close()
        
        if not watchlist:
            print("⚠️  监控列表为空，请先添加标的")
            return
        
        signals = []
        
        # 2. 对每个标的进行评分
        for symbol, market in watchlist:
            try:
                # 获取实时价格
                get_realtime_price(symbol, market)
                
                # 计算因子评分
                result = calculate_factor_score(symbol, market)
                
                score = result['total_score']
                rating = result['rating']
                signal = result['signal']
                
                print(f"  {symbol}: {score}分 [{rating}] - {signal}")
                
                # A级信号且置信度高的，发送通知
                if rating == 'A' and result['confidence'] > 0.7:
                    signals.append({
                        'symbol': symbol,
                        'signal': signal,
                        'price': self._get_latest_price(symbol),
                        'confidence': result['confidence'],
                        'score': score
                    })
                    
            except Exception as e:
                print(f"  ❌ {symbol} 评分失败: {e}")
        
        # 3. 发送信号通知
        for sig in signals:
            self.notifier.notify_trade_signal(
                symbol=sig['symbol'],
                signal=sig['signal'],
                price=sig['price'],
                confidence=sig['confidence']
            )
        
        if signals:
            print(f"\n🎯 发现 {len(signals)} 个高置信度信号，已发送通知")
        
        print(f"[{datetime.now()}] ✅ 市场扫描完成\n")
    
    def _get_latest_price(self, symbol: str) -> float:
        """获取最新价格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT price FROM realtime_price WHERE symbol = ?', (symbol,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0
    
    def scan_gmgn(self):
        """扫描冲狗市场"""
        print(f"\n[{datetime.now()}] 🐕 扫描冲狗市场...")
        
        # 获取热门代币
        tokens = self.gmgn.fetch_trending_tokens(limit=20)
        
        # 筛选高潜力新币
        new_tokens = [t for t in tokens if t.is_new and t.risk_score < 50]
        
        if new_tokens:
            print(f"\n🆕 发现 {len(new_tokens)} 个新币:")
            for t in new_tokens[:5]:
                print(f"  {t.symbol}: ${t.price:.8f} | 1h: {t.price_change_1h:+.2f}% | 风险: {t.risk_score}")
        
        print(f"[{datetime.now()}] ✅ 冲狗扫描完成\n")
    
    def execute_signals(self, dry_run: bool = True):
        """执行交易信号"""
        print(f"\n[{datetime.now()}] 💰 执行交易信号...")
        
        # 获取高置信度信号
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT symbol, market, signal, total_score, confidence 
            FROM factor_scores 
            WHERE rating = 'A' AND confidence > 0.7
            AND timestamp > datetime('now', '-1 hour')
            ORDER BY total_score DESC
            LIMIT 5
        ''')
        signals = cursor.fetchall()
        conn.close()
        
        if not signals:
            print("  当前无交易信号")
            return
        
        for symbol, market, signal, score, confidence in signals:
            if signal != "买入":
                continue
            
            price = self._get_latest_price(symbol)
            
            if dry_run:
                print(f"  [模拟] {symbol}: 买入信号 @ ${price:,.2f} (置信度: {confidence:.1%})")
                self.notifier.notify_order(symbol, "BUY", 0.1, price)
            else:
                # 真实交易逻辑
                print(f"  [实盘] {symbol}: 执行买入 @ ${price:,.2f}")
        
        print(f"[{datetime.now()}] ✅ 信号执行完成\n")
    
    def run_backtest(self, strategy: str = 'trend', days: int = 90):
        """运行策略回测"""
        print(f"\n📊 运行回测: {strategy} 策略 ({days}天)")
        
        engine = BacktestEngine(initial_capital=100000)
        
        # 选择策略
        strategies = {
            'trend': engine.trend_following_strategy,
            'mean_reversion': engine.mean_reversion_strategy,
            'breakout': engine.breakout_strategy,
            'meme': engine.meme_coin_strategy
        }
        
        if strategy not in strategies:
            print(f"❌ 未知策略: {strategy}")
            return
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取监控列表进行回测
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT symbol, market FROM watchlist LIMIT 3')
        watchlist = cursor.fetchall()
        conn.close()
        
        for symbol, market in watchlist:
            print(f"\n  回测 {symbol}...")
            try:
                result = engine.run_backtest(
                    symbol=symbol,
                    strategy_func=strategies[strategy],
                    start_date=start_date,
                    end_date=end_date,
                    strategy_name=strategy
                )
                engine.print_report(result)
                
                # 保存到数据库
                engine.save_result(result)
                
                # 如果表现好，更新知识库
                if result.total_return > 10 and result.sharpe_ratio > 1:
                    self.kb.learn_from_backtest({
                        'strategy_name': strategy,
                        'symbol': symbol,
                        'total_return': result.total_return,
                        'sharpe_ratio': result.sharpe_ratio
                    })
                    
            except Exception as e:
                print(f"  ❌ {symbol} 回测失败: {e}")
    
    def generate_daily_report(self):
        """生成日报"""
        print(f"\n[{datetime.now()}] 📈 生成日报...")
        
        # 获取今日统计
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 今日交易
        cursor.execute('''
            SELECT COUNT(*), SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)
            FROM trade_history 
            WHERE date(timestamp) = date('now')
        ''')
        trade_count, win_count = cursor.fetchone()
        win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0
        
        # 持仓
        cursor.execute('SELECT symbol, quantity, avg_price FROM positions')
        positions = [{'symbol': r[0], 'quantity': r[1], 'avg_price': r[2]} 
                    for r in cursor.fetchall()]
        
        conn.close()
        
        report_data = {
            'total_equity': 100000,
            'daily_pnl': 0,
            'daily_pnl_pct': 0,
            'total_return': 0,
            'trade_count': trade_count or 0,
            'win_rate': win_rate,
            'max_drawdown': 0,
            'positions': positions,
            'signals': []
        }
        
        self.notifier.notify_daily_report(report_data)
        print(f"[{datetime.now()}] ✅ 日报已发送\n")
    
    def start_scheduler(self):
        """启动定时任务"""
        print("\n⏰ 启动定时任务调度器...")
        print("  - 每5分钟: 市场扫描")
        print("  - 每15分钟: 冲狗扫描")
        print("  - 每30分钟: 执行信号")
        print("  - 每日8:00: 生成日报")
        print("\n按 Ctrl+C 停止\n")
        
        # 设置定时任务
        schedule.every(5).minutes.do(self.scan_market)
        schedule.every(15).minutes.do(self.scan_gmgn)
        schedule.every(30).minutes.do(lambda: self.execute_signals(dry_run=True))
        schedule.every().day.at("08:00").do(self.generate_daily_report)
        
        # 立即执行一次
        self.scan_market()
        self.scan_gmgn()
        
        self.running = True
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 停止调度器")
            self.running = False
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 统计监控标的
        cursor.execute('SELECT COUNT(*) FROM watchlist')
        watchlist_count = cursor.fetchone()[0]
        
        # 统计持仓
        cursor.execute('SELECT COUNT(*), SUM(quantity * avg_price) FROM positions')
        position_count, position_value = cursor.fetchone()
        
        # 今日交易
        cursor.execute('''
            SELECT COUNT(*) FROM trade_history 
            WHERE date(timestamp) = date('now')
        ''')
        today_trades = cursor.fetchone()[0]
        
        # 追踪的钱包
        cursor.execute('SELECT COUNT(*) FROM smart_wallets WHERE is_tracking = 1')
        tracking_wallets = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'version': self.version,
            'mode': '真实交易' if self.use_real_trading else '模拟交易',
            'watchlist_count': watchlist_count,
            'position_count': position_count or 0,
            'position_value': position_value or 0,
            'today_trades': today_trades or 0,
            'tracking_wallets': tracking_wallets or 0,
            'uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description=f'量化交易系统 v{VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 初始化系统
  python main.py --init
  
  # 添加监控标的
  python main.py --add BTCUSDT crypto
  python main.py --add AAPL stock
  
  # 启动自动交易
  python main.py --daemon
  
  # 手动扫描市场
  python main.py --scan
  
  # 运行回测
  python main.py --backtest trend --days 90
  
  # 查看状态
  python main.py --status
        """
    )
    
    parser.add_argument('--init', action='store_true', help='初始化系统')
    parser.add_argument('--add', nargs=2, metavar=('SYMBOL', 'MARKET'), 
                       help='添加监控标的')
    parser.add_argument('--scan', action='store_true', help='扫描市场')
    parser.add_argument('--gmgn', action='store_true', help='扫描冲狗市场')
    parser.add_argument('--backtest', choices=['trend', 'mean_reversion', 'breakout', 'meme'],
                       help='运行回测')
    parser.add_argument('--days', type=int, default=90, help='回测天数')
    parser.add_argument('--daemon', action='store_true', help='启动定时任务')
    parser.add_argument('--status', action='store_true', help='查看系统状态')
    parser.add_argument('--execute', action='store_true', help='执行交易信号')
    parser.add_argument('--report', action='store_true', help='生成日报')
    parser.add_argument('--real', action='store_true', 
                       help='启用真实交易(需要设置API密钥)')
    
    args = parser.parse_args()
    
    # 创建系统实例
    system = QuantTradingSystem()
    
    if args.init:
        system.init_system()
    
    elif args.add:
        symbol, market = args.add
        system.add_watchlist(symbol, market)
    
    elif args.scan:
        system.scan_market()
    
    elif args.gmgn:
        system.scan_gmgn()
    
    elif args.backtest:
        system.run_backtest(args.backtest, args.days)
    
    elif args.daemon:
        system.start_scheduler()
    
    elif args.status:
        status = system.get_status()
        print(f"\n📊 系统状态 v{status['version']}")
        print("=" * 40)
        print(f"运行模式: {status['mode']}")
        print(f"监控标的: {status['watchlist_count']} 个")
        print(f"当前持仓: {status['position_count']} 个 (${status['position_value']:,.2f})")
        print(f"今日交易: {status['today_trades']} 笔")
        print(f"追踪钱包: {status['tracking_wallets']} 个")
        print(f"系统时间: {status['uptime']}")
        print()
    
    elif args.execute:
        system.execute_signals(dry_run=not args.real)
    
    elif args.report:
        system.generate_daily_report()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
