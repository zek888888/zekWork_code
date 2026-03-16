from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import hashlib
import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'quant-trading-secret-key-2024'

# Flask-Login 配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 数据库路径
DATABASE_PATH = os.path.expanduser('~/.openclaw/workspace/quant-trading/data/market_data.db')

# 简单的密码哈希（避免Werkzeug版本问题）
def simple_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_hash(password, hashed):
    return simple_hash(password) == hashed

# 用户数据（演示用，生产环境应使用数据库）
users = {
    'admin': {
        'password': simple_hash('admin123'),
        'name': '管理员'
    }
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.name = users[username]['name']

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== 路由 ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and check_hash(password, users[username]['password']):
            user = User(username)
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    """总览仪表板"""
    conn = get_db_connection()
    
    # 获取账户总资产
    try:
        total_assets = conn.execute(
            "SELECT SUM(market_value) as total FROM positions"
        ).fetchone()['total'] or 0
    except:
        total_assets = 1000000  # 默认值
    
    # 获取今日盈亏
    try:
        today_pnl = conn.execute(
            "SELECT SUM(pnl) as pnl FROM positions WHERE date(updated_at) = date('now')"
        ).fetchone()['pnl'] or 0
    except:
        today_pnl = 0
    
    # 获取最新交易信号
    try:
        signals = conn.execute(
            """SELECT symbol, market, signal, total_score, confidence, created_at 
               FROM factor_scores 
               ORDER BY created_at DESC LIMIT 10"""
        ).fetchall()
    except:
        signals = []
    
    # 获取持仓数据
    try:
        positions = conn.execute(
            """SELECT p.*, rp.price as current_price,
                      (p.quantity * rp.price - p.cost_basis) as unrealized_pnl,
                      ((p.quantity * rp.price - p.cost_basis) / p.cost_basis * 100) as pnl_percent
               FROM positions p
               LEFT JOIN realtime_price rp ON p.symbol = rp.symbol
               ORDER BY p.market_value DESC LIMIT 10"""
        ).fetchall()
    except:
        positions = []
    
    # 计算总资产
    try:
        total_value = sum(p['market_value'] for p in positions) if positions else 0
    except:
        total_value = 0
    
    # 获取最新新闻（带情绪分析）
    try:
        news_items = conn.execute(
            """SELECT id, source, title, content, sentiment_score, sentiment_label, 
                      keywords, published_at, created_at
               FROM news 
               ORDER BY published_at DESC LIMIT 10"""
        ).fetchall()
    except:
        news_items = []
    
    # 获取情绪统计
    try:
        sentiment_stats = conn.execute(
            """SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN sentiment_score > 0.2 THEN 1 ELSE 0 END) as bullish,
                SUM(CASE WHEN sentiment_score < -0.2 THEN 1 ELSE 0 END) as bearish,
                AVG(sentiment_score) as avg_score
               FROM news 
               WHERE published_at >= datetime('now', '-24 hours')"""
        ).fetchone()
    except:
        sentiment_stats = {'total': 0, 'bullish': 0, 'bearish': 0, 'avg_score': 0}
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_value=total_value,
                         today_pnl=today_pnl,
                         signals=signals,
                         positions=positions,
                         news_items=news_items,
                         sentiment_stats=sentiment_stats)

@app.route('/market')
@login_required
def market():
    """市场数据页面"""
    conn = get_db_connection()
    
    try:
        # 获取实时价格
        prices = conn.execute(
            """SELECT rp.*, pd.close as prev_close
               FROM realtime_price rp
               LEFT JOIN price_data pd ON rp.symbol = pd.symbol
               WHERE pd.date = (SELECT MAX(date) FROM price_data WHERE symbol = rp.symbol)
               ORDER BY rp.change_percent DESC"""
        ).fetchall()
    except:
        prices = []
    
    conn.close()
    
    return render_template('market.html', prices=prices)

