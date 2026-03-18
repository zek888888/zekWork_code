#!/bin/bash
# 量化交易系统开机自启动脚本

PROJECT_ROOT="/Users/mac/.openclaw/workspace/quant-trading"
LOG_FILE="$PROJECT_ROOT/logs/autostart.log"

mkdir -p "$PROJECT_ROOT/logs"

echo "[$(date)] 系统开机，启动量化交易服务..." >> "$LOG_FILE"

# 等待网络就绪
sleep 10

# 启动数据收集
cd "$PROJECT_ROOT"
/usr/bin/python3 "$PROJECT_ROOT/千手财童_data_collector.py" >> "$LOG_FILE" 2>&1 &

echo "[$(date)] 服务启动完成" >> "$LOG_FILE"
