#!/bin/bash
# 提取YouTube视频文案
# 使用方法: ./提取YouTube文案.sh <视频URL>

VIDEO_URL="$1"

if [ -z "$VIDEO_URL" ]; then
    echo "用法: $0 <YouTube视频URL>"
    echo "示例: $0 'https://www.youtube.com/watch?v=W6U4AtAZL3o'"
    exit 1
fi

echo "=========================================="
echo "YouTube 文案提取工具"
echo "=========================================="

# 检查并安装依赖
check_install() {
    if ! command -v "$1" &> /dev/null; then
        echo "正在安装 $1..."
        if [ "$1" = "yt-dlp" ]; then
            brew install yt-dlp 2>/dev/null || pip3 install yt-dlp
        elif [ "$1" = "youtube-transcript-api" ]; then
            pip3 install youtube-transcript-api
        fi
    fi
}

echo ""
echo "请选择提取方式:"
echo "1. yt-dlp (下载字幕文件)"
echo "2. youtube-transcript-api (直接获取文本)"
echo "3. 手动教程"
read -p "输入选项 (1-3): " choice

case $choice in
    1)
        check_install yt-dlp
        echo ""
        echo "正在提取字幕..."
        
        # 创建输出目录
        OUTPUT_DIR="$HOME/Downloads/YoutubeTranscripts"
        mkdir -p "$OUTPUT_DIR"
        
        # 提取视频ID
        VIDEO_ID=$(echo "$VIDEO_URL" | grep -o 'v=[^&]*' | cut -d= -f2)
        
        # 下载字幕
        yt-dlp --list-subs "$VIDEO_URL"
        
        echo ""
        echo "下载英文字幕..."
        yt-dlp --write-auto-sub --sub-langs en --skip-download \
               -o "$OUTPUT_DIR/%(title)s.%(ext)s" "$VIDEO_URL"
        
        # 转换为文本
        find "$OUTPUT_DIR" -name "*.vtt" -o -name "*.srt" | head -1 | while read file; do
            echo ""
            echo "✅ 字幕已保存: $file"
            
            # 提取纯文本
            TEXT_FILE="${file%.*}.txt"
            grep -v '^[0-9]*$' "$file" | grep -v '^$' | grep -v '-->' > "$TEXT_FILE"
            echo "✅ 纯文本已保存: $TEXT_FILE"
            
            echo ""
            echo "文案预览:"
            head -50 "$TEXT_FILE"
        done
        ;;
        
    2)
        check_install youtube-transcript-api
        echo ""
        echo "正在提取文案..."
        
        python3 << EOF
from youtube_transcript_api import YouTubeTranscriptApi
import re
import sys

url = "$VIDEO_URL"
video_id = re.search(r'v=([^&]+)', url).group(1) if 'v=' in url else url

try:
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    
    print("\\n可用字幕:")
    for t in transcript_list:
        print(f"  - {t.language} ({t.language_code})")
    
    # 获取字幕
    try:
        transcript = transcript_list.find_transcript(['zh', 'en'])
    except:
        transcript = list(transcript_list)[0]
    
    data = transcript.fetch()
    
    # 输出文件
    output = f"/tmp/youtube_{video_id}_文案.txt"
    with open(output, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\\n")
        f.write(f"视频文案提取\\n")
        f.write(f"视频ID: {video_id}\\n")
        f.write("="*60 + "\\n\\n")
        
        full_text = ""
        for entry in data:
            text = entry['text']
            start = entry['start']
            f.write(f"[{start:.1f}s] {text}\\n")
            full_text += text + " "
        
        f.write("\\n" + "="*60 + "\\n")
        f.write("完整文案:\\n")
        f.write(full_text)
    
    print(f"\\n✅ 已保存: {output}")
    print(f"\\n文案预览 (前500字):")
    print(full_text[:500])
    
except Exception as e:
    print(f"❌ 错误: {e}")
EOF
        ;;
        
    3)
        echo ""
        echo "📖 手动提取教程:"
        echo ""
        echo "方法1 - YouTube自带字幕:"
        echo "  1. 打开视频页面"
        echo "  2. 点击视频下方的 '...' (更多)"
        echo "  3. 选择 '显示转录稿'"
        echo "  4. 点击 '复制' 按钮"
        echo ""
        echo "方法2 - 在线工具:"
        echo "  1. 访问 https://downsub.com/"
        echo "  2. 粘贴视频链接"
        echo "  3. 下载字幕文件"
        echo ""
        ;;
        
    *)
        echo "无效选项"
        exit 1
        ;;
esac
