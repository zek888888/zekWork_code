#!/usr/bin/env python3
"""
战颅将军 BTC状态快速查看
"""
import sys
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading/cron')

from btc_bottom_monitor import BTCBottomMonitor

if __name__ == "__main__":
    monitor = BTCBottomMonitor()
    monitor.run_monitor()
