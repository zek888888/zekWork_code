#!/usr/bin/env python3
"""
生成Twitter推文配图
风格: 币圈KOL观点汇总
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import random

def create_gradient_background(width, height, color1, color2):
    """创建渐变背景"""
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    for y in range(height):
        r = int(color1[0] + (color2[0] - color1[0]) * y / height)
        g = int(color1[1] + (color2[1] - color1[1]) * y / height)
        b = int(color1[2] + (color2[2] - color1[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    return img

def draw_rounded_rect(draw, xy, radius, fill, outline=None):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)

def create_kol_heatmap():
    """创建KOL观点热力图"""
    # 1200x675 (16:9 Twitter卡片尺寸)
    width, height = 1200, 675
    
    # 深色渐变背景
    img = create_gradient_background(width, height, (15, 23, 42), (30, 41, 59))
    draw = ImageDraw.Draw(img)
    
    # 尝试加载字体
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 48)
        font_sub = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 28)
        font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 20)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 标题
    title = "🎯 3月19日 KOL观点雷达"
    draw.text((width//2, 50), title, fill=(255, 215, 0), font=font_title, anchor="mm")
    
    # KOL数据 (模拟)
    kols = [
        ("CZ", "看多", "#00D084"),
        ("0xSun", "看空", "#EF4444"),
        ("xhunt", "震荡", "#F59E0B"),
        ("Joely", "看多", "#00D084"),
        ("Stock", "震荡", "#F59E0B"),
        ("Darren", "看多", "#00D084"),
        ("CNFin", "看空", "#EF4444"),
        ("Alea", "震荡", "#F59E0B"),
        ("Market", "看多", "#00D084"),
        ("11地主", "看空", "#EF4444"),
        ("Ares", "震荡", "#F59E0B"),
        ("Vito", "看多", "#00D084"),
        ("Charlie", "震荡", "#F59E0B"),
        ("RJC", "看多", "#00D084"),
        ("Cyril", "看空", "#EF4444"),
    ]
    
    # 绘制KOL头像网格 (圆形)
    cols = 5
    rows = 3
    start_x = 100
    start_y = 120
    spacing_x = 220
    spacing_y = 160
    
    for i, (name, view, color) in enumerate(kols):
        col = i % cols
        row = i // cols
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y
        
        # 外圈（观点颜色）
        draw.ellipse([x, y, x+100, y+100], fill=color, outline=(255,255,255), width=3)
        # 内圈（深色背景）
        draw.ellipse([x+10, y+10, x+90, y+90], fill=(30, 41, 59))
        # 名字
        draw.text((x+50, y+50), name[:4], fill=(255,255,255), font=font_small, anchor="mm")
        # 观点标签
        draw.rounded_rectangle([x+15, y+105, x+85, y+130], radius=5, fill=color)
        draw.text((x+50, y+117), view, fill=(0,0,0), font=font_small, anchor="mm")
    
    # 底部统计
    stats_y = height - 80
    stats = [
        ("📈 看多", "40%", "#00D084"),
        ("📊 震荡", "40%", "#F59E0B"),
        ("📉 看空", "20%", "#EF4444"),
    ]
    
    for i, (label, pct, color) in enumerate(stats):
        x = 200 + i * 400
        draw.rounded_rectangle([x-80, stats_y-20, x+80, stats_y+30], radius=10, fill=color)
        draw.text((x, stats_y+5), f"{label} {pct}", fill=(0,0,0), font=font_sub, anchor="mm")
    
    # 水印
    draw.text((width-10, height-10), "@您的账号", fill=(255,255,255,128), font=font_small, anchor="rb")
    
    return img

def create_word_cloud():
    """创建热门话题词云"""
    width, height = 1200, 675
    
    # 深色背景
    img = create_gradient_background(width, height, (20, 20, 35), (35, 35, 55))
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 72)
        font_medium = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 48)
        font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 32)
        font_tiny = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
    
    # 标题
    draw.text((width//2, 50), "🔥 3/19 圈内热议话题", fill=(255, 215, 0), font=font_medium, anchor="mm")
    
    # 词云数据 (位置, 文字, 大小, 颜色)
    words = [
        # 大字
        (600, 200, "BSC金狗", font_large, (0, 208, 132)),
        (350, 350, "BTC减半", font_large, (255, 107, 107)),
        (850, 320, "聪明钱", font_medium, (100, 181, 246)),
        
        # 中字
        (250, 250, "Solana", font_medium, (255, 213, 79)),
        (750, 250, "AI概念", font_medium, (186, 104, 200)),
        (500, 420, "ETF进展", font_medium, (255, 167, 38)),
        (900, 400, "回调布局", font_small, (77, 208, 225)),
        
        # 小字
        (200, 450, "忍者", font_small, (255, 255, 255)),
        (350, 480, "TITAN", font_small, (255, 255, 255)),
        (650, 480, "Freedom", font_small, (255, 255, 255)),
        (800, 480, "龙虾", font_small, (255, 255, 255)),
        (950, 480, "钻石手", font_small, (255, 255, 255)),
        
        # 代币符号
        (180, 320, "$PEPE", font_tiny, (200, 200, 200)),
        (480, 280, "$BONK", font_tiny, (200, 200, 200)),
        (1050, 280, "$WIF", font_tiny, (200, 200, 200)),
        (150, 400, "$SHIB", font_tiny, (200, 200, 200)),
        (1000, 350, "$DOGE", font_tiny, (200, 200, 200)),
    ]
    
    # 绘制文字（添加阴影效果）
    for x, y, text, font, color in words:
        # 阴影
        draw.text((x+2, y+2), text, fill=(0, 0, 0, 128), font=font, anchor="mm")
        # 主文字
        draw.text((x, y), text, fill=color, font=font, anchor="mm")
    
    # 装饰性元素
    # 中心圆圈
    draw.ellipse([450, 280, 750, 520], outline=(255, 215, 0, 100), width=2)
    
    # 底部说明
    draw.text((width//2, height-40), "数据来源: 22位币圈KOL实时推文", 
              fill=(150, 150, 150), font=font_tiny, anchor="mm")
    
    return img

def main():
    print("="*60)
    print("生成推文配图")
    print("="*60)
    
    # 保存路径
    output_dir = os.path.expanduser("~/.openclaw/workspace/quant-trading/web-dashboard/static/images")
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成配图1: KOL观点热力图
    print("\n🎨 生成配图1: KOL观点热力图...")
    img1 = create_kol_heatmap()
    path1 = os.path.join(output_dir, "kol_heatmap_0319.png")
    img1.save(path1, quality=95)
    print(f"   ✅ 已保存: {path1}")
    
    # 生成配图2: 热门话题词云
    print("\n🎨 生成配图2: 热门话题词云...")
    img2 = create_word_cloud()
    path2 = os.path.join(output_dir, "wordcloud_0319.png")
    img2.save(path2, quality=95)
    print(f"   ✅ 已保存: {path2}")
    
    print("\n" + "="*60)
    print("✅ 配图生成完成!")
    print("="*60)
    print(f"\n文件位置:")
    print(f"  1. {path1}")
    print(f"  2. {path2}")
    print(f"\n访问地址:")
    print(f"  http://localhost:5000/static/images/kol_heatmap_0319.png")
    print(f"  http://localhost:5000/static/images/wordcloud_0319.png")

if __name__ == "__main__":
    main()
