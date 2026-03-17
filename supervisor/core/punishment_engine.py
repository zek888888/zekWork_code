#!/usr/bin/env python3
"""
惩罚引擎 - 隔壁老王的生杀大权
任务不执行？API给你停了！换！
"""

import os
import sys
import yaml
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')


class PunishmentLevel(Enum):
    """惩罚级别"""
    WARNING = "warning"         # 警告
    SUSPEND = "suspend"         # 暂停API
    SWITCH = "switch"           # 切换API
    BLACKLIST = "blacklist"     # 彻底拉黑


class APIProvider:
    """API提供商配置"""
    PROVIDERS = {
        'deepseek': {
            'name': 'DeepSeek',
            'models': ['deepseek-chat', 'deepseek-reasoner'],
            'config_key': 'DEEPSEEK_API_KEY',
            'alternatives': ['moonshot', 'openai']
        },
        'moonshot': {
            'name': 'Moonshot/Kimi',
            'models': ['kimi-k2.5', 'moonshot-v1-8k'],
            'config_key': 'MOONSHOT_API_KEY',
            'alternatives': ['deepseek', 'openai']
        },
        'binance': {
            'name': 'Binance',
            'models': [],
            'config_key': 'BINANCE_API_KEY',
            'alternatives': ['yahoo', 'backup_binance']
        }
    }


