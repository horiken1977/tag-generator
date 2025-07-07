"""
基本機能テスト
Tag Generatorの主要コンポーネントの動作確認
"""

import unittest
import sys
import os
import json
from unittest.mock import Mock, patch

# パスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from tag_optimizer import TagOptimizer
import pandas as pd


class TestTagOptimizer(unittest.TestCase):
    """TagOptimizer の基本テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        # テスト用設定
        test_config = {
            'tag_optimization': {
                'min_frequency': 2,
                'similarity_threshold': 0.8,
                'importance_weights': {
                    'title': 0.3,
                    'skill': 0.25,
                    'description': 0.2,
                    'summary': 0.15,
                    'transcript': 0.1
                }
            },
            'processing': {
                'target_tag_count': 10,
                'min_tag_count': 5,
                'max_tag_count': 20
            }
        }
        
        # 一時的な設定ファイルを作成
        self.test_config_path = '/tmp/test_settings.json'
        with open(self.test_config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        self.optimizer = TagOptimizer(self.test_config_path)
    
    def tearDown(self):
        """テストクリーンアップ"""
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
    
    def test_clean_single_tag(self):
        """単一タグクリーニングのテスト"""
        # 正常なタグ
        self.assertEqual(self.optimizer._clean_single_tag("マーケティング"), "マーケティング")
        
        # スペースのトリム
        self.assertEqual(self.optimizer._clean_single_tag("  デジタル広告  "), "デジタル広告")
        
        # 長すぎるタグの除外
        long_tag = "a" * 51
        self.assertEqual(self.optimizer._clean_single_tag(long_tag), "")
        
        # 短すぎるタグの除外
        self.assertEqual(self.optimizer._clean_single_tag("a"), "")
        
        # 数字のみのタグの除外
        self.assertEqual(self.optimizer._clean_single_tag("123"), "")
        
        # 空文字・None の処理
        self.assertEqual(self.optimizer._clean_single_tag(""), "")
        self.assertEqual(self.optimizer._clean_single_tag(None), "")
    
    def test_normalize_characters(self):
        """文字正規化のテスト"""
        # 全角数字→半角数字
        self.assertEqual(self.optimizer._normalize_characters("１２３"), "123")
        
        # 全角英字→半角英字
        self.assertEqual(self.optimizer._normalize_characters("ＡＢＣ"), "ABC")
        self.assertEqual(self.optimizer._normalize_characters("ａｂｃ"), "abc")
        
        # 混在
        self.assertEqual(
            self.optimizer._normalize_characters("マーケティング１２３ＡＢＣ"), 
            "マーケティング123ABC"
        )
    
    def test_collect_and_clean_tags(self):
        """タグ収集・クリーニングのテスト"""
        all_tags = [
            ["マーケティング", "広告", ""],
            ["SEO", "   デジタル   ", "123"],
            ["コンテンツ", "a", "マーケティング"]  # 重複と無効なタグを含む
        ]
        
        cleaned = self.optimizer._collect_and_clean_tags(all_tags)
        
        # 有効なタグのみが残る
        expected_tags = ["マーケティング", "広告", "SEO", "デジタル", "コンテンツ", "マーケティング"]
        self.assertEqual(cleaned, expected_tags)
    
    def test_calculate_tag_similarity(self):
        """タグ類似度計算のテスト"""
        # 完全一致
        self.assertEqual(self.optimizer._calculate_tag_similarity("test", "test"), 1.0)
        
        # 包含関係
        similarity = self.optimizer._calculate_tag_similarity("マーケティング", "マーケティング戦略")
        self.assertGreater(similarity, 0.8)
        
        # 全く異なる
        similarity = self.optimizer._calculate_tag_similarity("マーケティング", "プログラミング")
        self.assertLess(similarity, 0.5)
    
    def test_generate_tag_analytics(self):
        """タグ分析レポート生成のテスト"""
        final_tags = ["マーケティング", "SEO", "広告"]
        all_tags = [
            ["マーケティング", "広告", "コンテンツ"],
            ["SEO", "検索", "最適化"],
            ["デジタル", "マーケティング", "戦略"]
        ]
        
        analytics = self.optimizer.generate_tag_analytics(final_tags, all_tags)
        
        # 基本統計の確認
        self.assertEqual(analytics['total_final_tags'], 3)
        self.assertEqual(analytics['total_original_tags'], 9)
        self.assertGreater(analytics['coverage_percentage'], 0)
        self.assertIn('reduction_ratio', analytics)


class TestConfigLoading(unittest.TestCase):
    """設定ファイル読み込みのテスト"""
    
    def test_load_valid_config(self):
        """有効な設定ファイルの読み込み"""
        config_data = {'test': 'value'}
        test_path = '/tmp/valid_config.json'
        
        with open(test_path, 'w') as f:
            json.dump(config_data, f)
        
        optimizer = TagOptimizer(test_path)
        self.assertEqual(optimizer.config['test'], 'value')
        
        # クリーンアップ
        os.remove(test_path)
    
    def test_load_invalid_config(self):
        """無効な設定ファイルの処理"""
        # 存在しないファイル
        optimizer = TagOptimizer('/tmp/nonexistent.json')
        self.assertEqual(optimizer.config, {})


class TestMemoryEfficiency(unittest.TestCase):
    """メモリ効率性のテスト"""
    
    def test_large_tag_list_processing(self):
        """大量タグリストの処理"""
        # 1000個のタグを生成
        large_tag_list = []
        for i in range(100):  # 100動画
            video_tags = [f"tag_{i}_{j}" for j in range(10)]  # 各動画10タグ
            large_tag_list.append(video_tags)
        
        optimizer = TagOptimizer()
        
        # メモリエラーが発生しないことを確認
        try:
            cleaned_tags = optimizer._collect_and_clean_tags(large_tag_list)
            self.assertEqual(len(cleaned_tags), 1000)
        except MemoryError:
            self.fail("メモリエラーが発生しました")


if __name__ == '__main__':
    # テスト実行
    unittest.main(verbosity=2)