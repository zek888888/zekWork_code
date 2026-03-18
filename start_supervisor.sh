#!/bin/bash
# 隔壁老王启动脚本 - 带看门狗双重保险

cd /Users/mac/.openclaw/workspace/quant-trading

# 确保日志目录存在
mkdir -p logs

echo "🧑‍🔧 隔壁老王开始上班了..."
echo "   时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 发送启动通知
/usr/bin/python3 -c "
import sys
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')
from supervisor.alerts.openclaw_notifier import OpenclawNotifier
notifier = OpenclawNotifier()
notifier.notify_system_startup()
" 2>/dev/null

# 启动监工系统
echo "📊 启动隔壁老王..."
/usr/bin/python3 supervisor/core/scheduler.py >> logs/supervisor.log 2>&1 &
PID=$!
echo $PID > supervisor.pid

echo "   老王PID: $PID"

# 等待一下确保老王启动成功
sleep 2

# 启动看门狗
echo "🐕 启动看门狗监督老王..."
./start_watchdog.sh 2>/dev/null

echo ""
echo "✅ 隔壁老王和看门狗都已就位!"
echo ""
echo "👷 隔壁老王职责:"
echo "   • 监控所有定时任务"
echo "   • 任务失败自动修复/惩罚API"
echo "   • 每分钟自我健康检查"
echo ""
echo "🐕 看门狗职责:"
echo "   • 每分钟检查老王是否活着"
echo "   • 老王挂了立即重启并告警"
echo ""
echo "📊 查看状态:"
echo "   日志: tail -f logs/supervisor.log"
echo "   控制台: http://localhost:5001/supervisor"
echo ""
echo "🛑 停止命令: ./stop_supervisor.sh"
