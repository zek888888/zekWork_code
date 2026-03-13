#!/usr/bin/env python3
"""
Agent-maintenance: GitHub 自动维护脚本
功能: 定时提交本地更改到GitHub
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

# 项目路径
PROJECT_PATH = Path.home() / ".openclaw/workspace/quant-trading"
LOG_FILE = PROJECT_PATH / ".agents/agent-maintenance/maintenance.log"

def log(message):
    """记录日志"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    # 追加到日志文件
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_msg + "\n")

def run_git_command(cmd, cwd=None):
    """执行Git命令"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_git_status():
    """检查Git状态"""
    success, stdout, stderr = run_git_command(['git', 'status', '--porcelain'])
    if not success:
        log(f"❌ 检查Git状态失败: {stderr}")
        return None
    
    # 解析状态
    changes = []
    for line in stdout.strip().split('\n'):
        if line:
            status = line[:2]
            file = line[3:]
            changes.append({'status': status, 'file': file})
    
    return changes

def sync_to_github():
    """同步本地更改到GitHub"""
    log("="*60)
    log("Agent-maintenance: GitHub 自动同步任务开始")
    log("="*60)
    
    # 1. 检查Git状态
    log("\n[1/5] 检查Git状态...")
    changes = check_git_status()
    
    if changes is None:
        log("❌ Git状态检查失败，退出")
        return False
    
    if not changes:
        log("✓ 没有需要提交的更改")
        log("\n" + "="*60)
        log("同步完成: 无需更新")
        log("="*60)
        return True
    
    log(f"发现 {len(changes)} 个文件更改:")
    for change in changes:
        log(f"  [{change['status']}] {change['file']}")
    
    # 2. 添加所有更改
    log("\n[2/5] 添加更改到暂存区...")
    success, stdout, stderr = run_git_command(['git', 'add', '-A'])
    if not success:
        log(f"❌ git add 失败: {stderr}")
        return False
    log("✓ 已添加所有更改")
    
    # 3. 创建提交
    log("\n[3/5] 创建提交...")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"Auto sync: {timestamp}"
    
    success, stdout, stderr = run_git_command(['git', 'commit', '-m', commit_msg])
    if not success:
        log(f"❌ git commit 失败: {stderr}")
        return False
    
    # 提取提交哈希
    commit_hash = stdout.split()[1] if stdout else "unknown"
    log(f"✓ 已创建提交: {commit_hash}")
    
    # 4. 推送到GitHub
    log("\n[4/5] 推送到GitHub...")
    success, stdout, stderr = run_git_command(['git', 'push', 'origin', 'main'])
    if not success:
        log(f"❌ git push 失败: {stderr}")
        return False
    log("✓ 已推送到GitHub")
    
    # 5. 验证推送
    log("\n[5/5] 验证推送状态...")
    success, stdout, stderr = run_git_command(['git', 'status'])
    if success and "Your branch is up to date" in stdout:
        log("✓ 推送验证成功")
    else:
        log("⚠️ 推送状态异常")
    
    log("\n" + "="*60)
    log(f"✅ 同步完成: {len(changes)} 个文件已提交并推送")
    log("="*60)
    
    return True

def main():
    """主函数"""
    # 确保日志目录存在
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 检查项目目录
    if not PROJECT_PATH.exists():
        log(f"❌ 项目路径不存在: {PROJECT_PATH}")
        sys.exit(1)
    
    # 执行同步
    success = sync_to_github()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
