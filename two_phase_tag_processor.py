#!/usr/bin/env python3
"""
Two-Phase Tag Processing System
Phase 1: Analyze all data (except transcripts) to create tag candidates
Phase 2: Individual video analysis with transcript for final tag selection
"""

import json
import logging
from typing import List, Dict, Any, Set
from collections import Counter
import re

class TwoPhaseTagProcessor:
    """Two-phase tag processing system as requested by user"""
    
    def __init__(self, ai_handler=None):
        self.ai_handler = ai_handler
        self.logger = logging.getLogger(__name__)
        self.tag_candidates = set()
        self.analyzed_content = {}
        
    def phase1_analyze_all_data(self, all_video_data: List[Dict[str, Any]]) -> Set[str]:
        """
        Phase 1: Analyze all videos (without transcripts) to create tag candidates
        
        Args:
            all_video_data: List of all video data dictionaries
            
        Returns:
            Set of candidate tags extracted from all data
        """
        print(f"=== PHASE 1: Analyzing {len(all_video_data)} videos (excluding transcripts) ===")
        
        # Collect all non-transcript content
        all_titles = []
        all_skills = []
        all_descriptions = []
        all_summaries = []
        
        for video in all_video_data:
            title = video.get('title', '').strip()
            skill = video.get('skill', '').strip()
            description = video.get('description', '').strip()
            summary = video.get('summary', '').strip()
            
            if title:
                all_titles.append(title)
            if skill:
                all_skills.append(skill)
            if description:
                all_descriptions.append(description)
            if summary:
                all_summaries.append(summary)
        
        # Analyze combined content to extract tag candidates
        combined_content = {
            'titles': ' '.join(all_titles),
            'skills': ' '.join(all_skills),
            'descriptions': ' '.join(all_descriptions),
            'summaries': ' '.join(all_summaries)
        }
        
        print(f"Phase 1 - Collected content:")
        print(f"  Titles: {len(all_titles)} items")
        print(f"  Skills: {len(all_skills)} items")
        print(f"  Descriptions: {len(all_descriptions)} items")
        print(f"  Summaries: {len(all_summaries)} items")
        
        # Extract tag candidates using AI analysis
        tag_candidates = self._extract_tag_candidates(combined_content)
        
        self.tag_candidates = set(tag_candidates)
        print(f"Phase 1 - Generated {len(self.tag_candidates)} tag candidates")
        print(f"Tag candidates: {sorted(list(self.tag_candidates))[:20]}...")  # Show first 20
        
        return self.tag_candidates
    
    def _extract_tag_candidates(self, combined_content: Dict[str, str]) -> List[str]:
        """Extract tag candidates from combined content using AI"""
        
        # Create a comprehensive prompt for tag candidate extraction
        prompt = f"""
以下の動画データ全体を分析して、タグ候補となる重要なキーワードを抽出してください。
これらは後で個別動画の詳細分析で使用される候補タグです。

全動画のタイトル: {combined_content['titles']}

全動画のスキル: {combined_content['skills']}

全動画の説明文: {combined_content['descriptions']}

全動画の要約: {combined_content['summaries']}

【タグ候補抽出の基準】:
1. 頻出する専門用語やビジネス用語
2. 具体的なツール名・サービス名・手法名
3. 業界固有の概念や理論
4. 測定可能な指標名
5. 具体的なプロセス名や手順名

【絶対に避ける】:
- 汎用的すぎる単語（「要素」「分類」「ポイント」「手法」等）
- 数字を含む汎用表現（「6つの要素」等）
- 抽象的なレベル表現（「基本」「応用」等）

出力: 具体的で有用なタグ候補のみをカンマ区切りで出力してください。
"""
        
        if self.ai_handler:
            try:
                candidates = self.ai_handler.call_openai(prompt)
                if candidates:
                    return candidates
            except Exception as e:
                print(f"AI analysis failed, using fallback: {e}")
        
        # Fallback: extract keywords using simple text analysis
        return self._extract_keywords_fallback(combined_content)
    
    def _extract_keywords_fallback(self, combined_content: Dict[str, str]) -> List[str]:
        """Fallback method to extract keywords without AI"""
        keywords = set()
        
        # Extract from all content
        for content_type, content in combined_content.items():
            # Split into words and filter
            words = re.findall(r'\b[A-Za-zａ-ｚＡ-Ｚ\u3041-\u3096\u30a1-\u30f6\u4e00-\u9faf]+\b', content)
            
            for word in words:
                word = word.strip()
                if len(word) > 2 and not self._is_generic_word(word):
                    keywords.add(word)
        
        return list(keywords)[:100]  # Limit candidates
    
    def _is_generic_word(self, word: str) -> bool:
        """Check if a word is too generic to be useful as a tag"""
        generic_words = {
            '要素', '分類', 'ポイント', '手法', '方法', '技術', '基本', '応用', 
            '実践', '理論', '概要', '入門', '初級', '中級', '上級', '基礎',
            '発展', '活用', 'について', 'による', 'ための', 'とは', 'です'
        }
        return word in generic_words or len(word) < 2
    
    def phase2_individual_analysis(self, video_data: Dict[str, Any], ai_engine: str = 'openai') -> List[str]:
        """
        Phase 2: Analyze individual video with transcript to select optimal tags
        
        Args:
            video_data: Single video data including transcript
            ai_engine: AI engine to use
            
        Returns:
            List of 10-15 optimal tags for this video
        """
        title = video_data.get('title', '')
        print(f"\n=== PHASE 2: Individual analysis for '{title[:50]}...' ===")
        
        # Create detailed prompt for individual video analysis
        prompt = self._create_individual_analysis_prompt(video_data)
        
        if self.ai_handler:
            try:
                selected_tags = self.ai_handler.generate_tags_from_candidates(
                    video_data, list(self.tag_candidates), ai_engine
                )
                if selected_tags:
                    print(f"Phase 2 - Selected {len(selected_tags)} tags from {len(self.tag_candidates)} candidates")
                    return selected_tags[:15]  # Limit to 15 tags
            except Exception as e:
                print(f"AI individual analysis failed, using fallback: {e}")
        
        # Fallback: select relevant candidates based on content similarity
        return self._select_tags_fallback(video_data)
    
    def _create_individual_analysis_prompt(self, video_data: Dict[str, Any]) -> str:
        """Create prompt for individual video analysis"""
        transcript = video_data.get('transcript', '')
        transcript_excerpt = transcript[:2000] if transcript else ''  # More content for analysis
        
        candidates_str = ', '.join(sorted(list(self.tag_candidates)))
        
        return f"""
以下の個別動画について、提供されたタグ候補から最も適切なタグを10-15個選択してください。

動画情報:
タイトル: {video_data.get('title', '')}
スキル名: {video_data.get('skill', '')}
説明文: {video_data.get('description', '')}
要約: {video_data.get('summary', '')}
文字起こし（重要）: {transcript_excerpt}

利用可能なタグ候補:
{candidates_str}

【選択基準】:
1. 文字起こし内容に直接関連するタグを最優先
2. この動画の具体的な内容を最も正確に表現するタグ
3. 検索時に有用で具体性の高いタグ
4. 他の類似動画との差別化に役立つタグ

【出力形式】:
選択したタグのみをカンマ区切りで出力してください。新しいタグは作成せず、候補からのみ選択してください。
"""
    
    def _select_tags_fallback(self, video_data: Dict[str, Any]) -> List[str]:
        """Fallback method to select tags without AI"""
        # Simple content-based matching
        content = f"{video_data.get('title', '')} {video_data.get('skill', '')} {video_data.get('description', '')} {video_data.get('summary', '')} {video_data.get('transcript', '')}".lower()
        
        selected = []
        for candidate in self.tag_candidates:
            if candidate.lower() in content and len(selected) < 15:
                selected.append(candidate)
        
        return selected
    
    def process_all_videos(self, all_video_data: List[Dict[str, Any]], ai_engine: str = 'openai') -> List[Dict[str, Any]]:
        """
        Complete two-phase processing for all videos
        
        Args:
            all_video_data: List of all video data
            ai_engine: AI engine to use
            
        Returns:
            List of processed video data with selected tags
        """
        print(f"Starting two-phase tag processing for {len(all_video_data)} videos")
        
        # Phase 1: Analyze all data to create tag candidates
        self.phase1_analyze_all_data(all_video_data)
        
        # Phase 2: Individual video analysis
        results = []
        for i, video in enumerate(all_video_data):
            print(f"\nProcessing video {i+1}/{len(all_video_data)}")
            
            selected_tags = self.phase2_individual_analysis(video, ai_engine)
            
            result = video.copy()
            result['selected_tags'] = selected_tags
            result['tag_count'] = len(selected_tags)
            result['processing_method'] = 'two_phase'
            
            results.append(result)
        
        print(f"\n=== Two-phase processing completed ===")
        print(f"Total tag candidates generated: {len(self.tag_candidates)}")
        print(f"Average tags per video: {sum(len(r['selected_tags']) for r in results) / len(results):.1f}")
        
        return results