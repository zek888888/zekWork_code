#!/bin/bash
# 看门狗启动脚本 - 监督隔壁老王

cd /Users/mac/.openclaw/workspace/quant-trading

echo "🐕 启动看门狗，正在监督隔壁老王..."
echo "   时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 启动看门狗
/usr/local/bin/python3 -c "
import sys
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')
from supervisor.core.self_monitor import Watchdog
watchdog = Watchdog()
watchdog.run()
" >> logs/watchdog.log 2>&1 &

PID=$!
echo $! > watchdog.pid

echo "✅ 看门狗已启动"
echo "   PID: $PID"
echo "   日志: tail -f logs/watchdog.log"
echo ""
echo "看门狗职责:"
echo "   • 每分钟检查老王是否活着"
echo "   • 老王挂了立即重启"
echo "   • 老王卡死了立即告警"
echo ""
echo "停止看门狗: kill \$(cat watchdog.pid)"