@app.route('/api/market-data/<symbol>')
@login_required
def market_data_api(symbol):
    """获取K线数据API"""
    conn = get_db_connection()
    
    try:
        data = conn.execute(
            """SELECT date, open, high, low, close, volume
               FROM price_data 
               WHERE symbol = ? 
               ORDER BY date DESC LIMIT 100""",
            (symbol,)
        ).fetchall()
        
        result = [{
            'date': row['date'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume']
        } for row in data]
    except:
        result = []
    
    conn.close()
    return jsonify(result)

@app.route('/signals')
@login_required
def signals():
    """交易信号页面"""
    conn = get_db_connection()
    
    # 获取筛选参数
    rating_filter = request.args.get('rating', '')
    market_filter = request.args.get('market', '')
    
    try:
        query = """SELECT fs.*, rp.price as current_price
                   FROM factor_scores fs
                   LEFT JOIN realtime_price rp ON fs.symbol = rp.symbol
                   WHERE 1=1"""
        params = []
        
        if rating_filter:
            query += " AND fs.strength >= ?"
            params.append(rating_filter)
        
        if market_filter:
            query += " AND fs.symbol LIKE ?"
            params.append(f'%{market_filter}%')
        
        query += " ORDER BY fs.created_at DESC LIMIT 50"
        
        signals_data = conn.execute(query, params).fetchall()
    except:
        signals_data = []
    
    conn.close()
    
    return render_template('signals.html', signals=signals_data)

@app.route('/portfolio')
@login_required
def portfolio():
    """持仓管理页面"""
    conn = get_db_connection()
    
    try:
        # 获取持仓列表
        positions = conn.execute(
            """SELECT p.*, rp.price as current_price,
                      (p.quantity * rp.price - p.cost_basis) as unrealized_pnl,
                      ((p.quantity * rp.price - p.cost_basis) / p.cost_basis * 100) as pnl_percent
               FROM positions p
               LEFT JOIN realtime_price rp ON p.symbol = rp.symbol
               ORDER BY p.market_value DESC"""
        ).fetchall()
        
        # 计算总资产
        total_value = sum(p['market_value'] for p in positions) if positions else 0
        
        # 持仓占比数据（用于饼图）
        allocation = [{
            'symbol': p['symbol'],
            'value': p['market_value'],
            'percent': (p['market_value'] / total_value * 100) if total_value > 0 else 0
        } for p in positions]
        
    except:
        positions = []
        allocation = []
    
    conn.close()
    
    return render_template('portfolio.html', 
                         positions=positions,
                         allocation=json.dumps(allocation))

@app.route('/trade', methods=['GET', 'POST'])
@login_required
def trade():
    """交易执行页面"""
    conn = get_db_connection()
    
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        action = request.form.get('action')  # buy/sell
        order_type = request.form.get('order_type')  # market/limit
        quantity = float(request.form.get('quantity', 0))
        price = float(request.form.get('price', 0)) if order_type == 'limit' else None
        stop_loss = float(request.form.get('stop_loss', 0)) or None
        take_profit = float(request.form.get('take_profit', 0)) or None
        
        try:
            conn.execute(
                """INSERT INTO orders (symbol, action, order_type, quantity, price, 
                                     stop_loss, take_profit, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))""",
                (symbol, action, order_type, quantity, price, stop_loss, take_profit)
            )
            conn.commit()
            flash('订单提交成功', 'success')
        except Exception as e:
            flash(f'订单提交失败: {str(e)}', 'danger')
    
    # 获取最近订单
    try:
        recent_orders = conn.execute(
            """SELECT * FROM orders ORDER BY created_at DESC LIMIT 10"""
        ).fetchall()
    except:
        recent_orders = []
    
    conn.close()
    
    return render_template('trade.html', orders=recent_orders)

@app.route('/reports')
@login_required
def reports():
    """报告页面"""
    report_type = request.args.get('type', 'daily')
    
    conn = get_db_connection()
    
    try:
        # 获取交易历史
        if report_type == 'daily':
            history = conn.execute(
                """SELECT * FROM trade_history 
                   WHERE date(created_at) = date('now')
                   ORDER BY created_at DESC"""
            ).fetchall()
        elif report_type == 'weekly':
            history = conn.execute(
                """SELECT * FROM trade_history 
                   WHERE created_at >= date('now', '-7 days')
                   ORDER BY created_at DESC"""
            ).fetchall()
        else:  # monthly
            history = conn.execute(
                """SELECT * FROM trade_history 
                   WHERE created_at >= date('now', '-30 days')
                   ORDER BY created_at DESC"""
            ).fetchall()
        
        # 计算绩效指标
        total_trades = len(history)
        winning_trades = len([h for h in history if h['pnl'] > 0]) if history else 0
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 收益曲线数据
        pnl_data = [h['pnl'] for h in history] if history else []
        cumulative_pnl = []
        cumulative = 0
        for pnl in reversed(pnl_data):
            cumulative += pnl
            cumulative_pnl.append(cumulative)
        
    except:
        history = []
        total_trades = 0
        win_rate = 0
        cumulative_pnl = []
    
    conn.close()
    
    return render_template('reports.html',
                         report_type=report_type,
                         history=history,
                         total_trades=total_trades,
                         win_rate=win_rate,
                         cumulative_pnl=json.dumps(cumulative_pnl))

# ==================== 系统配置模块 ====================

@app.route('/system_config')
@login_required
def system_config():
    """系统配置页面"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from ai_config_manager import AIConfigManager
    
    manager = AIConfigManager()
    ai_configs = manager.get_all_configs()
    
    return render_template('system_config.html', ai_configs=ai_configs)

@app.route('/api/ai_configs', methods=['GET'])
@login_required
def get_ai_configs_api():
    """获取所有AI配置"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from ai_config_manager import AIConfigManager
    
    manager = AIConfigManager()
    configs = manager.get_all_configs()
    
    return jsonify(configs)

@app.route('/api/ai_configs', methods=['POST'])
@login_required
def add_ai_config_api():
    """添加AI配置"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from ai_config_manager import AIConfigManager, AIConfig
    
    data = request.json
    
    config = AIConfig(
        name=data.get('name'),
        provider=data.get('provider'),
        model=data.get('model'),
        api_key=data.get('api_key'),
        base_url=data.get('base_url'),
        temperature=float(data.get('temperature', 0.7)),
        max_tokens=int(data.get('max_tokens', 2000)),
        timeout=int(data.get('timeout', 30)),
        weight=float(data.get('weight', 1.0)),
        status=data.get('status', 'active'),
        priority=int(data.get('priority', 1)),
        description=data.get('description', '')
    )
    
    manager = AIConfigManager()
    config_id = manager.add_ai_config(config)
    
    return jsonify({'success': True, 'id': config_id})

@app.route('/api/ai_configs/<int:config_id>', methods=['GET'])
@login_required
def get_ai_config_api(config_id):
    """获取单个AI配置"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from ai_config_manager import AIConfigManager
    
    manager = AIConfigManager()
    config = manager.get_ai_config(config_id)
    
    if config:
        return jsonify({
            'id': config.id,
            'name': config.name,
            'provider': config.provider,
            'model': config.model,
            'base_url': config.base_url,
            'temperature': config.temperature,
            'max_tokens': config.max_tokens,
            'timeout': config.timeout,
            'weight': config.weight,
            'status': config.status,
            'priority': config.priority,
            'description': config.description
        })
    else:
        return jsonify({'error': 'Config not found'}), 404

@app.route('/api/ai_configs/<int:config_id>', methods=['PUT'])
@login_required
def update_ai_config_api(config_id):
    """更新AI配置"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from ai_config_manager import AIConfigManager
    
    data = request.json
    manager = AIConfigManager()
    
    success = manager.update_ai_config(config_id, data)
    
    return jsonify({'success': success})

@app.route('/api/ai_configs/<int:config_id>', methods=['DELETE'])
@login_required
def delete_ai_config_api(config_id):
    """删除AI配置"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from ai_config_manager import AIConfigManager
    
    manager = AIConfigManager()
    success = manager.delete_ai_config(config_id)
    
    return jsonify({'success': success})

@app.route('/api/ai_configs/init_default', methods=['POST'])
@login_required
def init_default_ai_config():
    """初始化默认AI配置"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from ai_config_manager import AIConfigManager
    
    manager = AIConfigManager()
    manager.init_default_config()
    
    return jsonify({'success': True})

@app.route('/api/news/analyze', methods=['POST'])
@login_required
def analyze_news_api():
    """触发新闻AI分析"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/ai_models'))
    from news_analyzer import NewsAnalyzer
    
    data = request.json
    hours = data.get('hours', 24)
    limit = data.get('limit', 50)
    
    analyzer = NewsAnalyzer()
    analyzer.batch_analyze_news(hours=hours, limit=limit)
    
    return jsonify({'success': True, 'message': '分析任务已启动'})

@app.route('/api/news/with_decision')
@login_required
def get_news_with_decision_api():
    """获取带AI决策的新闻"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/ai_models'))
    from news_analyzer import NewsAnalyzer
    
    hours = request.args.get('hours', type=int, default=24)
    limit = request.args.get('limit', type=int, default=50)
    
    analyzer = NewsAnalyzer()
    news_list = analyzer.get_news_with_decision(hours=hours, limit=limit)
    
    return jsonify(news_list)

@app.route('/api/news/summary')
@login_required
def get_news_summary_api():
    """获取新闻汇总"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/research-layer/news-sentiment-scan'))
    from news_summary import NewsSummarizer
    
    hours = request.args.get('hours', type=int, default=24)
    
    summarizer = NewsSummarizer()
    result = summarizer.process_and_summarize(hours=hours)
    
    return jsonify(result)

# ==================== 推特数据模块 API ====================

@app.route('/api/twitter/watchlist')
@login_required
def get_twitter_watchlist_api():
    """获取所有推特观察人"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from twitter_watchlist_manager import TwitterWatchlistManager
    
    manager = TwitterWatchlistManager()
    items = manager.get_all_watchlist()
    
    return jsonify(items)

@app.route('/api/twitter/watchlist/<int:item_id>')
@login_required
def get_twitter_watchlist_item_api(item_id):
    """获取单个观察人"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from twitter_watchlist_manager import TwitterWatchlistManager
    
    manager = TwitterWatchlistManager()
    item = manager.get_watchlist_item(item_id)
    
    if item:
        return jsonify({
            'id': item.id,
            'username': item.username,
            'display_name': item.display_name,
            'category': item.category,
            'priority': item.priority,
            'is_active': item.is_active,
            'description': item.description,
            'last_fetch_at': item.last_fetch_at
        })
    else:
        return jsonify({'error': 'Not found'}), 404

@app.route('/api/twitter/watchlist', methods=['POST'])
@login_required
def add_twitter_watchlist_api():
    """添加推特观察人"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from twitter_watchlist_manager import TwitterWatchlistManager, TwitterWatchlistItem
    
    data = request.json
    
    item = TwitterWatchlistItem(
        username=data.get('username', '').replace('@', ''),
        display_name=data.get('display_name', ''),
        category=data.get('category', 'trader'),
        priority=int(data.get('priority', 1)),
        is_active=data.get('is_active', True),
        description=data.get('description', '')
    )
    
    manager = TwitterWatchlistManager()
    item_id = manager.add_watchlist_item(item)
    
    return jsonify({'success': True, 'id': item_id})

@app.route('/api/twitter/watchlist/<int:item_id>', methods=['PUT'])
@login_required
def update_twitter_watchlist_api(item_id):
    """更新推特观察人"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from twitter_watchlist_manager import TwitterWatchlistManager
    
    data = request.json
    manager = TwitterWatchlistManager()
    
    success = manager.update_watchlist_item(item_id, data)
    
    return jsonify({'success': success})

@app.route('/api/twitter/watchlist/<int:item_id>', methods=['DELETE'])
@login_required
def delete_twitter_watchlist_api(item_id):
    """删除推特观察人"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from twitter_watchlist_manager import TwitterWatchlistManager
    
    manager = TwitterWatchlistManager()
    success = manager.delete_watchlist_item(item_id)
    
    return jsonify({'success': success})

@app.route('/api/twitter/watchlist/init_default', methods=['POST'])
@login_required
def init_default_twitter_watchlist_api():
    """初始化默认推特观察人列表"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
    from twitter_watchlist_manager import TwitterWatchlistManager
    
    manager = TwitterWatchlistManager()
    manager.init_default_watchlist()
    
    return jsonify({'success': True})

@app.route('/api/twitter/fetch', methods=['POST'])
@login_required
def fetch_twitter_api():
    """手动触发获取推特数据"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/research-layer/twitter-sentiment'))
    from twitter_fetcher import TwitterFetcher
    
    fetcher = TwitterFetcher()
    result = fetcher.fetch_all_active(hours_back=1)
    
    return jsonify({
        'success': True,
        'total_fetched': result['total_fetched'],
        'total_new': result['total_new'],
        'total_duplicates': result['total_duplicates'],
        'by_user': result['by_user']
    })

@app.route('/api/twitter/posts')
@login_required
def get_twitter_posts_api():
    """获取推特推文列表"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/research-layer/twitter-sentiment'))
    from twitter_fetcher import TwitterFetcher
    
    # hours 可以是数字或 'all'
    hours_param = request.args.get('hours', default='24')
    try:
        hours = int(hours_param)
    except ValueError:
        hours = hours_param  # 保持为字符串 'all'
    
    username = request.args.get('username')
    sentiment = request.args.get('sentiment')
    limit = request.args.get('limit', type=int, default=100)
    
    fetcher = TwitterFetcher()
    posts = fetcher.get_recent_tweets(
        hours=hours,
        username=username,
        sentiment=sentiment,
        limit=limit
    )
    
    return jsonify(posts)

@app.route('/api/twitter/analyze', methods=['POST'])
@login_required
def analyze_twitter_api():
    """触发推特AI分析"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/ai_models'))
    from twitter_analyzer import TwitterAnalyzer
    
    data = request.json
    hours = data.get('hours', 24)
    limit = data.get('limit', 50)
    
    analyzer = TwitterAnalyzer()
    result = analyzer.batch_analyze_pending(hours=hours, limit=limit)
    
    return jsonify({
        'success': True,
        'total': result['total'],
        'analyzed': result['analyzed'],
        'results': result['results']
    })

@app.route('/api/twitter/stats')
@login_required
def get_twitter_stats_api():
    """获取推特统计信息"""
    import sys
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/research-layer/twitter-sentiment'))
    from twitter_fetcher import TwitterFetcher
    
    hours = request.args.get('hours', type=int, default=24)
    
    fetcher = TwitterFetcher()
    stats = fetcher.get_stats(hours=hours)
    
    return jsonify(stats)

@app.route('/api/twitter/test', methods=['POST'])
@login_required
def test_twitter_api():
    """测试Twitter API连接"""
    try:
        import sys
        sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
        from twitter_api_client import TwitterAPIClient
        
        client = TwitterAPIClient()
        
        # 测试获取用户
        user = client.get_user_by_username("twitter")
        
        if user:
            return jsonify({
                'success': True,
                'message': f'API连接正常！可访问用户: {user.get("name", "Unknown")}'
            })
        else:
            # 用户获取失败，可能是订阅限制
            return jsonify({
                'success': False,
                'message': 'API认证成功但无法获取数据。请检查Twitter API订阅状态（需要Basic $100/月或更高）'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'API连接失败: {str(e)}'
        })

@app.route('/api/twitter/config', methods=['POST'])
@login_required
def save_twitter_config():
    """保存Twitter API配置"""
    data = request.json
    
    try:
        # 保存到.env.twitter文件
        env_path = os.path.expanduser('~/.openclaw/workspace/quant-trading/.env.twitter')
        
        with open(env_path, 'w') as f:
            f.write(f"# Twitter API 凭证\n")
            f.write(f"TWITTER_BEARER_TOKEN={data.get('bearer_token', '')}\n")
            f.write(f"TWITTER_API_STATUS={data.get('status', 'inactive')}\n")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/news/fetch_free', methods=['POST'])
@login_required
def fetch_free_news_api():
    """手动触发免费新闻获取"""
    try:
        import sys
        sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/research-layer/news-sentiment-scan'))
        from free_news_fetcher import FreeNewsFetcher
        
        fetcher = FreeNewsFetcher()
        result = fetcher.fetch_all()
        
        return jsonify({
            'success': True,
            'message': f"获取完成！共 {result['saved']} 条新闻",
            'total': result['total'],
            'saved': result['saved'],
            'stats': result['stats']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/twitter/quota')
@login_required
def get_twitter_quota_api():
    """获取Twitter API额度状态"""
    from datetime import datetime, timedelta
    
    # 计算下次重置时间
    now = datetime.now()
    if now.day == 1:
        next_reset = now
    else:
        if now.month == 12:
            next_reset = datetime(now.year + 1, 1, 1)
        else:
            next_reset = datetime(now.year, now.month + 1, 1)
    
    days_remaining = (next_reset - now).days + 1
    
    # 检查是否有真实数据（判断额度是否可用）
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM twitter_posts 
        WHERE tweet_id NOT LIKE 'test_%' 
        AND tweet_id NOT LIKE 'demo_%'
        AND tweet_id NOT LIKE 'mock_%'
        AND created_at >= datetime('now', '-1 hours')
    ''')
    
    recent_real_tweets = cursor.fetchone()[0]
    conn.close()
    
    # 额度状态判断
    if recent_real_tweets > 0:
        status = 'active'
        status_text = '额度充足'
    else:
        status = 'limited'
        status_text = '已用完（演示数据）'
    
    return jsonify({
        'current_status': status,
        'status_text': status_text,
        'next_reset_date': next_reset.strftime('%Y-%m-%d'),
        'days_until_reset': days_remaining,
        'monthly_quota': 1500,
        'recent_real_tweets': recent_real_tweets,
        'data_source': 'demo' if status == 'limited' else 'api'
    })

@app.route('/api/realtime-prices')
@login_required
def realtime_prices_api():
    """实时价格API"""
    conn = get_db_connection()
    
    try:
        prices = conn.execute(
            """SELECT symbol, price, change_percent, updated_at
               FROM realtime_price ORDER BY change_percent DESC"""
        ).fetchall()
        
        result = [{
            'symbol': p['symbol'],
            'price': p['price'],
            'change_percent': p['change_percent'],
            'updated_at': p['updated_at']
        } for p in prices]
    except:
        result = []
    
    conn.close()
    return jsonify(result)

# ==================== 市场信息总览 API ====================

@app.route('/market_overview')
@login_required
def market_overview():
    """市场信息总览页面"""
    return render_template('market_overview.html')

@app.route('/api/news/latest')
@login_required
def latest_news_api():
    """获取最新新闻 - 支持时间范围筛选"""
    conn = get_db_connection()
    
    # 获取查询参数
    hours = request.args.get('hours', type=int, default=24)
    start_time = request.args.get('start_time')  # ISO格式
    end_time = request.args.get('end_time')      # ISO格式
    limit = request.args.get('limit', type=int, default=50)
    sentiment_filter = request.args.get('sentiment')  # bullish/bearish/neutral/all
    
    try:
        query = """SELECT id, source, title, content, sentiment_score, sentiment_label, 
                      keywords, published_at, created_at
               FROM news WHERE 1=1"""
        params = []
        
        # 时间范围筛选
        if start_time and end_time:
            query += " AND published_at BETWEEN ? AND ?"
            params.extend([start_time, end_time])
        elif hours:
            since = (datetime.now() - timedelta(hours=hours)).isoformat()
            query += " AND published_at > ?"
            params.append(since)
        
        # 情绪筛选
        if sentiment_filter == 'bullish':
            query += " AND sentiment_score > 0.2"
        elif sentiment_filter == 'bearish':
            query += " AND sentiment_score < -0.2"
        elif sentiment_filter == 'neutral':
            query += " AND sentiment_score BETWEEN -0.2 AND 0.2"
        
        query += " ORDER BY published_at DESC LIMIT ?"
        params.append(limit)
        
        news = conn.execute(query, params).fetchall()
        
        result = [{
            'id': n['id'],
            'source': n['source'],
            'title': n['title'],
            'content': n['content'][:200] + '...' if n['content'] and len(n['content']) > 200 else n['content'],
            'sentiment_score': n['sentiment_score'] or 0,
            'sentiment_label': n['sentiment_label'] or 'neutral',
            'keywords': n['keywords'] or '',
            'published_at': n['published_at'],
            'created_at': n['created_at']
        } for n in news]
        
        # 获取统计信息
        stats_query = """SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN sentiment_score > 0.2 THEN 1 ELSE 0 END) as bullish,
            SUM(CASE WHEN sentiment_score < -0.2 THEN 1 ELSE 0 END) as bearish,
            AVG(sentiment_score) as avg_sentiment
            FROM news WHERE published_at > ?"""
        
        since_for_stats = (datetime.now() - timedelta(hours=hours)).isoformat()
        stats = conn.execute(stats_query, (since_for_stats,)).fetchone()
        
        response = {
            'news': result,
            'stats': {
                'total': stats['total'] or 0,
                'bullish': stats['bullish'] or 0,
                'bearish': stats['bearish'] or 0,
                'neutral': (stats['total'] or 0) - (stats['bullish'] or 0) - (stats['bearish'] or 0),
                'avg_sentiment': round(stats['avg_sentiment'] or 0, 3)
            },
            'filters': {
                'hours': hours,
                'sentiment': sentiment_filter,
                'limit': limit
            }
        }
        
    except Exception as e:
        response = {'news': [], 'stats': {}, 'error': str(e)}
    
    conn.close()
    return jsonify(response)

@app.route('/api/news/stats')
@login_required
def news_stats_api():
    """获取新闻统计信息"""
    conn = get_db_connection()
    
    hours = request.args.get('hours', type=int, default=24)
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    
    try:
        # 新闻统计
        stats = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN sentiment_score > 0.2 THEN 1 ELSE 0 END) as bullish,
                SUM(CASE WHEN sentiment_score < -0.2 THEN 1 ELSE 0 END) as bearish,
                AVG(sentiment_score) as avg_sentiment,
                MAX(published_at) as latest_news_time
            FROM news WHERE published_at > ?
        """, (since,)).fetchone()
        
        # 抓取日志统计
        fetch_stats = conn.execute("""
            SELECT 
                COUNT(*) as fetch_count,
                SUM(items_new) as total_new,
                MAX(fetch_time) as last_fetch_time
            FROM news_fetch_log 
            WHERE fetch_time > ? AND status = 'success'
        """, (since,)).fetchone()
        
        result = {
            'period_hours': hours,
            'news_stats': {
                'total': stats['total'] or 0,
                'bullish': stats['bullish'] or 0,
                'bearish': stats['bearish'] or 0,
                'neutral': (stats['total'] or 0) - (stats['bullish'] or 0) - (stats['bearish'] or 0),
                'avg_sentiment': round(stats['avg_sentiment'] or 0, 3),
                'latest_news_time': stats['latest_news_time']
            },
            'fetch_stats': {
                'fetch_count': fetch_stats['fetch_count'] or 0,
                'total_new_items': fetch_stats['total_new'] or 0,
                'last_fetch_time': fetch_stats['last_fetch_time']
            }
        }
        
    except Exception as e:
        result = {'error': str(e)}
    
    conn.close()
    return jsonify(result)

