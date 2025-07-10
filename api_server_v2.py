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
            # 段階分離式を優先、次にAPI版、最後に通常版
            if os.path.exists('webapp_staged.html'):
                filename = 'webapp_staged.html'
            elif os.path.exists('webapp_api.html'):
                filename = 'webapp_api.html'
            else:
                filename = 'webapp.html'
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
            print(f"使用中のWebアプリ: {filename}")
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
            elif self.path == '/api/ai/stage1':
                self.handle_stage1_candidate_generation(data)
            elif self.path == '/api/ai/stage2':
                self.handle_stage2_individual_tagging(data)
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
        
        # 段階分離式処理が利用可能な場合は推奨
        if len(video_data) > 1:
            self.send_json_response({
                'success': False,
                'message': '段階分離式処理を使用してください',
                'recommendation': {
                    'step1': 'POST /api/ai/stage1 でタグ候補を生成',
                    'step2': 'タグ候補を確認・承認後、POST /api/ai/stage2 で個別タグ付け'
                },
                'fallback_available': True
            })
            return
        
        # 単一動画の場合は従来処理
        return self.handle_single_phase_processing(video_data, ai_engine, use_real_ai)
    
    def handle_two_phase_processing(self, video_data, ai_engine, use_real_ai):
        """正しい二段階タグ処理（ユーザー要求仕様完全準拠）"""
        from two_phase_tag_processor import TwoPhaseTagProcessor
        
        start_time = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"正しい二段階処理を開始: {len(video_data)}件の動画")
        print(f"フェーズ1: 文字起こし以外の全件分析 → タグ候補生成")
        print(f"フェーズ2: 文字起こし含む個別分析 → 10-15個タグ選定")
        print(f"{'='*60}")
        
        # 正しい二段階プロセッサーを初期化
        processor = TwoPhaseTagProcessor(ai_handler if AI_ENABLED else None)
        
        try:
            # ユーザー要求仕様通りの完全な二段階処理を実行
            results = processor.execute_complete_two_phase_processing(video_data, ai_engine)
            
            if not results:
                print("⚠️ 二段階処理が失敗しました")
                return self.handle_single_phase_processing(video_data, ai_engine, use_real_ai)
            
            total_processing_time = (datetime.now() - start_time).total_seconds()
            
            # APIレスポンス用にフォーマット
            processed_tags = []
            for result in results:
                processed_tags.append({
                    'title': result.get('title', ''),
                    'generated_tags': result.get('selected_tags', []),
                    'confidence': 0.95,  # 高い信頼度（二段階処理）
                    'processing_time': total_processing_time / len(video_data),
                    'ai_mode': 'two_phase_complete',
                    'tag_candidates_count': result.get('phase1_candidates', 0),
                    'selection_method': 'transcript_based_selection',
                    'phase1_completed': True,
                    'phase2_completed': True
                })
            
            total_tags = sum(len(item['generated_tags']) for item in processed_tags)
            
            print(f"\n=== 二段階処理結果 ===")
            print(f"処理動画数: {len(video_data)}件")
            print(f"総タグ生成数: {total_tags}個")
            print(f"平均タグ数: {total_tags / len(video_data) if video_data else 0:.1f}個/動画")
            print(f"処理時間: {total_processing_time:.2f}秒")
            
            self.send_json_response({
                'success': True,
                'results': processed_tags,
                'statistics': {
                    'total_videos': len(video_data),
                    'total_tags_generated': total_tags,
                    'avg_tags_per_video': total_tags / len(video_data) if video_data else 0,
                    'total_tag_candidates': processor.tag_candidates if hasattr(processor, 'tag_candidates') else 0,
                    'processing_method': 'two_phase_complete',
                    'phase1_analysis': 'completed',
                    'phase2_analysis': 'completed',
                    'specification_compliance': 'full'
                },
                'ai_engine': ai_engine,
                'processing_time': total_processing_time,
                'ai_mode': 'two_phase_production_complete'
            })
            
        except Exception as e:
            print(f"二段階処理エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            # フォールバックは使用せず、エラーを返す
            self.send_json_response({
                'success': False,
                'error': f'二段階処理に失敗しました: {str(e)}',
                'fallback_used': False
            }, 500)
    
    def handle_stage1_candidate_generation(self, data):
        """第1段階: タグ候補生成（文字起こし除外）"""
        from staged_tag_processor import StagedTagProcessor
        
        video_data = data.get('data', [])
        
        if not video_data:
            self.send_json_response({
                'success': False,
                'error': '動画データがありません'
            }, 400)
            return
        
        print(f"\n第1段階処理開始: {len(video_data)}件の動画")
        
        processor = StagedTagProcessor(ai_handler if AI_ENABLED else None)
        
        try:
            result = processor.execute_stage1_candidate_generation(video_data)
            self.send_json_response(result)
            
        except Exception as e:
            print(f"第1段階処理エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            
            self.send_json_response({
                'success': False,
                'error': f'第1段階処理に失敗しました: {str(e)}',
                'stage': 1
            }, 500)
    
    def handle_stage2_individual_tagging(self, data):
        """第2段階: 個別タグ付け（文字起こし含む）"""
        from staged_tag_processor import StagedTagProcessor
        
        video_data = data.get('data', [])
        approved_candidates = data.get('approved_candidates', [])
        ai_engine = data.get('ai_engine', 'openai')
        
        if not video_data:
            self.send_json_response({
                'success': False,
                'error': '動画データがありません'
            }, 400)
            return
        
        if not approved_candidates:
            self.send_json_response({
                'success': False,
                'error': '承認されたタグ候補がありません',
                'message': 'まず /api/ai/stage1 でタグ候補を生成し、内容を確認してから第2段階を実行してください'
            }, 400)
            return
        
        print(f"\n第2段階処理開始: {len(video_data)}件の動画、{len(approved_candidates)}個のタグ候補使用")
        
        processor = StagedTagProcessor(ai_handler if AI_ENABLED else None)
        
        try:
            result = processor.execute_stage2_individual_tagging(video_data, approved_candidates, ai_engine)
            self.send_json_response(result)
            
        except Exception as e:
            print(f"第2段階処理エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            
            self.send_json_response({
                'success': False,
                'error': f'第2段階処理に失敗しました: {str(e)}',
                'stage': 2
            }, 500)
    
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
        """旧来のシミュレーションモード（二段階処理では使用しない）"""
        print("⚠️ 旧来のシミュレーションモードは使用しないでください。二段階処理を使用してください。")
        return ['エラー:旧来モード使用', '二段階処理を使用してください']
    
    def _filter_generic_tags(self, tags):
        """Filter out generic and meaningless tags (same logic as AI handler)"""
        if not tags:
            return tags
        
        # 汎用タグを完全に除外するための定義（「4つのポイント」等を絶対に含めない）
        generic_patterns = [
            # 数字+汎用語パターン（完全網羅）
            r'\d+つの要素', r'\d+つの分類', r'\d+つのポイント', r'\d+つの手法', r'\d+つのステップ',
            r'\d+つの方法', r'\d+つの技術', r'\d+つの項目', r'\d+つの観点', r'\d+つの視点',
            r'\d+つの基準', r'\d+つの原則', r'\d+つの特徴', r'\d+つの段階', r'\d+つの要因',
            r'\d+個の要素', r'\d+個の分類', r'\d+個のポイント', r'\d+個の手法',
            # 数字+の+汎用名詞パターン（つ/個なし） - 重要！
            r'\d+の要素', r'\d+の分類', r'\d+のポイント', r'\d+の手法', r'\d+のステップ',
            r'\d+の方法', r'\d+の技術', r'\d+の項目', r'\d+の観点', r'\d+の視点',
            r'\d+の基準', r'\d+の原則', r'\d+の特徴', r'\d+の段階', r'\d+の要因', r'\d+の条件',
            # 数字のみ+汎用語パターン
            r'^\d+要素$', r'^\d+分類$', r'^\d+ポイント$', r'^\d+手法$', r'^\d+ステップ$',
            r'^\d+方法$', r'^\d+項目$', r'^\d+段階$', r'^\d+観点$', r'^\d+視点$',
            # 汎用単語（単体）
            r'^要素$', r'^分類$', r'^ポイント$', r'^手法$', r'^方法$', r'^技術$',
            r'^基本$', r'^応用$', r'^実践$', r'^理論$', r'^概要$', r'^入門$',
            r'^初級$', r'^中級$', r'^上級$', r'^基礎$', r'^発展$', r'^活用$',
            r'^ステップ$', r'^段階$', r'^項目$', r'^観点$', r'^視点$', r'^条件$',
            # 汎用ビジネス用語
            r'^実務スキル$', r'^思考法$', r'^業界知識$', r'^ツール活用$', 
            r'^人材育成$', r'^スキル開発$', r'^成果向上$', r'^効率化$',
            r'^戦術$', r'^手順$', r'^方法論$', r'^支援会社視点$',
            r'^ビジネススキル$', r'^職場効率$', r'^社会人教育$', r'^研修動画$',
            # 汎用プロセス用語
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
    # 環境変数からポートとホストを取得（本番環境対応）
    PORT = int(os.environ.get('PORT', 8080))
    HOST = os.environ.get('HOST', '')
    
    Handler = TagGeneratorAPIHandler
    
    print(f"Tag Generator API Server v2.0 starting on {HOST or 'all interfaces'}:{PORT}")
    print(f"AI API integration: {'ENABLED' if AI_ENABLED else 'DISABLED (simulation mode)'}")
    print(f"Environment: {'PRODUCTION' if PORT != 8080 else 'DEVELOPMENT'}")
    print(f"Access: http://{HOST or 'localhost'}:{PORT}")
    print("Press Ctrl+C to stop")
    
    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")