# 🌐 Web アクセス設定ガイド

`http://mokumoku.sakura.ne.jp/tags/` でアクセスできるようにする設定手順です。

## 🎯 目標
- **メインURL**: `http://mokumoku.sakura.ne.jp/tags/`
- **直接アクセス**: `http://mokumoku.sakura.ne.jp:8501`（バックアップ）

## 📋 設定手順

### 1. 基本デプロイ（既に完了している場合はスキップ）
```bash
# クイックデプロイ実行
./quick_deploy.sh
```

### 2. Web設定の実行
```bash
# Web設定スクリプト実行
./web_setup.sh
```

### 3. リモートサーバーでWeb設定
```bash
# SSH接続
ssh mokumoku@mokumoku.sakura.ne.jp

# プロジェクトディレクトリに移動
cd /home/mokumoku/www/tags

# .envファイル設定（まだの場合）
nano .env

# Web起動スクリプト実行
./start_tag_generator_web.sh
```

## 🔧 作成される設定ファイル

### 1. Apache プロキシ設定 (`.htaccess`)
```apache
RewriteEngine On

# /tags/ パスの処理
RewriteCond %{REQUEST_URI} ^/tags/(.*)$
RewriteRule ^tags/(.*)$ http://localhost:8501/$1 [P,L]

# プロキシ設定
ProxyPreserveHost On
ProxyPass /tags/ http://localhost:8501/
ProxyPassReverse /tags/ http://localhost:8501/
```

### 2. ランディングページ (`/home/mokumoku/www/tags/index.html`)
- アプリケーション起動チェック
- 自動リダイレクト機能
- 手動アクセスリンク

### 3. Streamlit Web設定 (`~/.streamlit/config.toml`)
```toml
[server]
port = 8501
address = "0.0.0.0"
baseUrlPath = "/tags"
headless = true

[browser]
gatherUsageStats = false
serverAddress = "mokumoku.sakura.ne.jp"
serverPort = 80
```

### 4. Web対応起動スクリプト (`start_tag_generator_web.sh`)
- Base URL パス設定
- CORS設定
- プロキシ対応設定

## 🌐 アクセス方法

### 推奨アクセス
```
http://mokumoku.sakura.ne.jp/tags/
```

### 直接アクセス（トラブル時）
```
http://mokumoku.sakura.ne.jp:8501
```

### アクセス流れ
1. `http://mokumoku.sakura.ne.jp/tags/` にアクセス
2. Apache/nginx がリクエストを受信
3. プロキシ設定により `localhost:8501` に転送
4. Streamlit アプリケーションが応答
5. ユーザーにコンテンツ表示

## 🔍 動作確認

### 1. Webサービス状況確認
```bash
ssh mokumoku@mokumoku.sakura.ne.jp
cd /home/mokumoku/www/tags
./status_tag_generator.sh
```

### 2. ポート確認
```bash
ssh mokumoku@mokumoku.sakura.ne.jp 'netstat -tlnp | grep :8501'
```

### 3. Web URL テスト
```bash
curl -I http://mokumoku.sakura.ne.jp/tags/
```

### 4. プロキシ動作確認
```bash
curl -v http://mokumoku.sakura.ne.jp/tags/ 2>&1 | grep -E "(HTTP|Location|Server)"
```

## 🚨 トラブルシューティング

### 問題1: `/tags/` でアクセスできない

**原因**: Apache/nginx の mod_proxy が無効
**解決方法**:
```bash
# さくらインターネットサポートに問い合わせ
# または .htaccess の書き換え権限確認
```

### 問題2: プロキシエラーが発生

**原因**: Streamlit アプリケーションが起動していない
**解決方法**:
```bash
ssh mokumoku@mokumoku.sakura.ne.jp
cd /home/mokumoku/www/tags
./start_tag_generator_web.sh
```

### 問題3: CSS/JSが読み込まれない

**原因**: Base URL パス設定の問題
**解決方法**:
```bash
# Streamlit設定を確認
cat ~/.streamlit/config.toml

# 設定が正しくない場合は再実行
./web_setup.sh
```

### 問題4: CORS エラー

**原因**: ブラウザのセキュリティ制限
**解決方法**:
- 直接アクセス使用: `http://mokumoku.sakura.ne.jp:8501`
- CORS設定確認

## 🔄 サービス管理

### 起動
```bash
# Web対応起動
./start_tag_generator_web.sh

# 標準起動
./start_tag_generator.sh
```

### 停止
```bash
./stop_tag_generator.sh
```

### 状況確認
```bash
./status_tag_generator.sh
```

### ログ確認
```bash
tail -f logs/service.log
```

## 📞 サポート

Web設定で問題が発生した場合:

1. **ログ確認**: `logs/service.log` の内容
2. **プロキシ確認**: `.htaccess` ファイルの存在と内容
3. **ポート確認**: 8501ポートでの直接アクセス
4. **権限確認**: ファイル・ディレクトリの実行権限

これらの情報と合わせて問題をご報告ください。