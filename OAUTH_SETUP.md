# 🔐 Google OAuth設定ガイド

Google Sheets APIの代わりにOAuth認証を使用するための設定手順です。

## 🎯 利点

- ✅ **簡単設定**: サービスアカウントJSONファイル不要
- ✅ **安全性**: ユーザーが自分のGoogleアカウントで認証
- ✅ **権限管理**: 必要な権限のみ要求（読み取り専用）
- ✅ **ユーザビリティ**: アプリ内で簡単に認証完了

## 📋 設定手順

### 1. Google Cloud Console設定

1. **[Google Cloud Console](https://console.cloud.google.com/) にアクセス**

2. **プロジェクトを作成または選択**
   ```
   新しいプロジェクト → プロジェクト名: "Tag Generator"
   ```

3. **APIを有効化**
   ```
   APIとサービス → ライブラリ → 以下を検索して有効化:
   - Google Sheets API
   - Google Drive API
   ```

4. **OAuth同意画面を設定**
   ```
   APIとサービス → OAuth同意画面
   - ユーザータイプ: 外部
   - アプリ名: Tag Generator
   - ユーザーサポートメール: あなたのメール
   - スコープ: 
     - ../auth/spreadsheets.readonly
     - ../auth/drive.readonly
   ```

5. **認証情報を作成**
   ```
   APIとサービス → 認証情報 → 認証情報を作成 → OAuth 2.0 クライアントID
   - アプリケーションの種類: ウェブアプリケーション
   - 名前: Tag Generator Web
   - 承認済みのリダイレクトURI:
     - http://localhost:8501
     - http://mokumoku.sakura.ne.jp/tags/
   ```

6. **クライアントIDとシークレットを取得**
   ```
   作成されたOAuth 2.0 クライアントIDをクリック
   - クライアントID: 数字-文字列.apps.googleusercontent.com
   - クライアントシークレット: GOCSPX-文字列
   ```

### 2. .env ファイル設定

```bash
# さくらインターネットサーバーで設定
ssh mokumoku@mokumoku.sakura.ne.jp
cd /home/mokumoku/www/tags
nano .env
```

**設定内容:**
```env
# Google OAuth設定
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-AbCdEfGhIjKlMnOpQrStUvWx

# AI API キー
OPENAI_API_KEY=sk-your-openai-key
CLAUDE_API_KEY=sk-your-claude-key
GEMINI_API_KEY=your-gemini-key
```

### 3. アプリケーション使用方法

1. **アプリにアクセス**
   ```
   http://mokumoku.sakura.ne.jp/tags/
   ```

2. **Google認証**
   - 「Google認証を開始」ボタンクリック
   - Googleアカウントでログイン
   - 権限を許可
   - 認証コードを取得

3. **認証コード入力**
   - アプリに戻り、認証コードを入力
   - 「認証実行」ボタンクリック

4. **スプレッドシート処理**
   - 認証完了後、通常どおりスプレッドシートURL入力
   - データ読み込み・タグ生成実行

## 🔧 トラブルシューティング

### 問題1: "redirect_uri_mismatch" エラー

**原因**: リダイレクトURIが一致しない

**解決方法**:
```
Google Cloud Console → 認証情報 → OAuth 2.0 クライアントID
承認済みのリダイレクトURIに以下を追加:
- http://localhost:8501
- http://mokumoku.sakura.ne.jp/tags/
- http://mokumoku.sakura.ne.jp:8501
```

### 問題2: "invalid_client" エラー

**原因**: クライアントIDまたはシークレットが間違っている

**解決方法**:
```bash
# .envファイルの設定を確認
cat /home/mokumoku/www/tags/.env

# Google Cloud Consoleの認証情報と一致しているか確認
```

### 問題3: 権限エラー

**原因**: 必要なスコープが設定されていない

**解決方法**:
```
OAuth同意画面 → スコープ → 以下を追加:
- https://www.googleapis.com/auth/spreadsheets.readonly
- https://www.googleapis.com/auth/drive.readonly
```

### 問題4: 認証コードが取得できない

**原因**: ポップアップブロックまたはJavaScript無効

**解決方法**:
```
1. ブラウザのポップアップブロックを無効化
2. JavaScriptを有効化
3. 認証リンクを新しいタブで開く
```

## 🔒 セキュリティ

### OAuth vs サービスアカウント

| 項目 | OAuth認証 | サービスアカウント |
|------|-----------|-------------------|
| 設定の複雑さ | 簡単 | 複雑 |
| セキュリティ | ユーザー権限のみ | 全アクセス権限 |
| 権限管理 | ユーザーが制御 | 開発者が制御 |
| 設定ファイル | ID・シークレットのみ | JSON秘密鍵 |
| 使いやすさ | 非常に良い | 技術的 |

### 推奨設定

```env
# 最小権限で設定
GOOGLE_CLIENT_ID=your-client-id  # 公開情報
GOOGLE_CLIENT_SECRET=your-secret # 秘密情報（適切に保護）
```

## 📞 サポート

OAuth設定で問題が発生した場合:

1. **Google Cloud Console確認**
   - APIが有効化されているか
   - OAuth同意画面が設定されているか
   - リダイレクトURIが正しいか

2. **アプリケーションログ確認**
   ```bash
   tail -f /home/mokumoku/www/tags/logs/service.log
   ```

3. **ブラウザ確認**
   - JavaScriptが有効か
   - ポップアップブロックが無効か
   - 認証コードが正しくコピーされたか

問題が続く場合は、上記の情報と合わせてご報告ください。