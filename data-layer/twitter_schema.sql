-- 推特数据模块数据库表结构

-- 推特观察人列表
CREATE TABLE IF NOT EXISTS twitter_watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,  -- 推特用户名（不含@）
    display_name TEXT,              -- 显示名称
    category TEXT,                  -- 分类：trader/influencer/official等
    priority INTEGER DEFAULT 1,     -- 优先级
    is_active INTEGER DEFAULT 1,    -- 是否激活
    follower_count INTEGER,         -- 粉丝数
    description TEXT,               -- 简介
    last_fetch_at TIMESTAMP,        -- 上次获取时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 推特推文数据
CREATE TABLE IF NOT EXISTS twitter_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tweet_id TEXT UNIQUE NOT NULL,  -- 推特ID
    username TEXT NOT NULL,         -- 发帖人
    content TEXT NOT NULL,          -- 推文内容
    posted_at TIMESTAMP,            -- 发布时间
    retweet_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    -- AI分析结果
    sentiment TEXT,                 -- bullish/bearish/neutral
    sentiment_score REAL,           -- 情绪分数
    confidence REAL,                -- 置信度
    ai_reasoning TEXT,              -- AI分析理由
    ai_analyzed_at TIMESTAMP,       -- AI分析时间
    -- 元数据
    is_processed INTEGER DEFAULT 0, -- 是否已处理
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES twitter_watchlist(username)
);

-- 推文获取日志
CREATE TABLE IF NOT EXISTS twitter_fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fetch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username TEXT,
    posts_fetched INTEGER DEFAULT 0,
    posts_new INTEGER DEFAULT 0,
    posts_duplicates INTEGER DEFAULT 0,
    status TEXT DEFAULT 'success',
    error_message TEXT
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_twitter_posts_username ON twitter_posts(username);
CREATE INDEX IF NOT EXISTS idx_twitter_posts_posted_at ON twitter_posts(posted_at);
CREATE INDEX IF NOT EXISTS idx_twitter_posts_sentiment ON twitter_posts(sentiment);
CREATE INDEX IF NOT EXISTS idx_twitter_posts_created_at ON twitter_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_twitter_watchlist_active ON twitter_watchlist(is_active);

-- 插入默认观察人
INSERT OR IGNORE INTO twitter_watchlist (username, display_name, category, priority, description) VALUES
('xiaomustock', '小木', 'trader', 2, '交易员'),
('thankUcrypto', 'ThankU Crypto', 'influencer', 2, '加密货币KOL'),
('dotyyds1234', 'DOT YYDS', 'trader', 2, 'DOT生态关注者'),
('monkeyjiang', 'Monkey Jiang', 'trader', 2, '交易员'),
('BTC563', 'BTC563', 'trader', 2, '比特币分析师'),
('cz_binance', 'CZ 🔶 Binance', 'official', 5, '币安创始人');
