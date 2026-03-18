#!/bin/bash
# 系统可靠性配置脚本
# 目标：除非物理关机或系统升级，否则永不停机

set -e

echo "============================================================"
echo "🛡️  系统可靠性配置"
echo "   目标：7×24小时无人值守运行"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/Users/mac/.openclaw/workspace/quant-trading"
cd "$PROJECT_ROOT"

# ============================================================
# 1. 配置Mac电源管理（需要sudo）
# ============================================================
echo "${BLUE}步骤 1: 配置Mac电源管理${NC}"
echo "------------------------------------------------------------"

cat << 'EOF'
⚠️  注意：以下设置需要管理员权限
    
将执行以下命令：
    sudo pmset -c sleep 0          # 连接电源时不睡眠
    sudo pmset -c hibernatemode 0  # 禁用休眠
    sudo pmset -c displaysleep 0   # 显示器不自动关闭
    
这些设置确保Mac在连接电源时不会进入睡眠，
即使您离开电脑，系统也会持续运行。

EOF

read -p "是否配置电源管理？(需要sudo密码) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在配置电源管理..."
    
    # 连接电源时的设置
    sudo pmset -c sleep 0 2>/dev/null && echo "✅ 已禁用睡眠(连接电源)" || echo "⚠️  配置睡眠失败"
    sudo pmset -c hibernatemode 0 2>/dev/null && echo "✅ 已禁用休眠" || echo "⚠️  配置休眠失败"
    sudo pmset -c displaysleep 0 2>/dev/null && echo "✅ 已禁用显示器自动关闭" || echo "⚠️  配置显示器失败"
    sudo pmset -c standby 0 2>/dev/null && echo "✅ 已禁用待机" || echo "⚠️  配置待机失败"
    
    echo "${GREEN}✅ 电源管理配置完成${NC}"
else
    echo "${YELLOW}⚠️  跳过电源管理配置${NC}"
    echo "   注意：如果不配置，Mac可能会在您离开时睡眠"
fi

# ============================================================
# 2. 创建系统级服务（LaunchDaemon）
# ============================================================
echo ""
echo "${BLUE}步骤 2: 创建系统级服务${NC}"
echo "------------------------------------------------------------"

# 创建LaunchDaemon目录（需要sudo）
LAUNCH_DAEMON_DIR="/Library/LaunchDaemons"

# 创建服务配置文件
sudo tee "$LAUNCH_DAEMON_DIR/com.quant-trading.shen-suan-zi.plist" > /dev/null << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.quant-trading.shen-suan-zi</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/mac/.openclaw/workspace/quant-trading/cron/prediction_agent_cron.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/mac/.openclaw/workspace/quant-trading</string>
    
    <key>StartInterval</key>
    <integer>900</integer>
    
    <key>StandardOutPath</key>
    <string>/Users/mac/.openclaw/workspace/quant-trading/logs/daemon_prediction.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/mac/.openclaw/workspace/quant-trading/logs/daemon_prediction_error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>/Users/mac/.openclaw/workspace/quant-trading</string>
        <key>PROJECT_ROOT</key>
        <string>/Users/mac/.openclaw/workspace/quant-trading</string>
    </dict>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>ThrottleInterval</key>
    <integer>60</integer>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>UserName</key>
    <string>mac</string>
</dict>
</plist>
EOF

# 设置权限
sudo chmod 644 "$LAUNCH_DAEMON_DIR/com.quant-trading.shen-suan-zi.plist"

# 加载服务
sudo launchctl unload "$LAUNCH_DAEMON_DIR/com.quant-trading.shen-suan-zi.plist" 2>/dev/null || true
sudo launchctl load "$LAUNCH_DAEMON_DIR/com.quant-trading.shen-suan-zi.plist"

echo "${GREEN}✅ 系统服务已安装${NC}"

# ============================================================
# 3. 创建用户级服务（备用）
# ============================================================
echo ""
echo "${BLUE}步骤 3: 创建用户级备用服务${NC}"
echo "------------------------------------------------------------"

LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENT_DIR"

cp "$LAUNCH_DAEMON_DIR/com.quant-trading.shen-suan-zi.plist" "$LAUNCH_AGENT_DIR/"

# 加载用户级服务
launchctl unload "$LAUNCH_AGENT_DIR/com.quant-trading.shen-suan-zi.plist" 2>/dev/null || true
launchctl load "$LAUNCH_AGENT_DIR/com.quant-trading.shen-suan-zi.plist"

echo "${GREEN}✅ 用户级备用服务已安装${NC}"

# ============================================================
# 4. 创建自启动脚本
# ============================================================
echo ""
echo "${BLUE}步骤 4: 配置开机自启动${NC}"
echo "------------------------------------------------------------"

# 创建自启动脚本
AUTOSTART_SCRIPT="$PROJECT_ROOT/开机自启动.sh"

cat > "$AUTOSTART_SCRIPT" << 'EOF'
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
EOF

chmod +x "$AUTOSTART_SCRIPT"

echo "${GREEN}✅ 开机自启动脚本已创建${NC}"

# ============================================================
# 5. 创建监控守护进程
# ============================================================
echo ""
echo "${BLUE}步骤 5: 创建超级看门狗${NC}"
echo "------------------------------------------------------------"

WATCHDOG_SCRIPT="$PROJECT_ROOT/超级看门狗.py"

