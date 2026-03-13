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
