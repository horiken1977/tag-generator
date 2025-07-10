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
        """Load environment variables from .env file or OS environment"""
        self.api_keys = {}
        
        # Try to load from .env file first
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")  # Remove quotes
                        if key in ['OPENAI_API_KEY', 'CLAUDE_API_KEY', 'GEMINI_API_KEY']:
                            self.api_keys[key] = value
            print(f"Loaded {len(self.api_keys)} API keys from .env file")
        except FileNotFoundError:
            print("Warning: .env file not found, checking OS environment variables")
        
        # Fallback to OS environment variables
        import os
        for key in ['OPENAI_API_KEY', 'CLAUDE_API_KEY', 'GEMINI_API_KEY']:
            if key not in self.api_keys:
                env_value = os.getenv(key)
                if env_value:
                    self.api_keys[key] = env_value
                    print(f"Loaded {key} from OS environment")
        
        # Debug info (without exposing actual keys)
        available_keys = [key for key, value in self.api_keys.items() if value]
        print(f"Available API keys: {available_keys}")
        
        if not available_keys:
            print("Warning: No API keys found. Will use fallback mode.")
    
    def generate_tags_prompt(self, video_data):
        """Generate prompt for tag generation"""
        # Expand transcript limit for better context
        transcript = video_data.get('transcript', '')
        transcript_excerpt = transcript[:1500] if transcript else ''  # Increased from 500 to 1500
        
        return f"""
以下のマーケティング教育動画の情報から、検索性の高いタグを15〜20個生成してください。
タグは日本語で、具体的かつ実用的なものにしてください。

タイトル: {video_data.get('title', '')}
スキル名: {video_data.get('skill', '')}
説明文: {video_data.get('description', '')}
要約: {video_data.get('summary', '')}
文字起こし（重要）: {transcript_excerpt}

タグ生成の基準:
1. 動画の主要なトピックとスキル
2. 対象となる職種や業界
3. 解決する課題や目的
4. 使用されるツールや手法
5. レベル（初級、中級、上級）
6. 文字起こし内容から読み取れる具体的な手法やポイント
7. 実際に話されている事例やケーススタディ

重要: 文字起こし内容を十分に分析し、動画固有の内容を反映したタグを生成してください。
同じタイトルでも文字起こし内容が異なれば、異なるタグを生成する必要があります。

タグのみをカンマ区切りで出力してください。
"""
    
    def call_openai(self, prompt):
        """Call OpenAI API"""
        if 'OPENAI_API_KEY' not in self.api_keys or not self.api_keys['OPENAI_API_KEY']:
            print("OpenAI API key not available")
            return None
        
        headers = {
            'Authorization': f"Bearer {self.api_keys['OPENAI_API_KEY']}",
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'あなたは教育コンテンツのタグ付け専門家です。動画の内容を分析して、検索性が高く実用的な日本語タグを生成してください。'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 300  # Increased for more comprehensive tags
        }
        
        try:
            print(f"Calling OpenAI API for tag generation...")
            req = urllib.request.Request(
                self.endpoints['openai'],
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=45) as response:  # Increased timeout
                if response.getcode() == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    content = result['choices'][0]['message']['content'].strip()
                    
                    # Parse tags from response
                    tags = [tag.strip() for tag in content.split(',') if tag.strip()]
                    
                    # Clean up tags (remove quotes, extra spaces, etc.)
                    cleaned_tags = []
                    for tag in tags:
                        clean_tag = tag.strip().strip('"').strip("'").strip()
                        if clean_tag and len(clean_tag) > 0:
                            cleaned_tags.append(clean_tag)
                    
                    print(f"OpenAI generated {len(cleaned_tags)} tags")
                    return cleaned_tags[:20]  # Limit to 20 tags
                else:
                    print(f"OpenAI API returned status: {response.getcode()}")
                    return None
                    
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"OpenAI API HTTP error {e.code}: {error_body}")
            return None
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            return None
    
    def call_claude(self, prompt):
        """Call Claude API"""
        if 'CLAUDE_API_KEY' not in self.api_keys or not self.api_keys['CLAUDE_API_KEY']:
            print("Claude API key not available")
            return None
        
        headers = {
            'x-api-key': self.api_keys['CLAUDE_API_KEY'],
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 300,  # Increased for more comprehensive tags
            'messages': [{
                'role': 'user',
                'content': prompt
            }]
        }
        
        try:
            print(f"Calling Claude API for tag generation...")
            req = urllib.request.Request(
                self.endpoints['claude'],
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=45) as response:  # Increased timeout
                if response.getcode() == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    content = result['content'][0]['text'].strip()
                    
                    # Parse tags from response
                    tags = [tag.strip() for tag in content.split(',') if tag.strip()]
                    
                    # Clean up tags (remove quotes, extra spaces, etc.)
                    cleaned_tags = []
                    for tag in tags:
                        clean_tag = tag.strip().strip('"').strip("'").strip()
                        if clean_tag and len(clean_tag) > 0:
                            cleaned_tags.append(clean_tag)
                    
                    print(f"Claude generated {len(cleaned_tags)} tags")
                    return cleaned_tags[:20]  # Limit to 20 tags
                else:
                    print(f"Claude API returned status: {response.getcode()}")
                    return None
                    
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Claude API HTTP error {e.code}: {error_body}")
            return None
        except Exception as e:
            print(f"Claude API error: {str(e)}")
            return None
    
    def call_gemini(self, prompt):
        """Call Gemini API"""
        if 'GEMINI_API_KEY' not in self.api_keys or not self.api_keys['GEMINI_API_KEY']:
            print("Gemini API key not available")
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
                'maxOutputTokens': 300  # Increased for more comprehensive tags
            }
        }
        
        try:
            print(f"Calling Gemini API for tag generation...")
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=45) as response:  # Increased timeout
                if response.getcode() == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    
                    # Handle Gemini response structure
                    if 'candidates' in result and len(result['candidates']) > 0:
                        candidate = result['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            content = candidate['content']['parts'][0]['text'].strip()
                            
                            # Parse tags from response
                            tags = [tag.strip() for tag in content.split(',') if tag.strip()]
                            
                            # Clean up tags (remove quotes, extra spaces, etc.)
                            cleaned_tags = []
                            for tag in tags:
                                clean_tag = tag.strip().strip('"').strip("'").strip()
                                if clean_tag and len(clean_tag) > 0:
                                    cleaned_tags.append(clean_tag)
                            
                            print(f"Gemini generated {len(cleaned_tags)} tags")
                            return cleaned_tags[:20]  # Limit to 20 tags
                    
                    print("Gemini API returned unexpected response structure")
                    return None
                else:
                    print(f"Gemini API returned status: {response.getcode()}")
                    return None
                    
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Gemini API HTTP error {e.code}: {error_body}")
            return None
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
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
        transcript = video_data.get('transcript', '').lower()
        description = video_data.get('description', '').lower()
        summary = video_data.get('summary', '').lower()
        
        # Combine all content for comprehensive analysis
        all_content = f"{title} {skill} {description} {summary} {transcript}".lower()
        
        # Enhanced keyword extraction with transcript analysis
        keywords = {
            'マーケティング': ['マーケティング', 'デジタルマーケティング', 'マーケティング戦略'],
            'プレゼン': ['プレゼンテーション', 'プレゼンスキル', '発表技法'],
            'リーダー': ['リーダーシップ', 'マネジメント', 'チームリーダー'],
            'コミュニケーション': ['コミュニケーション', '対人スキル', 'ビジネスコミュニケーション'],
            'データ': ['データ分析', 'データ活用', 'ビジネス分析'],
            'デジタル': ['デジタル化', 'DX', 'デジタルトランスフォーメーション'],
            'セールス': ['営業', 'セールス', '販売', '営業戦略'],
            '戦略': ['戦略立案', '企画', 'プランニング', '戦略思考'],
            '効率': ['効率化', '生産性向上', '時間管理', 'パフォーマンス'],
            '問題': ['問題解決', '課題解決', 'トラブルシューティング'],
            '顧客': ['顧客満足', 'CS', '顧客体験', 'CX', '顧客対応'],
            '品質': ['品質管理', 'QC', '改善', 'カイゼン']
        }
        
        # Apply keyword matching to all content
        for key, values in keywords.items():
            if key in all_content:
                tags.extend(values)
        
        # Transcript-specific analysis for detailed content
        if transcript:
            # Extract specific business concepts from transcript
            transcript_keywords = {
                '売上': ['売上向上', '収益改善', '業績向上'],
                '収益': ['収益改善', '利益向上', '売上向上'],
                '改善': ['業務改善', 'プロセス改善', '継続改善'],
                '分析': ['分析手法', 'データドリブン', '定量分析', '分析力'],
                '企画': ['企画立案', '企画力', 'プロジェクト企画'],
                'コスト': ['コスト削減', 'コスト管理', '効率化'],
                '組織': ['組織運営', '組織開発', 'チームビルディング'],
                '目標': ['目標設定', '目標管理', 'KPI管理'],
                '交渉': ['交渉術', '交渉力', 'ネゴシエーション'],
                '提案': ['提案力', 'プレゼンテーション', '企画提案'],
                '研修': ['人材育成', '教育', 'スキルアップ'],
                'イノベーション': ['創造性', 'イノベーション', '新規事業'],
                'プロジェクト': ['プロジェクト管理', 'PM', 'プロジェクトマネジメント']
            }
            
            for keyword, related_tags in transcript_keywords.items():
                if keyword in transcript:
                    tags.extend(related_tags)
        
        # Add skill-based tags with enhanced mapping
        skill_mappings = {
            'コミュニケーション': ['コミュニケーション', '対人スキル', '説得力', '傾聴'],
            'マネジメント': ['マネジメント', 'プロジェクト管理', '目標設定', '人材育成'],
            'リーダーシップ': ['リーダーシップ', 'チームビルディング', '組織運営'],
            'マーケティング': ['マーケティング戦略', 'マーケット分析', 'ブランド戦略'],
            'セールス': ['営業スキル', 'セールステクニック', '商談力']
        }
        
        for skill_key, skill_tags in skill_mappings.items():
            if skill_key in skill:
                tags.extend(skill_tags)
        
        # Add skill as-is if provided
        if skill:
            tags.append(skill)
            tags.append(f"{skill}スキル")
        
        # Add common business tags
        tags.extend(['ビジネススキル', '社会人教育', '研修動画'])
        
        # Generate content-based unique identifier to ensure different content gets different tags
        import hashlib
        content_hash = hashlib.md5(all_content.encode()).hexdigest()[:6]
        tags.append(f"Content-{content_hash}")
        
        return list(set(tags))[:20]  # Remove duplicates and expand limit

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