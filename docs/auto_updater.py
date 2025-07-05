#!/usr/bin/env python3
"""
チャット自動解析・ドキュメント更新スクリプト
Claude Codeとのチャット内容を解析し、各種ドキュメントを自動更新します。
"""

import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Any
import time

class DocumentAutoUpdater:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.progress_file = os.path.join(self.base_dir, 'progress_data.json')
        self.chat_history_file = os.path.join(self.base_dir, '..', 'CLAUDE.md')
        
        # 進捗データの初期化
        self.progress_data = self.load_progress_data()
        
        # キーワードパターンの定義
        self.patterns = {
            'feature': [
                r'機能[：:]\s*(.+)',
                r'実装[：:]\s*(.+)',
                r'追加[：:]\s*(.+)',
                r'開発[：:]\s*(.+)',
            ],
            'environment': [
                r'環境[：:]\s*(.+)',
                r'設定[：:]\s*(.+)',
                r'インストール[：:]\s*(.+)',
                r'構築[：:]\s*(.+)',
            ],
            'test': [
                r'テスト[：:]\s*(.+)',
                r'検証[：:]\s*(.+)',
                r'確認[：:]\s*(.+)',
                r'品質[：:]\s*(.+)',
            ]
        }
    
    def load_progress_data(self) -> Dict[str, Any]:
        """進捗データを読み込み"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # デフォルトの進捗データ
        return {
            'overall': 0,
            'feature': 0,
            'environment': 0,
            'test': 0,
            'phase': 'planning',
            'updateCount': 0,
            'nextTasks': [
                '機能要件の定義',
                '環境設計の詳細化',
                'テスト計画の策定'
            ],
            'features': [],
            'environments': [],
            'tests': [],
            'lastUpdate': None
        }
    
    def save_progress_data(self):
        """進捗データを保存"""
        self.progress_data['lastUpdate'] = datetime.now().isoformat()
        self.progress_data['updateCount'] += 1
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress_data, f, ensure_ascii=False, indent=2)
    
    def analyze_chat_content(self, content: str) -> Dict[str, List[str]]:
        """チャット内容を解析して情報を抽出"""
        extracted = {
            'features': [],
            'environments': [],
            'tests': []
        }
        
        lines = content.split('\n')
        
        for line in lines:
            # 機能関連の抽出
            for pattern in self.patterns['feature']:
                match = re.search(pattern, line)
                if match:
                    extracted['features'].append(match.group(1).strip())
            
            # 環境関連の抽出
            for pattern in self.patterns['environment']:
                match = re.search(pattern, line)
                if match:
                    extracted['environments'].append(match.group(1).strip())
            
            # テスト関連の抽出
            for pattern in self.patterns['test']:
                match = re.search(pattern, line)
                if match:
                    extracted['tests'].append(match.group(1).strip())
        
        return extracted
    
    def calculate_progress(self):
        """進捗率を計算"""
        # 各カテゴリの進捗を計算（簡易版）
        feature_items = len(self.progress_data.get('features', []))
        env_items = len(self.progress_data.get('environments', []))
        test_items = len(self.progress_data.get('tests', []))
        
        # 進捗率の計算（仮の計算式）
        self.progress_data['feature'] = min(feature_items * 10, 100)
        self.progress_data['environment'] = min(env_items * 15, 100)
        self.progress_data['test'] = min(test_items * 20, 100)
        
        # 全体進捗の計算
        self.progress_data['overall'] = (
            self.progress_data['feature'] * 0.4 +
            self.progress_data['environment'] * 0.3 +
            self.progress_data['test'] * 0.3
        )
        
        # フェーズの判定
        if self.progress_data['overall'] < 20:
            self.progress_data['phase'] = 'planning'
        elif self.progress_data['overall'] < 60:
            self.progress_data['phase'] = 'development'
        elif self.progress_data['overall'] < 90:
            self.progress_data['phase'] = 'testing'
        else:
            self.progress_data['phase'] = 'completed'
    
    def update_next_tasks(self):
        """次のタスクを更新"""
        phase = self.progress_data['phase']
        
        if phase == 'planning':
            self.progress_data['nextTasks'] = [
                '機能要件の詳細定義',
                '技術スタックの選定',
                'プロトタイプの作成'
            ]
        elif phase == 'development':
            self.progress_data['nextTasks'] = [
                'コア機能の実装',
                'UIの作成',
                'APIの開発'
            ]
        elif phase == 'testing':
            self.progress_data['nextTasks'] = [
                'ユニットテストの実行',
                '統合テストの実施',
                'パフォーマンステスト'
            ]
        else:
            self.progress_data['nextTasks'] = [
                'リリース準備',
                'ドキュメントの最終確認',
                'デプロイメント'
            ]
    
    def update_html_files(self):
        """HTMLファイルを更新"""
        # JavaScriptから読み込める形式でデータを準備
        js_data = f"const progressData = {json.dumps(self.progress_data, ensure_ascii=False)};"
        
        # progress_data.jsファイルを作成
        js_file = os.path.join(self.base_dir, 'progress_data.js')
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(js_data)
        
        print(f"✓ progress_data.jsを更新しました")
    
    def monitor_and_update(self):
        """チャット内容を監視して更新"""
        print("チャット自動解析・ドキュメント更新スクリプトを開始しました")
        print(f"監視対象: {self.chat_history_file}")
        print("Ctrl+Cで終了します\n")
        
        last_modified = 0
        
        try:
            while True:
                # CLAUDE.mdファイルの更新を確認
                if os.path.exists(self.chat_history_file):
                    current_modified = os.path.getmtime(self.chat_history_file)
                    
                    if current_modified > last_modified:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] チャット更新を検出")
                        
                        # ファイル内容を読み込み
                        with open(self.chat_history_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # チャット内容を解析
                        extracted = self.analyze_chat_content(content)
                        
                        # 抽出された情報を進捗データに追加
                        for feature in extracted['features']:
                            if feature not in self.progress_data['features']:
                                self.progress_data['features'].append(feature)
                                print(f"  → 新しい機能を検出: {feature}")
                        
                        for env in extracted['environments']:
                            if env not in self.progress_data['environments']:
                                self.progress_data['environments'].append(env)
                                print(f"  → 新しい環境設定を検出: {env}")
                        
                        for test in extracted['tests']:
                            if test not in self.progress_data['tests']:
                                self.progress_data['tests'].append(test)
                                print(f"  → 新しいテスト項目を検出: {test}")
                        
                        # 進捗を計算
                        self.calculate_progress()
                        
                        # 次のタスクを更新
                        self.update_next_tasks()
                        
                        # データを保存
                        self.save_progress_data()
                        
                        # HTMLファイルを更新
                        self.update_html_files()
                        
                        print(f"  → 進捗更新完了: 全体 {self.progress_data['overall']:.1f}%")
                        
                        last_modified = current_modified
                
                # 5秒ごとにチェック
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n\nスクリプトを終了しました")
            sys.exit(0)

def main():
    updater = DocumentAutoUpdater()
    
    # 引数なしで実行された場合は監視モード
    if len(sys.argv) == 1:
        updater.monitor_and_update()
    
    # --once オプションで1回だけ実行
    elif len(sys.argv) > 1 and sys.argv[1] == '--once':
        if os.path.exists(updater.chat_history_file):
            with open(updater.chat_history_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            extracted = updater.analyze_chat_content(content)
            
            # 抽出された情報を進捗データに追加
            updater.progress_data['features'].extend(extracted['features'])
            updater.progress_data['environments'].extend(extracted['environments'])
            updater.progress_data['tests'].extend(extracted['tests'])
            
            # 重複を削除
            updater.progress_data['features'] = list(set(updater.progress_data['features']))
            updater.progress_data['environments'] = list(set(updater.progress_data['environments']))
            updater.progress_data['tests'] = list(set(updater.progress_data['tests']))
            
            updater.calculate_progress()
            updater.update_next_tasks()
            updater.save_progress_data()
            updater.update_html_files()
            
            print("ドキュメントを更新しました")
        else:
            print(f"エラー: {updater.chat_history_file} が見つかりません")
    
    else:
        print("使用方法:")
        print("  python auto_updater.py         # 監視モードで実行")
        print("  python auto_updater.py --once  # 1回だけ実行")

if __name__ == '__main__':
    main()