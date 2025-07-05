"""
Claude API処理モジュール
"""

import os
from typing import List, Dict, Any
import anthropic
from dotenv import load_dotenv
from .base_processor import BaseAIProcessor

# .envファイルを読み込み
load_dotenv()


class ClaudeProcessor(BaseAIProcessor):
    """Claude処理クラス"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初期化
        
        Args:
            config: Claude設定
        """
        api_key = os.getenv('CLAUDE_API_KEY')
        super().__init__(api_key, config)
        
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY が設定されていません")
        
        # Claudeクライアントを初期化
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # デフォルト設定
        self.model = self.config.get('model', 'claude-3-haiku-20240307')
        self.max_tokens = self.config.get('max_tokens', 1500)
    
    def generate_tags(self, video_data: Dict[str, str]) -> List[str]:
        """
        Claude APIを使用してタグを生成
        
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
            
            # Claudeにリクエスト
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system="あなたはマーケティング教育動画の内容を分析して、検索に最適なタグを生成する専門家です。",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # レスポンスからタグを抽出
            tags_text = response.content[0].text.strip()
            tags = self.clean_tags(tags_text)
            
            self.logger.info(f"Claude: 動画「{video_data.get('title', 'Unknown')}」に対して{len(tags)}個のタグを生成")
            
            return tags
            
        except anthropic.APIError as e:
            self.logger.error(f"Claude APIエラー: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Claude処理エラー: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """
        API接続テスト
        
        Returns:
            接続成功可否
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[
                    {
                        "role": "user",
                        "content": "こんにちは"
                    }
                ]
            )
            return True
        except Exception as e:
            self.logger.error(f"Claude接続テストエラー: {str(e)}")
            return False