-- ============================================
-- 预测统计报告系统 - 数据库表结构
-- ============================================

-- 1. AI预测记录表 - 存储每次预测的详细信息
CREATE TABLE IF NOT EXISTS ai_prediction_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL DEFAULT 'BTCUSDT',
    interval TEXT NOT NULL DEFAULT '15m',
    
    -- 预测发起时间
    predict_initiated_at TIMESTAMP NOT NULL,
    
    -- 预测目标时间段（预测的是哪个时间段的走势）
    target_period_start TIMESTAMP NOT NULL,
    target_period_end TIMESTAMP NOT NULL,
    
    -- 预测时的价格数据
    price_at_predict REAL,
    macd_at_predict REAL,
    kdj_j_at_predict REAL,
    
    -- 综合预测结果
    consensus_prediction TEXT,  -- 'up' or 'down'
    consensus_up_probability INTEGER,
    consensus_down_probability INTEGER,
    consensus_confidence REAL,
    consensus_reason TEXT,
    
    -- 实际结果（回填）
    actual_result TEXT,  -- 'up' or 'down' or 'flat'
    price_at_target_start REAL,
    price_at_target_end REAL,
    actual_price_change_percent REAL,
    
    -- 预测准确性
    is_correct BOOLEAN,  -- 预测是否正确
    accuracy_score REAL, -- 准确性得分(0-1)
    
    -- 验证时间
    verified_at TIMESTAMP,
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, interval, target_period_start)
);

-- 2. 各AI详细预测结果表
CREATE TABLE IF NOT EXISTS ai_individual_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER NOT NULL,
    
    -- AI信息
    ai_name TEXT NOT NULL,
    ai_provider TEXT NOT NULL,
    ai_model TEXT,
    
    -- 预测结果
    prediction TEXT NOT NULL,  -- 'up' or 'down'
    up_probability INTEGER,
    down_probability INTEGER,
    confidence REAL,
    reason TEXT,
    
    -- 原始响应（用于知识库学习）
    raw_response TEXT,
    
    -- 该AI预测是否准确（回填）
    is_correct BOOLEAN,
    
    -- 调用耗时(秒)
    response_time_ms INTEGER,
    
    -- 状态
    status TEXT DEFAULT 'success',  -- 'success', 'error', 'timeout'
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (record_id) REFERENCES ai_prediction_records(id) ON DELETE CASCADE
);

-- 3. 知识库表 - 存储预测模式和学习数据
CREATE TABLE IF NOT EXISTS knowledge_base_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 模式类型
    pattern_type TEXT NOT NULL,  -- 'indicator_combination', 'price_action', 'time_pattern'
    
    -- 模式描述
    pattern_name TEXT NOT NULL,
    pattern_description TEXT,
    
    -- 技术指标条件（JSON格式存储）
    indicator_conditions TEXT,  -- {"macd_range": [-50, 0], "kdj_range": [0, 20], ...}
    
    -- 时间特征
    time_features TEXT,  -- {"hour": 14, "weekday": 1, ...}
    
    -- 统计信息
    total_occurrences INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    accuracy_rate REAL DEFAULT 0,
    
    -- 适用性
    best_interval TEXT,  -- 最适合的时间维度
    best_ai_provider TEXT,  -- 最适合的AI
    
    -- 成功案例引用
    success_examples TEXT,  -- JSON数组，存储成功预测的record_id
    failure_examples TEXT,  -- JSON数组，存储失败预测的record_id
    
    -- 学习权重
    confidence_weight REAL DEFAULT 1.0,
    
    -- 状态
    status TEXT DEFAULT 'active',  -- 'active', 'deprecated', 'learning'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 预测复盘分析表 - 存储每次预测的详细复盘
