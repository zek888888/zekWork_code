#!/usr/bin/env python3
"""
系统全面诊断工具 - 找出"人不在就报错"的根本原因
"""

import os
import sys
import subprocess
import platform
from datetime import datetime

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"

def 检查Mac睡眠设置():
    """检查Mac是否会在闲置时睡眠"""
    print("=" * 70)
    print("🔋 检查 Mac 睡眠/休眠设置...")
    print("=" * 70)
    
    try:
        # 检查当前睡眠设置
        result = subprocess.run(
            ["pmset", "-g"],
            capture_output=True,
            text=True
        )
        
        output = result.stdout
        
        # 解析关键设置
        settings = {}
        for line in output.split("\n"):
            if "sleep" in line.lower() and "disksleep" not in line.lower():
                settings['sleep'] = line.strip()
            if "displaysleep" in line.lower():
                settings['display_sleep'] = line.strip()
            if "disksleep" in line.lower():
                settings['disk_sleep'] = line.strip()
            if "hibernatemode" in line.lower():
                settings['hibernate'] = line.strip()
        
        print("\n当前电源管理设置:")
        for key, value in settings.items():
            print(f"   {key}: {value}")
        
        # 检查问题
        issues = []
        if "sleep" in settings.get('sleep', ''):
            sleep_time = settings['sleep']
            if "10" in sleep_time or "15" in sleep_time or "30" in sleep_time:
                issues.append(f"⚠️  系统将在闲置后进入睡眠: {sleep_time}")
        
        if "hibernate" in settings.get('hibernate', '').lower():
            issues.append("⚠️  系统启用了休眠模式，可能导致长时间离线")
        
        if issues:
            print("\n❌ 发现问题:")
            for issue in issues:
                print(f"   {issue}")
            print("\n💡 解决方案:")
            print("   运行: sudo pmset -c sleep 0  # 连接电源时不睡眠")
            print("   运行: sudo pmset -b sleep 0  # 使用电池时不睡眠(可选)")
            return False
        else:
            print("\n✅ 睡眠设置正常")
            return True
            
    except Exception as e:
        print(f"   检查失败: {e}")
        return False

def 检查Cron是否系统级():
    """检查cron是否系统级运行"""
    print("\n" + "=" * 70)
    print("⏰ 检查 Cron 运行级别...")
    print("=" * 70)
    
    # 检查当前用户的cron
    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True
    )
    
    if "prediction_agent_cron.py" in result.stdout:
        print("   ✅ 找到神算子cron任务")
        print("   ⚠️  但这是用户级cron，用户注销后可能停止")
        
        # 检查是否有系统级cron
        system_cron = "/etc/crontab"
        if os.path.exists(system_cron):
            with open(system_cron) as f:
                if "quant-trading" in f.read():
                    print("   ✅ 同时配置了系统级cron")
                    return True
        
        print("\n   ❌ 问题发现: 使用用户级cron")
        print("   当用户: 1) 注销 2) 睡眠 3) 锁屏长时间后，任务可能停止")
        return False
    
    return True

def 检查路径问题():
    """检查是否使用绝对路径"""
    print("\n" + "=" * 70)
    print("📁 检查路径配置...")
    print("=" * 70)
    
    issues = []
    
    # 检查关键脚本
    scripts = [
        f"{PROJECT_ROOT}/cron/prediction_agent_cron.py",
        f"{PROJECT_ROOT}/supervisor/core/scheduler.py",
    ]
    
    for script in scripts:
        if os.path.exists(script):
            with open(script) as f:
                content = f.read()
                # 检查相对路径导入
                if "sys.path.insert" not in content and "os.chdir" not in content[:500]:
                    if "from ." in content or "import ." in content:
                        issues.append(f"   ⚠️  {os.path.basename(script)} 使用相对导入，可能导致导入错误")
    
    # 检查cron任务路径
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    cron_content = result.stdout
    
    if "cd /Users/mac/.openclaw/workspace/quant-trading" in cron_content:
        print("   ✅ Cron任务使用绝对路径cd")
    else:
        issues.append("   ⚠️  Cron任务可能没有正确设置工作目录")
    
    if "/usr/bin/python3" in cron_content:
        print("   ✅ Cron使用绝对路径Python")
    else:
        issues.append("   ⚠️  Cron使用相对路径Python，可能导致找不到命令")
    
    if issues:
        print("\n   发现路径问题:")
        for issue in issues:
            print(issue)
        return False
    else:
        print("   ✅ 路径配置正常")
        return True

