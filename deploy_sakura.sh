#!/bin/sh

# さくらインターネット デプロイメントスクリプト
# Video Tag Generator Application

set -e  # エラー時に停止

echo "🚀 さくらインターネット デプロイメント開始"
echo "=========================================="

# 設定
DEPLOY_DIR="/home/username/tag_generator"  # さくらインターネットのディレクトリパスに変更
BACKUP_DIR="/home/username/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 関数定義
log_info() {
    echo "ℹ️  $1"
}

log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1"
}

# 前処理チェック
check_requirements() {
    log_info "環境要件をチェック中..."
    
    # Python3の確認
    if ! command -v python3 &> /dev/null; then
        log_error "Python3がインストールされていません"
        exit 1
    fi
    
    # pipの確認
    if ! python3 -m pip --version &> /dev/null; then
        log_error "pipがインストールされていません"
        exit 1
    fi
    
    log_success "環境要件チェック完了"
}

# バックアップ作成
create_backup() {
    if [ -d "$DEPLOY_DIR" ]; then
        log_info "既存のアプリケーションをバックアップ中..."
        mkdir -p "$BACKUP_DIR"
        cp -r "$DEPLOY_DIR" "$BACKUP_DIR/tag_generator_$TIMESTAMP"
        log_success "バックアップ作成完了: $BACKUP_DIR/tag_generator_$TIMESTAMP"
    fi
}

# アプリケーションのデプロイ
deploy_application() {
    log_info "アプリケーションをデプロイ中..."
    
    # ディレクトリ作成
    mkdir -p "$DEPLOY_DIR"
    
    # ファイルをコピー（現在のディレクトリからデプロイディレクトリへ）
    cp -r . "$DEPLOY_DIR/"
    
    # 実行権限を設定
    chmod +x "$DEPLOY_DIR/run_app.py"
    chmod +x "$DEPLOY_DIR/deploy_sakura.sh"
    
    log_success "アプリケーションデプロイ完了"
}

# 依存関係のインストール
install_dependencies() {
    log_info "依存関係をインストール中..."
    
    cd "$DEPLOY_DIR"
    
    # 仮想環境を作成（推奨）
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "仮想環境を作成しました"
    fi
    
    # 仮想環境をアクティベート
    source venv/bin/activate
    
    # 依存関係をインストール
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    
    log_success "依存関係インストール完了"
}

# 設定ファイルの確認
check_configuration() {
    log_info "設定ファイルを確認中..."
    
    cd "$DEPLOY_DIR"
    
    # .envファイルの存在確認
    if [ ! -f ".env" ]; then
        log_error ".envファイルが見つかりません"
        log_info "以下のテンプレートを参考に.envファイルを作成してください:"
        echo ""
        cat .env.template
        echo ""
        exit 1
    fi
    
    # 必要な環境変数の確認
    source .env
    
    if [ -z "$GOOGLE_PROJECT_ID" ]; then
        log_error "GOOGLE_PROJECT_ID が設定されていません"
        exit 1
    fi
    
    if [ -z "$GOOGLE_CLIENT_EMAIL" ]; then
        log_error "GOOGLE_CLIENT_EMAIL が設定されていません"
        exit 1
    fi
    
    if [ -z "$GOOGLE_PRIVATE_KEY" ]; then
        log_error "GOOGLE_PRIVATE_KEY が設定されていません"
        exit 1
    fi
    
    log_success "設定ファイル確認完了"
}

# アプリケーションのテスト
test_application() {
    log_info "アプリケーションをテスト中..."
    
    cd "$DEPLOY_DIR"
    source venv/bin/activate
    
    # 基本テストを実行
    if [ -f "tests/test_basic.py" ]; then
        python3 -m pytest tests/test_basic.py -v
        log_success "基本テスト完了"
    else
        log_info "テストファイルが見つかりません。スキップします。"
    fi
}

# サービス起動スクリプトの作成
create_service_script() {
    log_info "サービス起動スクリプトを作成中..."
    
    cd "$DEPLOY_DIR"
    
    cat > start_service.sh << 'EOF'
#!/bin/sh

# Tag Generator サービス起動スクリプト

DEPLOY_DIR="/home/username/tag_generator"  # 実際のパスに変更
LOG_FILE="$DEPLOY_DIR/logs/service.log"

echo "$(date): Tag Generator サービスを起動中..." >> "$LOG_FILE"

cd "$DEPLOY_DIR"
source venv/bin/activate

# バックグラウンドでStreamlitを起動
nohup python3 run_app.py >> "$LOG_FILE" 2>&1 &

echo $! > "$DEPLOY_DIR/service.pid"
echo "$(date): サービスが起動しました (PID: $(cat $DEPLOY_DIR/service.pid))" >> "$LOG_FILE"

echo "✅ Tag Generator サービスが起動しました"
echo "📊 アクセス URL: http://your-domain:8501"
echo "📝 ログファイル: $LOG_FILE"
EOF

    chmod +x start_service.sh
    
    # 停止スクリプトも作成
    cat > stop_service.sh << 'EOF'
#!/bin/sh

# Tag Generator サービス停止スクリプト

DEPLOY_DIR="/home/username/tag_generator"  # 実際のパスに変更
PID_FILE="$DEPLOY_DIR/service.pid"
LOG_FILE="$DEPLOY_DIR/logs/service.log"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "$(date): サービスを停止中 (PID: $PID)..." >> "$LOG_FILE"
    
    kill "$PID"
    rm "$PID_FILE"
    
    echo "$(date): サービスが停止しました" >> "$LOG_FILE"
    echo "✅ Tag Generator サービスが停止しました"
else
    echo "❌ サービスが起動していません"
fi
EOF

    chmod +x stop_service.sh
    
    log_success "サービススクリプト作成完了"
}

# メイン実行
main() {
    log_info "デプロイメント設定:"
    log_info "  デプロイ先: $DEPLOY_DIR"
    log_info "  バックアップ先: $BACKUP_DIR"
    log_info "  タイムスタンプ: $TIMESTAMP"
    echo ""
    
    check_requirements
    create_backup
    deploy_application
    install_dependencies
    check_configuration
    test_application
    create_service_script
    
    echo ""
    echo "🎉 デプロイメント完了!"
    echo "=========================================="
    echo "📁 デプロイ先: $DEPLOY_DIR"
    echo "🚀 起動コマンド: $DEPLOY_DIR/start_service.sh"
    echo "🛑 停止コマンド: $DEPLOY_DIR/stop_service.sh"
    echo "📊 アクセス URL: http://your-domain:8501"
    echo "📝 ログファイル: $DEPLOY_DIR/logs/"
    echo ""
    echo "⚠️  次の手順を実行してください:"
    echo "1. $DEPLOY_DIR/.env ファイルにAPIキーを設定"
    echo "2. $DEPLOY_DIR/start_service.sh でサービス起動"
    echo "3. ファイアウォール設定で8501ポートを開放"
}

# スクリプト実行
main "$@"