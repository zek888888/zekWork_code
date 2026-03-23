#!/bin/bash
# 每日自动推文生成脚本
# 运行时间：每天 UTC 12:00 (北京时间 20:00)

WORK_DIR="/Users/mac/.openclaw/workspace/quant-trading"
LOG_FILE="$WORK_DIR/logs/tweet_generator.log"
TWEET_DIR="$WORK_DIR/tweets_generated"

# 确保日志目录存在
mkdir -p "$WORK_DIR/logs"
mkdir -p "$TWEET_DIR"

echo "========================================" >> "$LOG_FILE"
echo "  每日推文生成任务 - $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 运行推文生成器
cd "$WORK_DIR"
python3 auto_tweet_generator.py >> "$LOG_FILE" 2>&1

# 检查是否生成成功
if [ $? -eq 0 ]; then
    echo "✅ 推文生成成功" >> "$LOG_FILE"
    
    # 获取最新生成的文件
    LATEST_A=$(ls -t "$TWEET_DIR"/tweet_*_A.txt 2>/dev/null | head -1)
    
    if [ -n "$LATEST_A" ]; then
        echo "📄 最新推文文件: $LATEST_A" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
        echo "【内容预览】:" >> "$LOG_FILE"
        head -10 "$LATEST_A" >> "$LOG_FILE"
    fi
else
    echo "❌ 推文生成失败" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

# 可选：自动发送推文（需要取消注释）
# LATEST_A=$(ls -t "$TWEET_DIR"/tweet_*_A.txt 2>/dev/null | head -1)
# if [ -n "$LATEST_A" ]; then
#     python3 post_tweet.py --file "$LATEST_A"
# fi
