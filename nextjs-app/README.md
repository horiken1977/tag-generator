# 🏷️ Tag Generator - Next.js Version

段階分離式タグ処理システム（Next.js + Vercel版）

## 🚀 特徴

- **Next.js App Router**: 最新のNext.js 14を使用
- **Vercelデプロイ**: ワンクリックデプロイ
- **サーバーレス**: API Routes（サーバーレス関数）
- **TypeScript**: 型安全性
- **Tailwind CSS**: モダンなUI

## 📋 機能

### 第1段階: タグ候補生成
- 文字起こし除外での全件分析
- JavaScript/TypeScriptによるキーワード抽出
- 汎用語フィルタリング
- バッチサイズ制限（最大50件）

### 第2段階: 個別タグ付け
- 承認されたタグ候補を使用
- 文字起こし含む詳細分析
- 10-15個の適切なタグ選定

## 🛠️ セットアップ

### 開発環境

```bash
# 依存関係をインストール
npm install

# 開発サーバーを起動
npm run dev
```

### Vercelデプロイ

#### 初回セットアップ
1. VercelでGitHubリポジトリを連携
2. プロジェクトを選択
3. Root Directory: `nextjs-app/`を設定
4. 環境変数を設定（オプション）

#### 自動デプロイ設定
1. GitHub Secretsを設定（[詳細ガイド](../GITHUB_SECRETS_SETUP.md)）:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`
2. `main`ブランチへのプッシュで自動デプロイ開始
3. PRでプレビューデプロイ自動作成

## 📁 ディレクトリ構造

```
nextjs-app/
├── app/
│   ├── api/
│   │   ├── sheets/data/route.ts    # Google Sheets読み込み
│   │   └── ai/
│   │       ├── stage1/route.ts     # タグ候補生成
│   │       └── stage2/route.ts     # 個別タグ付け
│   ├── globals.css                 # グローバルスタイル
│   ├── layout.tsx                  # レイアウト
│   └── page.tsx                    # メインページ
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vercel.json                     # Vercel設定
```

## 🔧 API エンドポイント

### POST /api/sheets/data
Google Sheetsからデータを読み込み

### POST /api/ai/stage1
第1段階: タグ候補生成

### POST /api/ai/stage2
第2段階: 個別タグ付け

## 🎯 メリット

### vs Sakura Internet（PHP）
- ✅ 権限問題なし（403エラー回避）
- ✅ 詳細なエラーログ
- ✅ 開発環境と本番環境の統一
- ✅ 自動HTTPS
- ✅ GitHub連携

### 開発効率
- 🚀 即座にプレビューURL生成
- 🔧 ホットリロード
- 📊 Vercel Analytics
- 🌐 CDN自動配信

## 📊 パフォーマンス

- **Cold Start**: < 1秒
- **API Response**: < 2秒
- **Build Time**: < 30秒
- **Deploy Time**: < 1分

## 🔐 セキュリティ

- 環境変数でAPI Key管理
- CORS設定
- TypeScript型安全性

## 📈 スケーラビリティ

- サーバーレス関数の自動スケーリング
- Vercelの高性能CDN
- リクエスト制限なし（Vercel Pro）