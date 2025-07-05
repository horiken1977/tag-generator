# Video Tag Generator

マーケティング教育動画のタグ生成アプリケーション

## 概要

Googleスプレッドシートからマーケティング教育動画のデータを読み込み、AI（OpenAI/Claude/Gemini）を使用して検索性の高いタグを自動生成するアプリケーションです。

## 機能

- **Google Sheets連携**: スプレッドシートURL入力による自動データ読み込み
- **マルチAI対応**: OpenAI GPT / Claude / Gemini から選択可能
- **バッチ処理**: メモリ効率的な分割処理（400動画対応）
- **タグ最適化**: 重複排除・重要度スコアリング
- **結果出力**: 元ファイルのコピーを作成してタグを追加

## さくらインターネット環境での設定

### 1. ファイルアップロード

```bash
# アプリケーションファイルをさくらインターネットサーバーにアップロード
scp -r tag_generator/ user@your_domain.sakura.ne.jp:~/www/
```

### 2. 環境設定

```bash
# .envファイルを作成してAPIキーを設定
cp .env.template .env
# .envファイルを編集してAPIキーを入力
```

### 3. 依存関係インストール

```bash
pip3 install -r requirements.txt
```

### 4. アプリケーション起動

```bash
# Streamlitアプリケーションを起動
streamlit run ui/streamlit_app.py --server.port 8501
```

## API キー設定

`.env` ファイルに以下の設定を行ってください：

```env
# AI Service API Keys
OPENAI_API_KEY=your_actual_openai_api_key
CLAUDE_API_KEY=your_actual_claude_api_key
GEMINI_API_KEY=your_actual_gemini_api_key

# Google Service Account
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_ACTUAL_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
GOOGLE_CLIENT_EMAIL=your_service_account@your_project.iam.gserviceaccount.com
```

## 使用方法

1. **スプレッドシート設定**
   - GoogleスプレッドシートのURLを入力
   - 対象シートを選択
   - データ列をマッピング（タイトル、スキル名、説明文、要約、文字起こし）

2. **AI選択**
   - OpenAI、Claude、Gemini から処理エンジンを選択

3. **処理実行**
   - バッチサイズを設定（推奨：10-20件）
   - タグ生成処理を開始

4. **結果確認**
   - 生成されたタグを確認
   - 新しいスプレッドシートのリンクを取得

## ディレクトリ構造

```
tag_generator/
├── src/                     # ソースコード
│   ├── sheets_client.py     # Google Sheets API
│   ├── ai_processors/       # AI処理モジュール
│   ├── batch_processor.py   # バッチ処理
│   └── tag_optimizer.py     # タグ最適化
├── ui/                      # ユーザーインターフェース
│   └── streamlit_app.py     # メインUI
├── config/                  # 設定ファイル
├── .env                     # 環境変数（要作成）
└── requirements.txt         # 依存関係
```

## 注意事項

- APIキーは `.env` ファイルに安全に保存してください
- Google Service Accountの権限設定を確認してください
- さくらインターネットのPython環境を事前に確認してください
- 処理中はブラウザを閉じないでください

## サポート

技術的な問題や質問がある場合は、Issues で報告してください。