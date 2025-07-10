# 🏷️ Tag Generator

マーケティング教育動画のAIタグ生成システム

## 🚀 最新版（推奨）

### Next.js + Vercel版
**[`/nextjs-app/`](./nextjs-app/) ← 🌟 こちらを使用してください**

- ✅ **403エラー解決済み**
- ✅ **TypeScript + React**
- ✅ **自動デプロイ対応**
- ✅ **高性能・高信頼性**

**デプロイ状況：**
- 🔄 GitHub Actions自動デプロイ設定済み
- 🌐 Vercel本番環境稼働中
- 📱 プレビューデプロイ対応

## 📋 システム概要

### 段階分離式処理システム
1. **第1段階**: 文字起こし除外での全件分析 → タグ候補生成
2. **第2段階**: 承認されたタグ候補での個別詳細分析 → 最終タグ付け

### 特徴
- 🎯 **高精度**: 汎用タグ完全除外
- 🚀 **高速**: バッチサイズ制限対応
- 🔒 **高信頼性**: ユーザー承認フロー
- 📊 **スケーラブル**: サーバーレス対応

## 🗂️ プロジェクト構成

```
/
├── nextjs-app/              # 🌟 Next.js版（推奨）
│   ├── app/
│   │   ├── api/            # API Routes
│   │   ├── page.tsx        # メインページ
│   │   └── layout.tsx      # レイアウト
│   ├── package.json
│   └── vercel.json         # Vercel設定
│
├── webapp_staged.html       # 📱 旧HTML版（レガシー）
├── api_server_v2.py        # 🖥️ 旧Python API（レガシー）
├── api_proxy.php           # 🔧 旧PHP Proxy（レガシー）
│
├── VERCEL_DEPLOY.md        # 📖 Vercelデプロイガイド
├── GITHUB_SECRETS_SETUP.md # 🔐 自動デプロイ設定ガイド
└── .github/workflows/      # 🤖 CI/CDワークフロー
```

## 🚀 クイックスタート

### 1. 開発環境
```bash
cd nextjs-app/
npm install
npm run dev
# http://localhost:3000 でアクセス
```

### 2. 本番デプロイ（Vercel）
1. [Vercelデプロイガイド](./VERCEL_DEPLOY.md)を参照
2. [GitHub Secrets設定](./GITHUB_SECRETS_SETUP.md)で自動デプロイ設定
3. `git push`で自動デプロイ開始

## 📈 バージョン履歴

| バージョン | 説明 | 状態 | 推奨度 |
|-----------|------|------|--------|
| **v3.0** | Next.js + Vercel | ✅ 稼働中 | 🌟🌟🌟 |
| v2.0 | Python API + PHP Proxy | ⚠️ 403エラー | ❌ |
| v1.0 | 静的HTML + シミュレーション | 📱 デモのみ | ❌ |

## 🆚 技術比較

| 項目 | v3.0 (Next.js) | v2.0 (PHP) | v1.0 (静的) |
|------|---------------|------------|------------|
| **API実装** | TypeScript | Python+PHP | JavaScript |
| **デプロイ** | Vercel自動 | SSH手動 | 静的ホスト |
| **エラー処理** | ✅ 詳細 | ❌ 限定的 | ❌ なし |
| **スケーリング** | ✅ 自動 | ❌ 固定 | ❌ なし |
| **開発体験** | ✅ 最新 | ❌ レガシー | ❌ 基本 |

## 🔧 API エンドポイント

### Next.js版（推奨）
```
POST /api/sheets/data     # Google Sheets読み込み
POST /api/ai/stage1       # タグ候補生成
POST /api/ai/stage2       # 個別タグ付け
```

### Python版（レガシー）
```
POST :8080/api/sheets/data     # Google Sheets読み込み
POST :8080/api/ai/stage1       # タグ候補生成  
POST :8080/api/ai/stage2       # 個別タグ付け
```

## 📊 パフォーマンス

### Next.js版
- **Cold Start**: < 1秒
- **API Response**: < 2秒
- **Build Time**: < 30秒
- **Deploy Time**: < 1分

### 旧版（参考）
- **起動時間**: 10-30秒
- **403エラー**: 頻発
- **デバッグ**: 困難

## 🌐 アクセス方法

### 本番環境
- **Next.js版**: [Vercelデプロイ後のURL]
- **旧版**: https://mokumoku.sakura.ne.jp/tags/

### 開発環境
- **Next.js版**: http://localhost:3000
- **旧版**: http://localhost:8080

## 🤝 コントリビューション

1. `nextjs-app/`ディレクトリで開発
2. プルリクエスト作成でプレビューデプロイ自動生成
3. マージで本番自動デプロイ

## 📞 サポート

- 🐛 Issues: GitHub Issues
- 📖 ドキュメント: 各READMEファイル
- 🚀 デプロイ: Vercel Dashboard

---

**推奨**: Next.js版（`/nextjs-app/`）をご利用ください 🌟