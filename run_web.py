#!/usr/bin/env python3
"""
启动Web展示服务
"""
import os
import sys

PROJECT_ROOT = "/Users/mac/.openclaw/workspace/quant-trading"
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

# 使用绝对路径导入
exec(open(f"{PROJECT_ROOT}/web_trade.py").read())
