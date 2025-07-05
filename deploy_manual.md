# 🚀 さくらインターネット デプロイメントガイド

mokumoku.sakura.ne.jp への Tag Generator アプリケーションのデプロイ手順です。

## 📋 デプロイ方法

### 方法1: 自動デプロイスクリプト（推奨）

```bash
# 実行権限を付与
chmod +x deploy_auto.sh

# 自動デプロイ実行
./deploy_auto.sh
```

**実行内容:**
- SSH接続テスト
- ファイル同期（rsync）
- 依存関係インストール
- サービススクリプト設定
- 動作確認

### 方法2: GitHub Actions自動デプロイ

1. **GitHub Secrets設定**
   ```
   Repository Settings > Secrets and variables > Actions
   
   Secret名: SAKURA_PASSWORD
   値: [さくらインターネットのパスワード]
   ```

2. **デプロイ実行**
   ```bash
   git add .
   git commit -m "Deploy to sakura internet"
   git push origin main
   ```

### 方法3: 手動SFTP/SCPデプロイ

```bash
# SCPでファイル転送
scp -r . mokumoku@mokumoku.sakura.ne.jp:/home/mokumoku/www/tags/

# SSH接続
ssh mokumoku@mokumoku.sakura.ne.jp

# 依存関係インストール
cd /home/mokumoku/www/tags
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## ⚙️ デプロイ後の設定

### 1. .env ファイル設定

```bash
# リモートサーバーに接続
ssh mokumoku@mokumoku.sakura.ne.jp

# .envファイル編集
cd /home/mokumoku/www/tags
nano .env
```

**設定内容:**
```env
# Google Sheets API
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_CLIENT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# AI API キー
OPENAI_API_KEY=sk-...
CLAUDE_API_KEY=sk-...
GEMINI_API_KEY=AIza...
```

### 2. サービス起動

```bash
# サービス起動
./start_tag_generator.sh

# サービス状況確認
./status_tag_generator.sh

# サービス停止
./stop_tag_generator.sh
```

## 🌐 アクセス確認

**アプリケーションURL:**
```
メインURL: http://mokumoku.sakura.ne.jp/tags/
直接アクセス: http://mokumoku.sakura.ne.jp:8501
```

**Web設定（初回のみ）:**
```bash
ssh mokumoku@mokumoku.sakura.ne.jp
cd /home/mokumoku/www/tags
./web_setup.sh
```

**接続確認:**
```bash
# Web URL確認
curl -I http://mokumoku.sakura.ne.jp/tags/

# 直接ポート確認
curl -I http://mokumoku.sakura.ne.jp:8501

# ログ確認
ssh mokumoku@mokumoku.sakura.ne.jp 'tail -f /home/mokumoku/www/tags/logs/service.log'
```

## 🔧 トラブルシューティング

### 問題1: SSH接続エラー
```bash
# 解決方法
ssh-keygen -R mokumoku.sakura.ne.jp
ssh -o StrictHostKeyChecking=no mokumoku@mokumoku.sakura.ne.jp
```

### 問題2: ポート8501にアクセスできない
**確認項目:**
- さくらインターネットのファイアウォール設定
- アプリケーションが起動しているか
- ポートが使用されているか

```bash
# ポート確認
ssh mokumoku@mokumoku.sakura.ne.jp 'netstat -tlnp | grep :8501'
```

### 問題3: 依存関係エラー
```bash
# 仮想環境の再作成
ssh mokumoku@mokumoku.sakura.ne.jp
cd /home/mokumoku/www/tags
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 問題4: .envファイルエラー
```bash
# .envファイル確認
ssh mokumoku@mokumoku.sakura.ne.jp 'cat /home/mokumoku/www/tags/.env'

# APIキー形式確認
# GOOGLE_PRIVATE_KEY は改行文字を \n で表記
```

## 📊 運用・監視

### ログ確認
```bash
# アプリケーションログ
ssh mokumoku@mokumoku.sakura.ne.jp 'tail -f /home/mokumoku/www/tags/logs/service.log'

# エラーログ
ssh mokumoku@mokumoku.sakura.ne.jp 'grep ERROR /home/mokumoku/www/tags/logs/service.log'
```

### パフォーマンス確認
```bash
# プロセス確認
ssh mokumoku@mokumoku.sakura.ne.jp 'ps aux | grep streamlit'

# メモリ使用量
ssh mokumoku@mokumoku.sakura.ne.jp 'free -h'

# ディスク使用量
ssh mokumoku@mokumoku.sakura.ne.jp 'df -h'
```

### 定期バックアップ
```bash
# 手動バックアップ
ssh mokumoku@mokumoku.sakura.ne.jp
cd /home/mokumoku
tar -czf backups/tag_generator_$(date +%Y%m%d_%H%M%S).tar.gz www/tags/
```

## 🔄 アップデート手順

```bash
# 1. ローカルで変更
git add .
git commit -m "Update features"
git push

# 2. 自動デプロイ実行
./deploy_auto.sh

# 3. サービス再起動
ssh mokumoku@mokumoku.sakura.ne.jp
cd /home/mokumoku/www/tags
./stop_tag_generator.sh
./start_tag_generator.sh
```

## 📞 サポート

問題が発生した場合は、以下の情報を収集してください:

1. **エラーログ**
   ```bash
   ssh mokumoku@mokumoku.sakura.ne.jp 'tail -50 /home/mokumoku/www/tags/logs/service.log'
   ```

2. **システム情報**
   ```bash
   ssh mokumoku@mokumoku.sakura.ne.jp 'uname -a && python3 --version'
   ```

3. **ネットワーク状況**
   ```bash
   ping mokumoku.sakura.ne.jp
   curl -I http://mokumoku.sakura.ne.jp:8501
   ```

この情報とともに問題の詳細をご報告ください。