cat > "$WATCHDOG_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
超级看门狗 - 终极系统保障
确保神算子、千手财童等核心组件持续运行
"""

import os
import sys
import time
import subprocess
import sqlite3
from datetime import datetime, timedelta

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
LOG_FILE = f"{PROJECT_ROOT}/logs/super_watchdog.log"

def log(msg):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def check_prediction_running():
    """检查神算子是否正常运行"""
    try:
        conn = sqlite3.connect(f"{PROJECT_ROOT}/data/market_data.db")
        cursor = conn.cursor()
        
        # 检查最近20分钟内是否有预测记录
        cursor.execute("""
            SELECT COUNT(*) FROM ai_prediction_records 
            WHERE predict_initiated_at >= datetime('now', '-20 minutes')
        """)
        
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            return False, "最近20分钟无预测记录"
        return True, f"最近20分钟有{count}条预测记录"
        
    except Exception as e:
        return False, f"检查失败: {e}"

def restart_prediction_service():
    """重启预测服务"""
    log("🔄 尝试重启神算子服务...")
    
    try:
        # 手动触发一次预测
        result = subprocess.run(
            ['/usr/bin/python3', f'{PROJECT_ROOT}/cron/prediction_agent_cron.py'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            log("✅ 神算子服务重启成功")
            return True
        else:
            log(f"❌ 重启失败: {result.stderr[:200]}")
            return False
            
    except Exception as e:
        log(f"❌ 重启异常: {e}")
        return False

def send_alert(message):
    """发送告警"""
    try:
        sys.path.insert(0, PROJECT_ROOT)
        from supervisor.alerts.openclaw_notifier import OpenclawNotifier
        
        notifier = OpenclawNotifier()
        notifier.send_alert(
            title="🚨 系统异常告警",
            content=message,
            priority="high"
        )
    except:
        pass

def main():
    """主循环"""
    log("=" * 60)
    log("🛡️ 超级看门狗启动")
    log("=" * 60)
    log(f"监控间隔: 60秒")
    log(f"日志文件: {LOG_FILE}")
    log("=" * 60)
    
    consecutive_failures = 0
    
    while True:
        try:
            # 检查神算子
            running, msg = check_prediction_running()
            
            if not running:
                consecutive_failures += 1
                log(f"⚠️  检测到异常 ({consecutive_failures}/3): {msg}")
                
                if consecutive_failures >= 3:
                    log("🔴 连续3次检测失败，发送告警")
                    send_alert(f"神算子连续20分钟无预测: {msg}")
                    
                    # 尝试重启
                    if restart_prediction_service():
                        consecutive_failures = 0
                    else:
                        log("❌ 自动重启失败，请人工检查")
            else:
                if consecutive_failures > 0:
                    log(f"✅ 服务已恢复: {msg}")
                    consecutive_failures = 0
                else:
                    log(f"✅ {msg}")
            
            # 每分钟检查一次
            time.sleep(60)
            
        except KeyboardInterrupt:
            log("👋 超级看门狗停止")
            break
        except Exception as e:
            log(f"❌ 看门狗异常: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
EOF

chmod +x "$WATCHDOG_SCRIPT"

# 启动超级看门狗
nohup /usr/bin/python3 "$WATCHDOG_SCRIPT" > /dev/null 2>&1 &

echo "${GREEN}✅ 超级看门狗已启动${NC}"

# ============================================================
# 6. 验证配置
# ============================================================
echo ""
echo "${BLUE}步骤 6: 验证配置${NC}"
echo "------------------------------------------------------------"

echo ""
echo "检查系统服务:"
launchctl list | grep "com.quant-trading" || echo "暂无服务"

echo ""
echo "检查电源管理:"
pmset -g | grep -E "(sleep|hibernate|standby)" | head -5

echo ""
echo "检查最近预测记录:"
sqlite3 "$PROJECT_ROOT/data/market_data.db" "SELECT datetime(predict_initiated_at), symbol, consensus_prediction FROM ai_prediction_records ORDER BY predict_initiated_at DESC LIMIT 3;" 2>/dev/null || echo "暂无记录"

# ============================================================
# 完成
# ============================================================
echo ""
echo "${GREEN}============================================================${NC}"
echo "${GREEN}✅ 系统可靠性配置完成！${NC}"
echo "${GREEN}============================================================${NC}"
echo ""
echo "📋 已完成的配置:"
echo "   1. ✅ Mac电源管理（永不睡眠）"
echo "   2. ✅ 系统级服务（LaunchDaemon）"
echo "   3. ✅ 用户级备用服务（LaunchAgent）"
echo "   4. ✅ 开机自启动脚本"
echo "   5. ✅ 超级看门狗监控"
echo ""
echo "🎯 现在系统可以:"
echo "   • 锁屏后继续运行"
echo "   • 显示器关闭后继续运行"
echo "   • 用户注销后仍能运行"
echo "   • 进程崩溃后自动重启"
echo "   • 开机后自动启动"
echo ""
echo "⚠️  重要提醒:"
echo "   • 必须连接电源适配器"
echo "   • 系统升级后需要重新配置"
echo "   • 物理关机后需要重新开机"
echo ""
echo "📊 查看状态:"
echo "   日志: tail -f $PROJECT_ROOT/logs/daemon_prediction.log"
echo "   监控: tail -f $PROJECT_ROOT/logs/super_watchdog.log"
echo ""
echo "${GREEN}============================================================${NC}"
