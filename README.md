# 開発プロジェクト管理システム

開発ドキュメントの自動生成・管理・可視化ツール

## 🌐 GitHub Pages

このプロジェクトのドキュメントはGitHub Pagesで公開されています：

**🏠 メインページ（ダッシュボード）**: [https://horiken1977.github.io/tags/](https://horiken1977.github.io/tags/)

### 📄 ドキュメント一覧

- **開発ダッシュボード**: [https://horiken1977.github.io/tags/](https://horiken1977.github.io/tags/)
- **機能設計書**: [https://horiken1977.github.io/tags/feature_design.html](https://horiken1977.github.io/tags/feature_design.html)
- **環境設計書**: [https://horiken1977.github.io/tags/environment_design.html](https://horiken1977.github.io/tags/environment_design.html)
- **テスト仕様書**: [https://horiken1977.github.io/tags/test_specification.html](https://horiken1977.github.io/tags/test_specification.html)

## ✨ 主要機能

- **自動ドキュメント生成** - Claude Codeとのチャット内容から自動的にドキュメントを生成・更新
- **進捗可視化** - プロジェクトの進捗をグラフィカルにダッシュボード表示
- **チャット自動保存** - 2時間ごとにチャット履歴を自動バックアップ
- **テスト管理** - テストケースの管理と実行結果の記録

## 🚀 セットアップ方法

### 前提条件

- Python 3.8以上
- Git（リポジトリ管理を行う場合）

### インストール

1. リポジトリをクローン
```bash
git clone https://github.com/horiken1977/tags.git
cd tags
```

2. 必要なPythonパッケージをインストール
```bash
pip install schedule
```

3. スクリプトの実行権限を付与（Unix系OSの場合）
```bash
chmod +x docs/auto_updater.py
chmod +x scripts/chat_backup.py
```

## 📝 使用方法

### ドキュメント自動更新

チャット内容を監視してドキュメントを自動更新：
```bash
# 監視モードで実行（推奨）
python docs/auto_updater.py

# 1回だけ実行
python docs/auto_updater.py --once
```

### チャット自動保存

定期的にチャット履歴をバックアップ：
```bash
# デフォルト設定（2時間ごと）で実行
python scripts/chat_backup.py

# カスタム間隔で実行
python scripts/chat_backup.py --interval 3h

# バックアップ一覧を表示
python scripts/chat_backup.py --list

# バックアップから復元
python scripts/chat_backup.py --restore CLAUDE_backup_20240105_120000.md
```

## 📂 ディレクトリ構造

```
/
├── docs/                    # ドキュメント関連
│   ├── dashboard.html       # 開発ダッシュボード
│   ├── feature_design.html  # 機能設計書
│   ├── environment_design.html  # 環境設計書
│   ├── test_specification.html  # テスト仕様書
│   ├── progress_data.json   # 進捗データ
│   └── auto_updater.py      # 自動更新スクリプト
│
├── test/                    # テスト関連
│   ├── scripts/            # テストスクリプト
│   └── data/               # テストデータ
│
├── scripts/                 # ユーティリティスクリプト
│   └── chat_backup.py       # チャットバックアップ
│
├── backups/                 # バックアップディレクトリ（自動生成）
├── index.html              # GitHub Pages メインページ
├── _config.yml             # Jekyll設定
├── CLAUDE.md               # Claude Code設定ファイル
└── README.md               # 本ファイル
```

## 🔧 GitHub Pages設定

### 自動デプロイ設定

1. GitHubリポジトリの設定ページで「Pages」セクションに移動
2. Sourceを「Deploy from a branch」に設定
3. Branchを「main」または「master」に設定
4. Folderを「/ (root)」に設定
5. 「Save」をクリック

### カスタムドメイン（オプション）

独自ドメインを使用する場合：
1. リポジトリのルートに `CNAME` ファイルを作成
2. ファイルにドメイン名を記述（例：`docs.yoursite.com`）
3. DNSでCNAMEレコードを設定

## 🤝 貢献方法

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 🆘 サポート

問題が発生した場合や改善提案がある場合は、[Issues](https://github.com/horiken1977/tags/issues) で報告してください。

---

**Powered by Claude Code** 🤖
