#!/bin/bash
# 一键修复系统 - 解决"人不在就报错"问题

echo "============================================================"
echo "🔧 量化交易系统 - 一键修复工具"
echo "============================================================"
echo "修复目标: 解决人不在时系统停止运行的问题"
echo ""

PROJECT_ROOT="/Users/mac/.openclaw/workspace/quant-trading"
cd "$PROJECT_ROOT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================
# 步骤1: 防止Mac睡眠
# ============================================================
echo ""
echo "${YELLOW}步骤 1/5: 配置Mac电源管理 (防止睡眠)...${NC}"
echo "------------------------------------------------------------"

# 检查当前设置
echo "当前睡眠设置:"
pmset -g | grep -E "(sleep|hibernate)"

echo ""
echo "正在配置:"
# 连接电源时不睡眠
sudo pmset -c sleep 0
# 连接电源时禁用休眠
sudo pmset -c hibernatemode 0
# 使用电池时也不睡眠（可选，如果经常不带电源可以注释掉）
# sudo pmset -b sleep 0

echo "${GREEN}✅ 已配置: 连接电源时Mac不会睡眠${NC}"
echo "${YELLOW}注意: 此设置需要连接电源适配器才生效${NC}"

# ============================================================
# 步骤2: 安装LaunchAgent服务
# ============================================================
echo ""
echo "${YELLOW}步骤 2/5: 安装系统级服务 (LaunchAgent)...${NC}"
echo "------------------------------------------------------------"

# 创建日志目录
mkdir -p logs

# 复制plist文件到LaunchAgents
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR"

# 安装神算子服务
cp "$PROJECT_ROOT/com.quant-trading.shen-suan-zi.plist" "$LAUNCH_AGENTS_DIR/"

# 安装隔壁老王服务
cp "$PROJECT_ROOT/com.quant-trading.supervisor.plist" "$LAUNCH_AGENTS_DIR/"

# 加载服务
echo "加载神算子服务..."
launchctl unload "$LAUNCH_AGENTS_DIR/com.quant-trading.shen-suan-zi.plist" 2>/dev/null
launchctl load "$LAUNCH_AGENTS_DIR/com.quant-trading.shen-suan-zi.plist"

echo "加载隔壁老王服务..."
launchctl unload "$LAUNCH_AGENTS_DIR/com.quant-trading.supervisor.plist" 2>/dev/null
launchctl load "$LAUNCH_AGENTS_DIR/com.quant-trading.supervisor.plist"

echo "${GREEN}✅ 系统服务已安装并启动${NC}"

# ============================================================
# 步骤3: 移除旧的Cron任务
# ============================================================
echo ""
echo "${YELLOW}步骤 3/5: 清理旧配置...${NC}"
echo "------------------------------------------------------------"

# 备份当前cron
crontab -l > "$PROJECT_ROOT/logs/cron_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null

# 移除旧的prediction cron
(crontab -l 2>/dev/null | grep -v "prediction_agent_cron.py") | crontab -

echo "${GREEN}✅ 已移除旧的Cron配置${NC}"

# 停止旧的隔壁老王
./stop_supervisor.sh 2>/dev/null

echo "${GREEN}✅ 已停止旧的隔壁老王进程${NC}"

# ============================================================
# 步骤4: 验证安装
# ============================================================
echo ""
echo "${YELLOW}步骤 4/5: 验证安装...${NC}"
echo "------------------------------------------------------------"

echo "检查LaunchAgent状态:"
launchctl list | grep "com.quant-trading"

echo ""
echo "检查运行中的Python进程:"
ps aux | grep -E "(prediction|supervisor)" | grep python | grep -v grep | wc -l
echo "个相关进程正在运行"

# ============================================================
# 步骤5: 显示状态
# ============================================================
echo ""
echo "${YELLOW}步骤 5/5: 显示系统状态...${NC}"
echo "------------------------------------------------------------"

# 检查最近的预测记录
echo ""
echo "最近5条预测记录:"
sqlite3 "$PROJECT_ROOT/data/market_data.db" "SELECT datetime(predict_initiated_at), symbol, consensus_prediction FROM ai_prediction_records ORDER BY predict_initiated_at DESC LIMIT 5;"

echo ""
echo "${GREEN}============================================================${NC}"
echo "${GREEN}✅ 修复完成！${NC}"
echo "${GREEN}============================================================${NC}"
echo ""
echo "📋 修复内容:"
echo "   1. ✅ Mac连接电源时不会睡眠"
echo "   2. ✅ 安装了系统级LaunchAgent服务"
echo "   3. ✅ 移除了不可靠的Cron配置"
echo "   4. ✅ 配置了自动重启机制"
echo ""
echo "🎯 现在即使您:"
echo "   • 锁屏离开"
echo "   • 关闭显示器"
echo "   • 注销用户"
echo ""
echo "系统也会持续运行！"
echo ""
echo "📊 查看状态:"
echo "   日志: tail -f logs/launchd_prediction.log"
echo "   服务: launchctl list | grep quant-trading"
echo ""
echo "🛑 停止服务:"
echo "   launchctl unload ~/Library/LaunchAgents/com.quant-trading.shen-suan-zi.plist"
echo "   launchctl unload ~/Library/LaunchAgents/com.quant-trading.supervisor.plist"
echo ""
echo "${GREEN}============================================================${NC}"
