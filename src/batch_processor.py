"""
バッチ処理モジュール
メモリ効率的な分割処理を提供
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional, Callable
import pandas as pd
import streamlit as st
from .ai_processors.openai_processor import OpenAIProcessor
from .ai_processors.claude_processor import ClaudeProcessor  
from .ai_processors.gemini_processor import GeminiProcessor


class BatchProcessor:
    """バッチ処理クラス"""
    
    def __init__(self, config_path: str = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path or "config/settings.json"
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)
        
        # 処理設定
        self.batch_size = self.config.get('processing', {}).get('batch_size', 10)
        self.max_memory_mb = self.config.get('processing', {}).get('max_memory_mb', 512)
        
        # AI processors
        self.processors = {}
        self._initialize_processors()
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {str(e)}")
            return {}
    
    def _initialize_processors(self):
        """AI processors を初期化"""
        ai_configs = self.config.get('ai_models', {})
        
        try:
            # OpenAI
            openai_config = ai_configs.get('openai', {})
            self.processors['openai'] = OpenAIProcessor(openai_config)
            
            # Claude
            claude_config = ai_configs.get('claude', {})
            self.processors['claude'] = ClaudeProcessor(claude_config)
            
            # Gemini
            gemini_config = ai_configs.get('gemini', {})
            self.processors['gemini'] = GeminiProcessor(gemini_config)
            
        except Exception as e:
            self.logger.error(f"AI processor初期化エラー: {str(e)}")
    
    def test_ai_connections(self) -> Dict[str, bool]:
        """
        全AIサービスの接続テスト
        
        Returns:
            各AIサービスの接続状況
        """
        results = {}
        
        for name, processor in self.processors.items():
            try:
                results[name] = processor.test_connection()
            except Exception as e:
                self.logger.error(f"{name} 接続テストエラー: {str(e)}")
                results[name] = False
                
        return results
    
    def process_videos_batch(
        self, 
        video_data: pd.DataFrame,
        ai_provider: str,
        column_mapping: Dict[str, str],
        progress_callback: Optional[Callable] = None
    ) -> List[List[str]]:
        """
        動画データをバッチ処理してタグを生成
        
        Args:
            video_data: 動画データのDataFrame
            ai_provider: 使用するAIプロバイダー ('openai', 'claude', 'gemini')
            column_mapping: 列マッピング辞書
            progress_callback: 進捗コールバック関数
            
        Returns:
            各動画のタグリスト
        """
        if ai_provider not in self.processors:
            raise ValueError(f"サポートされていないAIプロバイダー: {ai_provider}")
        
        processor = self.processors[ai_provider]
        total_videos = len(video_data)
        all_tags = []
        
        self.logger.info(f"バッチ処理開始: {total_videos}動画, プロバイダー: {ai_provider}")
        
        # バッチサイズでデータを分割
        for batch_start in range(0, total_videos, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_videos)
            batch_data = video_data.iloc[batch_start:batch_end]
            
            batch_tags = self._process_single_batch(
                batch_data, 
                processor, 
                column_mapping,
                batch_start
            )
            
            all_tags.extend(batch_tags)
            
            # 進捗を報告
            if progress_callback:
                progress = (batch_end / total_videos) * 100
                progress_callback(progress, batch_end, total_videos)
            
            # メモリクリーンアップ
            if batch_end < total_videos:
                time.sleep(1)  # API制限対応
                
        self.logger.info(f"バッチ処理完了: {len(all_tags)}動画分のタグを生成")
        return all_tags
    
    def _process_single_batch(
        self,
        batch_data: pd.DataFrame,
        processor,
        column_mapping: Dict[str, str],
        batch_start: int
    ) -> List[List[str]]:
        """
        単一バッチの処理
        
        Args:
            batch_data: バッチデータ
            processor: AI processor
            column_mapping: 列マッピング
            batch_start: バッチ開始インデックス
            
        Returns:
            バッチ内各動画のタグリスト
        """
        batch_tags = []
        
        for idx, row in batch_data.iterrows():
            try:
                # 動画データを構築
                video_info = {
                    'title': str(row.get(column_mapping.get('title', ''), '')),
                    'skill': str(row.get(column_mapping.get('skill', ''), '')),
                    'description': str(row.get(column_mapping.get('description', ''), '')),
                    'summary': str(row.get(column_mapping.get('summary', ''), '')),
                    'transcript': str(row.get(column_mapping.get('transcript', ''), ''))
                }
                
                # タグを生成
                tags = processor.generate_tags(video_info)
                batch_tags.append(tags)
                
                self.logger.debug(f"動画 {batch_start + len(batch_tags)}: {len(tags)}個のタグを生成")
                
            except Exception as e:
                self.logger.error(f"動画 {batch_start + len(batch_tags)} 処理エラー: {str(e)}")
                batch_tags.append([])  # 空のタグリストを追加
                
        return batch_tags
    
    def estimate_processing_time(
        self, 
        total_videos: int, 
        ai_provider: str
    ) -> Dict[str, float]:
        """
        処理時間を推定
        
        Args:
            total_videos: 総動画数
            ai_provider: AIプロバイダー
            
        Returns:
            推定時間情報
        """
        # AIプロバイダー別の処理時間（秒/動画）
        time_per_video = {
            'openai': 3.0,
            'claude': 4.0,
            'gemini': 2.5
        }
        
        base_time = time_per_video.get(ai_provider, 3.0)
        
        # レート制限を考慮
        rate_limit = self.config.get('ai_models', {}).get(ai_provider, {}).get('rate_limit_per_minute', 60)
        min_time_per_video = 60.0 / rate_limit
        
        actual_time_per_video = max(base_time, min_time_per_video)
        
        total_time_seconds = total_videos * actual_time_per_video
        total_batches = (total_videos + self.batch_size - 1) // self.batch_size
        
        return {
            'total_seconds': total_time_seconds,
            'total_minutes': total_time_seconds / 60,
            'total_hours': total_time_seconds / 3600,
            'total_batches': total_batches,
            'time_per_video': actual_time_per_video,
            'time_per_batch': actual_time_per_video * self.batch_size
        }
    
    def get_memory_usage_estimate(self, total_videos: int) -> Dict[str, float]:
        """
        メモリ使用量を推定
        
        Args:
            total_videos: 総動画数
            
        Returns:
            メモリ使用量推定
        """
        # 1動画あたりの推定メモリ使用量（MB）
        memory_per_video = 0.5  # テキストデータのため比較的小さい
        
        batch_memory = self.batch_size * memory_per_video
        total_memory = total_videos * memory_per_video
        
        return {
            'total_mb': total_memory,
            'batch_mb': batch_memory,
            'max_memory_mb': self.max_memory_mb,
            'memory_safe': batch_memory < self.max_memory_mb
        }
    
    def format_tags_for_sheets(self, tags_lists: List[List[str]]) -> List[List[str]]:
        """
        タグリストをSheets書き込み用にフォーマット
        
        Args:
            tags_lists: タグリストのリスト
            
        Returns:
            Sheets用フォーマット済みデータ
        """
        formatted_data = []
        
        for tags in tags_lists:
            if tags:
                # タグをカンマ区切りの文字列に変換
                tags_string = ', '.join(tags)
            else:
                tags_string = ''
            
            formatted_data.append([tags_string])
            
        return formatted_data