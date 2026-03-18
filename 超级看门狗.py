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
