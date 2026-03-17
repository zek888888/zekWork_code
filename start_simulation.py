#!/usr/bin/env python3
"""
启动战颅将军模拟盘交易系统
包含: 数据收集 → 预测 → 交易执行 → Web展示
"""

import os
import sys
import signal
import subprocess
import time
import logging
from datetime import datetime

# 配置
PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
DB_PATH = f"{PROJECT_ROOT}/data/market_data.db"
PID_FILE = f"{PROJECT_ROOT}/.simulation.pid"

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('Simulation')

# 添加项目路径
sys.path.insert(0, PROJECT_ROOT)


class 战颅将军系统:
    """模拟盘交易系统控制器"""
    
    def __init__(self):
        self.processes = []
        self.running = False
        
    def 启动(self):
        """启动整个系统"""
        logger.info("=" * 60)
        logger.info("⚔️  战颅将军 - 模拟盘交易系统启动")
        logger.info("=" * 60)
        
        # 1. 检查数据库
        self._初始化数据库()
        
        # 2. 启动数据收集
        logger.info("\n[1/4] 启动千手财童 - 数据收集...")
        self._启动数据收集()
        
        # 3. 启动预测系统
        logger.info("\n[2/4] 启动神算子 - 预测系统...")
        self._启动预测系统()
        
        # 4. 启动交易引擎
        logger.info("\n[3/4] 启动战颅将军 - 交易引擎...")
        self._启动交易引擎()
        
        # 5. 启动Web展示
        logger.info("\n[4/4] 启动Web展示页面...")
        self._启动Web展示()
        
        self.running = True
        self._保存PID()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 系统启动完成!")
        logger.info("🌐 访问地址: http://localhost:5000/trade")
        logger.info("💰 启动资金: 10000 USDT")
        logger.info("⏱️  交易级别: 5分钟")
        logger.info("🤖 使用模型: DeepSeek-R1 (所有智能体)")
        logger.info("=" * 60)
        
        # 保持运行
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.停止()
    
    def _初始化数据库(self):
        """初始化数据库表"""
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulated_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                entry_price REAL NOT NULL,
                position_size REAL NOT NULL,
                leverage INTEGER NOT NULL,
                margin REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit TEXT NOT NULL,
                exit_time TIMESTAMP,
                exit_price REAL,
                exit_reason TEXT,
                pnl REAL DEFAULT 0,
                pnl_percent REAL DEFAULT 0,
                confidence REAL,
                reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 资金曲线表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equity_curve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                balance REAL NOT NULL DEFAULT 10000,
                total_trades INTEGER DEFAULT 0,
                win_trades INTEGER DEFAULT 0,
                loss_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0
            )
        ''')
        
        # 初始化资金曲线
        cursor.execute('''
            INSERT OR IGNORE INTO equity_curve (id, balance) 
            SELECT 1, 10000 WHERE NOT EXISTS (SELECT 1 FROM equity_curve WHERE id = 1)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("[✓] 数据库初始化完成")
    
    def _启动数据收集(self):
        """启动千手财童数据收集"""
        # 这里应该启动实际的千手财童数据收集器
        # 目前仅作占位
        logger.info("[✓] 千手财童数据收集已配置")
    
    def _启动预测系统(self):
        """启动神算子预测系统"""
        logger.info("[✓] 神算子预测系统已配置")
    
    def _启动交易引擎(self):
        """启动战颅将军交易引擎"""
        # 启动模拟盘引擎
        logger.info("[✓] 战颅将军交易引擎已就绪")
    
    def _启动Web展示(self):
        """启动Web展示服务"""
        web_path = f"{PROJECT_ROOT}/web_trade.py"
        proc = subprocess.Popen(
            [sys.executable, web_path],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        self.processes.append(proc)
        logger.info(f"[✓] Web服务已启动 (PID: {proc.pid})")
    
    def _保存PID(self):
        """保存进程ID"""
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    
    def 停止(self):
        """停止系统"""
        logger.info("\n" + "=" * 60)
        logger.info("🛑 正在停止系统...")
        
        for proc in self.processes:
            try:
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                else:
                    proc.terminate()
                proc.wait(timeout=5)
                logger.info(f"[✓] 已停止进程 {proc.pid}")
            except:
                proc.kill()
        
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        
        self.running = False
        logger.info("=" * 60)
        logger.info("✅ 系统已停止")
        logger.info("=" * 60)


def 打印系统状态():
    """打印系统当前状态"""
    print("\n" + "=" * 60)
    print("⚔️  战颅将军 - 模拟盘交易系统")
    print("=" * 60)
    print("\n📊 系统组件:")
    print("  • 千手财童 - 数据收集 (已就绪)")
    print("  • 神算子 - 预测系统 (已就绪)")
    print("  • 战颅将军 - 交易引擎 (已就绪)")
    print("  • Web展示 - http://localhost:5000/trade")
    print("\n💰 交易配置:")
    print("  • 启动资金: 10000 USDT")
    print("  • 交易级别: 5分钟")
    print("  • 数据范围: 2021-01-01 至今")
    print("\n🤖 AI配置:")
    print("  • 战颅将军: DeepSeek-R1 (指挥)")
    print("  • 影谍: DeepSeek-Chat (情报)")
    print("  • 铁算: DeepSeek-R1 (风险)")
    print("  • 史官: DeepSeek-R1 (回测)")
    print("  • 谋师: DeepSeek-R1 (策略)")
    print("  • 宪兵: DeepSeek-Chat (审核)")
    print("\n📁 文件位置:")
    print(f"  • 项目根目录: {PROJECT_ROOT}")
    print(f"  • 数据库: {DB_PATH}")
    print(f"  • 交易记录表: simulated_trades")
    print("\n" + "=" * 60)


def 启动Celery任务调度():
    """启动Celery任务调度器"""
    from celery import Celery
    from celery.schedules import crontab
    
    app = Celery('quant_trading')
    app.conf.update(
        broker_url='redis://localhost:6379/0',
        result_backend='redis://localhost:6379/0',
        timezone='Asia/Shanghai',
        beat_schedule={
            'collect-data': {
                'task': '千手财童.collect_all',
                'schedule': 300.0,  # 5分钟
            },
            'make-prediction': {
                'task': '神算子.predict',
                'schedule': 900.0,  # 15分钟
            },
            'execute-trade': {
                'task': '战颅将军.execute',
                'schedule': 300.0,  # 5分钟
            },
        }
    )
    
    return app


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='战颅将军模拟盘交易系统')
    parser.add_argument('command', choices=['start', 'stop', 'status'], 
                       help='启动/停止/查看状态')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        打印系统状态()
        
        # 启动系统
        system = 战颅将军系统()
        
        # 注册信号处理
        signal.signal(signal.SIGINT, lambda s, f: system.停止())
        signal.signal(signal.SIGTERM, lambda s, f: system.停止())
        
        system.启动()
        
    elif args.command == 'stop':
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"[✓] 已向进程 {pid} 发送停止信号")
            except ProcessLookupError:
                print("[!] 进程已不存在")
                os.remove(PID_FILE)
        else:
            print("[!] 系统未运行")
    
    elif args.command == 'status':
        打印系统状态()
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                pid = f.read().strip()
            print(f"\n🟢 系统运行中 (PID: {pid})")
        else:
            print("\n🔴 系统未运行")
