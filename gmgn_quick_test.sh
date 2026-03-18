#!/bin/bash
# GMGN 快速测试脚本

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║           GMGN + Clash 代理快速测试                      ║"
echo "╚══════════════════════════════════════════════════════════╝"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "1️⃣  检查 Clash 代理..."
if lsof -Pi :7897 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Clash 代理端口 7897 正常${NC}"
else
    echo -e "   ${RED}❌ Clash 代理端口 7897 未检测到${NC}"
    echo "      请确认 Clash 正在运行"
    exit 1
fi

echo ""
echo "2️⃣  检测代理出口 IP..."
PROXY_IP=$(curl -x http://127.0.0.1:7897 -s https://v4.ident.me/ 2>/dev/null || echo "")
if [ -n "$PROXY_IP" ]; then
    echo -e "   ${GREEN}✅ 代理出口 IP: $PROXY_IP${NC}"
else
    echo -e "   ${RED}❌ 无法获取代理 IP${NC}"
    exit 1
fi

echo ""
echo "3️⃣  检查 API Key..."
if [ -f ~/.config/gmgn/.env ]; then
    API_KEY=$(grep "GMGN_API_KEY" ~/.config/gmgn/.env | cut -d'=' -f2 | head -1)
    if [ -n "$API_KEY" ] && [ "$API_KEY" != "your_gmgn_api_key_here" ]; then
        echo -e "   ${GREEN}✅ API Key 已配置${NC}"
    else
        echo -e "   ${RED}❌ API Key 未配置${NC}"
        exit 1
    fi
else
    echo -e "   ${RED}❌ 配置文件不存在${NC}"
    exit 1
fi

echo ""
echo "4️⃣  测试 GMGN API 连接..."
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897
export https_proxy=http://127.0.0.1:7897

cd ~/.config/gmgn
if gmgn-cli portfolio info >/dev/null 2>&1; then
    echo -e "   ${GREEN}✅ GMGN API 连接成功！${NC}"
    echo ""
    echo "🎉 所有配置正常，可以开始使用 GMGN！"
    echo ""
    gmgn-cli portfolio info 2>&1 | head -20
else
    echo -e "   ${RED}❌ GMGN API 连接失败${NC}"
    echo ""
    echo "💡 可能原因："
    echo "   1. 白名单未配置或正在审核"
    echo "   2. 需要将 IP $PROXY_IP 添加到 GMGN 白名单"
    echo ""
    echo "📋 操作步骤："
    echo "   1. 访问 https://gmgn.ai/"
    echo "   2. 进入设置 → API 管理"
    echo "   3. 添加白名单 IP: $PROXY_IP"
    echo "   4. 等待几分钟后重试"
    exit 1
fi
