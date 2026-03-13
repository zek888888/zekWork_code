#!/usr/bin/env python3
"""
AI配置管理模块
管理多个AI模型的配置，支持CRUD操作
"""

import os
import sys
import sqlite3
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# 配置层路径
CONFIG_LAYER_PATH = Path(os.path.expanduser("~/.openclaw/workspace/quant-trading/config-layer"))
DATA_LAYER_PATH = Path(os.path.expanduser("~/.openclaw/workspace/quant-trading/data-layer"))

# 数据库路径
DB_PATH = DATA_LAYER_PATH / "market_data.db"


@dataclass
class AIConfig:
    """AI配置数据类"""
    name: str
    provider: str  # moonshot, openai, anthropic, custom
    model: str
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    weight: float = 1.0
    status: str = "active"  # active, inactive
    priority: int = 1
    description: str = ""
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AIConfigManager:
    """AI配置管理器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self._ensure_table()
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_table(self):
        """确保ai_configs表存在"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                api_key TEXT,
                base_url TEXT,
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 2000,
                timeout INTEGER DEFAULT 30,
                weight REAL DEFAULT 1.0,
                status TEXT DEFAULT 'active',
                priority INTEGER DEFAULT 1,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_ai_config(self, config: AIConfig) -> int:
        """添加AI配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ai_configs 
            (name, provider, model, api_key, base_url, temperature, max_tokens, 
             timeout, weight, status, priority, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            config.name, config.provider, config.model, config.api_key,
            config.base_url, config.temperature, config.max_tokens,
            config.timeout, config.weight, config.status, config.priority,
            config.description
        ))
        
        config_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return config_id
    
    def update_ai_config(self, config_id: int, data: Dict[str, Any]) -> bool:
        """更新AI配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 构建更新字段
        allowed_fields = ['name', 'provider', 'model', 'api_key', 'base_url',
                         'temperature', 'max_tokens', 'timeout', 'weight',
                         'status', 'priority', 'description']
        
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = ?")
                values.append(data[field])
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(config_id)
        
        cursor.execute(f"""
            UPDATE ai_configs 
            SET {', '.join(updates)}
            WHERE id = ?
        """, values)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_ai_config(self, config_id: int) -> bool:
        """删除AI配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM ai_configs WHERE id = ?", (config_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_ai_config(self, config_id: int) -> Optional[AIConfig]:
        """获取单个AI配置"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ai_configs WHERE id = ?", (config_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return self._row_to_config(row)
        return None
    
    def get_all_configs(self, status: str = None) -> List[Dict]:
        """获取所有AI配置（排除API密钥）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT id, name, provider, model, base_url, temperature, 
                       max_tokens, timeout, weight, status, priority, 
                       description, created_at, updated_at
                FROM ai_configs WHERE status = ? ORDER BY priority DESC, id ASC
            """, (status,))
        else:
            cursor.execute("""
                SELECT id, name, provider, model, base_url, temperature, 
                       max_tokens, timeout, weight, status, priority, 
                       description, created_at, updated_at
                FROM ai_configs ORDER BY priority DESC, id ASC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_active_configs(self) -> List[AIConfig]:
        """获取活跃的AI配置（包含API密钥，用于实际调用）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM ai_configs 
            WHERE status = 'active' 
            ORDER BY priority DESC, id ASC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_config(row) for row in rows]
    
    def _row_to_config(self, row: sqlite3.Row) -> AIConfig:
        """将数据库行转换为AIConfig对象"""
        return AIConfig(
            id=row['id'],
            name=row['name'],
            provider=row['provider'],
            model=row['model'],
            api_key=row['api_key'] or "",
            base_url=row['base_url'] or "",
            temperature=row['temperature'],
            max_tokens=row['max_tokens'],
            timeout=row['timeout'],
            weight=row['weight'],
            status=row['status'],
            priority=row['priority'],
            description=row['description'] or "",
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def init_default_config(self):
        """初始化默认配置（从OpenClaw配置文件）"""
        # 尝试从OpenClaw配置读取
        openclaw_config_path = os.path.expanduser("~/.openclaw/openclaw.json")
        
        if os.path.exists(openclaw_config_path):
            try:
                with open(openclaw_config_path, 'r') as f:
                    config = json.load(f)
                
                # 检查是否已有Kimi配置
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ai_configs WHERE provider = 'moonshot'")
                count = cursor.fetchone()[0]
                conn.close()
                
                if count > 0:
                    print("Kimi配置已存在，跳过初始化")
                    return
                
                # 添加Kimi配置
                agents = config.get('agents', {})
                
                for agent_name, agent_config in agents.items():
                    if 'kimi' in agent_name.lower():
                        ai_config = AIConfig(
                            name="Kimi K2.5",
                            provider="moonshot",
                            model=agent_config.get('model', 'kimi-k2.5'),
                            api_key=agent_config.get('api_key', ''),
                            base_url=agent_config.get('base_url', 'https://api.moonshot.cn/v1'),
                            temperature=0.7,
                            max_tokens=2000,
                            weight=1.0,
                            status='active',
                            priority=1,
                            description="Kimi大模型，用于新闻情绪分析"
                        )
                        
                        self.add_ai_config(ai_config)
                        print(f"已添加默认配置: {ai_config.name}")
                        
            except Exception as e:
                print(f"读取OpenClaw配置失败: {e}")
        
        # 如果没有找到配置，添加一个空模板
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ai_configs")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            print("请手动添加AI配置")


def main():
    """测试AI配置管理器"""
    manager = AIConfigManager()
    
    # 显示当前配置
    print("=" * 60)
    print("当前AI配置列表:")
    print("=" * 60)
    
    configs = manager.get_all_configs()
    
    if not configs:
        print("暂无配置")
        print("\n正在初始化默认配置...")
        manager.init_default_config()
        configs = manager.get_all_configs()
    
    for config in configs:
        status_icon = "✓" if config['status'] == 'active' else "✗"
        print(f"[{status_icon}] {config['name']} ({config['provider']} - {config['model']})")
        print(f"    权重: {config['weight']}, 优先级: {config['priority']}")
        print(f"    描述: {config['description']}")
        print()
    
    print(f"总计: {len(configs)} 个配置")
    print("=" * 60)


if __name__ == "__main__":
    main()
