#!/bin/sh

# Web アクセス設定スクリプト
# http://mokumoku.sakura.ne.jp/tags/ でアクセスできるように設定

set -e

# 設定
REMOTE_HOST="mokumoku.sakura.ne.jp"
REMOTE_USER="mokumoku"
REMOTE_PATH="/home/mokumoku/www/tags"
WEB_ROOT="/home/mokumoku/www"

echo "🌐 Web アクセス設定"
echo "=================================="
echo "📍 URL: http://mokumoku.sakura.ne.jp/tags/"
echo "📁 配置先: $REMOTE_PATH"
echo ""

# パスワード入力
echo -n "🔑 さくらインターネットのパスワード: "
read -s PASSWORD
echo ""

echo "⚙️ Web設定を作成中..."

# リモートでWeb設定を実行
sshpass -p "$PASSWORD" ssh mokumoku@mokumoku.sakura.ne.jp << EOF
cd $REMOTE_PATH

echo "📄 Apache/nginx プロキシ設定を作成中..."

# .htaccess ファイルを作成（Apache用）
cat > $WEB_ROOT/.htaccess << 'HTACCESS_END'
# Tag Generator プロキシ設定
RewriteEngine On

# /tags/ パスの処理
RewriteCond %{REQUEST_URI} ^/tags/(.*)$
RewriteRule ^tags/(.*)$ http://localhost:8501/\$1 [P,L]

# /tags パスの処理（末尾スラッシュなし）
RewriteRule ^tags$ http://localhost:8501/ [P,L]

# プロキシ設定
ProxyPreserveHost On
ProxyPass /tags/ http://localhost:8501/
ProxyPassReverse /tags/ http://localhost:8501/
HTACCESS_END

# index.html リダイレクトページを作成
cat > $WEB_ROOT/tags/index.html << 'HTML_END'
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tag Generator - Loading</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .logo {
            font-size: 3em;
            margin-bottom: 20px;
        }
        .loading {
            font-size: 1.2em;
            margin-bottom: 30px;
        }
        .spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top: 4px solid white;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .manual-link {
            margin-top: 30px;
            font-size: 0.9em;
        }
        .manual-link a {
            color: #FFD700;
            text-decoration: none;
        }
        .manual-link a:hover {
            text-decoration: underline;
        }
    </style>
    <script>
        // Streamlit アプリケーションが起動しているかチェック
        function checkStreamlit() {
            fetch('/tags/health')
                .then(response => {
                    if (response.ok) {
                        // Streamlit が起動している場合、リダイレクト
                        window.location.href = '/tags/app/';
                    } else {
                        // まだ起動していない場合、再チェック
                        setTimeout(checkStreamlit, 3000);
                    }
                })
                .catch(error => {
                    // エラーの場合、Streamlit ポート直接アクセスを試行
                    setTimeout(() => {
                        window.location.href = 'http://mokumoku.sakura.ne.jp:8501';
                    }, 5000);
                });
        }
        
        // ページ読み込み後に開始
        window.onload = function() {
            setTimeout(checkStreamlit, 2000);
        };
    </script>
</head>
<body>
    <div class="logo">🏷️</div>
    <h1>Tag Generator</h1>
    <div class="loading">アプリケーションを起動中...</div>
    <div class="spinner"></div>
    
    <div class="manual-link">
        <p>自動リダイレクトされない場合は:</p>
        <a href="http://mokumoku.sakura.ne.jp:8501" target="_blank">
            直接アクセス (ポート8501)
        </a>
    </div>
</body>
</html>
HTML_END

echo "✅ Web設定ファイル作成完了"

# Streamlit 設定を更新（Web パス対応）
cat > streamlit_config.toml << 'CONFIG_END'
[server]
port = 8501
address = "0.0.0.0"
baseUrlPath = "/tags"
enableCORS = false
enableXsrfProtection = false
headless = true

[browser]
gatherUsageStats = false
serverAddress = "mokumoku.sakura.ne.jp"
serverPort = 80

[global]
developmentMode = false
CONFIG_END

# 設定ディレクトリ作成
mkdir -p ~/.streamlit
cp streamlit_config.toml ~/.streamlit/config.toml

echo "✅ Streamlit設定完了"

# サービススクリプトを更新（Web パス対応）
cat > start_tag_generator_web.sh << 'SERVICE_END'
#!/bin/sh

