#!/usr/bin/env python3
"""
BTC底部反转监控 - Cron入口
添加到crontab: */15 * * * * cd /Users/mac/.openclaw/workspace/quant-trading && python3 cron/btc_bottom_monitor_cron.py >> logs/btc_monitor.log 2>&1
"""

import sys
import os

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from btc_bottom_monitor import BTCBottomMonitor

if __name__ == "__main__":
    monitor = BTCBottomMonitor()
    monitor.run_monitor()
