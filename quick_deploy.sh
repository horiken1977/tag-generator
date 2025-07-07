#!/bin/sh

# クイックデプロイスクリプト
# さくらインターネット (mokumoku.sakura.ne.jp) へのワンクリックデプロイ

echo "🚀 Tag Generator - クイックデプロイ"
echo "=================================="
echo "📡 デプロイ先: mokumoku.sakura.ne.jp"
echo "📁 配置パス: /home/mokumoku/www/tags"
echo "🌐 アクセス: http://mokumoku.sakura.ne.jp:8501"
echo ""

# sshpass の確認
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass が必要です"
    echo ""
    echo "インストール方法:"
    echo "  macOS: brew install hudochenkov/sshpass/sshpass"
    echo "  Ubuntu: sudo apt-get install sshpass" 
    echo "  CentOS: sudo yum install sshpass"
    echo ""
    read -p "sshpassをインストール後、Enterキーを押してください..."
fi

# パスワード入力
echo -n "🔑 さくらインターネットのパスワード: "
read -s PASSWORD
echo ""
echo ""

echo "🔍 接続テスト中..."
if sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 mokumoku@mokumoku.sakura.ne.jp "echo '接続成功'" 2>/dev/null; then
    echo "✅ SSH接続成功"
else
    echo "❌ SSH接続に失敗しました"
    echo "   パスワードまたはサーバー設定を確認してください"
    exit 1
fi

echo ""
echo "📦 ファイルをアップロード中..."

# rsync でファイル同期
sshpass -p "$PASSWORD" rsync -avz --progress \
    --exclude=.git \
    --exclude=.env \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    --exclude=venv \
    --exclude=.DS_Store \
    --exclude=logs/*.log \
    -e "ssh -o StrictHostKeyChecking=no" \
    ./ mokumoku@mokumoku.sakura.ne.jp:/home/mokumoku/www/tags/

if [ $? -eq 0 ]; then
    echo "✅ ファイルアップロード完了"
else
    echo "❌ ファイルアップロードに失敗しました"
    exit 1
fi

echo ""
echo "⚙️ サーバーセットアップ中..."

# リモートでセットアップ実行
sshpass -p "$PASSWORD" ssh mokumoku@mokumoku.sakura.ne.jp << 'EOF'
cd /home/mokumoku/www/tags

echo "📁 ディレクトリ準備中..."
mkdir -p logs
mkdir -p /home/mokumoku/backups

echo "🐍 Python環境セットアップ中..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "📄 .envファイル準備中..."
if [ ! -f ".env" ] && [ -f ".env.template" ]; then
    cp .env.template .env
    echo "✅ .env.template から .envファイルを作成しました"
fi

echo "🔧 実行権限設定中..."
chmod +x *.sh 2>/dev/null
chmod +x run_app.py 2>/dev/null

echo "✅ セットアップ完了"
EOF

echo ""
echo "🎉 デプロイ完了!"
echo "=================================="
echo ""
echo "📋 次の手順:"
echo "1. SSH接続してAPIキーを設定:"
echo "   ssh mokumoku@mokumoku.sakura.ne.jp"
echo "   cd /home/mokumoku/www/tags"
echo "   nano .env"
echo ""
echo "2. Web設定（初回のみ）:"
echo "   ./web_setup.sh"
echo ""
echo "3. サービス起動:"
echo "   ./start_tag_generator_web.sh"
echo ""
echo "4. ブラウザでアクセス:"
echo "   http://mokumoku.sakura.ne.jp/tags/"
echo ""
echo "🔧 管理コマンド:"
echo "   Web起動: ./start_tag_generator_web.sh"
echo "   標準起動: ./start_tag_generator.sh"
echo "   停止: ./stop_tag_generator.sh"
echo "   状況: ./status_tag_generator.sh"
echo ""

# SSH接続するか確認
read -p "今すぐSSH接続して.envファイルを設定しますか？ (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔗 SSH接続中..."
    sshpass -p "$PASSWORD" ssh -t mokumoku@mokumoku.sakura.ne.jp "cd /home/mokumoku/www/tags && nano .env"
fi

echo ""
echo "📞 サポート:"
echo "   問題が発生した場合は deploy_manual.md を参照してください"