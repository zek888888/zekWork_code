#!/bin/bash
# 量化交易Web服务监控脚本
# 每5分钟检查一次，如果服务挂了自动重启

APP_DIR="$HOME/.openclaw/workspace/quant-trading/web-dashboard"
LOG_FILE="$APP_DIR/server.log"
PID_FILE="$APP_DIR/server.pid"

check_and_restart() {
    # 检查端口
    if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/login | grep -q "200"; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务异常，正在重启..." >> "$LOG_FILE"
        
        # 杀掉旧进程
        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null
            rm -f "$PID_FILE"
        fi
        pkill -f "python3 app.py" 2>/dev/null
        
        # 启动新进程
        cd "$APP_DIR"
        nohup python3 app.py >> "$LOG_FILE" 2>&1 &
        NEW_PID=$!
        echo $NEW_PID > "$PID_FILE"
        
        sleep 3
        
        # 验证启动
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/login | grep -q "200"; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务重启成功 (PID: $NEW_PID)" >> "$LOG_FILE"
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') - 服务重启失败!" >> "$LOG_FILE"
        fi
    fi
}

check_and_restart