CREATE TABLE IF NOT EXISTS prediction_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER NOT NULL,
    
    -- 复盘分析
    review_type TEXT,  -- 'success_analysis', 'failure_analysis'
    
    -- 成功/失败原因分析
    primary_reason TEXT,  -- 主要原因
    secondary_reasons TEXT,  -- 次要原因(JSON数组)
    
    -- 指标表现分析
    indicator_performance TEXT,  -- {"macd_accuracy": 0.8, "kdj_accuracy": 0.6, ...}
    
    -- 市场异常因素
    market_anomalies TEXT,  -- 突发新闻、大单等
    
    -- 改进建议
    improvement_suggestions TEXT,
    
    -- 关联的知识库条目
    related_pattern_ids TEXT,  -- JSON数组
    
    -- 是否需要更新知识库
    should_update_kb BOOLEAN DEFAULT FALSE,
    
    -- 复盘人员/AI
    reviewed_by TEXT DEFAULT 'system',
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (record_id) REFERENCES ai_prediction_records(id) ON DELETE CASCADE
);

-- 5. AI学习反馈表 - 存储AI的自我改进数据
CREATE TABLE IF NOT EXISTS ai_learning_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    ai_provider TEXT NOT NULL,
    ai_model TEXT,
    
    -- 学习周期
    period_start DATE,
    period_end DATE,
    
    -- 统计表现
    total_predictions INTEGER,
    correct_predictions INTEGER,
    accuracy_rate REAL,
    
    -- 擅长/不擅长的模式
    strong_patterns TEXT,  -- JSON数组
    weak_patterns TEXT,  -- JSON数组
    
    -- 改进建议
    prompt_adjustments TEXT,  -- Prompt调优建议
    parameter_tweaks TEXT,  -- 参数调整建议
    
    -- 实际应用的改进
    applied_improvements TEXT,
    improvement_effectiveness REAL,  -- 改进效果
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_prediction_records_time 
    ON ai_prediction_records(predict_initiated_at);
CREATE INDEX IF NOT EXISTS idx_prediction_records_target 
    ON ai_prediction_records(target_period_start, target_period_end);
CREATE INDEX IF NOT EXISTS idx_prediction_records_verified 
    ON ai_prediction_records(verified_at);
CREATE INDEX IF NOT EXISTS idx_prediction_records_correct 
    ON ai_prediction_records(is_correct);

CREATE INDEX IF NOT EXISTS idx_individual_pred_record 
    ON ai_individual_predictions(record_id);
CREATE INDEX IF NOT EXISTS idx_individual_pred_ai 
    ON ai_individual_predictions(ai_name);

CREATE INDEX IF NOT EXISTS idx_kb_pattern_type 
    ON knowledge_base_patterns(pattern_type, status);
CREATE INDEX IF NOT EXISTS idx_kb_accuracy 
    ON knowledge_base_patterns(accuracy_rate);

-- 创建触发器自动更新统计字段
CREATE TRIGGER IF NOT EXISTS update_prediction_timestamp 
AFTER UPDATE ON ai_prediction_records
BEGIN
    UPDATE ai_prediction_records SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 视图：预测准确率统计
CREATE VIEW IF NOT EXISTS v_prediction_accuracy_stats AS
SELECT 
    symbol,
    interval,
    DATE(predict_initiated_at) as date,
    COUNT(*) as total_predictions,
    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
    ROUND(
        SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) as accuracy_rate,
    AVG(consensus_confidence) as avg_confidence,
    AVG(accuracy_score) as avg_accuracy_score
FROM ai_prediction_records
WHERE is_correct IS NOT NULL
GROUP BY symbol, interval, DATE(predict_initiated_at)
ORDER BY date DESC;

-- 视图：各AI表现统计
CREATE VIEW IF NOT EXISTS v_ai_performance_stats AS
SELECT 
    ai_name,
    ai_provider,
    DATE(created_at) as date,
    COUNT(*) as total_predictions,
    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
    ROUND(
        SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) as accuracy_rate,
    AVG(response_time_ms) as avg_response_time,
    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
FROM ai_individual_predictions
WHERE is_correct IS NOT NULL
GROUP BY ai_name, ai_provider, DATE(created_at)
ORDER BY date DESC, accuracy_rate DESC;