class PunishmentEngine:
    """
    隔壁老王的惩罚引擎
    不干活？API给你扬了！
    """
    
    # 惩罚阈值配置
    THRESHOLDS = {
        'warning': 3,       # 3次失败 → 警告
        'suspend': 5,       # 5次失败 → 暂停API 30分钟
        'switch': 7,        # 7次失败 → 强制切换API
        'blacklist': 10     # 10次失败 → 拉黑该API
    }
    
    def __init__(self, db_path: str = "data/supervisor.db"):
        self.db_path = db_path
        self.config_path = "/Users/mac/.openclaw/workspace/quant-trading/config.yaml"
        self._init_punishment_log()
    
    def _init_punishment_log(self):
        """初始化惩罚记录表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API失败计数表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_failure_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_provider TEXT NOT NULL,
                task_id TEXT NOT NULL,
                failure_count INTEGER DEFAULT 0,
                last_failure TEXT,
                punishment_level TEXT DEFAULT 'none',
                suspended_until TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(api_provider, task_id)
            )
        ''')
        
        # 惩罚记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS punishment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_provider TEXT NOT NULL,
                task_id TEXT NOT NULL,
                level TEXT NOT NULL,
                reason TEXT,
                action_taken TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 被拉黑的API表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_provider TEXT NOT NULL UNIQUE,
                reason TEXT,
                blacklisted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                permanent BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_failure(self, api_provider: str, task_id: str, 
                       error_message: str = "") -> Dict[str, Any]:
        """记录API失败，返回惩罚决策"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # 获取当前失败计数
        cursor.execute('''
            SELECT failure_count, punishment_level, suspended_until
            FROM api_failure_counts
            WHERE api_provider = ? AND task_id = ?
        ''', (api_provider, task_id))
        
        row = cursor.fetchone()
        
        if row:
            failure_count = row[0] + 1
            current_level = row[1] or 'none'
            suspended_until = row[2]
            
            # 检查是否还在暂停期
            if suspended_until and datetime.now() < datetime.fromisoformat(suspended_until):
                conn.close()
                return {
                    'action': 'suspended',
                    'message': f'{api_provider} 还在暂停期，跳过',
                    'failure_count': failure_count
                }
            
            cursor.execute('''
                UPDATE api_failure_counts 
                SET failure_count = ?, last_failure = ?, updated_at = ?
                WHERE api_provider = ? AND task_id = ?
            ''', (failure_count, now, now, api_provider, task_id))
        else:
            failure_count = 1
            current_level = 'none'
            cursor.execute('''
                INSERT INTO api_failure_counts 
                (api_provider, task_id, failure_count, last_failure, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (api_provider, task_id, failure_count, now, now))
        
        conn.commit()
        conn.close()
        
        # 判断是否需要惩罚
        return self._evaluate_punishment(api_provider, task_id, failure_count, error_message)
    
    def _evaluate_punishment(self, api_provider: str, task_id: str, 
                            failure_count: int, error_message: str) -> Dict[str, Any]:
        """评估并执行惩罚"""
        
        # 检查是否已拉黑
        if self._is_blacklisted(api_provider):
            return {
                'action': 'blacklisted',
                'level': 'blacklist',
                'message': f'{api_provider} 已被拉黑，立即切换',
                'failure_count': failure_count
            }
        
        # 根据失败次数决定惩罚
        if failure_count >= self.THRESHOLDS['blacklist']:
            return self._execute_blacklist(api_provider, task_id, error_message)
        
        elif failure_count >= self.THRESHOLDS['switch']:
            return self._execute_switch(api_provider, task_id, error_message)
        
        elif failure_count >= self.THRESHOLDS['suspend']:
            return self._execute_suspend(api_provider, task_id, error_message)
        
        elif failure_count >= self.THRESHOLDS['warning']:
            return self._execute_warning(api_provider, task_id, failure_count)
        
        return {
            'action': 'none',
            'level': 'normal',
            'message': f'当前失败次数: {failure_count}',
            'failure_count': failure_count
        }
    
    def _execute_warning(self, api_provider: str, task_id: str, 
                        failure_count: int) -> Dict[str, Any]:
        """执行警告"""
        self._log_punishment(api_provider, task_id, 'warning', 
                            f'连续失败{failure_count}次', '发送警告通知')
        
        return {
            'action': 'warning',
            'level': 'warning',
            'message': f'⚠️ 警告: {api_provider} 连续失败{failure_count}次！再失败就要被老王惩罚了！',
            'failure_count': failure_count,
            'next_threshold': self.THRESHOLDS['suspend']
        }
    
    def _execute_suspend(self, api_provider: str, task_id: str, 
                        error_message: str) -> Dict[str, Any]:
        """执行暂停"""
        suspend_duration = 30  # 暂停30分钟
        suspended_until = (datetime.now() + timedelta(minutes=suspend_duration)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE api_failure_counts 
            SET punishment_level = 'suspend', suspended_until = ?
            WHERE api_provider = ? AND task_id = ?
        ''', (suspended_until, api_provider, task_id))
        conn.commit()
        conn.close()
        
        self._log_punishment(api_provider, task_id, 'suspend', 
                            error_message, f'暂停{suspend_duration}分钟')
        
        return {
            'action': 'suspend',
            'level': 'suspend',
            'message': f'🚫 {api_provider} 已被老王暂停 {suspend_duration}分钟！好好反省！',
            'suspended_until': suspended_until,
            'failure_count': 5
        }
    
    def _execute_switch(self, api_provider: str, task_id: str, 
                       error_message: str) -> Dict[str, Any]:
        """执行强制切换API"""
        # 获取备用API
        alternatives = APIProvider.PROVIDERS.get(api_provider, {}).get('alternatives', [])
        new_api = alternatives[0] if alternatives else 'manual'
        
        # 尝试切换
        switch_success = self._switch_api_provider(api_provider, new_api, task_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE api_failure_counts 
            SET punishment_level = 'switch'
            WHERE api_provider = ? AND task_id = ?
        ''', (api_provider, task_id))
        conn.commit()
        conn.close()
        
        self._log_punishment(api_provider, task_id, 'switch', 
                            error_message, f'切换至{new_api}')
        
        return {
            'action': 'switch',
            'level': 'switch',
            'message': f'🔥 {api_provider} 不干活，老王给你换了！现在用 {new_api}！',
            'old_api': api_provider,
            'new_api': new_api,
            'switch_success': switch_success,
            'failure_count': 7
        }
    
    def _execute_blacklist(self, api_provider: str, task_id: str, 
                          error_message: str) -> Dict[str, Any]:
        """执行拉黑"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 加入黑名单
        cursor.execute('''
            INSERT OR REPLACE INTO api_blacklist 
            (api_provider, reason, permanent)
            VALUES (?, ?, 1)
        ''', (api_provider, f'任务{task_id}连续失败10次: {error_message[:100]}'))
        
        # 更新状态
        cursor.execute('''
            UPDATE api_failure_counts 
            SET punishment_level = 'blacklist'
            WHERE api_provider = ? AND task_id = ?
        ''', (api_provider, task_id))
        
        conn.commit()
        conn.close()
        
        # 强制切换
        alternatives = APIProvider.PROVIDERS.get(api_provider, {}).get('alternatives', [])
        new_api = alternatives[0] if alternatives else 'manual'
        switch_success = self._switch_api_provider(api_provider, new_api, task_id)
        
        self._log_punishment(api_provider, task_id, 'blacklist', 
                            error_message, f'永久拉黑，强制切换至{new_api}')
        
        return {
            'action': 'blacklist',
            'level': 'blacklist',
            'message': f'💀 {api_provider} 已被老王彻底拉黑！永不录用！现在强制使用 {new_api}！',
            'old_api': api_provider,
            'new_api': new_api,
            'switch_success': switch_success,
            'permanent': True,
            'failure_count': 10
        }
    
    def _switch_api_provider(self, old_api: str, new_api: str, task_id: str) -> bool:
        """切换API提供商（修改配置文件）"""
        try:
            # 读取当前配置
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # 这里可以实现具体的切换逻辑
            # 例如：修改AI模型配置，把DeepSeek换成Moonshot
            
            if old_api in ['deepseek', 'moonshot']:
                # AI模型切换
                if 'ai_models' in config and 'news_analysis' in config['ai_models']:
                    for model in config['ai_models']['news_analysis']:
                        if model.get('provider') == old_api:
                            model['provider'] = new_api
                            model['status'] = 'active'
                            print(f"[老王] 已切换AI模型: {old_api} → {new_api}")
            
            # 保存配置
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            return True
            
        except Exception as e:
            print(f"[老王] 切换API失败: {e}")
            return False
    
    def _is_blacklisted(self, api_provider: str) -> bool:
        """检查API是否已被拉黑"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 1 FROM api_blacklist WHERE api_provider = ?
        ''', (api_provider,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def _log_punishment(self, api_provider: str, task_id: str, 
                       level: str, reason: str, action: str):
        """记录惩罚历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO punishment_history 
            (api_provider, task_id, level, reason, action_taken)
            VALUES (?, ?, ?, ?, ?)
        ''', (api_provider, task_id, level, reason, action))
        conn.commit()
        conn.close()
    
    def get_failure_stats(self, api_provider: str = None) -> Dict[str, Any]:
        """获取失败统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if api_provider:
            cursor.execute('''
                SELECT task_id, failure_count, punishment_level, last_failure
                FROM api_failure_counts
                WHERE api_provider = ?
                ORDER BY failure_count DESC
            ''', (api_provider,))
        else:
            cursor.execute('''
                SELECT api_provider, task_id, failure_count, punishment_level, last_failure
                FROM api_failure_counts
                ORDER BY failure_count DESC
            ''')
        
        rows = cursor.fetchall()
        
        # 获取黑名单
        cursor.execute('SELECT api_provider, reason, blacklisted_at FROM api_blacklist')
        blacklist = cursor.fetchall()
        
        conn.close()
        
        return {
            'failures': [
                {
                    'api': row[0] if not api_provider else api_provider,
                    'task': row[1] if not api_provider else row[0],
                    'count': row[2] if not api_provider else row[1],
                    'level': row[3] if not api_provider else row[2],
                    'last': row[4] if not api_provider else row[3]
                }
                for row in rows
            ],
            'blacklist': [
                {'api': row[0], 'reason': row[1], 'time': row[2]}
                for row in blacklist
            ]
        }
    
    def reset_counter(self, api_provider: str, task_id: str):
        """重置失败计数（API恢复正常后调用）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE api_failure_counts 
            SET failure_count = 0, punishment_level = 'none', suspended_until = NULL
            WHERE api_provider = ? AND task_id = ?
        ''', (api_provider, task_id))
        conn.commit()
        conn.close()
        print(f"[老王] {api_provider} ({task_id}) 的失败计数已重置")


if __name__ == "__main__":
    engine = PunishmentEngine()
    
    # 测试
    print("=" * 60)
    print("🧑‍🔧 隔壁老王的惩罚引擎")
    print("=" * 60)
    print()
    
    # 模拟连续失败
    for i in range(12):
        result = engine.record_failure('deepseek', 'shen_suan_zi', 'Connection timeout')
        print(f"第{i+1}次失败: {result['action']} - {result['message'][:60]}...")
    
    print()
    print("统计:")
    stats = engine.get_failure_stats()
    for f in stats['failures']:
        print(f"  {f['api']}: {f['count']}次 - {f['level']}")
