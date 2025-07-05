#!/usr/bin/env python3
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl

class AIAPIHandler:
    def __init__(self):
        # Load API keys from .env file
        self.load_env()
        
        # API endpoints
        self.endpoints = {
            'openai': 'https://api.openai.com/v1/chat/completions',
            'claude': 'https://api.anthropic.com/v1/messages',
            'gemini': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'
        }
    
    def load_env(self):
        """Load environment variables from .env file"""
        self.api_keys = {}
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if key in ['OPENAI_API_KEY', 'CLAUDE_API_KEY', 'GEMINI_API_KEY']:
                            self.api_keys[key] = value.strip()
        except FileNotFoundError:
            print("Warning: .env file not found")
    
    def generate_tags_prompt(self, video_data):
        """Generate prompt for tag generation"""
        return f"""
以下のマーケティング教育動画の情報から、検索性の高いタグを15〜20個生成してください。
タグは日本語で、具体的かつ実用的なものにしてください。

タイトル: {video_data.get('title', '')}
スキル名: {video_data.get('skill', '')}
説明文: {video_data.get('description', '')}
要約: {video_data.get('summary', '')}
文字起こし（抜粋）: {video_data.get('transcript', '')[:500]}

タグ生成の基準:
1. 動画の主要なトピックとスキル
2. 対象となる職種や業界
3. 解決する課題や目的
4. 使用されるツールや手法
5. レベル（初級、中級、上級）

タグのみをカンマ区切りで出力してください。
"""
    
    def call_openai(self, prompt):
        """Call OpenAI API"""
        if 'OPENAI_API_KEY' not in self.api_keys:
            return None
        
        headers = {
            'Authorization': f"Bearer {self.api_keys['OPENAI_API_KEY']}",
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'あなたは教育コンテンツのタグ付け専門家です。'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 200
        }
        
        try:
            req = urllib.request.Request(
                self.endpoints['openai'],
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                content = result['choices'][0]['message']['content']
                return [tag.strip() for tag in content.split(',')]
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
    
    def call_claude(self, prompt):
        """Call Claude API"""
        if 'CLAUDE_API_KEY' not in self.api_keys:
            return None
        
        headers = {
            'x-api-key': self.api_keys['CLAUDE_API_KEY'],
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 200,
            'messages': [{
                'role': 'user',
                'content': prompt
            }]
        }
        
        try:
            req = urllib.request.Request(
                self.endpoints['claude'],
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                content = result['content'][0]['text']
                return [tag.strip() for tag in content.split(',')]
        except Exception as e:
            print(f"Claude API error: {e}")
            return None
    
    def call_gemini(self, prompt):
        """Call Gemini API"""
        if 'GEMINI_API_KEY' not in self.api_keys:
            return None
        
        url = f"{self.endpoints['gemini']}?key={self.api_keys['GEMINI_API_KEY']}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            'contents': [{
                'parts': [{
                    'text': prompt
                }]
            }],
            'generationConfig': {
                'temperature': 0.7,
                'maxOutputTokens': 200
            }
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                content = result['candidates'][0]['content']['parts'][0]['text']
                return [tag.strip() for tag in content.split(',')]
        except Exception as e:
            print(f"Gemini API error: {e}")
            return None
    
    def generate_tags(self, video_data, ai_engine='openai'):
        """Generate tags using specified AI engine"""
        prompt = self.generate_tags_prompt(video_data)
        
        if ai_engine == 'openai':
            tags = self.call_openai(prompt)
        elif ai_engine == 'claude':
            tags = self.call_claude(prompt)
        elif ai_engine == 'gemini':
            tags = self.call_gemini(prompt)
        else:
            tags = None
        
        # Fallback to simple generation if API fails
        if not tags:
            tags = self.generate_fallback_tags(video_data)
        
        return tags[:20]  # Limit to 20 tags
    
    def generate_fallback_tags(self, video_data):
        """Generate fallback tags without AI"""
        tags = []
        title = video_data.get('title', '').lower()
        skill = video_data.get('skill', '').lower()
        
        # Basic keyword extraction
        keywords = {
            'マーケティング': ['マーケティング', 'デジタルマーケティング', 'マーケティング戦略'],
            'プレゼン': ['プレゼンテーション', 'プレゼンスキル', '発表技法'],
            'リーダー': ['リーダーシップ', 'マネジメント', 'チームリーダー'],
            'コミュニケーション': ['コミュニケーション', '対人スキル', 'ビジネスコミュニケーション'],
            'データ': ['データ分析', 'データ活用', 'ビジネス分析'],
            'デジタル': ['デジタル化', 'DX', 'デジタルトランスフォーメーション']
        }
        
        for key, values in keywords.items():
            if key in title or key in skill:
                tags.extend(values)
        
        # Add skill-based tags
        if skill:
            tags.append(skill)
            tags.append(f"{skill}スキル")
        
        # Add common business tags
        tags.extend(['ビジネススキル', '社会人教育', '研修動画'])
        
        return list(set(tags))  # Remove duplicates

# Integration with API server
def integrate_with_api_server():
    """Return the AI handler for use in api_server.py"""
    return AIAPIHandler()

if __name__ == '__main__':
    # Test the AI handler
    handler = AIAPIHandler()
    
    test_video = {
        'title': '効果的なプレゼンテーション技法',
        'skill': 'コミュニケーション',
        'description': '聴衆を惹きつけるプレゼンテーション技法を学ぶ',
        'summary': 'プレゼンテーションの基本構成と効果的な伝達方法',
        'transcript': 'プレゼンテーションにおいて最も重要なのは...'
    }
    
    print("Testing AI API Handler...")
    print("Loaded API keys:", list(handler.api_keys.keys()))
    
    # Test with fallback (no actual API call in test mode)
    tags = handler.generate_fallback_tags(test_video)
    print(f"Generated tags: {tags}")