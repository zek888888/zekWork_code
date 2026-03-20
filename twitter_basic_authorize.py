#!/usr/bin/env python3
"""
Twitter API Basic 重新授权
使用新的 Client ID/Secret 获取完整权限
"""

import os
import json
import urllib.parse
import urllib.request
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import webbrowser
import time

ENV_FILE = ".env.twitter.oauth2"
CALLBACK_PORT = 5000

auth_code = None
received_state = None

class CallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        global auth_code, received_state
        
        if '/callback' in self.path:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'code' in params:
                auth_code = params['code'][0]
                received_state = params.get('state', [None])[0]
                
                html = """
                <html><body style="text-align:center;padding:50px;font-family:Arial;">
                <h1>✅ 授权成功！</h1><p>请返回终端查看结果</p>
                </body></html>
                """
                self.wfile.write(html.encode())
            else:
                self.wfile.write(b"<h1>Authorization Failed</h1>")

def start_server():
    server = HTTPServer(('127.0.0.1', CALLBACK_PORT), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server

def generate_pkce():
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode('utf-8').rstrip('=')
    
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge

def load_config():
    config = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value.strip()
    return config

def save_config(config):
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            lines = f.readlines()
    
    # 移除旧的配置
    keys_to_update = ['TWITTER_OAUTH2_ACCESS_TOKEN', 'TWITTER_OAUTH2_REFRESH_TOKEN', 
                      'TWITTER_OAUTH2_TOKEN_EXPIRES_AT', 'TWITTER_USER_ID', 'TWITTER_USERNAME']
    lines = [l for l in lines if not any(l.startswith(k + '=') for k in keys_to_update)]
    
    # 添加新配置
    with open(ENV_FILE, 'w') as f:
        f.writelines(lines)
        for key, value in config.items():
            if key in keys_to_update:
                f.write(f"{key}={value}\n")

def main():
    print("="*70)
    print("  Twitter API Basic 授权流程")
    print("="*70)
    print()
    
    # 从 .env.twitter 读取新 Client ID
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_env = os.path.join(script_dir, ".env.twitter")
    creds = {}
    with open(main_env, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                creds[key] = value.strip()
    
    client_id = creds.get('TWITTER_CLIENT_ID')
    client_secret = creds.get('TWITTER_CLIENT_SECRET')
    
    if not client_id or 'TkJqOTEzVGNXVzZfZi14' not in client_id:
        print("❌ 请先在 .env.twitter 中填写新的 Client ID")
        return
    
    print(f"Client ID: {client_id[:30]}...")
    print()
    
    # 生成 PKCE
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(32)
    
    # 构建授权 URL
    redirect_uri = f'http://127.0.0.1:{CALLBACK_PORT}/callback'
    scopes = 'tweet.read tweet.write users.read offline.access'
    
    auth_url = (
        f'https://twitter.com/i/oauth2/authorize?'
        f'response_type=code&'
        f'client_id={client_id}&'
        f'redirect_uri={urllib.parse.quote(redirect_uri)}&'
        f'scope={urllib.parse.quote(scopes)}&'
        f'state={state}&'
        f'code_challenge={code_challenge}&'
        f'code_challenge_method=S256'
    )
    
    print("【步骤1】启动服务器...")
    server = start_server()
    print(f"✅ 服务器启动: http://127.0.0.1:{CALLBACK_PORT}")
    print()
    
    print("【步骤2】打开授权页面...")
    print(f"授权URL: {auth_url[:80]}...")
    webbrowser.open(auth_url)
    print()
    
    print("请在浏览器中完成授权...")
    
    # 等待回调
    global auth_code
    for i in range(300):
        if auth_code:
            break
        time.sleep(1)
        if i % 10 == 0:
            print(f"  等待中... {i}秒")
    
    server.shutdown()
    
    if not auth_code:
        print("❌ 授权超时")
        return
    
    print("✅ 收到授权码")
    print()
    
    # 交换 Token
    print("【步骤3】交换访问令牌...")
    
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    data = f"code={auth_code}&grant_type=authorization_code&redirect_uri={urllib.parse.quote(redirect_uri)}&code_verifier={code_verifier}".encode()
    
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
            
            access_token = result['access_token']
            refresh_token = result.get('refresh_token', '')
            expires_in = result.get('expires_in', 7200)
            
            print(f"✅ 获取令牌成功！")
            print(f"   Access Token: {access_token[:40]}...")
            print(f"   有效期: {expires_in}秒 ({expires_in//3600}小时)")
            print()
            
            # 获取用户信息
            print("【步骤4】获取用户信息...")
            req2 = urllib.request.Request(
                'https://api.twitter.com/2/users/me',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            with urllib.request.urlopen(req2) as response2:
                user_data = json.loads(response2.read().decode())
                user = user_data.get('data', {})
                print(f"✅ 授权用户: @{user.get('username', 'unknown')}")
                print()
            
            # 保存配置
            print("【步骤5】保存配置...")
            config = {
                'TWITTER_OAUTH2_ACCESS_TOKEN': access_token,
                'TWITTER_OAUTH2_REFRESH_TOKEN': refresh_token,
                'TWITTER_OAUTH2_TOKEN_EXPIRES_AT': (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
                'TWITTER_USER_ID': user.get('id', ''),
                'TWITTER_USERNAME': user.get('username', ''),
            }
            save_config(config)
            print(f"✅ 配置已保存到 {ENV_FILE}")
            print()
            
            print("="*70)
            print("🎉 API Basic 授权完成！")
            print("="*70)
            print()
            print("现在可以：")
            print("  1. 使用 Bearer Token 搜索推文 (50,000次/月)")
            print("  2. 使用 OAuth 2.0 发推 (1,000次/月)")
            print("  3. 获取用户时间线和推文")
            print()
            
    except urllib.error.HTTPError as e:
        error = e.read().decode()
        print(f"❌ 交换令牌失败: {error}")

if __name__ == '__main__':
    main()
