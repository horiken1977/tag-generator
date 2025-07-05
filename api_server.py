#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import re
import os
from datetime import datetime

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
            with open('webapp.html', 'r', encoding='utf-8') as f:
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
            self.send_json_response({
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'features': ['sheets_api', 'ai_processing', 'tag_optimization']
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
            req.add_header('User-Agent', 'TagGenerator/1.0')
            
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
        # Simulate data reading with realistic structure
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
    
    def handle_ai_process(self, data):
        video_data = data.get('data', [])
        ai_engine = data.get('ai_engine', 'openai')
        
        # Simulate AI processing
        processed_tags = []
        for video in video_data:
            tags = self.generate_sample_tags(video, ai_engine)
            processed_tags.append({
                'title': video.get('title', ''),
                'generated_tags': tags,
                'confidence': 0.85 + (len(tags) * 0.01)
            })
        
        self.send_json_response({
            'success': True,
            'results': processed_tags,
            'total_tags_generated': sum(len(item['generated_tags']) for item in processed_tags),
            'ai_engine': ai_engine,
            'processing_time': 2.3
        })
    
    def generate_sample_tags(self, video, ai_engine):
        title = video.get('title', '').lower()
        skill = video.get('skill', '').lower()
        
        base_tags = []
        
        # Title-based tags
        if 'プレゼン' in title:
            base_tags.extend(['プレゼンテーション', 'スピーチ', '発表技法', '聴衆分析'])
        if 'マーケティング' in title:
            base_tags.extend(['マーケティング', 'SEO', 'デジタル戦略', 'ブランディング'])
        if 'チーム' in title:
            base_tags.extend(['チームワーク', 'リーダーシップ', 'コラボレーション'])
        
        # Skill-based tags
        if 'コミュニケーション' in skill:
            base_tags.extend(['コミュニケーション', '対人スキル', '説得力'])
        if 'マネジメント' in skill:
            base_tags.extend(['マネジメント', 'プロジェクト管理', '目標設定'])
        
        # AI engine specific tags
        if ai_engine == 'openai':
            base_tags.extend(['AI分析', '自然言語処理'])
        elif ai_engine == 'claude':
            base_tags.extend(['論理的思考', '構造化分析'])
        elif ai_engine == 'gemini':
            base_tags.extend(['多角的視点', '創造的思考'])
        
        # Add common business tags
        base_tags.extend(['ビジネススキル', '職場効率', '成果向上'])
        
        return list(set(base_tags))[:15]  # Remove duplicates and limit
    
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
        
        self.send_json_response({
            'success': True,
            'original_count': len(set(tag for tag_list in all_tags for tag in tag_list)),
            'optimized_count': len(optimized),
            'optimized_tags': [tag for tag, freq in optimized],
            'tag_frequencies': dict(optimized[:20])  # Top 20 with frequencies
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
    
    print(f"Tag Generator API Server starting on port {PORT}")
    print(f"Access: http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")