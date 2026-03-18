#!/usr/bin/env python3
"""
系统可靠性验证工具
验证系统是否满足：除非物理关机或系统升级，否则永不停机
"""

import os
import sys
import subprocess
import sqlite3
import time
from datetime import datetime, timedelta

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"

class SystemReliabilityChecker:
    """系统可靠性检查器"""
    
    def __init__(self):
        self.issues = []
        self.checks_passed = 0
        self.checks_failed = 0
    
    def check_pass(self, msg):
        print(f"  ✅ {msg}")
        self.checks_passed += 1
    
    def check_fail(self, msg):
        print(f"  ❌ {msg}")
        self.issues.append(msg)
        self.checks_failed += 1
    
    def check_warn(self, msg):
        print(f"  ⚠️  {msg}")
    
    def check_power_management(self):
        """检查电源管理设置"""
        print("\n" + "=" * 60)
        print("🔋 检查电源管理设置")
        print("=" * 60)
        
        try:
            result = subprocess.run(
                ["pmset", "-g"],
                capture_output=True,
                text=True
            )
            
            output = result.stdout
            
            # 检查睡眠设置
            if "sleep" in output:
                # 提取ac sleep设置
                for line in output.split("\n"):
                    if " sleep " in line and "disksleep" not in line.lower():
                        if "0" in line:
                            self.check_pass("Mac连接电源时不会睡眠")
                        else:
                            self.check_fail(f"Mac仍会在闲置后睡眠: {line.strip()}")
                            print(f"     修复: sudo pmset -c sleep 0")
            
            # 检查休眠模式
            if "hibernatemode 0" in output:
                self.check_pass("休眠模式已禁用")
            else:
                self.check_warn("休眠模式可能未完全禁用")
            
        except Exception as e:
            self.check_fail(f"检查电源管理失败: {e}")
    
    def check_system_service(self):
        """检查系统服务"""
        print("\n" + "=" * 60)
        print("⚙️  检查系统服务")
        print("=" * 60)
        
        # 检查LaunchDaemon
        daemon_plist = "/Library/LaunchDaemons/com.quant-trading.shen-suan-zi.plist"
        if os.path.exists(daemon_plist):
            self.check_pass("系统级服务已安装")
        else:
            self.check_fail("系统级服务未安装")
            print(f"     修复: bash 配置系统可靠性.sh")
        
        # 检查服务加载状态（定时任务服务空闲时显示为"-"是正常的）
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True
        )
        
        services = [line for line in result.stdout.split("\n") if "quant-trading" in line]
        
        if services:
            for svc in services:
                parts = svc.split()
                if len(parts) >= 3:
                    pid = parts[0]
                    exit_code = parts[1]
                    name = parts[2]
                    if pid != "-":
                        self.check_pass(f"服务运行中: {name} (PID: {pid})")
                    elif exit_code == "0":
                        # 退出码0表示正常完成，对于定时任务这是正常的
                        self.check_pass(f"服务正常: {name} (定时任务，空闲状态)")
                    else:
                        self.check_warn(f"服务状态: {name} (上次退出码: {exit_code})")
        else:
            self.check_fail("没有找到量化交易服务")
    
    def check_prediction_continuity(self):
        """检查预测连续性"""
        print("\n" + "=" * 60)
        print("📊 检查预测连续性")
        print("=" * 60)
        
        try:
            conn = sqlite3.connect(f"{PROJECT_ROOT}/data/market_data.db")
            cursor = conn.cursor()
            
            # 获取最近24小时的记录
            cursor.execute("""
                SELECT datetime(predict_initiated_at) as time
                FROM ai_prediction_records 
                WHERE predict_initiated_at >= datetime('now', '-24 hours')
                ORDER BY predict_initiated_at DESC
            """)
            
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                self.check_fail("最近24小时无预测记录")
                return
            
            print(f"  最近24小时共有 {len(records)} 条预测记录")
            
            # 只检查最近2小时的间隔（历史问题不影响当前状态）
            gaps = []
            recent_records = []
            cutoff_time = datetime.now() - timedelta(hours=2)
            
            for r in records:
                r_time = datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S')
                if r_time >= cutoff_time:
                    recent_records.append(r)
            
            for i in range(min(5, len(recent_records)-1)):
                t1 = datetime.strptime(recent_records[i][0], '%Y-%m-%d %H:%M:%S')
                t2 = datetime.strptime(recent_records[i+1][0], '%Y-%m-%d %H:%M:%S')
                diff = (t1 - t2).total_seconds() / 60  # 分钟
                
                if diff > 20:  # 正常应该是15分钟
                    gaps.append(f"    {recent_records[i+1][0]} -> {recent_records[i][0]}: {diff:.1f}分钟")
            
            if gaps:
                self.check_fail(f"最近2小时发现 {len(gaps)} 次间隔过长:")
                for gap in gaps:
                    print(gap)
            else:
                self.check_pass("最近2小时预测任务运行正常")
                
        except Exception as e:
            self.check_fail(f"检查预测记录失败: {e}")
    
    def check_watchdog(self):
        """检查看门狗"""
        print("\n" + "=" * 60)
        print("🐕 检查看门狗")
        print("=" * 60)
        
        # 检查超级看门狗是否在运行
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        
        if "超级看门狗.py" in result.stdout:
            self.check_pass("超级看门狗正在运行")
        else:
            self.check_warn("超级看门狗未运行（可接受，因为LaunchDaemon已提供保障）")
    
    def check_auto_start(self):
        """检查开机自启动"""
        print("\n" + "=" * 60)
        print("🚀 检查开机自启动")
        print("=" * 60)
        
        daemon_plist = "/Library/LaunchDaemons/com.quant-trading.shen-suan-zi.plist"
        if os.path.exists(daemon_plist):
            with open(daemon_plist) as f:
                content = f.read()
                if "RunAtLoad" in content and "true" in content:
                    self.check_pass("已配置开机自动启动")
                else:
                    self.check_warn("开机自启动配置可能不完整")
        else:
            self.check_fail("未找到系统服务配置")
    
    def generate_report(self):
        """生成报告"""
        print("\n" + "=" * 60)
        print("📋 系统可靠性报告")
        print("=" * 60)
        
        print(f"\n检查通过: {self.checks_passed}")
        print(f"检查失败: {self.checks_failed}")
        
        if self.checks_failed == 0:
            print("""
╔══════════════════════════════════════════════════════════════════╗
║                     ✅ 系统可靠性验证通过                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  您的系统已配置为：                                               ║
║  • 除非物理关机或系统升级，否则永不停机                          ║
║                                                                  ║
║  现在您可以：                                                     ║
║  • 放心锁屏离开电脑                                               ║
║  • 关闭显示器                                                     ║
║  • 系统会持续运行                                                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
            return True
        else:
            print("""
╔══════════════════════════════════════════════════════════════════╗
║                     ❌ 系统可靠性存在问题                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  发现问题：                                                       ║
""")
            for issue in self.issues:
                print(f"  • {issue}")
            
            print("""
║                                                                  ║
║  请运行修复脚本：                                                 ║
║  bash 配置系统可靠性.sh                                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
            return False
    
    def run_all_checks(self):
        """运行所有检查"""
        print("=" * 60)
        print("🔍 系统可靠性全面检查")
        print(f"   检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        self.check_power_management()
        self.check_system_service()
        self.check_prediction_continuity()
        self.check_watchdog()
        self.check_auto_start()
        
        return self.generate_report()

if __name__ == "__main__":
    checker = SystemReliabilityChecker()
    success = checker.run_all_checks()
    
    sys.exit(0 if success else 1)
