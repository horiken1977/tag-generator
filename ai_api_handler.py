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

【絶対に守るべき厳格なルール】:
1. 文字起こし内容を最優先で分析し、そこから具体的なキーワードを抽出すること
2. 同じタイトルでも文字起こし内容が異なれば、必ず異なるタグセットを生成すること
3. 以下のような汎用的すぎるタグは絶対に生成禁止：
   - 「6つの要素」「8つの分類」「4つのポイント」「3つの手法」等の数字+汎用名詞
   - 「要素」「分類」「ポイント」「手法」「方法」「技術」等の単体使用
   - 「基本」「応用」「実践」「理論」「概要」「入門」等の抽象的レベル表現
4. 必須要件：文字起こしから具体的な以下を抽出してタグ化：
   - 実際に言及された企業名・サービス名・ツール名
   - 具体的な数値や指標名（ROI、CPA、CTR等）
   - 専門的な手法や理論の正式名称
   - 実際に説明された実務プロセスや業務フロー
5. 文字起こし内容の独自性を必ず反映：同一タイトルでも内容が違えば全く違うタグにする

出力：具体的で検索価値の高いタグのみをカンマ区切りで出力。汎用的な単語は一切含めない。
"""
    
    def filter_generic_tags(self, tags):
        """Filter out generic and meaningless tags"""
        if not tags:
            return tags
        
        # Patterns to filter out
        generic_patterns = [
            # Number + の + generic noun patterns
            r'\d+つの要素', r'\d+つの分類', r'\d+つのポイント', r'\d+つの手法',
            r'\d+つのステップ', r'\d+つの方法', r'\d+つの技術', r'\d+つの項目',
            r'\d+つの観点', r'\d+つの視点', r'\d+つの基準', r'\d+つの原則',
            r'\d+個の要素', r'\d+個の分類', r'\d+個のポイント', r'\d+個の手法',
            # Generic standalone words - Basic
            r'^要素$', r'^分類$', r'^ポイント$', r'^手法$', r'^方法$', r'^技術$',
            r'^基本$', r'^応用$', r'^実践$', r'^理論$', r'^概要$', r'^入門$',
            r'^初級$', r'^中級$', r'^上級$', r'^基礎$', r'^発展$', r'^活用$',
            # Generic business terms - Additional patterns from user feedback
            r'^実務スキル$', r'^思考法$', r'^業界知識$', r'^ツール活用$', 
            r'^人材育成$', r'^スキル開発$', r'^成果向上$', r'^効率化$',
            r'^戦術$', r'^手順$', r'^方法論$', r'^支援会社視点$',
            r'^ビジネススキル$', r'^職場効率$', r'^社会人教育$', r'^研修動画$',
            # Generic process terms
            r'^改善$', r'^最適化$', r'^強化$', r'^向上$', r'^推進$', r'^展開$',
            r'^構築$', r'^確立$', r'^設計$', r'^運用$', r'^管理$', r'^分析$'
        ]
        
        import re
        filtered_tags = []
        
        for tag in tags:
            tag = tag.strip()
            if not tag:
                continue
                
            # Check against generic patterns
            is_generic = False
            for pattern in generic_patterns:
                if re.match(pattern, tag):
                    print(f"  Filtered generic tag: {tag}")
                    is_generic = True
                    break
            
            # Additional filters
            if not is_generic:
                # Filter overly short tags (single characters or very short)
                if len(tag) < 2:
                    print(f"  Filtered short tag: {tag}")
                    is_generic = True
                # Filter tags with only numbers
                elif tag.isdigit():
                    print(f"  Filtered numeric tag: {tag}")
                    is_generic = True
                # Filter tags that are just punctuation
                elif not any(c.isalnum() for c in tag):
                    print(f"  Filtered punctuation tag: {tag}")
                    is_generic = True
            
            if not is_generic:
                filtered_tags.append(tag)
        
        print(f"  Tag filtering: {len(tags)} -> {len(filtered_tags)} tags")
        return filtered_tags

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
                {'role': 'system', 'content': 'あなたは教育コンテンツのタグ付け専門家です。文字起こし内容を詳細に分析し、その動画固有の具体的なキーワードのみをタグとして抽出してください。汎用的な表現（「要素」「手法」「ポイント」「基本」「応用」等）や数字を含む汎用表現（「6つの要素」等）は絶対に生成しないでください。文字起こしから実際に言及された企業名、ツール名、専門用語、具体的な指標名のみを抽出してください。'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.5,  # Reduced for more consistent results
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
                    
                    # Apply generic tag filtering
                    filtered_tags = self.filter_generic_tags(cleaned_tags)
                    
                    print(f"OpenAI generated {len(filtered_tags)} filtered tags")
                    return filtered_tags[:20]  # Limit to 20 tags
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
                    
                    # Apply generic tag filtering
                    filtered_tags = self.filter_generic_tags(cleaned_tags)
                    
                    print(f"Claude generated {len(filtered_tags)} filtered tags")
                    return filtered_tags[:20]  # Limit to 20 tags
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
                            
                            # Apply generic tag filtering
                            filtered_tags = self.filter_generic_tags(cleaned_tags)
                            
                            print(f"Gemini generated {len(filtered_tags)} filtered tags")
                            return filtered_tags[:20]  # Limit to 20 tags
                    
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
        
        # Extract specific keywords from transcript content (avoiding generic terms)
        specific_keywords = {}
        
        # Only include if transcript contains specific, concrete terms
        if 'Instagram' in all_content or 'TikTok' in all_content or 'YouTube' in all_content:
            specific_keywords['SNS'] = ['Instagram', 'TikTok', 'YouTube', 'SNSマーケティング']
        if 'Google Analytics' in all_content or 'Salesforce' in all_content:
            specific_keywords['ツール'] = ['Google Analytics', 'Salesforce', 'マーケティングツール']
        if 'ROI' in all_content or 'CPA' in all_content or 'CTR' in all_content:
            specific_keywords['指標'] = ['ROI', 'CPA', 'CTR', 'マーケティング指標']
        if 'PDCA' in all_content:
            specific_keywords['フレームワーク'] = ['PDCAサイクル', 'PDCA']
        if '財務諸表' in all_content or '損益計算書' in all_content:
            specific_keywords['財務'] = ['財務諸表', '損益計算書', '貸借対照表']
        
        # Apply specific keyword matching to content
        for key, values in specific_keywords.items():
            tags.extend(values)
        
        # Extract only very specific terms from transcript
        if transcript:
            # Only extract concrete, specific terms that are mentioned
            specific_terms = []
            
            # Extract specific tool/platform names mentioned
            tools = ['Google Analytics', 'Salesforce', 'Facebook', 'Instagram', 'TikTok', 'YouTube', 'Twitter', 'LinkedIn']
            for tool in tools:
                if tool.lower() in transcript:
                    specific_terms.append(tool)
            
            # Extract specific metrics mentioned  
            metrics = ['ROI', 'CPA', 'CPM', 'CTR', 'LTV', 'CAC', 'ROAS']
            for metric in metrics:
                if metric in transcript:
                    specific_terms.append(metric)
            
            # Extract specific methodologies mentioned
            methods = ['A/Bテスト', 'PDCAサイクル', 'KPI', 'OKR', 'アジャイル', 'リーンスタートアップ']
            for method in methods:
                if method in transcript:
                    specific_terms.append(method)
            
            tags.extend(specific_terms)
        
        # Add only the skill category itself (avoid generic compound terms)
        if skill and len(skill) > 1:
            tags.append(skill)
        
        # Add minimal specific tags only if no other tags found
        if len(tags) < 3:
            tags.extend(['マーケティング教育', 'ビジネス研修'])
        
        # Generate content-based unique identifier to ensure different content gets different tags
        import hashlib
        content_hash = hashlib.md5(all_content.encode()).hexdigest()[:6]
        tags.append(f"Content-{content_hash}")
        
        # Apply the same filtering as AI-generated tags
        unique_tags = list(set(tags))
        filtered_tags = self.filter_generic_tags(unique_tags)
        
        return filtered_tags[:20]  # Remove duplicates and expand limit

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