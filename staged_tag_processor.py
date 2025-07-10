#!/usr/bin/env python3
"""
段階分離式タグ処理システム

第1段階: 文字起こし除外で全件分析 → タグ候補生成 → Web表示 → ユーザー確認
第2段階: 承認済みタグ候補で1件ずつ詳細分析 → 最終タグ付け
"""

import json
import logging
from typing import List, Dict, Any, Set
import re
from datetime import datetime

class StagedTagProcessor:
    """段階分離式タグ処理システム"""
    
    def __init__(self, ai_handler=None):
        self.ai_handler = ai_handler
        self.logger = logging.getLogger(__name__)
        self.stage1_candidates = set()
        self.approved_candidates = set()
        
    def execute_stage1_candidate_generation(self, all_video_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        第1段階: 文字起こし除外での全件分析とタグ候補生成
        
        Args:
            all_video_data: 全動画データのリスト
            
        Returns:
            stage1結果（タグ候補、統計情報等）
        """
        print(f"\n{'='*60}")
        print(f"第1段階開始: タグ候補生成（文字起こし除外分析）")
        print(f"対象動画数: {len(all_video_data)}件")
        print(f"{'='*60}")
        
        start_time = datetime.now()
        
        # 文字起こし以外の全データを集約
        aggregated_data = self._aggregate_non_transcript_data(all_video_data)
        
        # タグ候補を生成
        self.stage1_candidates = self._generate_tag_candidates(aggregated_data)
        
        # 厳格な汎用タグフィルタリングを適用
        filtered_candidates = self._apply_strict_generic_filter(list(self.stage1_candidates))
        self.stage1_candidates = set(filtered_candidates)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            'stage': 1,
            'success': True,
            'tag_candidates': sorted(list(self.stage1_candidates)),
            'candidate_count': len(self.stage1_candidates),
            'processing_time': processing_time,
            'source_data_stats': {
                'total_videos': len(all_video_data),
                'titles_processed': len([v for v in all_video_data if v.get('title')]),
                'skills_processed': len([v for v in all_video_data if v.get('skill')]),
                'descriptions_processed': len([v for v in all_video_data if v.get('description')]),
                'summaries_processed': len([v for v in all_video_data if v.get('summary')]),
                'transcripts_excluded': True
            },
            'message': 'タグ候補が生成されました。内容を確認して承認してください。'
        }
        
        print(f"第1段階完了: {len(self.stage1_candidates)}個のタグ候補を生成")
        print(f"処理時間: {processing_time:.2f}秒")
        print(f"タグ候補例: {sorted(list(self.stage1_candidates))[:10]}...")
        
        return result
    
    def execute_stage2_individual_tagging(self, all_video_data: List[Dict[str, Any]], approved_candidates: List[str], ai_engine: str = 'openai') -> Dict[str, Any]:
        """
        第2段階: 承認されたタグ候補を使用しての1件ずつ詳細分析
        
        Args:
            all_video_data: 全動画データのリスト
            approved_candidates: ユーザーが承認したタグ候補のリスト
            ai_engine: 使用するAIエンジン
            
        Returns:
            stage2結果（各動画のタグ付け結果）
        """
        print(f"\n{'='*60}")
        print(f"第2段階開始: 個別動画タグ付け（文字起こし含む詳細分析）")
        print(f"対象動画数: {len(all_video_data)}件")
        print(f"使用タグ候補数: {len(approved_candidates)}個")
        print(f"{'='*60}")
        
        if not approved_candidates:
            return {
                'stage': 2,
                'success': False,
                'error': 'タグ候補が承認されていません',
                'results': []
            }
        
        self.approved_candidates = set(approved_candidates)
        start_time = datetime.now()
        
        # 各動画を個別に詳細分析
        results = []
        for i, video in enumerate(all_video_data):
            print(f"\n--- 動画 {i+1}/{len(all_video_data)} を分析中 ---")
            
            selected_tags = self._analyze_individual_video(video, ai_engine)
            
            result = {
                'video_index': i,
                'title': video.get('title', ''),
                'selected_tags': selected_tags,
                'tag_count': len(selected_tags),
                'confidence': self._calculate_confidence(selected_tags, video)
            }
            results.append(result)
            
            print(f"  タイトル: {video.get('title', 'Unknown')[:50]}...")
            print(f"  選定タグ数: {len(selected_tags)}")
            print(f"  タグ: {selected_tags[:5]}{'...' if len(selected_tags) > 5 else ''}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        final_result = {
            'stage': 2,
            'success': True,
            'results': results,
            'statistics': {
                'total_videos': len(all_video_data),
                'avg_tags_per_video': sum(len(r['selected_tags']) for r in results) / len(results) if results else 0,
                'total_tags_assigned': sum(len(r['selected_tags']) for r in results),
                'approved_candidates_used': len(approved_candidates),
                'processing_time': processing_time
            },
            'message': '全動画のタグ付けが完了しました'
        }
        
        print(f"\n第2段階完了: {len(all_video_data)}件の動画をタグ付け")
        print(f"処理時間: {processing_time:.2f}秒")
        print(f"平均タグ数: {final_result['statistics']['avg_tags_per_video']:.1f}個/動画")
        
        return final_result
    
    def _aggregate_non_transcript_data(self, all_video_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """文字起こし以外のデータを集約"""
        print("文字起こし以外のデータを集約中...")
        
        titles = []
        skills = []
        descriptions = []
        summaries = []
        
        for video in all_video_data:
            # 意図的に transcript は除外
            if video.get('title'):
                titles.append(video['title'].strip())
            if video.get('skill'):
                skills.append(video['skill'].strip())
            if video.get('description'):
                descriptions.append(video['description'].strip())
            if video.get('summary'):
                summaries.append(video['summary'].strip())
        
        aggregated = {
            'all_titles': ' '.join(titles),
            'all_skills': ' '.join(skills),
            'all_descriptions': ' '.join(descriptions),
            'all_summaries': ' '.join(summaries)
        }
        
        print(f"  タイトル: {len(titles)}件")
        print(f"  スキル: {len(skills)}件")
        print(f"  説明文: {len(descriptions)}件")
        print(f"  要約: {len(summaries)}件")
        print(f"  ※文字起こしは意図的に除外")
        
        return aggregated
    
    def _generate_tag_candidates(self, aggregated_data: Dict[str, str]) -> Set[str]:
        """集約データからタグ候補を生成"""
        
        # AIを使用したタグ候補生成
        if self.ai_handler:
            try:
                ai_candidates = self._generate_candidates_with_ai(aggregated_data)
                if ai_candidates:
                    print(f"AI分析で{len(ai_candidates)}個の候補を生成")
                    return set(ai_candidates)
            except Exception as e:
                print(f"AI分析エラー、フォールバック処理: {e}")
        
        # フォールバック: キーワード抽出
        return self._extract_candidates_fallback(aggregated_data)
    
    def _generate_candidates_with_ai(self, aggregated_data: Dict[str, str]) -> List[str]:
        """AI分析でタグ候補を生成"""
        
        prompt = f"""
以下の全動画データを分析して、タグ候補となるキーワードを抽出してください。
これらは後で個別動画の詳細分析で使用される候補です。

【全タイトル集約】:
{aggregated_data['all_titles']}

【全スキル集約】:
{aggregated_data['all_skills']}

【全説明文集約】:
{aggregated_data['all_descriptions']}

【全要約集約】:
{aggregated_data['all_summaries']}

【タグ候補抽出の基準】:
1. 具体的なツール名・サービス名・手法名
2. 業界固有の概念・理論・フレームワーク
3. 測定可能な指標名・KPI
4. 具体的なプロセス名・手順名
5. 職種・業界・分野名

【絶対に避けるべき汎用語】:
- 「6つの要素」「8つの分類」「4つのポイント」等の数字+汎用語
- 「要素」「分類」「ポイント」「手法」「方法」「技術」等の単体使用
- 「基本」「応用」「実践」「理論」「概要」「入門」等の抽象表現

出力: 具体的で有用なタグ候補のみをカンマ区切りで出力してください。
"""
        
        return self.ai_handler.call_openai(prompt)
    
    def _extract_candidates_fallback(self, aggregated_data: Dict[str, str]) -> Set[str]:
        """フォールバック: キーワード抽出"""
        candidates = set()
        
        all_text = ' '.join(aggregated_data.values())
        
        # 具体的なキーワードパターンを抽出
        specific_patterns = [
            r'Google Analytics?', r'Salesforce', r'Instagram', r'Facebook', r'TikTok', r'YouTube', 
            r'Twitter', r'LinkedIn', r'ROI', r'CPA', r'CPM', r'CTR', r'LTV', r'CAC', r'ROAS', 
            r'KPI', r'OKR', r'PDCAサイクル', r'PDCA', r'A/Bテスト', r'SEO', r'SEM'
        ]
        
        for pattern in specific_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            for match in matches:
                if len(match) > 2:
                    candidates.add(match)
        
        # 2文字以上の日本語キーワードを抽出
        japanese_words = re.findall(r'[あ-ん]+[ー]?[あ-ん]*|[ア-ン]+[ー]?[ア-ン]*|[一-龯]+', all_text)
        for word in japanese_words:
            if len(word) >= 3 and not self._is_generic_word(word):  # 3文字以上に制限
                candidates.add(word)
        
        return candidates
    
    def _apply_strict_generic_filter(self, tags: List[str]) -> List[str]:
        """厳格な汎用タグフィルタリング"""
        if not tags:
            return tags
        
        # より厳格な汎用パターン定義
        generic_patterns = [
            # 数字+汎用語パターン（完全網羅）
            r'\d+つの要素', r'\d+つの分類', r'\d+つのポイント', r'\d+つの手法', r'\d+つのステップ',
            r'\d+つの方法', r'\d+つの技術', r'\d+つの項目', r'\d+つの観点', r'\d+つの視点',
            r'\d+つの基準', r'\d+つの原則', r'\d+つの特徴', r'\d+つの段階', r'\d+つの要因',
            r'\d+個の要素', r'\d+個の分類', r'\d+個のポイント', r'\d+個の手法', r'\d+個のステップ',
            r'\d+の要素', r'\d+の分類', r'\d+のポイント', r'\d+の手法', r'\d+のステップ',
            r'\d+の方法', r'\d+の技術', r'\d+の項目', r'\d+の観点', r'\d+の視点',
            r'\d+の基準', r'\d+の原則', r'\d+の特徴', r'\d+の段階', r'\d+の要因', r'\d+の条件',
            # 数字のみ+汎用語
            r'^\\d+要素$', r'^\\d+分類$', r'^\\d+ポイント$', r'^\\d+手法$', r'^\\d+ステップ$',
            r'^\\d+方法$', r'^\\d+項目$', r'^\\d+段階$', r'^\\d+観点$', r'^\\d+視点$',
            # 汎用単語（単体）
            r'^要素$', r'^分類$', r'^ポイント$', r'^手法$', r'^方法$', r'^技術$',
            r'^基本$', r'^応用$', r'^実践$', r'^理論$', r'^概要$', r'^入門$',
            r'^初級$', r'^中級$', r'^上級$', r'^基礎$', r'^発展$', r'^活用$',
            r'^ステップ$', r'^段階$', r'^項目$', r'^観点$', r'^視点$', r'^条件$',
            # 汎用ビジネス用語
            r'^改善$', r'^最適化$', r'^強化$', r'^向上$', r'^推進$', r'^展開$',
            r'^構築$', r'^確立$', r'^設計$', r'^運用$', r'^管理$', r'^分析$',
            r'^実務スキル$', r'^思考法$', r'^業界知識$', r'^ツール活用$',
            r'^人材育成$', r'^スキル開発$', r'^成果向上$', r'^効率化$'
        ]
        
        filtered = []
        removed_count = 0
        
        for tag in tags:
            tag = tag.strip()
            if not tag or len(tag) < 2:
                continue
            
            is_generic = False
            for pattern in generic_patterns:
                if re.match(pattern, tag):
                    print(f"    汎用タグを除外: '{tag}'")
                    is_generic = True
                    removed_count += 1
                    break
            
            if not is_generic:
                filtered.append(tag)
        
        print(f"  汎用タグフィルタリング: {len(tags)}個 → {len(filtered)}個 ({removed_count}個除外)")
        return filtered
    
    def _is_generic_word(self, word: str) -> bool:
        """汎用語チェック"""
        generic_words = {
            '要素', '分類', 'ポイント', '手法', '方法', '技術', '基本', '応用',
            '実践', '理論', '概要', '入門', '初級', '中級', '上級', '基礎',
            '発展', '活用', 'について', 'による', 'ための', 'とは', 'です',
            '改善', '最適化', '強化', '向上', '推進', '展開', '構築', '確立',
            '設計', '運用', '管理', '分析', 'ステップ', '段階', '項目', '観点', '視点',
            '条件', '特徴', '要因', '基準', '原則'
        }
        return word in generic_words
    
    def _analyze_individual_video(self, video_data: Dict[str, Any], ai_engine: str) -> List[str]:
        """個別動画の詳細分析（文字起こし含む）"""
        title = video_data.get('title', '')[:30]
        print(f"    分析中: {title}...")
        
        if self.ai_handler:
            try:
                return self._ai_individual_analysis(video_data, ai_engine)
            except Exception as e:
                print(f"    AI分析エラー、フォールバック: {e}")
        
        return self._fallback_individual_analysis(video_data)
    
    def _ai_individual_analysis(self, video_data: Dict[str, Any], ai_engine: str) -> List[str]:
        """AI による個別動画分析"""
        transcript = video_data.get('transcript', '')
        transcript_excerpt = transcript[:2500] if transcript else ''
        
        candidates_str = ', '.join(sorted(list(self.approved_candidates)))
        
        prompt = f"""
以下の動画について、承認されたタグ候補から最も適切なタグを10-15個選択してください。

【動画情報】:
タイトル: {video_data.get('title', '')}
スキル: {video_data.get('skill', '')}
説明文: {video_data.get('description', '')}
要約: {video_data.get('summary', '')}

【文字起こし内容（重要）】:
{transcript_excerpt}

【承認済みタグ候補】:
{candidates_str}

【選定基準】:
1. 文字起こし内容に直接言及されているキーワードを最優先
2. この動画の具体的内容を最も正確に表現するタグ
3. 検索時に実用的で具体性の高いタグ
4. 他の動画との差別化に役立つタグ

【厳守事項】:
- 新しいタグは作成せず、承認済み候補からのみ選択
- 文字起こしに関連しないタグは選択しない
- 10-15個の範囲で選択

出力: 選択したタグのみをカンマ区切りで出力してください。
"""
        
        if ai_engine == 'openai':
            return self.ai_handler.call_openai(prompt)
        elif ai_engine == 'claude':
            return self.ai_handler.call_claude(prompt)
        elif ai_engine == 'gemini':
            return self.ai_handler.call_gemini(prompt)
        else:
            return []
    
    def _fallback_individual_analysis(self, video_data: Dict[str, Any]) -> List[str]:
        """フォールバック個別分析"""
        content = f"{video_data.get('title', '')} {video_data.get('skill', '')} {video_data.get('description', '')} {video_data.get('summary', '')} {video_data.get('transcript', '')}".lower()
        
        selected = []
        for candidate in self.approved_candidates:
            if candidate.lower() in content and len(selected) < 15:
                selected.append(candidate)
        
        # 最低限の数を確保
        if len(selected) < 10:
            remaining_candidates = [c for c in self.approved_candidates if c not in selected]
            for candidate in remaining_candidates[:10-len(selected)]:
                selected.append(candidate)
        
        return selected[:15]
    
    def _calculate_confidence(self, selected_tags: List[str], video_data: Dict[str, Any]) -> float:
        """信頼度計算"""
        if not selected_tags:
            return 0.0
        
        # 文字起こしとの関連度をチェック
        transcript = video_data.get('transcript', '').lower()
        if transcript:
            related_count = sum(1 for tag in selected_tags if tag.lower() in transcript)
            transcript_relevance = related_count / len(selected_tags)
        else:
            transcript_relevance = 0.5
        
        # タグ数による信頼度
        tag_count_factor = min(1.0, len(selected_tags) / 12.0)
        
        # 総合信頼度
        confidence = (transcript_relevance * 0.7 + tag_count_factor * 0.3)
        return round(confidence, 2)