# Tag Generator Web サービス起動スクリプト

DEPLOY_DIR="$REMOTE_PATH"
LOG_FILE="\$DEPLOY_DIR/logs/service.log"
PID_FILE="\$DEPLOY_DIR/service.pid"

echo "\$(date): Tag Generator Web サービスを起動中..." >> "\$LOG_FILE"

cd "\$DEPLOY_DIR"
source venv/bin/activate

# 既存プロセスの確認
if [ -f "\$PID_FILE" ]; then
    OLD_PID=\$(cat "\$PID_FILE")
    if ps -p \$OLD_PID > /dev/null 2>&1; then
        echo "既存のサービスが実行中です (PID: \$OLD_PID)"
        echo "先に stop_tag_generator.sh を実行してください"
        exit 1
    else
        rm "\$PID_FILE"
    fi
fi

# Streamlit を Web パス対応で起動
export STREAMLIT_SERVER_BASE_URL_PATH="/tags"
nohup python3 -m streamlit run ui/streamlit_app.py \\
    --server.port=8501 \\
    --server.address=0.0.0.0 \\
    --server.baseUrlPath="/tags" \\
    --browser.gatherUsageStats=false \\
    --server.headless=true \\
    --server.enableCORS=false \\
    --server.enableXsrfProtection=false \\
    >> "\$LOG_FILE" 2>&1 &

echo \$! > "\$PID_FILE"
echo "\$(date): Web サービスが起動しました (PID: \$(cat \$PID_FILE))\" >> \"\$LOG_FILE\"

echo "✅ Tag Generator Web サービスが起動しました"
echo "🌐 アクセス URL: http://mokumoku.sakura.ne.jp/tags/"
echo "🔗 直接アクセス: http://mokumoku.sakura.ne.jp:8501"
echo "📝 ログファイル: \$LOG_FILE"
echo "🛑 停止: ./stop_tag_generator.sh"
SERVICE_END

chmod +x start_tag_generator_web.sh

# ヘルスチェックエンドポイント作成
cat > health_check.py << 'HEALTH_END'
#!/usr/bin/env python3
"""
Tag Generator ヘルスチェック用簡易サーバー
"""

import http.server
import socketserver
import json
import os
import sys
from threading import Thread

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/tags/health':
            # Streamlit プロセスが起動しているかチェック
            try:
                import requests
                response = requests.get('http://localhost:8501', timeout=5)
                if response.status_code == 200:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok", "streamlit": "running"}).encode())
                else:
                    raise Exception("Streamlit not responding")
            except:
                self.send_response(503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "streamlit": "not running"}).encode())
        else:
            super().do_GET()

if __name__ == "__main__":
    PORT = 8080
    Handler = HealthHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"ヘルスチェックサーバーをポート {PORT} で起動")
        httpd.serve_forever()
HEALTH_END

chmod +x health_check.py

echo "✅ Web アクセス設定完了"
echo ""
echo "📋 設定されたファイル:"
echo "  - $WEB_ROOT/.htaccess (Apache プロキシ設定)"
echo "  - $WEB_ROOT/tags/index.html (ランディングページ)"
echo "  - ~/.streamlit/config.toml (Streamlit Web設定)"
echo "  - start_tag_generator_web.sh (Web対応起動スクリプト)"
echo ""
echo "🌐 アクセス方法:"
echo "  メイン: http://mokumoku.sakura.ne.jp/tags/"
echo "  直接: http://mokumoku.sakura.ne.jp:8501"
EOF

echo ""
echo "✅ Web設定完了!"
echo "=================================="
echo ""
echo "🌐 アクセスURL: http://mokumoku.sakura.ne.jp/tags/"
echo ""
echo "📋 次の手順:"
echo "1. Webサービス起動:"
echo "   ssh mokumoku@mokumoku.sakura.ne.jp"
echo "   cd /home/mokumoku/www/tags"
echo "   ./start_tag_generator_web.sh"
echo ""
echo "2. ブラウザでアクセス:"
echo "   http://mokumoku.sakura.ne.jp/tags/"
echo ""
echo "📞 トラブルシューティング:"
echo "   - Apache/nginx の mod_proxy が有効か確認"
echo "   - ファイアウォールで8501ポートが開放されているか確認"
echo "   - 直接アクセス: http://mokumoku.sakura.ne.jp:8501"