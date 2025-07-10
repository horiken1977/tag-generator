#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import re
import os
import sys
from datetime import datetime

# Import AI handler
try:
    from ai_api_handler import AIAPIHandler
    ai_handler = AIAPIHandler()
    AI_ENABLED = True
except ImportError:
    AI_ENABLED = False
    print("Warning: AI API handler not available, using fallback mode")

class TagGeneratorAPIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_webapp()
        elif self.path.startswith('/api/'):
            self.handle_api_get()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_error(405)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def serve_webapp(self):
        try:
            # Try API version first
            filename = 'webapp_api.html' if os.path.exists('webapp_api.html') else 'webapp.html'
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404)
    
    def handle_api_get(self):
        if self.path == '/api/status':
            # Check actual API key availability
            available_engines = []
            if AI_ENABLED:
                if hasattr(ai_handler, 'api_keys'):
                    if ai_handler.api_keys.get('OPENAI_API_KEY'):
                        available_engines.append('openai')
                    if ai_handler.api_keys.get('CLAUDE_API_KEY'):
                        available_engines.append('claude')
                    if ai_handler.api_keys.get('GEMINI_API_KEY'):
                        available_engines.append('gemini')
            
            production_mode = len(available_engines) > 0
            
            self.send_json_response({
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'features': ['sheets_api', 'ai_processing', 'tag_optimization'],
                'ai_enabled': AI_ENABLED,
                'production_mode': production_mode,
                'available_engines': available_engines,
                'default_engine': available_engines[0] if available_engines else 'simulation',
                'force_production': True  # Force production mode when API keys are available
            })
        else:
            self.send_error(404)
    
    def handle_api_post(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            if self.path == '/api/sheets/test':
                self.handle_sheets_test(data)
            elif self.path == '/api/sheets/data':
                self.handle_sheets_data(data)
            elif self.path == '/api/ai/process':
                self.handle_ai_process(data)
            elif self.path == '/api/tags/optimize':
                self.handle_tag_optimize(data)
            else:
                self.send_error(404)
                
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)}, 500)
    
    def handle_sheets_test(self, data):
        url = data.get('url', '')
        
        if not url or 'docs.google.com/spreadsheets' not in url:
            self.send_json_response({
                'success': False, 
                'error': 'Invalid Google Sheets URL'
            }, 400)
            return
        
        # Extract spreadsheet ID
        sheet_id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        if not sheet_id_match:
            self.send_json_response({
                'success': False, 
                'error': 'Could not extract spreadsheet ID'
            }, 400)
            return
        
        sheet_id = sheet_id_match.group(1)
        
        # Try to access public CSV export
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        
        try:
            req = urllib.request.Request(csv_url)
            req.add_header('User-Agent', 'TagGenerator/2.0')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.getcode() == 200:
                    # Read first few lines to check format
                    content = response.read().decode('utf-8')
                    lines = content.strip().split('\n')
                    
                    if len(lines) < 2:
                        self.send_json_response({
                            'success': False,
                            'error': 'Spreadsheet appears to be empty'
                        })
                        return
                    
                    # Parse headers
                    headers = [col.strip('"') for col in lines[0].split(',')]
                    
                    self.send_json_response({
                        'success': True,
                        'message': 'Connection successful',
                        'sheet_id': sheet_id,
                        'rows': len(lines) - 1,
                        'columns': headers,
                        'sample_data': lines[1] if len(lines) > 1 else None
                    })
                else:
                    self.send_json_response({
                        'success': False,
                        'error': f'HTTP {response.getcode()}: Could not access spreadsheet'
                    })
                    
        except urllib.error.HTTPError as e:
            if e.code == 403:
                self.send_json_response({
                    'success': False,
                    'error': 'Access denied. Please make the spreadsheet public or check sharing settings.'
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': f'HTTP Error {e.code}: {e.reason}'
                })
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': f'Connection failed: {str(e)}'
            })
    
    def handle_sheets_data(self, data):
        url = data.get('url', '')
        preview = data.get('preview', False)
        
        # If no URL provided, return sample data
        if not url or preview:
            self.send_json_response({
                'success': True,
                'data': [
                    {
                        'title': '効果的なプレゼンテーション技法',
                        'skill': 'コミュニケーション',
                        'description': '聴衆を惹きつけるプレゼンテーション技法を学ぶ',
                        'summary': 'プレゼンテーションの基本構成と効果的な伝達方法',
                        'transcript': 'プレゼンテーションにおいて最も重要なのは...'
                    },
                    {
                        'title': 'デジタルマーケティング基礎',
                        'skill': 'マーケティング',
                        'description': 'SEOとSNS活用による効果的なデジタルマーケティング戦略',
                        'summary': 'デジタル時代のマーケティング手法と実践方法',
                        'transcript': 'デジタルマーケティングの核心は顧客との接点を...'
                    }
                ],
                'total_rows': 400,
                'processed_rows': 2
            })
            return
        
        # TODO: Implement actual CSV reading from Google Sheets
        self.send_json_response({
            'success': True,
            'data': [],
            'total_rows': 0,
            'processed_rows': 0,
            'message': 'Real-time data reading will be implemented'
        })
    
    def handle_ai_process(self, data):
        video_data = data.get('data', [])
        ai_engine = data.get('ai_engine', 'openai')
        use_real_ai = data.get('use_real_ai', True)
        use_two_phase = data.get('use_two_phase', True)  # Enable two-phase processing by default
        
        print(f"Processing {len(video_data)} videos with AI engine: {ai_engine}")
        print(f"Two-phase processing: {'ENABLED' if use_two_phase else 'DISABLED'}")
        
        if use_two_phase and len(video_data) > 1:
            # Use two-phase processing for batch operations
            return self.handle_two_phase_processing(video_data, ai_engine, use_real_ai)
        else:
            # Use original single-phase processing for single videos or when disabled
            return self.handle_single_phase_processing(video_data, ai_engine, use_real_ai)
    
    def handle_two_phase_processing(self, video_data, ai_engine, use_real_ai):
        """Handle two-phase tag processing as requested by user"""
        from two_phase_tag_processor import TwoPhaseTagProcessor
        
        start_time = datetime.now()
        
        # Initialize two-phase processor
        processor = TwoPhaseTagProcessor(ai_handler if AI_ENABLED else None)
        
        try:
            # Execute two-phase processing
            results = processor.process_all_videos(video_data, ai_engine)
            
            total_processing_time = (datetime.now() - start_time).total_seconds()
            
            # Format results for API response
            processed_tags = []
            for result in results:
                processed_tags.append({
                    'title': result.get('title', ''),
                    'generated_tags': result.get('selected_tags', []),
                    'confidence': 0.90,  # High confidence for two-phase processing
                    'processing_time': total_processing_time / len(video_data),
                    'ai_mode': 'two_phase_analysis',
                    'tag_candidates_count': len(processor.tag_candidates),
                    'selection_method': 'content_based_selection'
                })
            
            total_tags = sum(len(item['generated_tags']) for item in processed_tags)
            
            self.send_json_response({
                'success': True,
                'results': processed_tags,
                'statistics': {
                    'total_videos': len(video_data),
                    'total_tags_generated': total_tags,
                    'avg_tags_per_video': total_tags / len(video_data) if video_data else 0,
                    'total_tag_candidates': len(processor.tag_candidates),
                    'processing_method': 'two_phase',
                    'phase1_analysis': 'completed',
                    'phase2_analysis': 'completed'
                },
                'ai_engine': ai_engine,
                'processing_time': total_processing_time,
                'ai_mode': 'two_phase_production'
            })
            
        except Exception as e:
            print(f"Two-phase processing failed: {str(e)}")
            # Fallback to single-phase processing
            return self.handle_single_phase_processing(video_data, ai_engine, use_real_ai)
    
    def handle_single_phase_processing(self, video_data, ai_engine, use_real_ai):
        """Original single-phase processing (fallback)"""
        # Process with AI
        processed_tags = []
        total_processing_time = 0
        success_count = 0
        fallback_count = 0
        
        print(f"Using single-phase processing for {len(video_data)} videos")
        print(f"AI_ENABLED: {AI_ENABLED}, use_real_ai: {use_real_ai}")
        
        for i, video in enumerate(video_data):
            start_time = datetime.now()
            tags = None
            ai_mode = 'simulation'
            
            # Force production mode if API keys are available
            force_production = AI_ENABLED and hasattr(ai_handler, 'api_keys') and any(
                ai_handler.api_keys.get(key) for key in ['OPENAI_API_KEY', 'CLAUDE_API_KEY', 'GEMINI_API_KEY']
            )
            
            if force_production or (AI_ENABLED and use_real_ai):
                # Try real AI API first
                try:
                    print(f"Processing video {i+1}/{len(video_data)}: {video.get('title', 'Unknown')[:50]}...")
                    print(f"  Using {ai_engine} API in PRODUCTION MODE")
                    tags = ai_handler.generate_tags(video, ai_engine)
                    if tags and len(tags) > 0:
                        ai_mode = 'real_ai'
                        success_count += 1
                        print(f"  ✓ AI generated {len(tags)} tags")
                    else:
                        print(f"  ⚠ AI returned no tags, falling back to simulation")
                        tags = None
                except Exception as e:
                    print(f"  ✗ AI processing error: {str(e)}")
                    tags = None
            
            # Fallback to simulation only if AI completely failed
            if not tags:
                print(f"  → Using enhanced simulation mode")
                tags = self.generate_sample_tags(video, ai_engine)
                ai_mode = 'simulation'
                fallback_count += 1
            
            # Ensure we have tags
            if not tags:
                tags = ['タグ生成エラー', 'ビジネススキル', '研修動画']
                print(f"  ⚠ Using default tags as last resort")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            total_processing_time += processing_time
            
            # Calculate confidence based on source and tag count
            if ai_mode == 'real_ai':
                confidence = min(0.95, 0.85 + (len(tags) * 0.01))
            else:
                confidence = min(0.80, 0.65 + (len(tags) * 0.01))
            
            processed_tags.append({
                'title': video.get('title', ''),
                'generated_tags': tags,
                'confidence': confidence,
                'processing_time': processing_time,
                'ai_mode': ai_mode
            })
        
        # Calculate overall statistics
        total_tags = sum(len(item['generated_tags']) for item in processed_tags)
        avg_processing_time = total_processing_time / len(video_data) if video_data else 0
        
        print(f"Processing complete: {success_count} AI success, {fallback_count} fallbacks")
        
        self.send_json_response({
            'success': True,
            'results': processed_tags,
            'statistics': {
                'total_videos': len(video_data),
                'total_tags_generated': total_tags,
                'avg_tags_per_video': total_tags / len(video_data) if video_data else 0,
                'ai_success_count': success_count,
                'fallback_count': fallback_count,
                'success_rate': (success_count / len(video_data) * 100) if video_data else 0
            },
            'ai_engine': ai_engine,
            'processing_time': total_processing_time,
            'avg_processing_time': avg_processing_time,
            'ai_mode': 'hybrid' if (success_count > 0 and fallback_count > 0) else ('real' if success_count > 0 else 'simulation')
        })
    
    def generate_sample_tags(self, video, ai_engine):
        """Generate sample tags for simulation mode"""
        title = video.get('title', '').lower()
        skill = video.get('skill', '').lower()
        transcript = video.get('transcript', '').lower()
        description = video.get('description', '').lower()
        summary = video.get('summary', '').lower()
        
        base_tags = []
        
        # Combine all text content for analysis
        all_content = f"{title} {skill} {description} {summary} {transcript}".lower()
        
        # Enhanced keyword matching using transcript content
        keyword_mappings = {
            'プレゼン': ['プレゼンテーション', 'スピーチ', '発表技法', '聴衆分析'],
            'マーケティング': ['マーケティング', 'SEO', 'デジタル戦略', 'ブランディング'],
            'チーム': ['チームワーク', 'リーダーシップ', 'コラボレーション'],
            'データ': ['データ分析', 'データ活用', 'ビジネス分析', '統計'],
            'セールス': ['営業', 'セールス', '顧客対応', '提案'],
            '戦略': ['戦略立案', '企画', 'プランニング', '戦略思考'],
            '効率': ['効率化', '生産性', '時間管理', 'パフォーマンス'],
            '問題': ['問題解決', '課題解決', 'トラブルシューティング'],
            '創造': ['創造性', 'イノベーション', 'アイデア発想'],
            '顧客': ['顧客満足', 'CS', '顧客体験', 'CX'],
            'デジタル': ['DX', 'デジタル化', 'IT活用', 'テクノロジー'],
            '品質': ['品質管理', 'QC', '改善', 'カイゼン']
        }
        
        # Apply enhanced keyword matching to all content
        for keyword, tags in keyword_mappings.items():
            if keyword in all_content:
                base_tags.extend(tags)
        
        # Transcript-specific content analysis
        if transcript:
            # Extract specific concepts from transcript
            if '顧客' in transcript:
                base_tags.extend(['顧客理解', '顧客ニーズ', '顧客志向'])
            if '売上' in transcript or '収益' in transcript:
                base_tags.extend(['売上向上', '収益改善', '業績向上'])
            if '改善' in transcript:
                base_tags.extend(['業務改善', 'プロセス改善', '継続改善'])
            if '分析' in transcript:
                base_tags.extend(['分析手法', 'データドリブン', '定量分析'])
            if '企画' in transcript:
                base_tags.extend(['企画立案', '企画力', 'プロジェクト企画'])
            if 'コスト' in transcript:
                base_tags.extend(['コスト削減', 'コスト管理', '効率化'])
        
        # Skill-based tags (enhanced)
        skill_mappings = {
            'コミュニケーション': ['コミュニケーション', '対人スキル', '説得力', '傾聴'],
            'マネジメント': ['マネジメント', 'プロジェクト管理', '目標設定', '人材育成'],
            'リーダーシップ': ['リーダーシップ', 'チームビルディング', '組織運営'],
            'マーケティング': ['マーケティング戦略', 'マーケット分析', 'ブランド戦略'],
            'セールス': ['営業スキル', 'セールステクニック', '商談力']
        }
        
        for skill_key, skill_tags in skill_mappings.items():
            if skill_key in skill:
                base_tags.extend(skill_tags)
        
        # AI engine specific tags (simulation)
        if ai_engine == 'openai':
            base_tags.extend(['AI分析', '自然言語処理'])
        elif ai_engine == 'claude':
            base_tags.extend(['論理的思考', '構造化分析'])
        elif ai_engine == 'gemini':
            base_tags.extend(['多角的視点', '創造的思考'])
        
        # Add minimal business context only if no specific tags found
        if len(base_tags) < 3:
            base_tags.extend(['マーケティング教育'])
        
        # Generate unique identifier based on content to ensure uniqueness
        import hashlib
        content_hash = hashlib.md5(all_content.encode()).hexdigest()[:4]
        base_tags.append(f"ID-{content_hash}")
        
        # Apply same filtering logic as AI handler
        filtered_tags = self._filter_generic_tags(list(set(base_tags)))
        
        return filtered_tags[:15]  # Remove duplicates and limit
    
    def _filter_generic_tags(self, tags):
        """Filter out generic and meaningless tags (same logic as AI handler)"""
        if not tags:
            return tags
        
        # Patterns to filter out
        generic_patterns = [
            # Number + つの/個の + generic noun patterns
            r'\d+つの要素', r'\d+つの分類', r'\d+つのポイント', r'\d+つの手法',
            r'\d+つのステップ', r'\d+つの方法', r'\d+つの技術', r'\d+つの項目',
            r'\d+つの観点', r'\d+つの視点', r'\d+つの基準', r'\d+つの原則',
            r'\d+個の要素', r'\d+個の分類', r'\d+個のポイント', r'\d+個の手法',
            # Number + の + generic noun patterns (WITHOUT つ/個) - THIS WAS MISSING!
            r'\d+の要素', r'\d+の分類', r'\d+のポイント', r'\d+の手法',
            r'\d+のステップ', r'\d+の方法', r'\d+の技術', r'\d+の項目',
            r'\d+の観点', r'\d+の視点', r'\d+の基準', r'\d+の原則',
            r'\d+の特徴', r'\d+の段階', r'\d+の要因', r'\d+の条件',
            # Any number + generic words patterns (broader coverage)
            r'^\d+要素$', r'^\d+分類$', r'^\d+ポイント$', r'^\d+手法$',
            r'^\d+ステップ$', r'^\d+方法$', r'^\d+項目$', r'^\d+段階$',
            # Generic standalone words - Basic
            r'^要素$', r'^分類$', r'^ポイント$', r'^手法$', r'^方法$', r'^技術$',
            r'^基本$', r'^応用$', r'^実践$', r'^理論$', r'^概要$', r'^入門$',
            r'^初級$', r'^中級$', r'^上級$', r'^基礎$', r'^発展$', r'^活用$',
            r'^ステップ$', r'^段階$', r'^項目$', r'^観点$', r'^視点$', r'^条件$',
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
                    is_generic = True
                    break
            
            # Additional filters
            if not is_generic:
                # Filter overly short tags (single characters or very short)
                if len(tag) < 2:
                    is_generic = True
                # Filter tags with only numbers
                elif tag.isdigit():
                    is_generic = True
                # Filter tags that are just punctuation
                elif not any(c.isalnum() for c in tag):
                    is_generic = True
            
            if not is_generic:
                filtered_tags.append(tag)
        
        return filtered_tags
    
    def handle_tag_optimize(self, data):
        all_tags = data.get('tags', [])
        max_tags = data.get('max_tags', 200)
        
        # Simulate tag optimization
        tag_frequency = {}
        for tag_list in all_tags:
            for tag in tag_list:
                tag_frequency[tag] = tag_frequency.get(tag, 0) + 1
        
        # Sort by frequency and importance score
        optimized = sorted(tag_frequency.items(), key=lambda x: x[1], reverse=True)[:max_tags]
        
        # Calculate importance scores
        max_freq = max([freq for _, freq in optimized]) if optimized else 1
        tag_scores = {
            tag: {
                'frequency': freq,
                'score': round((freq / max_freq) * 10, 1)
            }
            for tag, freq in optimized
        }
        
        self.send_json_response({
            'success': True,
            'original_count': len(set(tag for tag_list in all_tags for tag in tag_list)),
            'optimized_count': len(optimized),
            'optimized_tags': [tag for tag, freq in optimized],
            'tag_frequencies': dict(optimized[:20]),  # Top 20 with frequencies
            'tag_scores': dict(list(tag_scores.items())[:10])  # Top 10 with scores
        })
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))

if __name__ == '__main__':
    PORT = 8080
    Handler = TagGeneratorAPIHandler
    
    print(f"Tag Generator API Server v2.0 starting on port {PORT}")
    print(f"AI API integration: {'ENABLED' if AI_ENABLED else 'DISABLED (simulation mode)'}")
    print(f"Access: http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")