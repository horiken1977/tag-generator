#!/bin/bash
# Tag Generator API Server Startup Script

DEPLOY_DIR="/home/mokumoku/www/tags"
LOG_DIR="$DEPLOY_DIR/logs"
PID_FILE="$DEPLOY_DIR/api_server.pid"

# Create logs directory if not exists
mkdir -p "$LOG_DIR"

# Stop existing server if running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Stopping existing API server (PID: $OLD_PID)..."
        kill "$OLD_PID"
        sleep 2
    fi
fi

# Update index.html to use the new version
if [ -f "$DEPLOY_DIR/index_final.html" ]; then
    cp "$DEPLOY_DIR/index_final.html" "$DEPLOY_DIR/index.html"
    echo "Updated index.html"
fi

# Start the API server with AI integration
cd "$DEPLOY_DIR"
echo "Starting Tag Generator API Server v2..."
nohup python3 api_server_v2.py > "$LOG_DIR/api_server.log" 2>&1 &
NEW_PID=$!
echo $NEW_PID > "$PID_FILE"

# Wait and check if server started successfully
sleep 3
if ps -p "$NEW_PID" > /dev/null 2>&1; then
    echo "✅ API Server started successfully (PID: $NEW_PID)"
    echo "Server log: $LOG_DIR/api_server.log"
    
    # Test API status
    curl -s http://localhost:8080/api/status | head -10
else
    echo "❌ Failed to start API Server"
    echo "Check log file: $LOG_DIR/api_server.log"
    tail -20 "$LOG_DIR/api_server.log"
    exit 1
fi