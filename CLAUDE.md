# Claude Code Configuration

このファイルはClaude Codeとの開発セッション用の設定と履歴を保存します。

## プロジェクト概要

開発支援ツールの構築プロジェクト。以下の機能を含みます：
- 開発ドキュメントの自動生成と更新
- チャット内容の自動解析と反映
- 進捗状況の可視化
- テスト管理と自動実行

## 環境設定

### ディレクトリ構造
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
├── CLAUDE.md               # 本ファイル
└── backups/                # バックアップディレクトリ
```

## Auto-save Settings
- Interval: 2 hours
- Backup location: ./backups/
- Max backups: 10
- Last backup: Never
- Total backups: 0
- Auto-save: enabled

## Document Update Settings
- Auto-update: enabled
- Update trigger: on chat message
- Progress calculation: automatic

## スクリプト実行方法

### ドキュメント自動更新
```bash
# 監視モードで実行（推奨）
python docs/auto_updater.py

# 1回だけ実行
python docs/auto_updater.py --once
```

### チャット自動保存
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

## 開発メモ

### 実装済み機能
- ✅ 開発ダッシュボード
- ✅ 機能設計書
- ✅ 環境設計書
- ✅ テスト仕様書
- ✅ チャット解析・ドキュメント更新スクリプト
- ✅ チャット自動保存スクリプト

### 今後の実装予定
- テスト実行スクリプト
- パフォーマンス監視
- エラーログ管理
- CI/CD統合

## チャット履歴

以下にClaude Codeとのチャット履歴が自動的に保存されます。

---

### セッション開始: 2025-01-05

ユーザー: 開発環境の整備をお願いしました。
- 開発ドキュメントの作成と自動更新
- チャット自動保存機能（2時間ごと）
- ダッシュボードでの進捗可視化

Claude Code: 必要なディレクトリ構造を作成し、各種HTMLドキュメントと自動化スクリプトを実装しました。