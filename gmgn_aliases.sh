#!/bin/bash
# GMGN 快捷别名配置
# 使用方式: source gmgn_aliases.sh

# 基础代理设置
export GMGN_PROXY="http://127.0.0.1:7897"
export https_proxy="$GMGN_PROXY"
export http_proxy="$GMGN_PROXY"
export HTTPS_PROXY="$GMGN_PROXY"
export HTTP_PROXY="$GMGN_PROXY"

# 工作目录
export GMGN_DIR="$HOME/.config/gmgn"

# ============ 核心别名 ============

# 基础命令
alias gmgn='cd "$GMGN_DIR" && https_proxy="$GMGN_PROXY" gmgn-cli'

# 钱包相关
alias gmgn-wallet='gmgn portfolio info'
alias gmgn-holdings='gmgn portfolio holdings'
alias gmgn-activity='gmgn portfolio activity'
alias gmgn-stats='gmgn portfolio stats'

# 市场数据
alias gmgn-trending='gmgn market trending'
alias gmgn-kline='gmgn market kline'

# 代币信息
alias gmgn-token='gmgn token info'
alias gmgn-security='gmgn token security'
alias gmgn-pool='gmgn token pool'
alias gmgn-holders='gmgn token holders'

# ============ 链特定快捷命令 ============

# SOL 链快捷命令
alias gmgn-sol='gmgn --chain sol'
alias gmgn-sol-wallet='gmgn portfolio holdings --chain sol --wallet AJALQx1j5XJB5aHdXC2CMQfVWehAv6YFkhBFk7MYx4qU'
alias gmgn-sol-trending='gmgn market trending --chain sol --interval 1h --limit 10'
alias gmgn-sol-top='gmgn market trending --chain sol --interval 1h --order-by volume --limit 20'

# BSC 链快捷命令
alias gmgn-bsc='gmgn --chain bsc'
alias gmgn-bsc-wallet='gmgn portfolio holdings --chain bsc --wallet 0x53c167e3ca0785bba3e58a5778efa3337b07f45a'
alias gmgn-bsc-trending='gmgn market trending --chain bsc --interval 1h --limit 10'

# Base 链快捷命令
alias gmgn-base='gmgn --chain base'
alias gmgn-base-wallet='gmgn portfolio holdings --chain base --wallet 0x53c167e3ca0785bba3e58a5778efa3337b07f45a'
alias gmgn-base-trending='gmgn market trending --chain base --interval 1h --limit 10'

# ============ 实用功能别名 ============

# 热门代币发现
alias 金狗='gmgn market trending --chain sol --interval 1h --order-by volume --limit 20 --filter not_honeypot --filter has_social'
alias 金狗1h='gmgn market trending --chain sol --interval 1h --order-by volume --limit 20'
alias 金狗5m='gmgn market trending --chain sol --interval 1h --order-by change5m --limit 20'
alias 金狗聪明钱='gmgn market trending --chain sol --interval 1h --order-by smart_degen_count --limit 20'

# Pump.fun 代币
alias pump='gmgn market trending --chain sol --interval 1h --platform Pump.fun --limit 20'

# 安全代币筛选
alias 安全狗='gmgn market trending --chain sol --interval 1h --filter not_honeypot --filter verified --filter renounced --limit 20'

# 查看我的持仓
alias 我的持仓='gmgn portfolio holdings --chain sol --wallet AJALQx1j5XJB5aHdXC2CMQfVWehAv6YFkhBFk7MYx4qU'
alias 我的交易='gmgn portfolio activity --chain sol --wallet AJALQx1j5XJB5aHdXC2CMQfVWehAv6YFkhBFk7MYx4qU'
alias 我的统计='gmgn portfolio stats --chain sol --wallet AJALQx1j5XJB5aHdXC2CMQfVWehAv6YFkhBFk7MYx4qU'

# ============ 代币地址常量 ============

# SOL 链常用代币
export SOL_TOKEN="So11111111111111111111111111111111111111112"
export SOL_USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# BSC 链常用代币
export BSC_BNB="0x0000000000000000000000000000000000000000"
export BSC_USDC="0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"
export BSC_USDT="0x55d398326f99059ff775485246999027b3197955"

# Base 链常用代币
export BASE_ETH="0x0000000000000000000000000000000000000000"
export BASE_USDC="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# ============ 帮助信息 ============

alias gmgn-help='echo "
🚀 GMGN 快捷命令

📊 市场数据:
  金狗          - SOL 热门代币 (按交易量)
  金狗1h        - SOL 1小时热门
  金狗5m        - SOL 5分钟涨幅榜
  金狗聪明钱    - 聪明钱关注的代币
  pump          - Pump.fun 代币
  安全狗        - 安全代币筛选

💼 钱包管理:
  gmgn-wallet   - 查看绑定钱包
  我的持仓      - SOL 链持仓
  我的交易      - SOL 链交易历史
  我的统计      - SOL 链交易统计

🔍 代币分析:
  gmgn-token <地址>     - 代币信息
  gmgn-security <地址>  - 安全分析
  gmgn-pool <地址>      - 流动性池
  gmgn-holders <地址>   - 持仓地址

⛓️ 链特定命令:
  gmgn-sol      - SOL 链命令
  gmgn-bsc      - BSC 链命令
  gmgn-base     - Base 链命令

💰 交易 (⚠️ 真实交易):
  gmgn swap ... - 执行兑换

📖 更多帮助: gmgn-cli --help
"'

# 显示加载成功信息
echo "✅ GMGN 快捷别名已加载！"
echo ""
echo "🎯 常用命令:"
echo "   金狗     - 发现热门代币"
echo "   我的持仓 - 查看钱包持仓"
echo "   gmgn-help - 显示完整帮助"
echo ""
