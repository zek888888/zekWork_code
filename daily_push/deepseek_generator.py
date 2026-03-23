#!/usr/bin/env python3
"""
DeepSeek内容生成模块
调用DeepSeek API整理KOL数据和价格信息，生成推文
"""

import os
import json
import urllib.request
from datetime import datetime

# DeepSeek API配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = "sk-612745625de4483586baaf1397799cc6"


class DeepSeekGenerator:
    """DeepSeek内容生成器"""
    
    def __init__(self):
        self.api_url = DEEPSEEK_API_URL
        self.api_key = DEEPSEEK_API_KEY
        
    def generate_tweet(self, kol_data, prices):
        """
        生成推文内容
        
        Args:
            kol_data: KOL推文数据汇总
            prices: 价格数据字典
            
        Returns:
            生成的推文内容
        """
        
        # 构造Prompt
        prompt = self._build_prompt(kol_data, prices)
        
        # 调用DeepSeek API
        try:
            content = self._call_api(prompt)
            return content
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
            # 返回备用模板
            return self._fallback_template(kol_data, prices)
    
    def _build_prompt(self, kol_data, prices):
        """构造Prompt"""
        
        # 提取KOL观点摘要
        kol_summary = self._summarize_kol_data(kol_data)
        
        prompt = f"""你是一位资深的加密货币和美股分析师，擅长用痞气、接地气、略带江湖气的语言风格分析市场。

请根据以下数据，整理成一篇推文：

【KOL观点汇总】
{kol_summary}

【实时价格】
- BTC: ${prices.get('btc', 'N/A'):,.0f}
- 黄金: ${prices.get('gold', 'N/A'):,.0f}/盎司
- 石油: ${prices.get('oil', 'N/A'):,.0f}
- 特斯拉: ${prices.get('tesla', 'N/A'):,.0f}
- 微软: ${prices.get('microsoft', 'N/A'):,.0f}

【写作要求】
1. 标题要醒目、吸睛、带痞气（如"别TM瞎买了""醒醒吧韭菜们"）
2. 直接表达观点，不要说"有人说""有人认为"
3. 分析BTC、黄金、石油、美股四个资产的关联
4. 基于现象推导观点，有逻辑链条
5. 语言接地气，有感情色彩，可以带粗口（如"我呸""锤子""屁"）
6. 结尾给出明确的操作策略（3-5条）
7. 字数控制在1000-1500字
8. 带标签 #BTC #黄金 #石油 #美股 #投资真相

【风格示例】
- "我呸！当所有人都喊避险的时候，这玩意还避险个锤子？"
- "现在进去就是给庄家抬轿，性价比极低，我不碰。"
- "前两年赚钱是老天爷赏饭吃，不是你有本事。"
- "傻子赚钱的阶段过去了，接下来拼认知。"

请直接输出推文内容，不要加任何解释。"""
        
        return prompt
    
    def _summarize_kol_data(self, kol_data):
        """Summarize KOL数据"""
        if not kol_data:
            return "今日KOL数据收集失败，基于市场公开信息分析。"
        
        summary = []
        for kol in kol_data[:5]:  # 只取前5位活跃KOL
            username = kol.get('username', '未知')
            count = kol.get('count', 0)
            tweets = kol.get('tweets', [])
            if tweets:
                latest = tweets[0].get('text', '')[:100]
                summary.append(f"@{username}: {latest}...")
        
        return "\n".join(summary) if summary else "今日市场观点分歧较大。"
    
    def _call_api(self, prompt):
        """调用DeepSeek API"""
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.95
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        req = urllib.request.Request(
            self.api_url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result['choices'][0]['message']['content']
            return content
    
    def _fallback_template(self, kol_data, prices):
        """备用模板（API失败时使用）"""
        
        btc = prices.get('btc', 0)
        gold = prices.get('gold', 0)
        oil = prices.get('oil', 0)
        tsla = prices.get('tesla', 0)
        msft = prices.get('microsoft', 0)
        
        date_str = datetime.now().strftime("%m月%d日")
        
        return f"""【别TM瞎买了！{date_str}市场已经变天了】

今天一看盘，四个大爷（BTC、黄金、石油、美股）各玩各的，但逻辑串起来就一个结论：疯狗行情结束，接下来拼脑子了。

BTC现在${btc:,.0f}。
硬资产故事又被炒冷饭，一堆人喊避险。我呸！当所有人都喊避险时，还避险个锤子？现在这种全民抱团，分明是"互相取暖怕冻死"。BTC已从"暴富彩票"变成"债券备胎"，拿着可以，但别指望翻十倍，年化20%就该磕头谢恩了。

黄金现在${gold:,.0f}/盎司。
现在进去就是给庄家抬轿。有人说能避险？避个屁！十年不涨，通胀都能啃成骨头。买黄金是"慢性自杀式存款"，不如存银行。

石油现在${oil:,.0f}。
地缘一紧张就暴涨，缓和就暴跌。但你看清楚了，全球搞新能源，石油长期逻辑是downward。短期撸波段可以，长期持有？当传家宝传给孙子？

美股更热闹。特斯拉${tsla:,.0f}，微软${msft:,.0f}。
一帮人吵特斯拉拆股，想历史重演？醒醒吧，那时候是美联储疯狂印钱，现在钱紧，环境完全不同。微软被喊归零更是笑话，这种印钞机公司，跌下来是送钱，不是坑。

看明白了吗？这四个大爷同时在动，但背后的逻辑是同一个：钱变贵了，乱买乱涨的时代结束了。

以前美联储放水，你买狗屎都能飞。现在水退了，谁在裸泳一目了然。BTC从投机变配置，黄金高位套人，石油长期看空，美股只有真家伙能涨。

我的策略就四句话：
1. BTC当债券拿着，别做梦暴富
2. 黄金石油不碰，进去就是接盘
3. 美股只买印钞机公司，跌了就加仓
4. 留一半现金，等恐慌的时候捡尸体

最后说句糙话：前两年赚钱是老天爷赏饭吃，不是你有本事。现在赏饭结束了，真刀真枪的时候到了。没本事的，趁早离场保命。

#BTC #黄金 #石油 #美股 #投资真相
"""


if __name__ == '__main__':
    # 测试
    generator = DeepSeekGenerator()
    
    test_kol = [
        {"username": "cz_binance", "count": 2, "tweets": [{"text": "Bitcoin is a hard asset"}]},
        {"username": "monkeyjiang", "count": 3, "tweets": [{"text": "MEME红利期快结束了"}]}
    ]
    
    test_prices = {
        'btc': 70482,
        'gold': 2200,
        'oil': 82,
        'tesla': 175,
        'microsoft': 425
    }
    
    print("测试DeepSeek内容生成...")
    content = generator.generate_tweet(test_kol, test_prices)
    print(content[:500] + "...")
