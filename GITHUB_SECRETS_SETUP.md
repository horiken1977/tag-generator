# 🔐 GitHub Secrets設定ガイド

Vercel自動デプロイのためのGitHub Secrets設定方法

## 📋 必要なSecrets

以下のSecretsをGitHubリポジトリに設定してください：

### 1. VERCEL_TOKEN 🔑
**取得方法：**
1. [Vercel Settings → Tokens](https://vercel.com/account/tokens)
2. 「Create Token」をクリック
3. 名前: `github-actions-deploy`
4. Scope: `Full Account`
5. Expiration: `No Expiration` (推奨)
6. 🔗 **トークンをコピー**（再表示されません）

### 2. VERCEL_ORG_ID 🏢
**取得方法：**
1. [Vercel Team Settings](https://vercel.com/teams)
2. Team ID をコピー
3. または、ローカルで：
   ```bash
   npx vercel whoami
   ```

### 3. VERCEL_PROJECT_ID 📋
**取得方法：**
1. Vercelプロジェクト → Settings → General
2. Project IDをコピー
3. または、プロジェクトURL最後の部分
   - URL: `https://vercel.com/user/project-name`
   - Project ID: `project-name`

## ⚙️ GitHub Secrets設定手順

### 1. GitHubリポジトリにアクセス
```
https://github.com/horiken1977/tag-generator/settings/secrets/actions
```

### 2. 「New repository secret」で以下を順番に追加:

#### Secret 1: VERCEL_TOKEN
```
Name: VERCEL_TOKEN
Secret: vercel_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Secret 2: VERCEL_ORG_ID
```
Name: VERCEL_ORG_ID
Secret: team_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Secret 3: VERCEL_PROJECT_ID
```
Name: VERCEL_PROJECT_ID
Secret: prj_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 設定確認
設定後、以下が表示されれば成功：
```
✅ VERCEL_TOKEN        Updated now
✅ VERCEL_ORG_ID       Updated now  
✅ VERCEL_PROJECT_ID   Updated now
```

## 🔧 Vercel CLI設定方法

ローカルでのVercel設定：

```bash
# Vercel CLIインストール
npm install -g vercel

# nextjs-appディレクトリに移動
cd nextjs-app/

# Vercelプロジェクトとリンク
vercel login
vercel link

# プロジェクト情報確認
cat .vercel/project.json
```

`.vercel/project.json`の例：
```json
{
  "orgId": "team_xxxxxxxxxxxxxxxxx",
  "projectId": "prj_xxxxxxxxxxxxxxxxx"
}
```

## 🚀 自動デプロイの動作

### Mainブランチへのプッシュ
- ✅ 本番環境にデプロイ
- ✅ `nextjs-app/`配下の変更を検知
- ✅ 自動ビルド・テスト・デプロイ

### プルリクエスト作成
- ✅ プレビュー環境にデプロイ
- ✅ PRにプレビューURLをコメント
- ✅ レビュー前にテスト可能

### 手動実行
- ✅ GitHub ActionsのWorkflowページから手動実行可能

## 📊 デプロイフロー

```mermaid
graph TD
    A[git push] --> B[GitHub Actions]
    B --> C[Dependencies Install]
    C --> D[Build Project]
    D --> E[Deploy to Vercel]
    E --> F[本番URL取得]
    F --> G[デプロイ完了通知]
```

## ✅ 設定確認方法

1. **Secrets設定完了後：**
   ```bash
   git add .
   git commit -m "Setup Vercel auto-deploy"
   git push origin main
   ```

2. **GitHub Actionsページで確認：**
   - Actions タブで実行状況確認
   - デプロイログをチェック

3. **Vercelダッシュボードで確認：**
   - デプロイ履歴確認
   - 本番URLアクセステスト

## 🔗 参考リンク

- [Vercel CLI Documentation](https://vercel.com/docs/cli)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vercel GitHub Integration](https://vercel.com/docs/git/vercel-for-github)

設定完了後、自動的にコミット→プッシュ→Vercelデプロイが実行されます！