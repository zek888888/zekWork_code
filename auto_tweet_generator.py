#!/usr/bin/env python3
"""
自动化推文生成系统
每日自动获取BTC、黄金、原油、特斯拉、微软价格，生成推文
作者：战颅将军
版本：1.0
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime

class PriceFetcher:
    """价格获取器"""
    
    @staticmethod
    def get_btc_price():
        """从币安获取BTC价格"""
        try:
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                return float(data['price'])
        except Exception as e:
            print(f"获取BTC价格失败: {e}")
            return None
    
    @staticmethod
    def get_gold_price():
        """获取黄金价格（美元/盎司）"""
        try:
            # 使用GoldAPI或替代方案
            # 这里使用一个免费的替代API
            url = "https://api.metals.live/v1/spot"
            req = urllib.request.Request(url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                # 返回黄金价格
                if isinstance(data, dict) and 'gold' in data:
                    return float(data['gold'])
                elif isinstance(data, list) and len(data) > 0:
                    return float(data[0].get('gold', 0))
        except Exception as e:
            print(f"获取黄金价格失败: {e}")
            # 备用：使用Yahoo Finance方式
            return PriceFetcher._get_yahoo_price("GC=F")  # 黄金期货
    
    @staticmethod
    def get_oil_price():
        """获取原油价格（WTI）"""
        try:
            # WTI原油期货
            return PriceFetcher._get_yahoo_price("CL=F")
        except Exception as e:
            print(f"获取原油价格失败: {e}")
            return None
    
    @staticmethod
    def get_tesla_price():
        """获取特斯拉股价"""
        try:
            return PriceFetcher._get_yahoo_price("TSLA")
        except Exception as e:
            print(f"获取特斯拉价格失败: {e}")
            return None
    
    @staticmethod
    def get_microsoft_price():
        """获取微软股价"""
        try:
            return PriceFetcher._get_yahoo_price("MSFT")
        except Exception as e:
            print(f"获取微软价格失败: {e}")
            return None
    
    @staticmethod
    def _get_yahoo_price(symbol):
        """从Yahoo Finance获取价格"""
        try:
            # Yahoo Finance API
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                result = data['chart']['result'][0]
                price = result['meta']['regularMarketPrice']
                return float(price)
        except Exception as e:
            print(f"Yahoo Finance获取{symbol}失败: {e}")
            return None


class TweetGenerator:
    """推文生成器"""
    
    def __init__(self, prices):
        self.prices = prices
        self.date_str = datetime.now().strftime("%m月%d日")
    
    def generate_template_a(self):
        """生成版本A：硬核痞气版"""
        btc = self.prices.get('btc', '未知')
        gold = self.prices.get('gold', '未知')
        oil = self.prices.get('oil', '未知')
        tsla = self.prices.get('tesla', '未知')
        msft = self.prices.get('microsoft', '未知')
        
        return f"""【别TM瞎买了！{self.date_str}市场已经变天了】

今天一看盘，四个大爷（BTC、黄金、石油、美股）各玩各的，但逻辑串起来就一个结论：疯狗行情结束，接下来拼脑子了。

BTC现在${btc:,.0f}。
硬资产故事又被炒冷饭，一堆人喊避险。我呸！当所有人都喊避险时，还避险个锤子？现在这种全民抱团，分明是"互相取暖怕冻死"。BTC已从"暴富彩票"变成"债券备胎"，拿着可以，但别指望翻十倍，年化20%就该磕头谢恩了。

黄金现在${gold:,.0f}/盎司。
现在进去就是给庄家抬轿。有人说能避险？避个屁！十年不涨，通胀都能啃成骨头。买黄金是"慢性自杀式存款"，不如存银行。

石油现在${oil:,.0f}。
地缘一紧张就暴涨，缓和就暴跌。但看清楚，全球搞新能源，石油长期逻辑是downward。短期撸波段可以，长期持有？当传家宝传给孙子？

美股：特斯拉${tsla:,.0f}，微软${msft:,.0f}。
一帮人吵特斯拉拆股，想历史重演？醒醒吧，2020年是美联储疯狂印钱，现在钱紧，环境完全不同。微软被喊归零更是笑话，这种印钞机公司，跌下来是送钱。

看明白了吗？钱变贵了，乱买乱涨时代结束了。

策略：
1. BTC当债券拿着，别做梦暴富
2. 黄金石油不碰，进去就是接盘  
3. 美股只买印钞机公司，跌了就加仓
4. 留一半现金，等恐慌捡尸体

前两年赚钱是老天爷赏饭，现在赏饭结束了。真刀真枪的时候到了，没本事的趁早离场。

