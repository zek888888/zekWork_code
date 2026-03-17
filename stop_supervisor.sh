#!/bin/bash
# 停止隔壁老王和看门狗

cd /Users/mac/.openclaw/workspace/quant-trading

echo "🛑 正在停止隔壁老王和看门狗..."

# 发送停止通知
/usr/local/bin/python3 -c "
import sys
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')
from supervisor.alerts.openclaw_notifier import OpenclawNotifier
notifier = OpenclawNotifier()
notifier.notify_system_shutdown()
" 2>/dev/null

# 停止看门狗
if [ -f watchdog.pid ]; then
    WATCHDOG_PID=$(cat watchdog.pid)
    if kill -0 $WATCHDOG_PID 2>/dev/null; then
        kill $WATCHDOG_PID
        echo "✅ 看门狗已停止 (PID: $WATCHDOG_PID)"
    else
        echo "⚠️ 看门狗进程 $WATCHDOG_PID 不存在"
    fi
    rm watchdog.pid
else
    echo "⚠️ 看门狗PID文件不存在"
fi

# 停止老王
if [ -f supervisor.pid ]; then
    SUPERVISOR_PID=$(cat supervisor.pid)
    if kill -0 $SUPERVISOR_PID 2>/dev/null; then
        kill $SUPERVISOR_PID
        echo "✅ 隔壁老王已停止 (PID: $SUPERVISOR_PID)"
    else
        echo "⚠️ 老王进程 $SUPERVISOR_PID 不存在"
    fi
    rm supervisor.pid
else
    # 尝试查找并停止
    PID=$(ps aux | grep "supervisor/core/scheduler.py" | grep -v grep | awk '{print $2}')
    if [ -n "$PID" ]; then
        kill $PID
        echo "✅ 老王已停止 (PID: $PID)"
    else
        echo "⚠️ 未找到运行中的老王进程"
    fi
fi

echo ""
echo "隔壁老王和看门狗已休息"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
