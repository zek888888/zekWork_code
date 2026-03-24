#!/usr/bin/env python3
"""
每日一推 - 主控制脚本
协调各模块执行，生成每日推文
定时执行：每天中午12:00
"""

import os
import sys
import json
import time
from datetime import datetime

# 确保可以导入同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deepseek_generator import DeepSeekGenerator
from twitter_publisher import TwitterPublisher


class DailyPushController:
    """每日一推主控制器"""
    
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(self.script_dir)
        self.output_dir = os.path.join(self.root_dir, 'daily_output')
        self.log_file = os.path.join(self.root_dir, 'logs', 'daily_push.log')
        
        # 确保目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def log(self, message, level='INFO'):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {level}: {message}"
        print(log_line)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def run(self):
        """执行每日一推任务"""
        self.log("="*60)
        self.log("每日一推任务开始")
        self.log("="*60)
        
        try:
            # 步骤1：收集KOL数据
            self.log("步骤1: 收集KOL数据...")
            kol_data = self._collect_kol_data()
            self.log(f"成功收集{len(kol_data)}位KOL数据")
            
            # 步骤2：获取实时价格
            self.log("步骤2: 获取实时价格...")
            prices = self._fetch_prices()
            self.log(f"价格数据: BTC=${prices.get('btc', 'N/A')}")
            
            # 步骤3：调用DeepSeek生成内容
            self.log("步骤3: 调用DeepSeek API生成内容...")
            content = self._generate_content(kol_data, prices)
            self.log("内容生成成功")
            
            # 步骤4：保存文件
            self.log("步骤4: 保存推文文件...")
            filepath = self._save_content(content)
            self.log(f"文件已保存: {filepath}")
            
            # 步骤5：自动发布到Twitter
            self.log("步骤5: 自动发布到Twitter...")
            publish_result = self._publish_to_twitter(content)
            if publish_result['success']:
                self.log(f"✅ 推文发布成功！链接: {publish_result['link']}")
            else:
                self.log(f"⚠️ 推文发布失败: {publish_result.get('error', '未知错误')}", level='WARNING')
            
            # 步骤6：发送通知
            self.log("步骤6: 发送通知...")
            self._send_notification(filepath, content, prices, publish_result)
            self.log("通知发送成功")
            
            self.log("="*60)
            self.log("✅ 每日一推任务完成！")
            self.log("="*60)
            
            return True
            
        except Exception as e:
            self.log(f"❌ 任务执行失败: {str(e)}", level='ERROR')
            self._send_error_notification(str(e))
            return False
    
    def _collect_kol_data(self):
        """收集KOL数据"""
        # 调用外部脚本或直接使用之前的收集逻辑
        # 这里简化处理，实际应该调用完整的KOL收集脚本
        try:
            import subprocess
            result = subprocess.run(
                ['python3', os.path.join(self.root_dir, 'fetch_kol_tweets_v2.py')],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # 解析输出获取数据
            # 实际应该从文件或API获取
            return self._load_kol_data_from_file()
        except Exception as e:
            self.log(f"KOL数据收集异常: {e}", level='WARNING')
            return []
    
    def _load_kol_data_from_file(self):
        """从文件加载KOL数据"""
        import glob
        kol_files = glob.glob('/tmp/kol_tweets_*.json')
        if kol_files:
            latest_file = max(kol_files, key=os.path.getctime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # JSON结构: {kol_data: [...], topic_data: {...}, ...}
                kol_data = data.get('kol_data', [])
                # 已经是列表格式，直接使用
                self.log(f"从文件加载 {len(kol_data)} 位KOL数据")
                return kol_data
        return []
    
    def _fetch_prices(self):
        """获取实时价格"""
        # 复用之前的价格获取逻辑
        sys.path.insert(0, self.root_dir)
        try:
            from auto_tweet_generator import PriceFetcher
            fetcher = PriceFetcher()
            return {
                'btc': fetcher.get_btc_price(),
                'gold': fetcher.get_gold_price(),
                'oil': fetcher.get_oil_price(),
                'tesla': fetcher.get_tesla_price(),
                'microsoft': fetcher.get_microsoft_price()
            }
        except Exception as e:
            self.log(f"价格获取异常: {e}", level='WARNING')
            return {}
    
    def _generate_content(self, kol_data, prices):
        """生成推文内容"""
        generator = DeepSeekGenerator()
        return generator.generate_tweet(kol_data, prices)
    
    def _save_content(self, content):
        """保存内容到文件"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{date_str}_每日一推.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def _publish_to_twitter(self, content):
        """发布到Twitter"""
        try:
            publisher = TwitterPublisher()
            result = publisher.publish_tweet(content)
            return result
        except Exception as e:
            self.log(f"Twitter发布异常: {e}", level='ERROR')
            return {'success': False, 'error': str(e)}
    
    def _send_notification(self, filepath, content, prices, publish_result=None):
        """发送成功通知"""
        # 这里可以实现飞书/邮件通知
        # 简化版本：记录到日志
        preview = content[:300] if len(content) > 300 else content
        self.log(f"通知内容预览:\n{preview}...")
        
        # 实际应该调用通知模块
        # 创建通知文件
        notify_file = os.path.join(self.output_dir, 'latest_notification.txt')
        with open(notify_file, 'w', encoding='utf-8') as f:
            f.write(f"每日一推已生成！\n")
            f.write(f"文件路径: {filepath}\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"BTC价格: ${prices.get('btc', 'N/A')}\n")
            if publish_result and publish_result.get('success'):
                f.write(f"✅ 已自动发布到Twitter\n")
                f.write(f"推文链接: {publish_result['link']}\n")
            elif publish_result:
                f.write(f"⚠️ Twitter发布失败: {publish_result.get('error', '未知错误')}\n")
            f.write(f"\n内容预览:\n{preview}...\n")
    
    def _send_error_notification(self, error_msg):
        """发送错误通知"""
        self.log(f"错误通知已发送: {error_msg}", level='ERROR')
        
        # 创建错误通知文件
        error_file = os.path.join(self.output_dir, 'error_notification.txt')
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"❌ 每日一推生成失败！\n")
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"错误: {error_msg}\n")
            f.write(f"请检查日志: {self.log_file}\n")


def main():
    """主函数"""
    controller = DailyPushController()
    success = controller.run()
    
    # 返回状态码供crontab使用
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
