#!/bin/bash
# 战颅将军 BTC底部反转监控启动脚本

echo "=============================================="
echo "  战颅将军 BTC底部反转监控系统"
echo "=============================================="
echo ""

WORK_DIR="/Users/mac/.openclaw/workspace/quant-trading"
LOG_FILE="$WORK_DIR/logs/btc_monitor.log"

# 确保日志目录存在
mkdir -p "$WORK_DIR/logs"

# 测试运行一次
echo "[1/3] 测试监控程序..."
cd /tmp && python3 "$WORK_DIR/cron/btc_bottom_monitor.py"
if [ $? -ne 0 ]; then
    echo "❌ 监控程序测试失败！"
    exit 1
fi
echo "✅ 监控程序正常"
echo ""

# 添加到crontab
echo "[2/3] 配置定时任务（每15分钟）..."
CRON_JOB="*/15 * * * * cd /tmp && python3 $WORK_DIR/cron/btc_bottom_monitor.py >> $LOG_FILE 2>&1"

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "btc_bottom_monitor"; then
    echo "✅ 定时任务已存在"
else
    # 添加新任务
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ 定时任务已添加"
fi
echo ""

# 显示当前状态
echo "[3/3] 监控状态:"
echo "----------------------------------------------"
echo "日志文件: $LOG_FILE"
echo "监控频率: 每15分钟"
echo "当前时间: $(date)"
echo ""

# 显示实时监控命令
echo "【常用命令】"
echo "  查看实时日志: tail -f $LOG_FILE"
echo "  手动运行监控: python3 $WORK_DIR/cron/btc_bottom_monitor.py"
echo "  停止监控: crontab -l | grep -v btc_bottom_monitor | crontab -"
echo ""
echo "=============================================="
echo "✅ BTC底部监控已启动！"
echo "=============================================="
