#!/bin/sh

# さくらインターネット自動デプロイスクリプト
# mokumoku.sakura.ne.jp への Tag Generator デプロイ

set -e  # エラー時に停止

# デプロイ設定
REMOTE_HOST="mokumoku.sakura.ne.jp"
REMOTE_USER="mokumoku"
REMOTE_PORT="22"
REMOTE_PATH="/home/mokumoku/www/tags"
LOCAL_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="/home/mokumoku/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# パスワード入力
get_password() {
    echo -n "さくらインターネットのパスワードを入力してください: "
    read -s REMOTE_PASSWORD
    echo
}

# SSH接続テスト
test_ssh_connection() {
    log_info "SSH接続をテスト中..."
    
    if sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "echo 'SSH接続成功'" 2>/dev/null; then
        log_success "SSH接続テスト成功"
        return 0
    else
        log_error "SSH接続に失敗しました"
        return 1
    fi
}

# 必要なツールの確認
check_tools() {
    log_info "必要なツールを確認中..."
    
    # sshpass の確認
    if ! command -v sshpass &> /dev/null; then
        log_error "sshpass がインストールされていません"
        log_info "以下のコマンドでインストールしてください:"
        log_info "  macOS: brew install hudochenkov/sshpass/sshpass"
        log_info "  Ubuntu: sudo apt-get install sshpass"
        log_info "  CentOS: sudo yum install sshpass"
        exit 1
    fi
    
    # rsync の確認
    if ! command -v rsync &> /dev/null; then
        log_error "rsync がインストールされていません"
        exit 1
    fi
    
    log_success "必要なツール確認完了"
}

# リモートディレクトリの準備
prepare_remote_directories() {
    log_info "リモートディレクトリを準備中..."
    
    # バックアップディレクトリ作成
    sshpass -p "$REMOTE_PASSWORD" ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
        mkdir -p $BACKUP_DIR
        mkdir -p $REMOTE_PATH
        mkdir -p $REMOTE_PATH/logs
    " 2>/dev/null
    
    log_success "リモートディレクトリ準備完了"
}

