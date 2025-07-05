#!/usr/bin/env python3
"""
チャット自動保存スクリプト
Claude Codeとのチャット履歴を定期的に保存し、クラッシュ対応を行います。
"""

import os
import sys
import time
import json
import shutil
from datetime import datetime, timedelta
import signal
import threading
import schedule

class ChatBackupManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.claude_md_path = os.path.join(self.base_dir, 'CLAUDE.md')
        self.backup_dir = os.path.join(self.base_dir, 'backups')
        self.config_file = os.path.join(self.base_dir, '.chat_backup_config.json')
        
        # バックアップディレクトリの作成
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 設定の読み込み
        self.config = self.load_config()
        
        # シャットダウンフラグ
        self.shutdown = False
        
        # シグナルハンドラの設定
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def load_config(self):
        """設定ファイルを読み込み"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # デフォルト設定
        return {
            'interval_hours': 2,
            'max_backups': 10,
            'last_backup': None,
            'backup_count': 0,
            'auto_save_enabled': True
        }
    
    def save_config(self):
        """設定ファイルを保存"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def signal_handler(self, signum, frame):
        """シグナルハンドラ"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 終了シグナルを受信しました")
        self.shutdown = True
        sys.exit(0)
    
    def create_backup(self):
        """バックアップを作成"""
        if not os.path.exists(self.claude_md_path):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CLAUDE.mdファイルが見つかりません")
            return False
        
        # バックアップファイル名を生成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"CLAUDE_backup_{timestamp}.md"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # ファイルをコピー
            shutil.copy2(self.claude_md_path, backup_path)
            
            # 設定を更新
            self.config['last_backup'] = datetime.now().isoformat()
            self.config['backup_count'] += 1
            self.save_config()
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ バックアップ作成完了: {backup_filename}")
            
            # 古いバックアップを削除
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ バックアップ失敗: {str(e)}")
            return False
    
    def cleanup_old_backups(self):
        """古いバックアップを削除"""
        backups = []
        
        # バックアップファイルをリストアップ
        for filename in os.listdir(self.backup_dir):
            if filename.startswith('CLAUDE_backup_') and filename.endswith('.md'):
                filepath = os.path.join(self.backup_dir, filename)
                backups.append((filepath, os.path.getctime(filepath)))
        
        # 作成日時でソート（新しい順）
        backups.sort(key=lambda x: x[1], reverse=True)
        
        # 最大保存数を超えた分を削除
        max_backups = self.config.get('max_backups', 10)
        for filepath, _ in backups[max_backups:]:
            try:
                os.remove(filepath)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 古いバックアップを削除: {os.path.basename(filepath)}")
            except:
                pass
    
    def update_claude_md(self):
        """CLAUDE.mdファイルに設定情報を追記"""
        content = []
        
        # 既存の内容を読み込み
        if os.path.exists(self.claude_md_path):
            with open(self.claude_md_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
        
        # 設定セクションを探す
        config_start = -1
        config_end = -1
        
        for i, line in enumerate(content):
            if line.strip() == '## Auto-save Settings':
                config_start = i
            elif config_start != -1 and line.startswith('##') and i > config_start:
                config_end = i
                break
        
        # 設定情報を準備
        config_section = [
            '## Auto-save Settings\n',
            f'- Interval: {self.config["interval_hours"]} hours\n',
            f'- Backup location: ./backups/\n',
            f'- Max backups: {self.config["max_backups"]}\n',
            f'- Last backup: {self.config.get("last_backup", "Never")}\n',
            f'- Total backups: {self.config["backup_count"]}\n',
            f'- Auto-save: {"enabled" if self.config["auto_save_enabled"] else "disabled"}\n',
            '\n'
        ]
        
        # 設定セクションを更新または追加
        if config_start != -1:
            if config_end == -1:
                config_end = len(content)
            content[config_start:config_end] = config_section
        else:
            # セクションが存在しない場合は追加
            if content and not content[-1].endswith('\n'):
                content.append('\n')
            content.extend(['\n'] + config_section)
        
        # ファイルに書き込み
        with open(self.claude_md_path, 'w', encoding='utf-8') as f:
            f.writelines(content)
    
    def display_status(self):
        """ステータスをターミナルに表示"""
        print(f"\n{'='*60}")
        print(f"チャット自動保存スクリプト - ステータス")
        print(f"{'='*60}")
        print(f"現在時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"最終バックアップ: {self.config.get('last_backup', 'なし')}")
        print(f"バックアップ回数: {self.config['backup_count']}")
        print(f"保存間隔: {self.config['interval_hours']}時間")
        
        # 次回バックアップ時刻を計算
        if self.config.get('last_backup'):
            last_backup_time = datetime.fromisoformat(self.config['last_backup'])
            next_backup_time = last_backup_time + timedelta(hours=self.config['interval_hours'])
            print(f"次回バックアップ: {next_backup_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"次回バックアップ: 2時間後")
        
        print(f"{'='*60}\n")
    
    def scheduled_backup(self):
        """スケジュールされたバックアップを実行"""
        self.create_backup()
        self.update_claude_md()
        self.display_status()
    
    def run(self, interval_hours=2):
        """メインループ"""
        self.config['interval_hours'] = interval_hours
        self.save_config()
        
        print(f"チャット自動保存スクリプトを開始しました")
        print(f"バックアップ間隔: {interval_hours}時間")
        print(f"バックアップ保存先: {self.backup_dir}")
        print(f"Ctrl+Cで終了します\n")
        
        # 初回のステータス表示
        self.display_status()
        
        # 初回バックアップを実行
        self.scheduled_backup()
        
        # スケジュールを設定
        schedule.every(interval_hours).hours.do(self.scheduled_backup)
        
        # 2時間ごとにステータスを表示
        schedule.every(2).hours.do(self.display_status)
        
        # メインループ
        while not self.shutdown:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック

def main():
    """メイン関数"""
    manager = ChatBackupManager()
    
    # コマンドライン引数の処理
    interval_hours = 2
    
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:]):
            if arg == '--interval' and i + 2 < len(sys.argv):
                interval_str = sys.argv[i + 2]
                if interval_str.endswith('h'):
                    try:
                        interval_hours = int(interval_str[:-1])
                    except ValueError:
                        print(f"エラー: 無効な間隔指定 '{interval_str}'")
                        sys.exit(1)
            elif arg == '--restore' and i + 2 < len(sys.argv):
                # バックアップからの復元機能
                backup_file = sys.argv[i + 2]
                backup_path = os.path.join(manager.backup_dir, backup_file)
                
                if os.path.exists(backup_path):
                    try:
                        shutil.copy2(backup_path, manager.claude_md_path)
                        print(f"✓ バックアップから復元しました: {backup_file}")
                        sys.exit(0)
                    except Exception as e:
                        print(f"✗ 復元に失敗しました: {str(e)}")
                        sys.exit(1)
                else:
                    print(f"エラー: バックアップファイルが見つかりません: {backup_file}")
                    sys.exit(1)
            elif arg == '--list':
                # バックアップ一覧を表示
                print("利用可能なバックアップ:")
                backups = []
                for filename in os.listdir(manager.backup_dir):
                    if filename.startswith('CLAUDE_backup_') and filename.endswith('.md'):
                        filepath = os.path.join(manager.backup_dir, filename)
                        size = os.path.getsize(filepath) / 1024  # KB
                        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        backups.append((filename, size, mtime))
                
                backups.sort(key=lambda x: x[2], reverse=True)
                
                for filename, size, mtime in backups:
                    print(f"  - {filename} ({size:.1f} KB) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                
                sys.exit(0)
    
    # バックアップを開始
    try:
        manager.run(interval_hours)
    except KeyboardInterrupt:
        print("\n\nチャット自動保存スクリプトを終了しました")
        sys.exit(0)

if __name__ == '__main__':
    main()