#BTC #黄金 #石油 #美股 #投资真相"""

    def generate_template_b(self):
        """生成版本B：街头江湖版"""
        btc = self.prices.get('btc', '未知')
        gold = self.prices.get('gold', '未知')
        oil = self.prices.get('oil', '未知')
        tsla = self.prices.get('tesla', '未知')
        msft = self.prices.get('microsoft', '未知')
        
        return f"""【醒醒吧！{self.date_str}游戏规则变了】

今天这市场，四个大哥同时在喊话：傻钱不好赚了。

BTC现在${btc:,.0f}。
大V喊硬资产，我笑了。当菜市场大妈都问怎么买的时候，还避险？避险资产是偷偷涨，现在是全民抱团怕死在一起。

黄金${gold:,.0f}/盎司。
现在买的，我敬你是条韭菜。十年不涨，买进去就是站岗。你说避险？避个锤子！通胀都能避成穷人。

石油${oil:,.0f}。
地缘冲突一响就涨，缓和就跌。但长远看，全世界搞电动车，石油需求往下走。短期撸一把可以，长期持有等于自杀。

美股：特斯拉${tsla:,.0f}，微软${msft:,.0f}。
特斯拉那帮人研究拆股历史，想重演？脑子进水了吧！那时候是疫情放水，现在钱紧，能一样吗？

看清楚了：钱紧了，乱买必亏。

我的态度：
- BTC：拿着别动，但别指望发财
- 黄金石油：滚蛋，不碰
- 美股：只买能印钞的
- 现金：留一半，等血流成河进场

前两年赚钱是运气，现在赚钱是实力。没实力的，赶紧退场保命。

#比特币 #黄金 #美股 #石油 #投资真相"""

    def generate_template_c(self):
        """生成版本C：冷静分析版"""
        btc = self.prices.get('btc', '未知')
        gold = self.prices.get('gold', '未知')
        oil = self.prices.get('oil', '未知')
        tsla = self.prices.get('tesla', '未知')
        msft = self.prices.get('microsoft', '未知')
        
        return f"""【{self.date_str}市场分析：变天了】

BTC、黄金、石油、美股四个主流资产同时释放信号：钱变贵了。

BTC：${btc:,.0f}
硬资产叙事被炒，但悖论是：当所有人都认同它是避险资产时，它还能避险吗？全民共识更像是"抱团取暖"。BTC已完成从"高风险投机"到"低风险配置"的转型，拿着可以，但收益预期要降到年化15-20%。

黄金：${gold:,.0f}/盎司
当前价位性价比极低。黄金不会归零，但可能"赢了价格输了时间"——十年不涨，跑输通胀。现在进场等于给前期多头抬轿。

石油：${oil:,.0f}
地缘冲突驱动短期波动，但长期逻辑向下。全球能源转型，石油需求峰值已过。短线可博弈，长线不明智。

美股：特斯拉${tsla:,.0f}，微软${msft:,.0f}
特斯拉拆股历史被频繁引用，但历史不会简单重复。2020-2022年是流动性泛滥期，当前是紧缩周期，宏观环境完全不同。

微软被部分资金看空，但基于现金流和护城河分析，这种质量公司跌下来是机会。

关联逻辑：
四个资产同时异动，指向流动性拐点。美联储从放水转向收水，资产定价从"情绪驱动"转向"业绩驱动"。

策略：
1. BTC：降低预期，配置持有
2. 黄金/石油：回避，性价比差
3. 美股：精选现金流稳定的优质公司
4. 现金储备：保持30-50%，等待错杀机会

市场已进入"结构牛"阶段，乱买必亏，认知决定收益。

#BTC #黄金 #石油 #美股 #市场分析"""


def main():
    """主函数"""
    print("="*60)
    print("  自动化推文生成系统")
    print(f"  日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)
    print()
    
    # 获取价格
    print("【获取实时价格】...")
    fetcher = PriceFetcher()
    
    prices = {
        'btc': fetcher.get_btc_price(),
        'gold': fetcher.get_gold_price(),
        'oil': fetcher.get_oil_price(),
        'tesla': fetcher.get_tesla_price(),
        'microsoft': fetcher.get_microsoft_price()
    }
    
    print(f"  BTC: ${prices['btc']:,.2f}" if prices['btc'] else "  BTC: 获取失败")
    print(f"  黄金: ${prices['gold']:,.2f}" if prices['gold'] else "  黄金: 获取失败")
    print(f"  石油: ${prices['oil']:,.2f}" if prices['oil'] else "  石油: 获取失败")
    print(f"  特斯拉: ${prices['tesla']:,.2f}" if prices['tesla'] else "  特斯拉: 获取失败")
    print(f"  微软: ${prices['microsoft']:,.2f}" if prices['microsoft'] else "  微软: 获取失败")
    print()
    
    # 检查是否有获取失败的数据
    failed = [k for k, v in prices.items() if v is None]
    if failed:
        print(f"⚠️ 警告: {', '.join(failed)} 获取失败，使用备用数据或手动填写")
        print()
    
    # 生成推文
    print("【生成推文】...")
    generator = TweetGenerator(prices)
    
    templates = {
        'A': generator.generate_template_a(),
        'B': generator.generate_template_b(),
        'C': generator.generate_template_c()
    }
    
    # 保存到文件
    output_dir = "/Users/mac/.openclaw/workspace/quant-trading/tweets_generated"
    os.makedirs(output_dir, exist_ok=True)
    
    date_str = datetime.now().strftime("%m%d")
    for name, content in templates.items():
        filename = f"{output_dir}/tweet_{date_str}_{name}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  版本{name}已保存: {filename}")
    
    print()
    print("="*60)
    print("✅ 推文生成完成！")
    print("="*60)
    print()
    print("【版本A预览】(硬核痞气版):")
    print(templates['A'][:300] + "...")
    print()
    print("使用说明:")
    print("  1. 查看生成的推文文件")
    print("  2. 选择合适版本")
    print("  3. 使用 post_tweet.py 发布")
    print()
    print(f"  文件位置: {output_dir}/")


if __name__ == '__main__':
    main()
