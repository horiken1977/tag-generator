"""
OpenAI GPT処理モジュール
"""

import os
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv
from .base_processor import BaseAIProcessor

# .envファイルを読み込み
load_dotenv()


class OpenAIProcessor(BaseAIProcessor):
    """OpenAI GPT処理クラス"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初期化
        
        Args:
            config: OpenAI設定
        """
        api_key = os.getenv('OPENAI_API_KEY')
        super().__init__(api_key, config)
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY が設定されていません")
        
        # OpenAIクライアントを初期化
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # デフォルト設定
        self.model = self.config.get('model', 'gpt-3.5-turbo')
        self.temperature = self.config.get('temperature', 0.3)
        self.max_tokens = self.config.get('max_tokens', 1500)
    
    def generate_tags(self, video_data: Dict[str, str]) -> List[str]:
        """
        OpenAI GPTを使用してタグを生成
        
        Args:
            video_data: 動画データ辞書
            
        Returns:
            生成されたタグのリスト
        """
        try:
            # レート制限を適用
            self._enforce_rate_limit()
            
            # プロンプトを作成
            prompt = self.create_prompt(video_data)
            
            # GPTにリクエスト
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "あなたはマーケティング教育動画の内容を分析して、検索に最適なタグを生成する専門家です。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # レスポンスからタグを抽出
            tags_text = response.choices[0].message.content.strip()
            tags = self.clean_tags(tags_text)
            
            self.logger.info(f"OpenAI: 動画「{video_data.get('title', 'Unknown')}」に対して{len(tags)}個のタグを生成")
            
            return tags
            
        except openai.APIError as e:
            self.logger.error(f"OpenAI APIエラー: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"OpenAI処理エラー: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """
        API接続テスト
        
        Returns:
            接続成功可否
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "こんにちは"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            self.logger.error(f"OpenAI接続テストエラー: {str(e)}")
            return False