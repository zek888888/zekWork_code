#!/usr/bin/env python3
"""
Twitter OAuth 2.0 授权流程
获取发推权限的 Access Token

使用方法:
1. 填写 .env.twitter.oauth2 中的 CLIENT_ID 和 CLIENT_SECRET
2. 运行: python3 twitter_oauth2_authorize.py
3. 浏览器会自动打开授权页面
4. 授权后，令牌会自动保存到 .env.twitter.oauth2
"""

import os
import sys
import urllib.parse
import urllib.request
import json
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import webbrowser

# 配置
ENV_FILE = ".env.twitter.oauth2"
CALLBACK_PORT = 5000
CALLBACK_PATH = "/callback"

# 读取配置
def load_config():
    """从.env文件加载配置"""
    config = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
    return config

def save_config(config):
    """保存配置到.env文件"""
    lines = []
    existing_keys = set()
    
    # 读取现有文件保留注释
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key = line.split('=', 1)[0]
                    if key in config:
                        lines.append(f"{key}={config[key]}\n")
                        existing_keys.add(key)
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
    
    # 添加新配置
    for key, value in config.items():
        if key not in existing_keys:
            lines.append(f"{key}={value}\n")
    
    with open(ENV_FILE, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ 配置已保存到 {ENV_FILE}")

# PKCE 生成
def generate_pkce():
    """生成PKCE参数"""
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode('utf-8').rstrip('=')
    
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge

# 全局变量存储授权码
auth_code = None
received_state = None

class CallbackHandler(BaseHTTPRequestHandler):
    """处理OAuth回调"""
    
    def log_message(self, format, *args):
        pass  # 静默日志
    
    def do_GET(self):
        global auth_code, received_state
        
        if self.path.startswith(CALLBACK_PATH):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # 解析参数
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'code' in params:
                auth_code = params['code'][0]
                received_state = params.get('state', [None])[0]
                
                html = """
                <html>
                <head><title>授权成功</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>✅ 授权成功！</h1>
                    <p>请返回终端查看结果。</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
            elif 'error' in params:
                error = params['error'][0]
                error_desc = params.get('error_description', ['Unknown error'])[0]
                
                html = f"""
                <html>
                <head><title>授权失败</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ 授权失败</h1>
                    <p>错误: {error}</p>
                    <p>描述: {error_desc}</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
            else:
                self.wfile.write(b"Invalid request")
        else:
            self.send_response(404)
            self.end_headers()

def start_callback_server():
    """启动回调服务器"""
    server = HTTPServer(('127.0.0.1', CALLBACK_PORT), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server

def get_authorization_url(client_id, redirect_uri, state, code_challenge):
    """构建授权URL"""
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'tweet.read tweet.write users.read offline.access',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    
    url = 'https://twitter.com/i/oauth2/authorize?' + urllib.parse.urlencode(params)
    return url

def exchange_code_for_token(code, client_id, client_secret, redirect_uri, code_verifier):
    """用授权码交换访问令牌"""
    
    # 构建Basic Auth
    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()
    
    data = urllib.parse.urlencode({
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier,
    }).encode()
    
    req = urllib.request.Request(
        'https://api.twitter.com/2/oauth2/token',
        data=data,
        headers={
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ 交换令牌失败: {error_body}")
        return None

def get_user_info(access_token):
    """获取用户信息"""
    req = urllib.request.Request(
        'https://api.twitter.com/2/users/me',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result.get('data', {})
    except Exception as e:
        print(f"获取用户信息失败: {e}")
        return {}

def main():
    print("="*60)
    print("  Twitter OAuth 2.0 授权流程")
    print("="*60)
    print()
    
    # 加载配置
    config = load_config()
    
    client_id = config.get('TWITTER_CLIENT_ID', '')
    client_secret = config.get('TWITTER_CLIENT_SECRET', '')
    redirect_uri = config.get('TWITTER_REDIRECT_URI', f'http://127.0.0.1:{CALLBACK_PORT}{CALLBACK_PATH}')
    
    if not client_id or client_id == 'your_client_id_here':
        print(f"❌ 请先在 {ENV_FILE} 中填写 TWITTER_CLIENT_ID")
        print("   从 Twitter Developer Portal → Keys and Tokens → OAuth 2.0 Client ID")
        return
    
    if not client_secret or client_secret == 'your_client_secret_here':
        print(f"❌ 请先在 {ENV_FILE} 中填写 TWITTER_CLIENT_SECRET")
        return
    
    print(f"Client ID: {client_id[:20]}...")
    print(f"回调URL: {redirect_uri}")
    print()
    
    # 生成PKCE
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(32)
    
    # 构建授权URL
    auth_url = get_authorization_url(client_id, redirect_uri, state, code_challenge)
    
    print("【步骤1】启动本地回调服务器...")
    server = start_callback_server()
    print(f"✅ 服务器已启动: http://127.0.0.1:{CALLBACK_PORT}")
    print()
    
    print("【步骤2】打开浏览器进行授权...")
    print(f"授权URL: {auth_url[:80]}...")
    print()
    
    # 自动打开浏览器
    webbrowser.open(auth_url)
    
    print("请在浏览器中完成授权...")
    print("(如果浏览器没有自动打开，请手动复制上面的URL)")
    print()
    
    # 等待回调
    global auth_code, received_state
    timeout = 300  # 5分钟超时
    waited = 0
    
    while auth_code is None and waited < timeout:
        import time
        time.sleep(1)
        waited += 1
        if waited % 10 == 0:
            print(f"  等待授权中... {waited}秒")
    
    server.shutdown()
    
    if auth_code is None:
        print("❌ 授权超时，请重试")
        return
    
    print("✅ 收到授权码")
    print()
    
    # 验证state
    if received_state != state:
        print("⚠️ 警告: State 不匹配，可能存在安全风险")
    
    print("【步骤3】交换访问令牌...")
    token_response = exchange_code_for_token(
        auth_code, client_id, client_secret, redirect_uri, code_verifier
    )
    
    if not token_response:
        print("❌ 获取访问令牌失败")
        return
    
    access_token = token_response.get('access_token')
    refresh_token = token_response.get('refresh_token')
    expires_in = token_response.get('expires_in', 7200)
    
    print("✅ 获取令牌成功！")
    print(f"   Access Token: {access_token[:30]}...")
    print(f"   Refresh Token: {refresh_token[:30]}..." if refresh_token else "   Refresh Token: 无")
    print(f"   有效期: {expires_in}秒 ({expires_in//3600}小时)")
    print()
    
    # 计算过期时间
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    print("【步骤4】获取用户信息...")
    user_info = get_user_info(access_token)
    if user_info:
        print(f"✅ 授权用户: @{user_info.get('username', 'unknown')}")
        print(f"   User ID: {user_info.get('id', 'unknown')}")
    print()
    
    # 保存配置
    print("【步骤5】保存配置...")
    config.update({
        'TWITTER_OAUTH2_ACCESS_TOKEN': access_token,
        'TWITTER_OAUTH2_REFRESH_TOKEN': refresh_token or '',
        'TWITTER_OAUTH2_TOKEN_EXPIRES_AT': expires_at.isoformat(),
        'TWITTER_USER_ID': user_info.get('id', ''),
        'TWITTER_USERNAME': user_info.get('username', ''),
    })
    save_config(config)
    
    print()
    print("="*60)
    print("✅ OAuth 2.0 授权完成！")
    print("="*60)
    print()
    print("现在可以使用以下命令发推了:")
    print("  python3 post_tweet_oauth2.py '您的推文内容'")
    print()

if __name__ == '__main__':
    main()
