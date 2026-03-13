#!/usr/bin/env python3
"""
推特观察人管理模块
管理推特关注列表的增删改查
"""

import os
import sys
import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

# 数据库路径
DB_PATH = os.path.expanduser("~/.openclaw/workspace/quant-trading/data-layer/market_data.db")


@dataclass
class TwitterWatchlistItem:
    """推特观察人数据类"""
    id: Optional[int] = None
    username: str = ""
    display_name: str = ""
    category: str = "trader"  # trader/influencer/official/analyst
    priority: int = 1
    is_active: bool = True
    follower_count: Optional[int] = None
    description: str = ""
    last_fetch_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TwitterWatchlistManager:
    """推特观察人管理器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._init_schema()
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_schema(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 读取并执行SQL文件
        schema_path = os.path.join(
            os.path.dirname(__file__), 
            '../data-layer/twitter_schema.sql'
        )
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                cursor.executescript(f.read())
        else:
            # 直接创建表（如果SQL文件不存在）
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS twitter_watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    category TEXT,
                    priority INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    follower_count INTEGER,
                    description TEXT,
                    last_fetch_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS twitter_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    content TEXT NOT NULL,
                    posted_at TIMESTAMP,
                    retweet_count INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    reply_count INTEGER DEFAULT 0,
                    sentiment TEXT,
                    sentiment_score REAL,
                    confidence REAL,
                    ai_reasoning TEXT,
                    ai_analyzed_at TIMESTAMP,
                    is_processed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
        
        conn.commit()
        conn.close()
    
    def add_watchlist_item(self, item: TwitterWatchlistItem) -> int:
        """添加观察人"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO twitter_watchlist 
            (username, display_name, category, priority, is_active, follower_count, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.username.lower().replace('@', ''),
            item.display_name,
            item.category,
            item.priority,
            1 if item.is_active else 0,
            item.follower_count,
            item.description
        ))
        
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return item_id
    
    def update_watchlist_item(self, item_id: int, data: Dict[str, Any]) -> bool:
        """更新观察人"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        allowed_fields = ['username', 'display_name', 'category', 'priority', 
                         'is_active', 'follower_count', 'description', 'last_fetch_at']
        
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = ?")
                if field == 'is_active':
                    values.append(1 if data[field] else 0)
                elif field == 'username':
                    values.append(data[field].lower().replace('@', ''))
                else:
                    values.append(data[field])
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(item_id)
        
        cursor.execute(f'''
            UPDATE twitter_watchlist 
            SET {', '.join(updates)}
            WHERE id = ?
        ''', values)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_watchlist_item(self, item_id: int) -> bool:
        """删除观察人"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM twitter_watchlist WHERE id = ?", (item_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_watchlist_item(self, item_id: int) -> Optional[TwitterWatchlistItem]:
        """获取单个观察人"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM twitter_watchlist WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return self._row_to_item(row)
        return None
    
    def get_all_watchlist(self, active_only: bool = False) -> List[Dict]:
        """获取所有观察人"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute('''
                SELECT * FROM twitter_watchlist 
                WHERE is_active = 1
                ORDER BY priority DESC, created_at DESC
            ''')
        else:
            cursor.execute('''
                SELECT * FROM twitter_watchlist 
                ORDER BY priority DESC, created_at DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_active_usernames(self) -> List[str]:
        """获取所有活跃的用户名列表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username FROM twitter_watchlist 
            WHERE is_active = 1
            ORDER BY priority DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    
    def update_last_fetch(self, username: str):
        """更新上次获取时间"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE twitter_watchlist 
            SET last_fetch_at = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (username.lower(),))
        
        conn.commit()
        conn.close()
    
    def init_default_watchlist(self):
        """初始化默认观察人列表"""
        default_users = [
            ('xiaomustock', '小木', 'trader', 2, '交易员'),
            ('thankUcrypto', 'ThankU Crypto', 'influencer', 2, '加密货币KOL'),
            ('dotyyds1234', 'DOT YYDS', 'trader', 2, 'DOT生态关注者'),
            ('monkeyjiang', 'Monkey Jiang', 'trader', 2, '交易员'),
            ('BTC563', 'BTC563', 'trader', 2, '比特币分析师'),
            ('cz_binance', 'CZ 🔶 Binance', 'official', 5, '币安创始人'),
        ]
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for username, display_name, category, priority, description in default_users:
            cursor.execute('''
                INSERT OR IGNORE INTO twitter_watchlist 
                (username, display_name, category, priority, is_active, description)
                VALUES (?, ?, ?, ?, 1, ?)
            ''', (username, display_name, category, priority, description))
        
        conn.commit()
        conn.close()
        
        print(f"✓ 已初始化 {len(default_users)} 个默认观察人")
    
    def _row_to_item(self, row: sqlite3.Row) -> TwitterWatchlistItem:
        """将数据库行转换为对象"""
        return TwitterWatchlistItem(
            id=row['id'],
            username=row['username'],
            display_name=row['display_name'],
            category=row['category'],
            priority=row['priority'],
            is_active=bool(row['is_active']),
            follower_count=row['follower_count'],
            description=row['description'],
            last_fetch_at=row['last_fetch_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )


def main():
    """测试管理器"""
    manager = TwitterWatchlistManager()
    
    # 初始化默认列表
    manager.init_default_watchlist()
    
    # 显示当前列表
    print("\n" + "="*60)
    print("推特观察人列表")
    print("="*60)
    
    items = manager.get_all_watchlist()
    for item in items:
        status = "✓" if item['is_active'] else "✗"
        print(f"[{status}] @{item['username']} ({item['display_name']}) - {item['category']}")
    
    print(f"\n总计: {len(items)} 人")
    print("="*60)


if __name__ == "__main__":
    main()
