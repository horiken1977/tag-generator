#!/usr/bin/env python3
"""
二段階タグ処理システム - ユーザー要求仕様に完全準拠

フェーズ1: 文字起こし以外の列を全件読み込み → 要素分析してタグ候補作成
フェーズ2: 文字起こし含む列を1件ずつ読み込み → 詳細分析して10-15個のタグ選定
"""

import json
import logging
from typing import List, Dict, Any, Set
from collections import Counter
import re

class TwoPhaseTagProcessor:
    """ユーザー要求仕様に完全準拠した二段階タグ処理システム"""
    
    def __init__(self, ai_handler=None):
        self.ai_handler = ai_handler
        self.logger = logging.getLogger(__name__)
        self.tag_candidates = set()
        
    def phase1_analyze_all_videos_without_transcript(self, all_video_data: List[Dict[str, Any]]) -> Set[str]:
        """
        フェーズ1: 文字起こし以外の列を全件読み込み、要素分析してタグ候補を作成
        
        Args:
            all_video_data: 全動画データのリスト
            
        Returns:
            全体分析から抽出されたタグ候補のセット
        """
        print(f"\n=== フェーズ1開始: {len(all_video_data)}件の動画を分析（文字起こし除外） ===")
        
        # 文字起こし以外の全データを収集
        combined_data = {
            'all_titles': [],
            'all_skills': [],
            'all_descriptions': [],
            'all_summaries': []
        }
        
        for video in all_video_data:
            # 文字起こしは意図的に除外
            title = video.get('title', '').strip()
            skill = video.get('skill', '').strip()
            description = video.get('description', '').strip()
            summary = video.get('summary', '').strip()
            
            if title:
                combined_data['all_titles'].append(title)
            if skill:
                combined_data['all_skills'].append(skill)
            if description:
                combined_data['all_descriptions'].append(description)
            if summary:
                combined_data['all_summaries'].append(summary)
        
        print(f"収集データ:")
        print(f"  タイトル: {len(combined_data['all_titles'])}件")
        print(f"  スキル: {len(combined_data['all_skills'])}件")
        print(f"  説明文: {len(combined_data['all_descriptions'])}件")
        print(f"  要約: {len(combined_data['all_summaries'])}件")
        print(f"  ※文字起こしは意図的に除外")
        
        # 全体要素分析を実行してタグ候補を生成
        self.tag_candidates = self._execute_phase1_analysis(combined_data)
        
        print(f"フェーズ1完了: {len(self.tag_candidates)}個のタグ候補を生成")
        print(f"タグ候補例: {sorted(list(self.tag_candidates))[:10]}...")
        
        return self.tag_candidates
    
    def _execute_phase1_analysis(self, combined_data: Dict[str, List[str]]) -> Set[str]:
        """フェーズ1の要素分析を実行"""
        
        # 全データを結合して分析用テキストを作成
        all_titles_text = ' '.join(combined_data['all_titles'])
        all_skills_text = ' '.join(combined_data['all_skills'])
        all_descriptions_text = ' '.join(combined_data['all_descriptions'])
        all_summaries_text = ' '.join(combined_data['all_summaries'])
        
        # AI分析用のプロンプトを作成
        phase1_prompt = f"""
以下は全動画データの集約情報です。この情報を分析して、タグ候補となる有用なキーワードを抽出してください。
これらのタグ候補は後のフェーズ2で個別動画の詳細分析に使用されます。

【全動画のタイトル集約】:
{all_titles_text}

【全動画のスキル集約】:
{all_skills_text}

【全動画の説明文集約】:
{all_descriptions_text}

【全動画の要約集約】:
{all_summaries_text}

【タグ候補抽出の基準】:
1. 頻出する専門用語・ビジネス用語
2. 具体的なツール名・サービス名・手法名
3. 業界固有の概念・理論・フレームワーク
4. 測定可能な指標名・KPI
5. 具体的なプロセス名・手順名
6. 職種・業界・分野名

【絶対に避けるべき汎用語】:
- 「要素」「分類」「ポイント」「手法」「方法」「技術」等の単体使用
- 「基本」「応用」「実践」「理論」「概要」「入門」等の抽象表現
- 「4つのポイント」「6つの要素」「8つの分類」等の数字+汎用語
- 「改善」「最適化」「強化」「向上」等の汎用プロセス語

【重要】: 具体的で検索価値の高いキーワードのみを抽出してください。

出力: 有用なタグ候補をカンマ区切りで出力してください。
"""
        
        if self.ai_handler:
            try:
                print("AI分析でタグ候補を生成中...")
                candidates = self.ai_handler.call_openai(phase1_prompt)
                if candidates and len(candidates) > 0:
                    # 汎用タグフィルターを適用
                    filtered_candidates = self._filter_generic_tags(candidates)
                    print(f"AI分析: {len(candidates)}個 → フィルター後: {len(filtered_candidates)}個")
                    return set(filtered_candidates)
            except Exception as e:
                print(f"AI分析エラー、フォールバック処理: {e}")
        
        # フォールバック: キーワード抽出分析
        return self._extract_candidates_fallback(combined_data)
    
    def _extract_candidates_fallback(self, combined_data: Dict[str, List[str]]) -> Set[str]:
        """AI分析失敗時のフォールバック処理"""
        candidates = set()
        
        # 各データタイプから特定パターンを抽出
        all_text = ' '.join(
            combined_data['all_titles'] + 
            combined_data['all_skills'] + 
            combined_data['all_descriptions'] + 
            combined_data['all_summaries']
        )
        
        # 具体的なキーワードパターンを抽出
        specific_patterns = [
            # ツール・サービス名
            r'Google Analytics?', r'Salesforce', r'Instagram', r'Facebook', r'TikTok', r'YouTube', r'Twitter', r'LinkedIn',
            # 指標・KPI
            r'ROI', r'CPA', r'CPM', r'CTR', r'LTV', r'CAC', r'ROAS', r'KPI', r'OKR',
            # 手法・フレームワーク
            r'PDCAサイクル', r'PDCA', r'A/Bテスト', r'アジャイル', r'リーンスタートアップ',
            # 専門用語
            r'SEO', r'SEM', r'SNSマーケティング', r'デジタルマーケティング', r'コンテンツマーケティング'
        ]
        
        for pattern in specific_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            for match in matches:
                if len(match) > 2:
                    candidates.add(match)
        
        # 2文字以上の日本語キーワードを抽出（汎用語除外）
        japanese_words = re.findall(r'[あ-ん]+[ー]?[あ-ん]*|[ア-ン]+[ー]?[ア-ン]*|[一-龯]+', all_text)
        for word in japanese_words:
            if len(word) >= 2 and not self._is_generic_word(word):
                candidates.add(word)
        
        return candidates
    
    def _filter_generic_tags(self, tags: List[str]) -> List[str]:
        """汎用タグを完全に除外"""
        if not tags:
            return tags
        
        # 厳格な汎用パターン定義
        generic_patterns = [
            # 数字+汎用語パターン（全形式）
            r'\d+つの要素', r'\d+つの分類', r'\d+つのポイント', r'\d+つの手法', r'\d+つのステップ',
            r'\d+つの方法', r'\d+つの技術', r'\d+つの項目', r'\d+つの観点', r'\d+つの視点',
            r'\d+個の要素', r'\d+個の分類', r'\d+個のポイント', r'\d+個の手法',
            r'\d+の要素', r'\d+の分類', r'\d+のポイント', r'\d+の手法', r'\d+のステップ',
            r'\d+の方法', r'\d+の技術', r'\d+の項目', r'\d+の観点', r'\d+の視点',
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
        for tag in tags:
            tag = tag.strip()
            if not tag or len(tag) < 2:
                continue
            
            is_generic = False
            for pattern in generic_patterns:
                if re.match(pattern, tag):
                    print(f"  汎用タグをフィルター: {tag}")
                    is_generic = True
                    break
            
            if not is_generic:
                filtered.append(tag)
        
        return filtered
    
    def _is_generic_word(self, word: str) -> bool:
        """汎用語チェック"""
        generic_words = {
            '要素', '分類', 'ポイント', '手法', '方法', '技術', '基本', '応用',
            '実践', '理論', '概要', '入門', '初級', '中級', '上級', '基礎',
            '発展', '活用', 'について', 'による', 'ための', 'とは', 'です',
            '改善', '最適化', '強化', '向上', '推進', '展開', '構築', '確立',
            '設計', '運用', '管理', '分析', 'ステップ', '段階', '項目', '観点', '視点'
        }
        return word in generic_words
    
    def phase2_individual_analysis_with_transcript(self, video_data: Dict[str, Any], ai_engine: str = 'openai') -> List[str]:
        """
        フェーズ2: 文字起こし含む個別動画の詳細分析で10-15個のタグを選定
        
        Args:
            video_data: 個別動画データ（文字起こし含む）
            ai_engine: 使用するAIエンジン
            
        Returns:
            選定された10-15個のタグのリスト
        """
        title = video_data.get('title', '')
        print(f"\n=== フェーズ2開始: 個別分析 '{title[:30]}...' ===")
        print(f"利用可能タグ候補: {len(self.tag_candidates)}個")
        
        # 文字起こしを含む詳細分析プロンプトを作成
        transcript = video_data.get('transcript', '')
        transcript_for_analysis = transcript[:2500] if transcript else ''  # 十分な文字数を確保
        
        candidates_list = sorted(list(self.tag_candidates))
        candidates_str = ', '.join(candidates_list)
        
        phase2_prompt = f"""
以下の動画について、承認されたタグ候補から最も適切なタグを15個選択してください。

【動画情報】:
タイトル: {video_data.get('title', '')}
スキル: {video_data.get('skill', '')}
説明文: {video_data.get('description', '')}
要約: {video_data.get('summary', '')}

【文字起こし内容（重要）】:
{transcript_for_analysis}

【承認済みタグ候補】:
{candidates_str}

【選定基準（優先順位順）】:
🎯 **最優先: 差別化と特異性**
1. この動画でしか言及されない具体的なツール名・サービス名・手法名
2. 文字起こしに登場する固有名詞・数値・具体的事例
3. 他の類似動画では扱われない専門的な概念・理論

🔍 **第2優先: 文字起こし直接関連性**
4. 文字起こしで複数回言及される重要キーワード
5. 動画の核心内容を表す専門用語

⚡ **第3優先: 実用性と検索価値**
6. 検索時に有用で具体性の高いタグ
7. 学習者が求める実践的な知識を表すタグ

【絶対に避けるべき汎用タグ（具体例）】:
❌ 「ビジネススキル」「マーケティング」「営業」「コミュニケーション」
❌ 「プレゼンテーション」「リーダーシップ」「マネジメント」「戦略」
❌ 「分析」「改善」「効率化」「最適化」「向上」「強化」
❌ 「基本」「応用」「実践」「理論」「入門」「概要」
❌ 「スキル開発」「人材育成」「業務改善」「組織運営」

【厳守事項】:
- 新しいタグは作成せず、承認済み候補からのみ選択
- 文字起こしに全く関連しないタグは絶対に選択しない
- 汎用的すぎるタグは差別化の観点から除外
- 必ず15個のタグを選択（12-18個の範囲で調整可能）

出力: 選択したタグのみをカンマ区切りで出力してください。
"""
        
        if self.ai_handler:
            try:
                print("文字起こし含む詳細分析を実行中...")
                selected_tags = self._call_ai_for_phase2(phase2_prompt, ai_engine)
                if selected_tags and len(selected_tags) >= 10:
                    final_tags = selected_tags[:15]  # 最大15個に制限
                    print(f"フェーズ2完了: {len(final_tags)}個のタグを選定")
                    return final_tags
            except Exception as e:
                print(f"AI分析エラー、フォールバック処理: {e}")
        
        # フォールバック処理
        return self._select_tags_fallback(video_data)
    
    def _call_ai_for_phase2(self, prompt: str, ai_engine: str) -> List[str]:
        """フェーズ2のAI分析を実行"""
        if ai_engine == 'openai':
            return self.ai_handler.call_openai(prompt)
        elif ai_engine == 'claude':
            return self.ai_handler.call_claude(prompt)
        elif ai_engine == 'gemini':
            return self.ai_handler.call_gemini(prompt)
        else:
            return None
    
    def _select_tags_fallback(self, video_data: Dict[str, Any]) -> List[str]:
        """AI分析失敗時のフォールバック処理"""
        content = f"{video_data.get('title', '')} {video_data.get('skill', '')} {video_data.get('description', '')} {video_data.get('summary', '')} {video_data.get('transcript', '')}".lower()
        
        selected = []
        for candidate in self.tag_candidates:
            if candidate.lower() in content and len(selected) < 15:
                selected.append(candidate)
        
        # 10個未満の場合は最低限のタグを追加
        if len(selected) < 10:
            basic_tags = ['マーケティング教育', 'ビジネス研修', video_data.get('skill', '')]
            for tag in basic_tags:
                if tag and tag not in selected and len(selected) < 15:
                    selected.append(tag)
        
        return selected[:15]
    
    def execute_complete_two_phase_processing(self, all_video_data: List[Dict[str, Any]], ai_engine: str = 'openai') -> List[Dict[str, Any]]:
        """
        完全な二段階処理を実行
        
        Args:
            all_video_data: 全動画データのリスト
            ai_engine: 使用するAIエンジン
            
        Returns:
            タグ選定済みの動画データリスト
        """
        print(f"\n{'='*60}")
        print(f"二段階タグ処理システム開始: {len(all_video_data)}件の動画を処理")
        print(f"{'='*60}")
        
        # フェーズ1: 文字起こし以外の全件分析でタグ候補生成
        self.phase1_analyze_all_videos_without_transcript(all_video_data)
        
        if len(self.tag_candidates) == 0:
            print("⚠️ フェーズ1でタグ候補が生成されませんでした")
            return []
        
        # フェーズ2: 個別動画の詳細分析（文字起こし含む）
        results = []
        for i, video in enumerate(all_video_data):
            print(f"\n--- 動画 {i+1}/{len(all_video_data)} を処理中 ---")
            
            selected_tags = self.phase2_individual_analysis_with_transcript(video, ai_engine)
            
            result = video.copy()
            result['selected_tags'] = selected_tags
            result['tag_count'] = len(selected_tags)
            result['processing_method'] = 'two_phase_complete'
            result['phase1_candidates'] = len(self.tag_candidates)
            
            results.append(result)
        
        print(f"\n{'='*60}")
        print(f"二段階処理完了")
        print(f"フェーズ1生成候補: {len(self.tag_candidates)}個")
        print(f"平均選定タグ数: {sum(len(r['selected_tags']) for r in results) / len(results):.1f}個/動画")
        print(f"{'='*60}")
        
        return results