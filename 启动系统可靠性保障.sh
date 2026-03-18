#!/bin/bash
# 启动系统可靠性保障机制

echo "============================================================"
echo "🛡️ 启动系统可靠性保障"
echo "   目标：除非物理关机或系统升级，否则永不停机"
echo "============================================================"
echo ""

PROJECT_ROOT="/Users/mac/.openclaw/workspace/quant-trading"
cd "$PROJECT_ROOT"

# 确保日志目录存在
mkdir -p logs

# 步骤1：检查并启动系统服务
echo "步骤 1: 启动系统服务..."
LAUNCH_DAEMON="/Library/LaunchDaemons/com.quant-trading.shen-suan-zi.plist"
if [ -f "$LAUNCH_DAEMON" ]; then
    sudo launchctl load "$LAUNCH_DAEMON" 2>/dev/null && echo "  ✅ 系统服务已启动" || echo "  ℹ️  系统服务已在运行"
else
    echo "  ⚠️  系统服务未安装，请先运行: bash 配置系统可靠性.sh"
fi

# 步骤2：启动用户级备用服务
echo ""
echo "步骤 2: 启动用户级备用服务..."
LAUNCH_AGENT="$HOME/Library/LaunchAgents/com.quant-trading.shen-suan-zi.plist"
if [ -f "$LAUNCH_AGENT" ]; then
    launchctl load "$LAUNCH_AGENT" 2>/dev/null && echo "  ✅ 用户级服务已启动" || echo "  ℹ️  用户级服务已在运行"
else
    echo "  ⚠️  用户级服务未安装"
fi

# 步骤3：启动超级看门狗
echo ""
echo "步骤 3: 启动超级看门狗..."
WATCHDOG_PID=$(pgrep -f "超级看门狗.py")
if [ -z "$WATCHDOG_PID" ]; then
    nohup /usr/bin/python3 "$PROJECT_ROOT/超级看门狗.py" > /dev/null 2>&1 &
    echo "  ✅ 超级看门狗已启动"
else
    echo "  ℹ️  超级看门狗已在运行 (PID: $WATCHDOG_PID)"
fi

# 步骤4：验证运行状态
echo ""
echo "步骤 4: 验证运行状态..."
echo "  正在检查..."
sleep 2

echo ""
echo "服务状态:"
launchctl list | grep "com.quant-trading" | while read line; do
    pid=$(echo $line | awk '{print $1}')
    name=$(echo $line | awk '{print $3}')
    if [ "$pid" != "-" ]; then
        echo "  ✅ $name - 运行中 (PID: $pid)"
    else
        echo "  🔴 $name - 未运行"
    fi
done

echo ""
echo "最近预测记录:"
sqlite3 "$PROJECT_ROOT/data/market_data.db" "SELECT datetime(predict_initiated_at), symbol, consensus_prediction FROM ai_prediction_records ORDER BY predict_initiated_at DESC LIMIT 3;" 2>/dev/null || echo "  暂无记录"

echo ""
echo "============================================================"
echo "✅ 系统可靠性保障已启动"
echo "============================================================"
echo ""
echo "现在您的系统可以："
echo "  • 锁屏后继续运行"
echo "  • 显示器关闭后继续运行"
echo "  • 用户注销后仍能运行"
echo "  • 进程崩溃后自动重启"
echo ""
echo "查看状态:"
echo "  服务日志: tail -f $PROJECT_ROOT/logs/daemon_prediction.log"
echo "  看门狗日志: tail -f $PROJECT_ROOT/logs/super_watchdog.log"
echo "  全面检查: python3 验证系统可靠性.py"
echo ""
