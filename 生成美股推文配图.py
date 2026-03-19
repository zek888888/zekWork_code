#!/usr/bin/env python3
"""
生成美股推文配图
"""

from PIL import Image, ImageDraw, ImageFont
import os

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

def create_mu_chart():
    """配图1: 美光新高"""
    width, height = 1200, 675
    
    # 绿色渐变背景（上涨氛围）
    img = create_gradient_background(width, height, (20, 40, 30), (30, 80, 60))
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 80)
        font_medium = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 48)
        font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 标题
    draw.text((width//2, 100), "🚀 美光 $MU", fill=(0, 255, 150), font=font_large, anchor="mm")
    
    # 核心信息
    draw.text((width//2, 220), "财报大超预期", fill=(255, 255, 255), font=font_medium, anchor="mm")
    
    # 数据对比
    draw.rounded_rectangle([200, 300, 1000, 450], radius=20, fill=(0, 0, 0, 100))
    
    draw.text((width//2, 350), "EPS: 12.2  vs  预期: 3.54", fill=(0, 255, 100), font=font_small, anchor="mm")
    draw.text((width//2, 420), "营收: 238.6亿  vs  预期: 191.6亿", fill=(0, 255, 100), font=font_small, anchor="mm")
    
    # 底部建议
    draw.text((width//2, 550), "别猜顶，继续盯着 👀", fill=(255, 215, 0), font=font_medium, anchor="mm")
    
    # 装饰：上升箭头
    draw.polygon([(900, 200), (950, 150), (1000, 200)], fill=(0, 255, 100))
    
    return img

def create_market_status():
    """配图2: 市场震荡现状"""
    width, height = 1200, 675
    
    # 黄灰色渐变（震荡/模糊氛围）
    img = create_gradient_background(width, height, (40, 40, 35), (60, 60, 50))
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 72)
        font_medium = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 44)
        font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 32)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 标题
    draw.text((width//2, 100), "💤 美股现状：震荡磨人", fill=(255, 200, 100), font=font_large, anchor="mm")
    
    # 多空对比
    # 多头
    draw.rounded_rectangle([150, 200, 550, 450], radius=15, fill=(0, 100, 50, 150), outline=(0, 200, 100), width=3)
    draw.text((350, 250), "🟢 多头", fill=(0, 255, 100), font=font_medium, anchor="mm")
    draw.text((350, 320), "想涨涨不动", fill=(200, 255, 200), font=font_small, anchor="mm")
    draw.text((350, 380), "支撑还在守", fill=(200, 255, 200), font=font_small, anchor="mm")
    
    # 空头
    draw.rounded_rectangle([650, 200, 1050, 450], radius=15, fill=(100, 30, 30, 150), outline=(255, 100, 100), width=3)
    draw.text((850, 250), "🔴 空头", fill=(255, 100, 100), font=font_medium, anchor="mm")
    draw.text((850, 320), "想跌跌不透", fill=(255, 200, 200), font=font_small, anchor="mm")
    draw.text((850, 380), "阻力压着呢", fill=(255, 200, 200), font=font_small, anchor="mm")
    
    # 中间状态
    draw.text((width//2, 520), "↔️ 结果：横盘震荡，方向不明", fill=(255, 255, 255), font=font_medium, anchor="mm")
    
    # 底部建议
    draw.text((width//2, 600), "操作建议：带好止损，或减仓观望 🛡️", fill=(255, 215, 0), font=font_small, anchor="mm")
    
    return img

def main():
    print("="*60)
    print("生成美股推文配图")
    print("="*60)
    
    output_dir = os.path.expanduser("~/.openclaw/workspace/quant-trading/web-dashboard/static/images")
    os.makedirs(output_dir, exist_ok=True)
    
    # 配图1: 美光新高
    print("\n🎨 生成配图1: 美光财报亮点...")
    img1 = create_mu_chart()
    path1 = os.path.join(output_dir, "mu_earnings_0318.png")
    img1.save(path1, quality=95)
    print(f"   ✅ {path1}")
    
    # 配图2: 市场震荡
    print("\n🎨 生成配图2: 市场震荡现状...")
    img2 = create_market_status()
    path2 = os.path.join(output_dir, "market_choppy_0318.png")
    img2.save(path2, quality=95)
    print(f"   ✅ {path2}")
    
    print("\n" + "="*60)
    print("✅ 配图生成完成!")
    print("="*60)
    print("\n访问地址:")
    print(f"  1. http://localhost:5000/static/images/mu_earnings_0318.png")
    print(f"  2. http://localhost:5000/static/images/market_choppy_0318.png")

if __name__ == "__main__":
    main()
