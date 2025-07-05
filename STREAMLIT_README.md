# 🏷️ Video Tag Generator - Streamlit Web UI

Googleスプレッドシート内の400動画に対して、検索最適化されたタグを自動生成するWebアプリケーションです。

## 🌟 主な機能

- **Googleスプレッドシート連携**: URLからデータを直接読み込み
- **マルチAI対応**: OpenAI GPT、Claude、Google Geminiから選択可能
- **インテリジェントな列マッピング**: スプレッドシートの列を自動認識
- **バッチ処理**: メモリ効率的な分割処理でスケーラブル
- **タグ最適化**: 重複排除・重要度スコアリングで最終150-200タグに最適化
- **リアルタイム進捗表示**: 処理状況をリアルタイムで確認
- **結果保存**: 新しいGoogleスプレッドシートとして結果を保存

## 🚀 クイックスタート

### 1. 環境準備（さくらインターネット）

```bash
# プロジェクトディレクトリに移動
cd tag_generator

# 依存関係をインストール
python3 -m pip install -r requirements.txt

# .envファイルを設定（APIキーが必要）
# Google Sheets API、OpenAI、Claude、Gemini のAPIキーを設定
```

### 2. アプリケーション起動

```bash
# 簡単起動（推奨）
python3 run_app.py

# または直接Streamlit起動
python3 -m streamlit run ui/streamlit_app.py
```

### 3. Webブラウザでアクセス

```
http://localhost:8501
```

## 📋 使用方法

### ステップ1: スプレッドシート読み込み
1. GoogleスプレッドシートのURLを入力
2. シート名を指定（デフォルト: Sheet1）
3. 「スプレッドシート読み込み」ボタンをクリック

### ステップ2: 列マッピング設定
- **動画タイトル** (必須): タイトル列を選択
- **スキル/カテゴリ**: スキル分類列を選択
- **動画説明**: 説明文列を選択
- **要約**: 要約列を選択（あれば）
- **音声テキスト**: 文字起こしテキスト列を選択（あれば）

### ステップ3: AI・処理設定
- **AIプロバイダー選択**: OpenAI/Claude/Gemini から選択
- **バッチサイズ**: 一度に処理する動画数（1-50）
- **目標タグ数**: 最終的に出力するタグ数（100-300）

### ステップ4: タグ生成実行
- 処理推定情報を確認
- 「タグ生成開始」ボタンをクリック
- 進捗バーでリアルタイム進捗を確認

### ステップ5: 結果確認・保存
- 生成されたタグセットを確認
- CSVダウンロードまたはGoogleスプレッドシート保存

## ⚙️ 設定ファイル

### config/settings.json
```json
{
  "processing": {
    "batch_size": 10,
    "target_tag_count": 175
  },
  "ai_models": {
    "openai": {
      "model": "gpt-3.5-turbo",
      "temperature": 0.3
    }
  },
  "tag_optimization": {
    "similarity_threshold": 0.8,
    "importance_weights": {
      "title": 0.3,
      "skill": 0.25,
      "description": 0.2
    }
  }
}
```

## 🔑 環境変数設定（.env）

```env
# Google Sheets API
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_CLIENT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# OpenAI API
OPENAI_API_KEY=sk-...

# Claude API
CLAUDE_API_KEY=sk-...

# Google Gemini API
GEMINI_API_KEY=AIza...
```

## 📊 処理フロー

```mermaid
graph TD
    A[Googleスプレッドシート] --> B[データ読み込み]
    B --> C[列マッピング]
    C --> D[バッチ分割]
    D --> E[AI処理（タグ生成）]
    E --> F[タグ最適化]
    F --> G[結果表示]
    G --> H[Googleスプレッドシート保存]
```

## 🧠 AI処理詳細

### タグ生成プロンプト
各AIモデルに以下の形式でプロンプトを送信：

```
【動画情報】
タイトル: {title}
スキル: {skill}
説明: {description}
要約: {summary}
音声テキスト: {transcript}

【タスク】
この動画の内容に基づいて、検索に最適化されたタグを30-40個生成してください。
対象者：マーケティング担当者
形式：カンマ区切り
```

### タグ最適化アルゴリズム
1. **収集・クリーニング**: 全AIから生成されたタグを収集
2. **頻度分析**: 出現頻度と正規化処理
3. **重要度スコアリング**: TF-IDFベースの重要度計算
4. **類似タグ統合**: 編集距離ベースの類似タグマージ
5. **最終選択**: スコア順で150-200タグを選択

## 🔧 トラブルシューティング

### よくある問題

**Q: APIキーエラーが発生する**
A: .envファイルの設定を確認し、各APIキーが正しく設定されているか確認してください。

**Q: スプレッドシートが読み込めない**
A: スプレッドシートの共有設定を「リンクを知っている全員が閲覧可能」に設定してください。

**Q: メモリエラーが発生する**
A: バッチサイズを小さくして（5-10）再実行してください。

**Q: 処理が遅い**
A: AIプロバイダーのレート制限により処理時間が長くなる場合があります。Geminiが比較的高速です。

### ログ確認
```bash
# アプリケーションログを確認
tail -f logs/tag_generator.log
```

## 📈 パフォーマンス目安

| 動画数 | OpenAI (GPT-3.5) | Claude (Haiku) | Gemini (Pro) |
|--------|------------------|----------------|--------------|
| 100動画 | 約5分 | 約7分 | 約4分 |
| 400動画 | 約20分 | 約28分 | 約16分 |

※ネットワーク環境とAPIレート制限により変動

## 🔒 セキュリティ

- APIキーは.envファイルで管理（Gitにコミットしない）
- サービスアカウント認証でGoogle API接続
- 処理データは一時的にメモリ保持のみ
- ログには機密情報を出力しない

## 📝 ライセンス

このプロジェクトは内部利用目的で開発されています。

## 🆘 サポート

問題が発生した場合は、ログファイルと合わせて報告してください：
- アプリケーションログ: `logs/tag_generator.log`
- エラーメッセージのスクリーンショット
- 使用したスプレッドシートの構造（機密情報を除く）