# 既存アプリケーションのバックアップ
backup_existing_app() {
    log_info "既存アプリケーションをバックアップ中..."
    
    sshpass -p "$REMOTE_PASSWORD" ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
        if [ -d '$REMOTE_PATH' ] && [ \"\$(ls -A $REMOTE_PATH 2>/dev/null)\" ]; then
            cp -r $REMOTE_PATH $BACKUP_DIR/tag_generator_$TIMESTAMP
            echo 'バックアップ作成: $BACKUP_DIR/tag_generator_$TIMESTAMP'
        else
            echo '既存アプリケーションが見つかりません。新規デプロイを実行します。'
        fi
    " 2>/dev/null
    
    log_success "バックアップ完了"
}

# ファイル同期
sync_files() {
    log_info "ファイルを同期中..."
    
    # 除外ファイル設定
    EXCLUDE_OPTS="--exclude=.git --exclude=.env --exclude=__pycache__ --exclude=*.pyc --exclude=venv --exclude=.DS_Store --exclude=logs/*.log"
    
    # rsync でファイル同期
    if sshpass -p "$REMOTE_PASSWORD" rsync -avz --delete $EXCLUDE_OPTS -e "ssh -p $REMOTE_PORT -o StrictHostKeyChecking=no" \
        "$LOCAL_PROJECT_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"; then
        log_success "ファイル同期完了"
    else
        log_error "ファイル同期に失敗しました"
        exit 1
    fi
}

# .env ファイルの確認
check_env_file() {
    log_info ".envファイルを確認中..."
    
    ENV_EXISTS=$(sshpass -p "$REMOTE_PASSWORD" ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
        if [ -f '$REMOTE_PATH/.env' ]; then
            echo 'exists'
        else
            echo 'missing'
        fi
    " 2>/dev/null)
    
    if [ "$ENV_EXISTS" = "missing" ]; then
        log_warning ".envファイルが存在しません"
        log_info "リモートサーバーに.envファイルを作成します..."
        
        # .env.template をコピーして .env を作成
        sshpass -p "$REMOTE_PASSWORD" ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
            cd $REMOTE_PATH
            if [ -f '.env.template' ]; then
                cp .env.template .env
                echo '.env.template から .envファイルを作成しました'
                echo '手動でAPIキーを設定してください:'
                echo '  nano $REMOTE_PATH/.env'
            else
                echo '.env.template が見つかりません'
            fi
        " 2>/dev/null
        
        log_warning "デプロイ後に手動で .env ファイルにAPIキーを設定してください"
    else
        log_success ".envファイル確認完了"
    fi
}

# 依存関係のインストール
install_dependencies() {
    log_info "依存関係をインストール中..."
    
    sshpass -p "$REMOTE_PASSWORD" ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
        cd $REMOTE_PATH
        
        # Python3 の確認
        if ! command -v python3 &> /dev/null; then
            echo 'エラー: Python3がインストールされていません'
            exit 1
        fi
        
        # 仮想環境の作成・アクティベート
        if [ ! -d 'venv' ]; then
            python3 -m venv venv
            echo '仮想環境を作成しました'
        fi
        
        source venv/bin/activate
        
        # pip の更新
        python3 -m pip install --upgrade pip
        
        # 依存関係インストール
        if [ -f 'requirements.txt' ]; then
            python3 -m pip install -r requirements.txt
            echo '依存関係インストール完了'
        else
            echo 'エラー: requirements.txt が見つかりません'
            exit 1
        fi
    " 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_success "依存関係インストール完了"
    else
        log_error "依存関係インストールに失敗しました"
        exit 1
    fi
}

# サービススクリプトの設定
setup_service_scripts() {
    log_info "サービススクリプトを設定中..."
    
    sshpass -p "$REMOTE_PASSWORD" ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
        cd $REMOTE_PATH
        
        # 実行権限を設定
        chmod +x run_app.py
        chmod +x deploy_sakura.sh
        
        # カスタムサービススクリプトを作成
        cat > start_tag_generator.sh << 'EOF'
#!/bin/sh

# Tag Generator サービス起動スクリプト（さくらインターネット用）

DEPLOY_DIR=\"$REMOTE_PATH\"
LOG_FILE=\"\$DEPLOY_DIR/logs/service.log\"
PID_FILE=\"\$DEPLOY_DIR/service.pid\"

echo \"\$(date): Tag Generator サービスを起動中...\" >> \"\$LOG_FILE\"

cd \"\$DEPLOY_DIR\"
source venv/bin/activate

# 既存プロセスの確認
if [ -f \"\$PID_FILE\" ]; then
    OLD_PID=\$(cat \"\$PID_FILE\")
    if ps -p \$OLD_PID > /dev/null 2>&1; then
        echo \"既存のサービスが実行中です (PID: \$OLD_PID)\"
        echo \"先に stop_tag_generator.sh を実行してください\"
        exit 1
    else
        rm \"\$PID_FILE\"
    fi
fi

# バックグラウンドでStreamlitを起動
nohup python3 -m streamlit run ui/streamlit_app.py \\
    --server.port=8501 \\
    --server.address=0.0.0.0 \\
    --browser.gatherUsageStats=false \\
    --server.headless=true \\
    >> \"\$LOG_FILE\" 2>&1 &

echo \$! > \"\$PID_FILE\"
echo \"\$(date): サービスが起動しました (PID: \$(cat \$PID_FILE))\" >> \"\$LOG_FILE\"

echo \"✅ Tag Generator サービスが起動しました\"
echo \"📊 アクセス URL: http://mokumoku.sakura.ne.jp:8501\"
echo \"📝 ログファイル: \$LOG_FILE\"
echo \"🛑 停止: ./stop_tag_generator.sh\"
EOF

        # 停止スクリプトを作成
        cat > stop_tag_generator.sh << 'EOF'
#!/bin/sh

# Tag Generator サービス停止スクリプト（さくらインターネット用）

DEPLOY_DIR=\"$REMOTE_PATH\"
PID_FILE=\"\$DEPLOY_DIR/service.pid\"
LOG_FILE=\"\$DEPLOY_DIR/logs/service.log\"

if [ -f \"\$PID_FILE\" ]; then
    PID=\$(cat \"\$PID_FILE\")
    echo \"\$(date): サービスを停止中 (PID: \$PID)...\" >> \"\$LOG_FILE\"
    
    if ps -p \$PID > /dev/null 2>&1; then
        kill \$PID
        sleep 2
        
        # 強制終了が必要な場合
        if ps -p \$PID > /dev/null 2>&1; then
            kill -9 \$PID
            echo \"\$(date): サービスを強制終了しました\" >> \"\$LOG_FILE\"
        fi
    fi
    
    rm \"\$PID_FILE\"
    echo \"\$(date): サービスが停止しました\" >> \"\$LOG_FILE\"
    echo \"✅ Tag Generator サービスが停止しました\"
else
    echo \"❌ サービスが起動していません\"
fi
EOF

        # ステータス確認スクリプトを作成
        cat > status_tag_generator.sh << 'EOF'
#!/bin/sh

# Tag Generator サービス状況確認スクリプト

DEPLOY_DIR=\"$REMOTE_PATH\"
PID_FILE=\"\$DEPLOY_DIR/service.pid\"
LOG_FILE=\"\$DEPLOY_DIR/logs/service.log\"

echo \"=== Tag Generator サービス状況 ===\"

if [ -f \"\$PID_FILE\" ]; then
    PID=\$(cat \"\$PID_FILE\")
    if ps -p \$PID > /dev/null 2>&1; then
        echo \"✅ サービス実行中 (PID: \$PID)\"
        echo \"📊 アクセス URL: http://mokumoku.sakura.ne.jp:8501\"
        
        # ポート使用状況確認
        if command -v netstat &> /dev/null; then
            echo \"📡 ポート使用状況:\"
            netstat -tlnp 2>/dev/null | grep :8501 || echo \"   ポート8501は使用されていません\"
        fi
    else
        echo \"❌ PIDファイルは存在しますが、プロセスが実行されていません\"
        rm \"\$PID_FILE\"
    fi
else
    echo \"❌ サービスが起動していません\"
fi

echo \"\"
echo \"📝 最新ログ (最後の10行):\"
if [ -f \"\$LOG_FILE\" ]; then
    tail -10 \"\$LOG_FILE\"
else
    echo \"   ログファイルが見つかりません\"
fi
EOF

        # 実行権限を設定
        chmod +x start_tag_generator.sh
        chmod +x stop_tag_generator.sh
        chmod +x status_tag_generator.sh
        
        echo 'サービススクリプト設定完了'
    " 2>/dev/null
    
    log_success "サービススクリプト設定完了"
}

# アプリケーションのテスト
test_deployment() {
    log_info "デプロイメントをテスト中..."
    
    TEST_RESULT=$(sshpass -p "$REMOTE_PASSWORD" ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
        cd $REMOTE_PATH
        source venv/bin/activate
        
        # 基本的なPythonインポートテスト
        python3 -c '
import sys
import os
sys.path.append(\"src\")

try:
    import pandas as pd
    import streamlit as st
    print(\"✅ パッケージインポート成功\")
    
    # 設定ファイル読み込みテスト
    import json
    with open(\"config/settings.json\", \"r\") as f:
        config = json.load(f)
    print(\"✅ 設定ファイル読み込み成功\")
    
    print(\"✅ デプロイメントテスト成功\")
except Exception as e:
    print(f\"❌ テストエラー: {e}\")
    sys.exit(1)
        '
    " 2>/dev/null)
    
    echo "$TEST_RESULT"
    
    if echo "$TEST_RESULT" | grep -q "デプロイメントテスト成功"; then
        log_success "デプロイメントテスト成功"
    else
        log_error "デプロイメントテストに失敗しました"
        exit 1
    fi
}

# メイン実行
main() {
    echo "🚀 さくらインターネット自動デプロイ開始"
    echo "=========================================="
    echo "📡 接続先: $REMOTE_HOST"
    echo "👤 ユーザー: $REMOTE_USER"
    echo "📁 配置先: $REMOTE_PATH"
    echo "🌐 URL: http://mokumoku.sakura.ne.jp:8501"
    echo ""
    
    # パスワード入力
    get_password
    
    # 実行
    check_tools
    test_ssh_connection
    prepare_remote_directories
    backup_existing_app
    sync_files
    check_env_file
    install_dependencies
    setup_service_scripts
    test_deployment
    
    echo ""
    echo "🎉 デプロイメント完了!"
    echo "=========================================="
    echo "📁 デプロイ先: $REMOTE_PATH"
    echo "🚀 標準起動: ssh mokumoku@mokumoku.sakura.ne.jp 'cd $REMOTE_PATH && ./start_tag_generator.sh'"
    echo "🌐 Web起動: ssh mokumoku@mokumoku.sakura.ne.jp 'cd $REMOTE_PATH && ./start_tag_generator_web.sh'"
    echo "🛑 停止: ssh mokumoku@mokumoku.sakura.ne.jp 'cd $REMOTE_PATH && ./stop_tag_generator.sh'"
    echo "📊 状況: ssh mokumoku@mokumoku.sakura.ne.jp 'cd $REMOTE_PATH && ./status_tag_generator.sh'"
    echo ""
    echo "🌐 アクセス方法:"
    echo "  メインURL: http://mokumoku.sakura.ne.jp/tags/"
    echo "  直接アクセス: http://mokumoku.sakura.ne.jp:8501"
    echo ""
    echo "⚠️  次の手順:"
    echo "1. SSH でリモートサーバーに接続"
    echo "2. $REMOTE_PATH/.env ファイルにAPIキーを設定"
    echo "3. Web設定を実行: ./web_setup.sh（初回のみ）"
    echo "4. ./start_tag_generator_web.sh でサービス起動"
}

# スクリプト実行
main "$@"