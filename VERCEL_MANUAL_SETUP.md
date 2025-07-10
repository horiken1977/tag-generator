# 🚨 Vercel手動設定ガイド

自動ビルドでPythonエラーが続く場合の手動設定方法

## 🔧 Vercelダッシュボードでの設定

### 1. Vercelプロジェクト設定変更

1. **Vercelダッシュボード**にアクセス
2. プロジェクト選択 → **Settings**
3. **General** タブで以下を設定：

```
Framework Preset: Next.js
Root Directory: nextjs-app/
Build Command: npm run build
Output Directory: .next
Install Command: npm install
Development Command: npm run dev
```

### 2. 環境変数設定

**Settings** → **Environment Variables**:
```
NODE_ENV = production
```

### 3. 手動再デプロイ

**Deployments** タブ → **Redeploy** ボタン

## 📋 期待される結果

```
✅ Framework: Next.js detected
✅ Root Directory: nextjs-app/
✅ Build Command: npm run build (in nextjs-app/)
✅ Dependencies: package.json (Next.js)
❌ Python: Ignored
```

## 🔄 代替方法: 新規プロジェクト作成

現在のプロジェクトでエラーが続く場合：

### 1. 新規Vercelプロジェクト作成
1. **Add New...** → **Project**
2. GitHubリポジトリ選択: `horiken1977/tag-generator`
3. **Configure Project**:
   - Project Name: `tag-generator-nextjs`
   - Framework: `Next.js`
   - Root Directory: `nextjs-app`

### 2. ビルド設定
```
Build Command: npm run build
Output Directory: .next
Install Command: npm install
```

### 3. デプロイ実行
自動的にNext.jsとして正しくビルドされます。

## ✅ 成功確認

ビルドログで以下が表示されれば成功：
```
✓ Detected Next.js
✓ Installing dependencies...
✓ Building Next.js application...
✓ Deployment successful
```

## 🔗 参考

- [Vercel Next.js Documentation](https://vercel.com/docs/frameworks/nextjs)
- [Root Directory Configuration](https://vercel.com/docs/projects/project-configuration)

手動設定後、次回のプッシュから正常にビルドされるはずです。