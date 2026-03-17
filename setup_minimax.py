#!/usr/bin/env python3
"""
添加 MiniMAX AI 到神算子配置
"""

import os
import sys
import sqlite3

sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading')
sys.path.insert(0, '/Users/mac/.openclaw/workspace/quant-trading/config-layer')

DB_PATH = "/Users/mac/.openclaw/workspace/quant-trading/data/market_data.db"


def setup_minimax():
    """配置 MiniMAX AI"""
    
    # 从环境变量读取配置
    base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.minimaxi.com/v1')
    api_key = os.environ.get('OPENAI_API_KEY', '')
    
    if not api_key:
        print("❌ 错误: OPENAI_API_KEY 环境变量未设置")
        print("请先设置环境变量:")
        print("  export OPENAI_API_KEY=sk-api-...")
        return False
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 确保表存在
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
    
    # 检查是否已存在 MiniMAX 配置
    cursor.execute("SELECT * FROM ai_configs WHERE name = ?", ("MiniMAX",))
    existing = cursor.fetchone()
    
    if existing:
        print(f"⚠️  MiniMAX 配置已存在 (ID: {existing['id']})")
        print("正在更新配置...")
        
        # 更新配置
        cursor.execute("""
            UPDATE ai_configs 
            SET api_key = ?, base_url = ?, status = 'active', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (api_key, base_url, existing['id']))
        
        conn.commit()
        print("✅ MiniMAX 配置已更新")
    else:
        # 创建新配置
        cursor.execute("""
            INSERT INTO ai_configs 
            (name, provider, model, api_key, base_url, temperature, max_tokens, 
             timeout, weight, status, priority, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "MiniMAX",
            "openai",  # MiniMAX 使用 OpenAI 兼容接口
            "MiniMax-Text-01",  # 或其他可用模型
            api_key,
            base_url,
            0.3,  # temperature
            400,  # max_tokens
            30,   # timeout
            1.0,  # weight
            "active",
            3,    # priority
            "MiniMAX AI - OpenAI兼容接口"
        ))
        
        config_id = cursor.lastrowid
        conn.commit()
        print(f"✅ MiniMAX 配置已添加 (ID: {config_id})")
    
    # 显示所有活跃配置
    print("\n📊 当前活跃的AI配置:")
    cursor.execute("""
        SELECT id, name, provider, model, status, priority 
        FROM ai_configs 
        WHERE status = 'active' 
        ORDER BY priority DESC, id ASC
    """)
    
    for row in cursor.fetchall():
        print(f"  • {row['name']} ({row['provider']}) - {row['model']} [优先级:{row['priority']}]")
    
    conn.close()
    return True


def test_minimax():
    """测试 MiniMAX 连接"""
    print("\n🧪 测试 MiniMAX 连接...")
    
    import requests
    
    api_key = os.environ.get('OPENAI_API_KEY', '')
    base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.minimaxi.com/v1')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'MiniMax-Text-01',
        'messages': [
            {'role': 'user', 'content': 'Hello, are you working?'}
        ],
        'max_tokens': 50
    }
    
    try:
        response = requests.post(
            f'{base_url}/chat/completions',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ MiniMAX 连接成功!")
            print(f"   响应: {content[:50]}...")
            return True
        else:
            print(f"❌ MiniMAX 连接失败: {response.status_code}")
            print(f"   错误: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ MiniMAX 连接异常: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 神算子 - MiniMAX AI 配置工具")
    print("=" * 60)
    print()
    
    # 设置 MiniMAX
    if setup_minimax():
        print()
        # 测试连接
        test_minimax()
    
    print()
    print("=" * 60)
    print("配置完成!")
    print("神算子现在可以使用 MiniMAX 进行预测了")
    print("=" * 60)
