"""
タグ最適化モジュール
重複排除、重要度スコアリング、タグ統合機能を提供
"""

import json
import logging
import re
from collections import Counter, defaultdict
from typing import List, Dict, Any, Set, Tuple
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class TagOptimizer:
    """タグ最適化クラス"""
    
    def __init__(self, config_path: str = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path or "config/settings.json"
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)
        
        # 最適化設定
        self.optimization_config = self.config.get('tag_optimization', {})
        self.min_frequency = self.optimization_config.get('min_frequency', 2)
        self.similarity_threshold = self.optimization_config.get('similarity_threshold', 0.8)
        self.importance_weights = self.optimization_config.get('importance_weights', {
            'title': 0.3,
            'skill': 0.25,
            'description': 0.2,
            'summary': 0.15,
            'transcript': 0.1
        })
        
        # 目標タグ数
        self.target_tag_count = self.config.get('processing', {}).get('target_tag_count', 175)
        self.min_tag_count = self.config.get('processing', {}).get('min_tag_count', 150)
        self.max_tag_count = self.config.get('processing', {}).get('max_tag_count', 200)
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {str(e)}")
            return {}
    
    def optimize_tags(
        self, 
        all_tags: List[List[str]],
        video_data: pd.DataFrame,
        column_mapping: Dict[str, str]
    ) -> List[str]:
        """
        全タグを最適化して最終タグセットを生成
        
        Args:
            all_tags: 各動画のタグリスト
            video_data: 動画データ
            column_mapping: 列マッピング
            
        Returns:
            最適化されたタグリスト
        """
        self.logger.info("タグ最適化処理を開始")
        
        # Step 1: 全タグを収集・クリーニング
        cleaned_tags = self._collect_and_clean_tags(all_tags)
        self.logger.info(f"クリーニング後タグ数: {len(cleaned_tags)}")
        
        # Step 2: 頻度分析
        tag_frequencies = self._analyze_tag_frequencies(cleaned_tags)
        self.logger.info(f"ユニークタグ数: {len(tag_frequencies)}")
        
        # Step 3: 重要度スコア計算
        tag_scores = self._calculate_importance_scores(
            cleaned_tags, video_data, column_mapping
        )
        
        # Step 4: 類似タグの統合
        merged_tags = self._merge_similar_tags(tag_frequencies, tag_scores)
        self.logger.info(f"統合後タグ数: {len(merged_tags)}")
        
        # Step 5: 最終選択
        final_tags = self._select_final_tags(merged_tags)
        self.logger.info(f"最終タグ数: {len(final_tags)}")
        
        return final_tags
    
    def _collect_and_clean_tags(self, all_tags: List[List[str]]) -> List[str]:
        """
        全タグを収集・クリーニング
        
        Args:
            all_tags: 各動画のタグリスト
            
        Returns:
            クリーニング済みタグリスト
        """
        cleaned_tags = []
        
        for video_tags in all_tags:
            for tag in video_tags:
                cleaned_tag = self._clean_single_tag(tag)
                if cleaned_tag:
                    cleaned_tags.append(cleaned_tag)
        
        return cleaned_tags
    
    def _clean_single_tag(self, tag: str) -> str:
        """
        単一タグをクリーニング
        
        Args:
            tag: 元のタグ
            
        Returns:
            クリーニング済みタグ
        """
        if not tag or not isinstance(tag, str):
            return ""
        
        # 基本的なクリーニング
        tag = tag.strip()
        
        # 長すぎるタグは除外
        if len(tag) > 50:
            return ""
        
        # 短すぎるタグは除外
        if len(tag) < 2:
            return ""
        
        # 数字のみのタグは除外
        if tag.isdigit():
            return ""
        
        # 特殊文字をクリーニング
        tag = re.sub(r'[^\w\s\-ー・]', '', tag)
        tag = re.sub(r'\s+', ' ', tag)
        
        return tag.strip()
    
    def _analyze_tag_frequencies(self, tags: List[str]) -> Counter:
        """
        タグ頻度を分析
        
        Args:
            tags: タグリスト
            
        Returns:
            タグ頻度カウンター
        """
        # 大小文字・表記揺れを正規化
        normalized_tags = []
        for tag in tags:
            # 小文字化
            normalized = tag.lower()
            # 全角・半角統一
            normalized = self._normalize_characters(normalized)
            normalized_tags.append(normalized)
        
        return Counter(normalized_tags)
    
    def _normalize_characters(self, text: str) -> str:
        """
        文字の正規化
        
        Args:
            text: 元のテキスト
            
        Returns:
            正規化されたテキスト
        """
        # 全角数字を半角に
        text = text.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        
        # 全角英字を半角に
        text = text.translate(str.maketrans(
            'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        ))
        
        return text
    
    def _calculate_importance_scores(
        self, 
        tags: List[str],
        video_data: pd.DataFrame,
        column_mapping: Dict[str, str]
    ) -> Dict[str, float]:
        """
        タグの重要度スコアを計算
        
        Args:
            tags: タグリスト
            video_data: 動画データ
            column_mapping: 列マッピング
            
        Returns:
            タグ重要度スコア辞書
        """
        tag_scores = defaultdict(float)
        
        # 各動画のコンテンツを結合
        all_content = []
        for _, row in video_data.iterrows():
            content_parts = []
            
            for field, weight in self.importance_weights.items():
                column_name = column_mapping.get(field, '')
                if column_name and column_name in row:
                    text = str(row[column_name])
                    # 重要度に応じて重み付け
                    weighted_text = ' '.join([text] * int(weight * 10))
                    content_parts.append(weighted_text)
            
            all_content.append(' '.join(content_parts))
        
        # TF-IDFでタグの重要度を計算
        try:
            # ユニークタグを取得
            unique_tags = list(set(tags))
            
            if len(unique_tags) > 1 and len(all_content) > 0:
                vectorizer = TfidfVectorizer(
                    vocabulary=unique_tags,
                    ngram_range=(1, 3),
                    max_features=1000
                )
                
                tfidf_matrix = vectorizer.fit_transform(all_content)
                feature_names = vectorizer.get_feature_names_out()
                
                # 各タグのTF-IDFスコアを平均
                for i, tag in enumerate(feature_names):
                    scores = tfidf_matrix[:, i].toarray().flatten()
                    tag_scores[tag] = float(np.mean(scores))
        
        except Exception as e:
            self.logger.warning(f"TF-IDF計算エラー: {str(e)}")
            # フォールバック: 頻度ベースのスコア
            tag_freq = Counter(tags)
            max_freq = max(tag_freq.values()) if tag_freq else 1
            for tag, freq in tag_freq.items():
                tag_scores[tag] = freq / max_freq
        
        return dict(tag_scores)
    
    def _merge_similar_tags(
        self, 
        tag_frequencies: Counter,
        tag_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        類似タグを統合
        
        Args:
            tag_frequencies: タグ頻度
            tag_scores: タグ重要度スコア
            
        Returns:
            統合後タグスコア辞書
        """
        tags_list = list(tag_frequencies.keys())
        merged_scores = {}
        processed_tags = set()
        
        for tag in tags_list:
            if tag in processed_tags:
                continue
            
            # 類似タグを検索
            similar_tags = self._find_similar_tags(tag, tags_list)
            
            if len(similar_tags) > 1:
                # 類似タグがある場合は統合
                best_tag = self._select_best_tag(similar_tags, tag_frequencies, tag_scores)
                total_score = sum(tag_scores.get(t, 0) for t in similar_tags)
                total_frequency = sum(tag_frequencies.get(t, 0) for t in similar_tags)
                
                # 統合スコア計算
                merged_scores[best_tag] = total_score + (total_frequency * 0.1)
                processed_tags.update(similar_tags)
            else:
                # 類似タグがない場合はそのまま
                frequency = tag_frequencies.get(tag, 0)
                importance = tag_scores.get(tag, 0)
                merged_scores[tag] = importance + (frequency * 0.1)
                processed_tags.add(tag)
        
        return merged_scores
    
    def _find_similar_tags(self, target_tag: str, all_tags: List[str]) -> List[str]:
        """
        類似タグを検索
        
        Args:
            target_tag: 対象タグ
            all_tags: 全タグリスト
            
        Returns:
            類似タグリスト
        """
        similar_tags = [target_tag]
        
        for tag in all_tags:
            if tag != target_tag:
                similarity = self._calculate_tag_similarity(target_tag, tag)
                if similarity >= self.similarity_threshold:
                    similar_tags.append(tag)
        
        return similar_tags
    
    def _calculate_tag_similarity(self, tag1: str, tag2: str) -> float:
        """
        タグ間の類似度を計算
        
        Args:
            tag1: タグ1
            tag2: タグ2
            
        Returns:
            類似度 (0-1)
        """
        # 文字レベルの類似度
        if tag1 == tag2:
            return 1.0
        
        # 包含関係チェック
        if tag1 in tag2 or tag2 in tag1:
            return 0.9
        
        # 編集距離ベースの類似度
        def levenshtein_distance(s1, s2):
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        max_len = max(len(tag1), len(tag2))
        if max_len == 0:
            return 1.0
        
        distance = levenshtein_distance(tag1, tag2)
        similarity = 1.0 - (distance / max_len)
        
        return similarity
    
    def _select_best_tag(
        self, 
        similar_tags: List[str],
        tag_frequencies: Counter,
        tag_scores: Dict[str, float]
    ) -> str:
        """
        類似タグの中から最適なタグを選択
        
        Args:
            similar_tags: 類似タグリスト
            tag_frequencies: タグ頻度
            tag_scores: タグ重要度スコア
            
        Returns:
            最適なタグ
        """
        best_tag = similar_tags[0]
        best_score = 0
        
        for tag in similar_tags:
            # 頻度と重要度の重み付きスコア
            frequency = tag_frequencies.get(tag, 0)
            importance = tag_scores.get(tag, 0)
            
            # より短く、一般的でないタグを優先
            length_bonus = 1.0 / (len(tag) + 1)
            
            total_score = importance + (frequency * 0.1) + length_bonus
            
            if total_score > best_score:
                best_score = total_score
                best_tag = tag
        
        return best_tag
    
    def _select_final_tags(self, merged_tags: Dict[str, float]) -> List[str]:
        """
        最終タグセットを選択
        
        Args:
            merged_tags: 統合済みタグスコア辞書
            
        Returns:
            最終タグリスト
        """
        # スコア順にソート
        sorted_tags = sorted(
            merged_tags.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # 目標タグ数に基づいて選択
        if len(sorted_tags) <= self.min_tag_count:
            # タグ数が少なすぎる場合は全て採用
            final_tags = [tag for tag, score in sorted_tags]
        elif len(sorted_tags) <= self.max_tag_count:
            # 適切な範囲内の場合は全て採用
            final_tags = [tag for tag, score in sorted_tags]
        else:
            # 多すぎる場合は上位を選択
            final_tags = [tag for tag, score in sorted_tags[:self.target_tag_count]]
        
        # 最小頻度フィルタリング
        final_tags = [
            tag for tag in final_tags
            if merged_tags[tag] >= self.min_frequency * 0.1
        ]
        
        return final_tags
    
    def generate_tag_analytics(
        self, 
        final_tags: List[str],
        all_tags: List[List[str]]
    ) -> Dict[str, Any]:
        """
        タグ分析レポートを生成
        
        Args:
            final_tags: 最終タグリスト
            all_tags: 元の全タグリスト
            
        Returns:
            分析レポート
        """
        # 基本統計
        total_original_tags = sum(len(tags) for tags in all_tags)
        unique_original_tags = len(set(tag for tags in all_tags for tag in tags))
        
        # カバレッジ計算
        coverage = self._calculate_coverage(final_tags, all_tags)
        
        return {
            'total_final_tags': len(final_tags),
            'total_original_tags': total_original_tags,
            'unique_original_tags': unique_original_tags,
            'reduction_ratio': 1 - (len(final_tags) / unique_original_tags) if unique_original_tags > 0 else 0,
            'coverage_percentage': coverage,
            'final_tags': final_tags
        }
    
    def _calculate_coverage(self, final_tags: List[str], all_tags: List[List[str]]) -> float:
        """
        タグカバレッジを計算
        
        Args:
            final_tags: 最終タグリスト
            all_tags: 元の全タグリスト
            
        Returns:
            カバレッジ率
        """
        final_tags_set = set(tag.lower() for tag in final_tags)
        covered_videos = 0
        
        for video_tags in all_tags:
            video_tags_set = set(tag.lower() for tag in video_tags)
            if final_tags_set.intersection(video_tags_set):
                covered_videos += 1
        
        return (covered_videos / len(all_tags)) * 100 if all_tags else 0