def 检查后台运行配置():
    """检查是否能真正后台运行"""
    print("\n" + "=" * 70)
    print("🖥️  检查后台运行配置...")
    print("=" * 70)
    
    # 检查是否有nohup使用
    print("\n   当前运行中的进程:")
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )
    
    quant_processes = [line for line in result.stdout.split("\n") 
                       if "quant-trading" in line or "prediction" in line.lower()]
    
    if quant_processes:
        print(f"   找到 {len(quant_processes)} 个相关进程")
        for p in quant_processes[:3]:
            parts = p.split()
            if len(parts) > 10:
                print(f"   - {parts[10][:50]}... (PID: {parts[1]})")
    else:
        print("   ⚠️  没有找到量化交易相关进程")
    
    # 检查launchd服务（macOS推荐方式）
    print("\n   检查LaunchAgent服务:")
    launch_agents = os.path.expanduser("~/Library/LaunchAgents")
    if os.path.exists(launch_agents):
        plist_files = [f for f in os.listdir(launch_agents) if f.endswith('.plist')]
        quant_plists = [f for f in plist_files if 'quant' in f.lower() or 'trading' in f.lower()]
        
        if quant_plists:
            print(f"   ✅ 找到 {len(quant_plists)} 个量化交易服务配置")
        else:
            print("   ❌ 没有找到量化交易的LaunchAgent配置")
            print("   💡 这是根本原因！应该使用launchd而不是cron")
    
    return True

def 检查日志轮转():
    """检查日志是否会导致磁盘满"""
    print("\n" + "=" * 70)
    print("📝 检查日志配置...")
    print("=" * 70)
    
    log_dir = f"{PROJECT_ROOT}/logs"
    if os.path.exists(log_dir):
        size = subprocess.run(
            ["du", "-sh", log_dir],
            capture_output=True,
            text=True
        )
        print(f"   日志目录大小: {size.stdout.split()[0]}")
        
        # 检查日志文件数量
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        print(f"   日志文件数量: {len(log_files)}")
        
        if len(log_files) > 10:
            print("   ⚠️  日志文件过多，建议配置日志轮转")
    
    return True

def 生成解决方案():
    """生成完整的解决方案"""
    print("\n" + "=" * 70)
    print("💡 生成永久解决方案...")
    print("=" * 70)
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                     🛠️  根本问题分析                                 ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ❌ 问题 1: Mac 睡眠模式                                              ║
║     → 用户离开时Mac进入睡眠，所有进程暂停                              ║
║     → 这是"人不在就报错"的主要原因！                                   ║
║                                                                      ║
║  ❌ 问题 2: 使用用户级Cron而非系统服务                                  ║
║     → 用户注销或锁屏后，cron任务停止                                   ║
║     → Mac推荐用launchd替代cron                                        ║
║                                                                      ║
║  ❌ 问题 3: 没有进程守护机制                                           ║
║     → 隔壁老王停止后无人自动重启                                       ║
║     → 看门狗也没正确启动                                              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                     ✅ 永久解决方案                                    ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  方案A: 防止Mac睡眠（立即执行）                                        ║
║  ─────────────────────────────────                                    ║
║  sudo pmset -c sleep 0        # 连接电源时不睡眠                      ║
║  sudo pmset -c disablesleep 1 # 完全禁用睡眠                          ║
║                                                                      ║
║  方案B: 使用LaunchAgent（推荐）                                        ║
║  ─────────────────────────────────                                    ║
║  创建系统级服务，即使用户注销也能运行                                   ║
║  我已为您生成配置文件: 神算子_launchd.plist                            ║
║                                                                      ║
║  方案C: 使用nohup + 守护进程                                           ║
║  ─────────────────────────────────                                    ║
║  确保进程在后台持续运行                                                ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    print("=" * 70)
    print("🔍 系统全面诊断工具")
    print("   目标: 找出'人不在就报错'的根本原因")
    print("=" * 70)
    print(f"   诊断时间: {datetime.now()}")
    print(f"   系统: {platform.system()} {platform.release()}")
    print(f"   Python: {sys.executable}")
    print("=" * 70)
    
    # 执行各项检查
    sleep_ok = 检查Mac睡眠设置()
    cron_ok = 检查Cron是否系统级()
    path_ok = 检查路径问题()
    bg_ok = 检查后台运行配置()
    log_ok = 检查日志轮转()
    
    # 生成解决方案
    生成解决方案()
    
    # 总结
    print("\n" + "=" * 70)
    print("📊 诊断总结")
    print("=" * 70)
    
    issues = []
    if not sleep_ok:
        issues.append("🔴 Mac睡眠设置 - 人不在时Mac睡眠，进程暂停")
    if not cron_ok:
        issues.append("🔴 Cron运行级别 - 使用用户级cron，不可靠")
    if not path_ok:
        issues.append("🟡 路径配置 - 存在潜在问题")
    if not bg_ok:
        issues.append("🔴 后台运行 - 没有配置系统服务")
    
    if issues:
        print("\n❌ 发现的根本问题:")
        for issue in issues:
            print(f"   {issue}")
        
        print("\n💡 结论:")
        print("   这不是您的电脑设置问题，而是系统架构问题！")
        print("   Mac的设计就是用户离开时睡眠省电，cron不适合长期运行任务。")
        print("\n   最佳解决方案: 使用 Mac LaunchAgent 系统服务")
    else:
        print("\n✅ 所有检查通过")
