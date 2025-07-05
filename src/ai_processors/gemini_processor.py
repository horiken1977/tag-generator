"""
Google Gemini処理モジュール
"""

import os
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
from .base_processor import BaseAIProcessor

# .envファイルを読み込み
load_dotenv()


class GeminiProcessor(BaseAIProcessor):
    """Google Gemini処理クラス"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初期化
        
        Args:
            config: Gemini設定
        """
        api_key = os.getenv('GEMINI_API_KEY')
        super().__init__(api_key, config)
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY が設定されていません")
        
        # Gemini APIを設定
        genai.configure(api_key=self.api_key)
        
        # デフォルト設定
        self.model_name = self.config.get('model', 'gemini-pro')
        self.temperature = self.config.get('temperature', 0.3)
        self.max_tokens = self.config.get('max_tokens', 1500)
        
        # モデルを初期化
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_tags(self, video_data: Dict[str, str]) -> List[str]:
        """
        Google Geminiを使用してタグを生成
        
        Args:
            video_data: 動画データ辞書
            
        Returns:
            生成されたタグのリスト
        """
        try:
            # レート制限を適用
            self._enforce_rate_limit()
            
            # プロンプトを作成
            system_prompt = "あなたはマーケティング教育動画の内容を分析して、検索に最適なタグを生成する専門家です。"
            user_prompt = self.create_prompt(video_data)
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Geminiにリクエスト
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    top_p=1,
                    top_k=40
                )
            )
            
            # レスポンスからタグを抽出
            tags_text = response.text.strip()
            tags = self.clean_tags(tags_text)
            
            self.logger.info(f"Gemini: 動画「{video_data.get('title', 'Unknown')}」に対して{len(tags)}個のタグを生成")
            
            return tags
            
        except Exception as e:
            self.logger.error(f"Gemini処理エラー: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """
        API接続テスト
        
        Returns:
            接続成功可否
        """
        try:
            response = self.model.generate_content("こんにちは")
            return True
        except Exception as e:
            self.logger.error(f"Gemini接続テストエラー: {str(e)}")
            return False