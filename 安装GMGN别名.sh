#!/bin/bash
# 安装 GMGN 快捷别名到 shell 配置文件

echo "╔══════════════════════════════════════════════════════════╗"
echo "║           GMGN 快捷别名安装工具                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 检测 shell
if [ -n "$ZSH_VERSION" ] || [ "$(basename "$SHELL")" = "zsh" ]; then
    SHELL_TYPE="zsh"
    CONFIG_FILE="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ] || [ "$(basename "$SHELL")" = "bash" ]; then
    SHELL_TYPE="bash"
    CONFIG_FILE="$HOME/.bashrc"
else
    echo "⚠️  无法检测 shell 类型，默认使用 .zshrc"
    SHELL_TYPE="zsh"
    CONFIG_FILE="$HOME/.zshrc"
fi

echo "检测到 Shell: $SHELL_TYPE"
echo "配置文件: $CONFIG_FILE"
echo ""

# 检查是否已安装
if grep -q "GMGN 快捷别名配置" "$CONFIG_FILE" 2>/dev/null; then
    echo "⚠️  GMGN 别名已安装在 $CONFIG_FILE"
    echo ""
    read -p "是否重新安装? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 0
    fi
    # 删除旧配置
    sed -i.bak '/# GMGN 快捷别名配置/,/# GMGN 快捷别名配置结束/d' "$CONFIG_FILE"
    echo "已删除旧配置"
fi

echo ""
echo "📦 安装 GMGN 快捷别名..."

# 添加到配置文件
cat >> "$CONFIG_FILE" << 'EOF'

# ============ GMGN 快捷别名配置 ============
# 加载 GMGN 快捷命令
source "$HOME/.openclaw/workspace/quant-trading/gmgn_aliases.sh" 2>/dev/null || true
# ============ GMGN 快捷别名配置结束 ============

EOF

echo "✅ 别名已添加到 $CONFIG_FILE"
echo ""
echo "🔄 重新加载配置..."

# 尝试立即加载
source "$CONFIG_FILE" 2>/dev/null || true

echo ""
echo "🎉 安装完成！"
echo ""
echo "使用方法:"
echo "   1. 重新打开终端，或运行: source $CONFIG_FILE"
echo "   2. 使用命令: 金狗"
echo ""
echo "📖 查看所有别名: gmgn-help"
echo ""

# 显示预览
echo "🎯 可用快捷命令预览:"
echo "   金狗          - 发现 SOL 热门代币"
echo "   我的持仓      - 查看钱包持仓"
echo "   gmgn-wallet   - 查看所有绑定钱包"
echo "   gmgn-help     - 显示完整帮助"
echo ""