@app.route('/api/news/fetch', methods=['POST'])
@login_required
def fetch_news_api():
    """人工触发获取新闻"""
    try:
        import sys
        sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/research-layer/news-sentiment-scan'))
        from scan import fetch_and_save_news
        
        # 执行获取
        result = fetch_and_save_news(source='jin10', with_sentiment=True)
        
        return jsonify({
            'success': True,
            'message': '获取完成',
            'fetched': result.get('fetched', 0),
            'saved': result.get('saved', 0),
            'duplicates': result.get('duplicates', 0),
            'status': result.get('status', 'success'),
            'fetch_time': result.get('fetch_time')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/crypto/btc')
@login_required
def btc_data_api():
    """获取BTC K线数据"""
    import random
    from datetime import datetime, timedelta
    
    interval = request.args.get('interval', '15m')
    
    # 生成模拟数据（实际项目中应从币安API获取）
    base_price = 67000
    klines = {'times': [], 'candles': [], 'volumes': [], 'macd': [], 'macdHist': []}
    
    # 根据interval确定数据点数量
    points = 100 if interval == '15m' else 50
    
    for i in range(points):
        time = datetime.now() - timedelta(minutes=15 * (points - i))
        klines['times'].append(time.strftime('%H:%M'))
        
        # 生成模拟K线数据
        open_p = base_price + random.uniform(-500, 500)
        close_p = open_p + random.uniform(-200, 200)
        high_p = max(open_p, close_p) + random.uniform(0, 100)
        low_p = min(open_p, close_p) - random.uniform(0, 100)
        
        klines['candles'].append([open_p, close_p, low_p, high_p])
        klines['volumes'].append(random.uniform(100, 1000))
        klines['macd'].append(random.uniform(-50, 50))
        klines['macdHist'].append(random.uniform(-20, 20))
    
    return jsonify({
        'price': base_price + random.uniform(-100, 100),
        'change': random.uniform(-2, 2),
        'klines': klines
    })

@app.route('/api/gmgn/hot')
@login_required
def gmgn_hot_api():
    """获取GMGN热门币种（模拟数据）"""
    import random
    
    # 模拟GMGN热门币种数据
    tokens = [
        {'name': 'PEPE', 'symbol': 'PEPE', 'price': 0.000001234, 'change_24h': 45.23},
        {'name': 'SHIB', 'symbol': 'SHIB', 'price': 0.00002845, 'change_24h': 12.56},
        {'name': 'DOGE', 'symbol': 'DOGE', 'price': 0.15678, 'change_24h': 8.92},
        {'name': 'FLOKI', 'symbol': 'FLOKI', 'price': 0.00004567, 'change_24h': 23.45},
        {'name': 'BONK', 'symbol': 'BONK', 'price': 0.00002341, 'change_24h': -5.67},
        {'name': 'WIF', 'symbol': 'WIF', 'price': 2.456, 'change_24h': 34.12},
        {'name': 'BOME', 'symbol': 'BOME', 'price': 0.01234, 'change_24h': 67.89},
        {'name': 'POPCAT', 'symbol': 'POPCAT', 'price': 0.567, 'change_24h': 15.34},
        {'name': 'MOG', 'symbol': 'MOG', 'price': 0.000000456, 'change_24h': 89.12},
        {'name': 'SPX', 'symbol': 'SPX', 'price': 0.123, 'change_24h': -12.34}
    ]
    
    # 随机调整价格
    for token in tokens:
        token['price'] *= (1 + random.uniform(-0.05, 0.05))
    
    return jsonify(tokens)


# ========== 币安实时数据API ==========
import requests
import hmac
import hashlib
import urllib.parse

BINANCE_API_BASE = 'https://api.binance.com'

def get_binance_klines(symbol='BTCUSDT', interval='15m', limit=100):
    """获取币安K线数据"""
    try:
        url = f'{BINANCE_API_BASE}/api/v3/klines'
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        klines = {
            'times': [],
            'candles': [],
            'volumes': [],
            'macd': [],
            'macdHist': []
        }
        
        for item in data:
            # 时间格式化
            timestamp = datetime.fromtimestamp(item[0] / 1000)
            klines['times'].append(timestamp.strftime('%H:%M'))
            # K线数据 [open, close, low, high]
            klines['candles'].append([
                float(item[1]),   # open
                float(item[4]),   # close
                float(item[3]),   # low
                float(item[2])    # high
            ])
            klines['volumes'].append(float(item[5]))
        
        # 计简单MACD
        closes = [c[1] for c in klines['candles']]
        klines['macd'], klines['macdHist'] = calculate_macd(closes)
        
        return klines
    except Exception as e:
        print(f"获取币安数据失败: {e}")
        return None

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    if len(prices) < slow:
        return [0] * len(prices), [0] * len(prices)
    
    # 计算EMA
    def ema(data, period):
        multiplier = 2 / (period + 1)
        ema_values = [data[0]]
        for price in data[1:]:
            ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])
        return ema_values
    
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    
    # MACD线 = 快线EMA - 慢线EMA
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    # 信号线 = MACD的EMA
    signal_line = ema(macd_line, signal)
    # 柱状图 = MACD - 信号
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    
    return macd_line, histogram

