# GMGN 快捷别名

## ✅ 安装完成

快捷别名已安装到 `~/.zshrc`

## 🚀 使用方法

重新打开终端或运行：
```bash
source ~/.zshrc
```

## 📋 可用别名

### 核心命令
```bash
gmgn           # GMGN CLI 基础命令
gmgn-wallet    # 查看绑定钱包
gmgn-help      # 显示帮助
```

### 快捷命令
```bash
# "金狗" - 发现热门代币
alias jg='cd ~/.config/gmgn && https_proxy=http://127.0.0.1:7897 gmgn-cli market trending --chain sol --interval 1h --orderby volume --limit 20'

# "我的持仓"
alias myhold='cd ~/.config/gmgn && https_proxy=http://127.0.0.1:7897 gmgn-cli portfolio holdings --chain sol --wallet AJALQx1j5XJB5aHdXC2CMQfVWehAv6YFkhBFk7MYx4qU'
```

## 📝 手动使用

由于中文别名在某些 shell 中可能有问题，建议直接使用：

```bash
# 设置代理
export https_proxy=http://127.0.0.1:7897

# 热门代币
cd ~/.config/gmgn
gmgn-cli market trending --chain sol --interval 1h --orderby volume --limit 20

# 查看钱包
gmgn-cli portfolio info
```

## 🎯 常用命令速查

```bash
# 热门代币 (按交易量)
gmgn-cli market trending --chain sol --interval 1h --orderby volume --limit 20

# 热门代币 (按涨幅)
gmgn-cli market trending --chain sol --interval 1h --orderby change1h --limit 20

# Pump.fun 代币
gmgn-cli market trending --chain sol --interval 1h --platform Pump.fun --limit 20

# 代币信息
gmgn-cli token info --chain sol --address <token_address>

# 安全分析
gmgn-cli token security --chain sol --address <token_address>

# 钱包持仓
gmgn-cli portfolio holdings --chain sol --wallet AJALQx1j5XJB5aHdXC2CMQfVWehAv6YFkhBFk7MYx4qU
```

## 📁 相关文件

| 文件 | 路径 |
|------|------|
| 别名脚本 | `~/.openclaw/workspace/quant-trading/gmgn_aliases.sh` |
| 配置文件 | `~/.config/gmgn/.env` |
| Python 客户端 | `~/.openclaw/workspace/quant-trading/gmgn_client.py` |

## ✅ 测试

运行测试：
```bash
cd ~/.config/gmgn
export https_proxy=http://127.0.0.1:7897
gmgn-cli portfolio info
```
