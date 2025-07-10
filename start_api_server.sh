#\!/bin/bash
# 本番環境でAPIサーバーを起動するスクリプト

# プロセスの確認
echo "Checking for existing API server process..."
ps aux | grep "api_server_v2.py" | grep -v grep

# 既存プロセスを停止
pkill -f "api_server_v2.py" 2>/dev/null

# APIサーバーを起動
echo "Starting API server on port 8080..."
nohup python3 api_server_v2.py > api_server.log 2>&1 &

echo "API server started. PID: $\!"
echo "Log file: api_server.log"

# 起動確認
sleep 2
curl -s http://localhost:8080/api/status || echo "API server not responding yet"