def get_binance_ticker(symbol='BTCUSDT'):
    """获取币安24小时涨跌数据"""
    try:
        url = f'{BINANCE_API_BASE}/api/v3/ticker/24hr'
        params = {'symbol': symbol}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            'price': float(data['lastPrice']),
            'change': float(data['priceChangePercent']),
            'high': float(data['highPrice']),
            'low': float(data['lowPrice']),
            'volume': float(data['volume'])
        }
    except Exception as e:
        print(f"获取币安ticker失败: {e}")
        return None

def get_klines_from_db(symbol: str, interval: str, limit: int = 200):
    """从数据库获取K线数据（优化版，限制200条）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 使用索引优化查询
        cursor.execute('''
            SELECT timestamp, open, high, low, close, volume,
                   macd, macd_signal, macd_hist,
                   kdj_k, kdj_d, kdj_j
            FROM kline_data
            WHERE symbol = ? AND interval = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (symbol, interval, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        # 转换为前端需要的格式
        klines = {
            'times': [],
            'candles': [],
            'volumes': [],
            'macd': [],
            'macdSignal': [],
            'macdHist': [],
            'kdjK': [],
            'kdjD': [],
            'kdjJ': []
        }
        
        # 格式化时间函数
        def format_time(ts_str, interval):
            try:
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00').replace('+00:00', ''))
                if interval in ['5m', '15m', '30m', '1h']:
                    return ts.strftime('%m-%d %H:%M')
                elif interval in ['4h', '12h']:
                    return ts.strftime('%m-%d %H:%M')
                else:
                    return ts.strftime('%Y-%m-%d')
            except:
                return ts_str
        
        # 逆序遍历（从旧到新）
        for row in reversed(rows):
            klines['times'].append(format_time(row['timestamp'], interval))
            klines['candles'].append([row['open'], row['close'], row['low'], row['high']])
            klines['volumes'].append(row['volume'])
            klines['macd'].append(float(row['macd']) if row['macd'] is not None else 0)
            klines['macdSignal'].append(float(row['macd_signal']) if row['macd_signal'] is not None else 0)
            klines['macdHist'].append(float(row['macd_hist']) if row['macd_hist'] is not None else 0)
            klines['kdjK'].append(float(row['kdj_k']) if row['kdj_k'] is not None else 50)
            klines['kdjD'].append(float(row['kdj_d']) if row['kdj_d'] is not None else 50)
            klines['kdjJ'].append(float(row['kdj_j']) if row['kdj_j'] is not None else 50)
        
        return klines
    except Exception as e:
        print(f"从数据库获取K线失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def calculate_kdj(prices, highs, lows, n=9, m1=3, m2=3):
    """计算KDJ指标"""
    try:
        import pandas as pd
        df = pd.DataFrame({'close': prices, 'high': highs, 'low': lows})
        
        low_list = df['low'].rolling(window=n, min_periods=n).min()
        high_list = df['high'].rolling(window=n, min_periods=n).max()
        rsv = (df['close'] - low_list) / (high_list - low_list) * 100
        
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        d = k.ewm(com=m2-1, adjust=False).mean()
        j = 3 * k - 2 * d
        
        return k.tolist(), d.tolist(), j.tolist()
    except:
        return [50]*len(prices), [50]*len(prices), [50]*len(prices)

@app.route('/api/crypto/binance/<symbol>')
@login_required
def binance_data_api(symbol):
    """获取币安实时数据（优化版，限制200条，响应更快）"""
    try:
        interval = request.args.get('interval', '15m')
        
        # 格式化symbol
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'
        
        # 并行获取数据：从数据库获取K线 + 获取24h涨跌
        klines = get_klines_from_db(symbol, interval, 200)
        ticker = get_binance_ticker(symbol)
        
        if klines and ticker:
            return jsonify({
                'success': True,
                'symbol': symbol,
                'price': ticker['price'],
                'change': ticker['change'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['volume'],
                'klines': klines,
                'indicators': {
                    'macd': klines['macd'][-1] if klines['macd'] else 0,
                    'macdSignal': klines['macdSignal'][-1] if klines['macdSignal'] else 0,
                    'macdHist': klines['macdHist'][-1] if klines['macdHist'] else 0,
                    'kdjK': klines['kdjK'][-1] if klines['kdjK'] else 50,
                    'kdjD': klines['kdjD'][-1] if klines['kdjD'] else 50,
                    'kdjJ': klines['kdjJ'][-1] if klines['kdjJ'] else 50
                },
                'timestamp': datetime.now().isoformat(),
                'source': 'db'
            })
        elif ticker:
            # 数据库无数据，使用币安API获取实时数据
            klines_api = get_binance_klines(symbol, interval, 200)
            
            if klines_api:
                return jsonify({
                    'success': True,
                    'symbol': symbol,
                    'price': ticker['price'],
                    'change': ticker['change'],
                    'high': ticker['high'],
                    'low': ticker['low'],
                    'volume': ticker['volume'],
                    'klines': klines_api,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'api'
                })
        
        # 返回模拟数据作为后备
        import random
        base_price = 67000
        mock_klines = {
            'times': [],
            'candles': [],
            'volumes': [],
            'macd': [],
            'macdSignal': [],
            'macdHist': [],
            'kdjK': [],
            'kdjD': [],
            'kdjJ': []
        }
        for i in range(100):
            time = datetime.now() - timedelta(minutes=15 * (100 - i))
            mock_klines['times'].append(time.strftime('%H:%M'))
            open_p = base_price + random.uniform(-500, 500)
            close_p = open_p + random.uniform(-200, 200)
            high_p = max(open_p, close_p) + random.uniform(0, 100)
            low_p = min(open_p, close_p) - random.uniform(0, 100)
            mock_klines['candles'].append([open_p, close_p, low_p, high_p])
            mock_klines['volumes'].append(random.uniform(100, 1000))
            mock_klines['macd'].append(random.uniform(-50, 50))
            mock_klines['macdSignal'].append(random.uniform(-50, 50))
            mock_klines['macdHist'].append(random.uniform(-20, 20))
            mock_klines['kdjK'].append(random.uniform(0, 100))
            mock_klines['kdjD'].append(random.uniform(0, 100))
            mock_klines['kdjJ'].append(random.uniform(0, 100))
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'price': base_price + random.uniform(-100, 100),
            'change': random.uniform(-2, 2),
            'high': base_price * 1.02,
            'low': base_price * 0.98,
            'volume': random.uniform(10000, 50000),
            'klines': mock_klines,
            'timestamp': datetime.now().isoformat(),
            'source': 'mock'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== AI预测分析API ==========
@app.route('/api/crypto/predict', methods=['POST'])
@login_required
def crypto_predict_api():
    """使用AI分析预测加密货币价格走势"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTCUSDT')
        
        # 获取币安数据作为分析依据
        ticker = get_binance_ticker(symbol)
        klines = get_binance_klines(symbol, '15m', 50)
        
        if not ticker or not klines:
            return jsonify({
                'success': False,
                'error': '无法获取市场数据'
            }), 400
        
        # 计算技术指标
        closes = [c[1] for c in klines['candles']]
        volumes = klines['volumes']
        
        # 计算近期趋势
        recent_closes = closes[-20:]
        price_change_1h = (recent_closes[-1] - recent_closes[-4]) / recent_closes[-4] * 100 if len(recent_closes) >= 4 else 0
        price_change_24h = ticker['change']
        
        # 计算成交量变化
        recent_volume = sum(volumes[-5:]) / 5
        prev_volume = sum(volumes[-10:-5]) / 5 if len(volumes) >= 10 else recent_volume
        volume_change = (recent_volume - prev_volume) / prev_volume * 100 if prev_volume > 0 else 0
        
        # 构建AI分析提示词
        analysis_prompt = f"""你是一个专业的加密货币分析师。请根据以下数据对{symbol}进行技术分析并预测短期走势：

【当前市场数据】
- 当前价格: ${ticker['price']:,.2f}
- 24h涨跌幅: {price_change_24h:+.2f}%
- 1h涨跌幅: {price_change_1h:+.2f}%
- 24h最高: ${ticker['high']:,.2f}
- 24h最低: ${ticker['low']:,.2f}
- 成交量变化: {volume_change:+.2f}%

【技术指标分析】
- 最新MACD柱状值: {klines['macdHist'][-1]:.2f}
- 价格位于24h区间位置: {(ticker['price'] - ticker['low']) / (ticker['high'] - ticker['low']) * 100:.1f}%

请分析并预测：
1. 未来15分钟价格走势 (看涨/看跌/中性)
2. 未来1小时价格走势 (看涨/看跌/中性)
3. 给出置信度(0-1)和分析理由

请以JSON格式返回：
{{
    "predictions": [
        {{"timeframe": "15分钟后", "prediction": "bullish/bearish/neutral", "confidence": 0.75, "reason": "..."}},
        {{"timeframe": "1小时后", "prediction": "bullish/bearish/neutral", "confidence": 0.65, "reason": "..."}}
    ]
}}
"""
        
        # 调用AI配置进行分析
        try:
            sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/quant-trading/config-layer'))
            from ai_config_manager import AIConfigManager
            
            manager = AIConfigManager()
            active_configs = manager.get_active_configs()
            
            if not active_configs:
                # 没有AI配置，使用模拟数据
                raise Exception("无可用AI配置")
            
            # 使用第一个活跃的AI配置进行分析
            ai_config = active_configs[0]
            
            # 根据不同提供商调用API
            if ai_config.provider == 'deepseek':
                predictions = call_deepseek_api(ai_config, analysis_prompt)
            elif ai_config.provider == 'moonshot':
                predictions = call_moonshot_api(ai_config, analysis_prompt)
            else:
                # 其他提供商使用通用OpenAI格式
                predictions = call_openai_compatible_api(ai_config, analysis_prompt)
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'predictions': predictions,
                'timestamp': datetime.now().isoformat(),
                'ai_provider': ai_config.provider,
                'ai_model': ai_config.model
            })
            
        except Exception as ai_error:
            print(f"AI调用失败，使用模拟数据: {ai_error}")
            # 使用模拟数据作为后备
            import random
            
            # 根据技术指标生成合理的预测
            macd_trend = klines['macdHist'][-1] > klines['macdHist'][-5] if len(klines['macdHist']) >= 5 else True
            price_above_mid = ticker['price'] > (ticker['high'] + ticker['low']) / 2
            
            predictions = [
                {
                    'timeframe': '15分钟后',
                    'prediction': 'bullish' if macd_trend else 'bearish',
                    'confidence': 0.65 + random.uniform(0, 0.25),
                    'reason': f"技术面显示MACD呈现{'上行' if macd_trend else '下行'}趋势，当前价格位于24h区间{'上半区' if price_above_mid else '下半区'}，预计短期{'小幅上涨' if macd_trend else '小幅回调'}。"
                },
                {
                    'timeframe': '1小时后',
                    'prediction': 'neutral' if abs(price_change_24h) < 1 else ('bullish' if price_change_24h < -2 else 'bearish'),
                    'confidence': 0.55 + random.uniform(0, 0.20),
                    'reason': f"综合24h涨跌幅{price_change_24h:+.2f}%和当前市场情绪，建议{'持续观察' if abs(price_change_24h) < 2 else '注意回调风险'}，等待更明确信号。"
                }
            ]
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'predictions': predictions,
                'timestamp': datetime.now().isoformat(),
                'source': 'mock'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def call_deepseek_api(config, prompt):
    """调用DeepSeek API"""
    import requests
    
    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': config.model,
        'messages': [
            {'role': 'system', 'content': '你是一个专业的加密货币分析师，请以JSON格式返回分析结果。'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7,
        'max_tokens': 1000
    }
    
    response = requests.post(
        f'{config.base_url}/chat/completions',
        headers=headers,
        json=data,
        timeout=30
    )
    response.raise_for_status()
    result = response.json()
    
    # 解析AI返回的JSON
    content = result['choices'][0]['message']['content']
    # 提取JSON部分
    import json
    import re
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        predictions_data = json.loads(json_match.group())
        return predictions_data.get('predictions', [])
    return []

def call_moonshot_api(config, prompt):
    """调用Moonshot(Kimi) API"""
    import requests
    
    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': config.model,
        'messages': [
            {'role': 'system', 'content': '你是一个专业的加密货币分析师，请以JSON格式返回分析结果。'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7,
        'max_tokens': 1000
    }
    
    response = requests.post(
        f'{config.base_url}/chat/completions',
        headers=headers,
        json=data,
        timeout=30
    )
    response.raise_for_status()
    result = response.json()
    
    import json
    import re
    content = result['choices'][0]['message']['content']
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        predictions_data = json.loads(json_match.group())
        return predictions_data.get('predictions', [])
    return []

def call_openai_compatible_api(config, prompt):
    """调用通用OpenAI兼容API"""
    import requests
    
    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': config.model,
        'messages': [
            {'role': 'system', 'content': '你是一个专业的加密货币分析师，请以JSON格式返回分析结果。'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7,
        'max_tokens': 1000
    }
    
    base_url = config.base_url or 'https://api.openai.com/v1'
    response = requests.post(
        f'{base_url}/chat/completions',
        headers=headers,
        json=data,
        timeout=30
    )
    response.raise_for_status()
    result = response.json()
    
    import json
    import re
    content = result['choices'][0]['message']['content']
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        predictions_data = json.loads(json_match.group())
        return predictions_data.get('predictions', [])
    return []

# 聪明钱包相关API
smart_wallets = []  # 内存存储，实际应使用数据库

@app.route('/api/smart_wallet/list')
@login_required
def list_wallets_api():
    """获取追踪的钱包列表"""
    import random
    
    # 为每个钱包生成模拟持仓数据
    result = []
    for wallet in smart_wallets:
        holdings = [
            {'token': 'ETH', 'amount': random.uniform(10, 100), 'value': random.uniform(20000, 200000)},
            {'token': 'USDT', 'amount': random.uniform(1000, 10000), 'value': random.uniform(1000, 10000)},
            {'token': 'PEPE', 'amount': random.uniform(1000000, 10000000), 'value': random.uniform(1000, 10000)}
        ]
        total_value = sum(h['value'] for h in holdings)
        
        result.append({
            'address': wallet['address'],
            'total_value': total_value,
            'holdings': holdings
        })
    
    return jsonify(result)

@app.route('/api/smart_wallet/add', methods=['POST'])
@login_required
def add_wallet_api():
    """添加聪明钱包"""
    address = request.form.get('address', '').strip()
    
    if not address or not address.startswith('0x') or len(address) != 42:
        return jsonify({'error': '无效的钱包地址'}), 400
    
    # 检查是否已存在
    if any(w['address'].lower() == address.lower() for w in smart_wallets):
        return jsonify({'error': '钱包已存在'}), 400
    
    smart_wallets.append({
        'address': address,
        'added_at': datetime.now().isoformat()
    })
    
    return jsonify({'success': True, 'address': address})

@app.route('/api/smart_wallet/remove', methods=['POST'])
@login_required
def remove_wallet_api():
    """移除聪明钱包"""
    address = request.form.get('address', '').strip()
    
    global smart_wallets
    smart_wallets = [w for w in smart_wallets if w['address'].lower() != address.lower()]
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
