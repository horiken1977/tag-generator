"""
AI処理の基底クラス
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import time
import logging

class BaseAIProcessor(ABC):
    """AI処理の基底クラス"""
    
    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        """
        初期化
        
        Args:
            api_key: APIキー
            config: AI設定
        """
        self.api_key = api_key
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.last_request_time = 0
        self.rate_limit_per_minute = self.config.get('rate_limit_per_minute', 60)
        
    def _enforce_rate_limit(self):
        """レート制限を適用"""
        min_interval = 60.0 / self.rate_limit_per_minute
        elapsed = time.time() - self.last_request_time
        
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    @abstractmethod
    def generate_tags(self, video_data: Dict[str, str]) -> List[str]:
        """
        動画データからタグを生成
        
        Args:
            video_data: 動画データ辞書
                - title: タイトル
                - skill: スキル名
                - description: 説明文
                - summary: 要約
                - transcript: 文字起こし
                
        Returns:
            生成されたタグのリスト
        """
        pass
    
    def create_prompt(self, video_data: Dict[str, str]) -> str:
        """
        プロンプトを作成
        
        Args:
            video_data: 動画データ
            
        Returns:
            プロンプト文字列
        """
        prompt = f"""
以下のマーケティング教育動画の情報から、検索性が高く具体的なタグを10-15個生成してください。

【動画情報】
タイトル: {video_data.get('title', '')}
スキル名: {video_data.get('skill', '')}
説明文: {video_data.get('description', '')}
要約: {video_data.get('summary', '')}

【文字起こし（抜粋）】
{self._truncate_transcript(video_data.get('transcript', ''))}

【タグ生成ルール】
1. マーケティング、ビジネス、スキルに関連するキーワードを中心に
2. 検索しやすい具体的な用語を使用
3. 動画の内容を正確に表現
4. 一般的すぎる単語（例：「マーケティング」単体）は避ける
5. 複数の類似タグは統合する

【出力形式】
カンマ区切りでタグのみを出力してください。
例: SNSマーケティング, コンテンツ戦略, ブランディング手法, 顧客獲得
"""
        return prompt
    
    def _truncate_transcript(self, transcript: str, max_chars: int = 1000) -> str:
        """
        文字起こしを適切な長さに切り詰め
        
        Args:
            transcript: 文字起こし
            max_chars: 最大文字数
            
        Returns:
            切り詰められた文字起こし
        """
        if not transcript or len(transcript) <= max_chars:
            return transcript
        
        # 文章の区切りで切り詰める
        truncated = transcript[:max_chars]
        last_period = truncated.rfind('。')
        last_sentence_end = truncated.rfind('\n')
        
        cut_point = max(last_period, last_sentence_end)
        if cut_point > max_chars * 0.8:  # 80%以上の位置なら
            return truncated[:cut_point + 1] + "..."
        else:
            return truncated + "..."
    
    def clean_tags(self, tags_text: str) -> List[str]:
        """
        生成されたタグテキストをクリーニング
        
        Args:
            tags_text: AIが生成したタグテキスト
            
        Returns:
            クリーニングされたタグリスト
        """
        # カンマで分割
        tags = [tag.strip() for tag in tags_text.split(',')]
        
        # 空文字や不適切なタグを除去
        cleaned_tags = []
        for tag in tags:
            tag = tag.strip()
            if tag and len(tag) > 1 and not tag.startswith('#'):
                # 特殊文字を除去
                tag = ''.join(char for char in tag if char.isalnum() or char in 'ー・ ')
                if tag:
                    cleaned_tags.append(tag)
        
        return cleaned_tags[:15]  # 最大15個まで