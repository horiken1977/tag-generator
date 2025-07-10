#!/usr/bin/env python3
"""
二段階タグ処理システムのテスト
「4つのポイント」等の汎用タグが完全に除外されることを確認
"""

import sys
sys.path.append('.')

from two_phase_tag_processor import TwoPhaseTagProcessor

def test_generic_tag_filtering():
    """汎用タグフィルタリングのテスト"""
    print("=== 汎用タグフィルタリングテスト ===")
    
    processor = TwoPhaseTagProcessor(None)  # AI handler無しでテスト
    
    # 問題のある汎用タグのテストセット
    test_tags = [
        '4つのポイント', '6つの要素', '8つの分類', '10の要素',
        '3つの手法', '5つのステップ', '7つの方法', '9つの観点',
        '12個の分類', '15個の要素',
        # 有効なタグも含める
        'マーケティング', 'Google Analytics', 'PDCAサイクル', 'ROI', 'Instagram'
    ]
    
    print(f"入力タグ: {test_tags}")
    
    filtered_tags = processor._filter_generic_tags(test_tags)
    print(f"フィルター後: {filtered_tags}")
    
    # 汎用タグが残っているかチェック
    problematic_tags = []
    for tag in filtered_tags:
        if any(char.isdigit() for char in tag) and ('つの' in tag or '個の' in tag or 'の' in tag):
            problematic_tags.append(tag)
    
    if problematic_tags:
        print(f"❌ 問題のある汎用タグが残っています: {problematic_tags}")
        return False
    else:
        print("✅ 汎用タグが正しくフィルターされました")
        return True

def test_two_phase_processing():
    """二段階処理のテスト"""
    print("\n=== 二段階処理テスト ===")
    
    # テスト用の動画データ
    test_videos = [
        {
            'title': 'マーケティング指標と財務指標を結びつけるPDCA〜財務諸表を理解する〜',
            'skill': 'マーケティング',
            'description': 'ROIとCPAを使った効果測定',
            'summary': 'Googleアナリティクスを活用した分析手法',
            'transcript': 'まず最初に、Google Analyticsでユーザー行動を分析します。CPAが150円、ROIが300%という結果が出ています。次にInstagramでのエンゲージメント率を見てみましょう。'
        },
        {
            'title': 'デジタルマーケティングの基礎',
            'skill': 'マーケティング',
            'description': 'SNSを活用したマーケティング戦略',
            'summary': 'Facebook広告とInstagram広告の比較',
            'transcript': 'Facebook広告では、ターゲティング精度が重要です。年齢層は25-34歳、興味関心はビジネス書籍とした場合のCTRは2.3%でした。一方、Instagram広告では同条件でCTRが3.1%と高い結果を示しています。'
        }
    ]
    
    processor = TwoPhaseTagProcessor(None)  # AI handler無しでテスト
    
    try:
        # フェーズ1: 文字起こし以外の分析
        print("フェーズ1実行中...")
        tag_candidates = processor.phase1_analyze_all_videos_without_transcript(test_videos)
        print(f"タグ候補生成数: {len(tag_candidates)}")
        
        # フェーズ2: 個別分析
        print("フェーズ2実行中...")
        results = []
        for video in test_videos:
            selected_tags = processor.phase2_individual_analysis_with_transcript(video)
            results.append({
                'title': video['title'][:30] + '...',
                'selected_tags': selected_tags,
                'tag_count': len(selected_tags)
            })
        
        # 結果確認
        print("\n=== 結果 ===")
        for result in results:
            print(f"動画: {result['title']}")
            print(f"選定タグ数: {result['tag_count']}")
            print(f"タグ: {result['selected_tags']}")
            
            # 汎用タグチェック
            problematic = [tag for tag in result['selected_tags'] 
                          if any(char.isdigit() for char in tag) and ('つの' in tag or '個の' in tag or 'ポイント' in tag)]
            if problematic:
                print(f"❌ 汎用タグが含まれています: {problematic}")
                return False
            print()
        
        print("✅ 二段階処理が正常に動作しました")
        return True
        
    except Exception as e:
        print(f"❌ 二段階処理でエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("二段階タグ処理システム - 完全テスト")
    print("=" * 50)
    
    # テスト実行
    filter_test_passed = test_generic_tag_filtering()
    processing_test_passed = test_two_phase_processing()
    
    print("\n" + "=" * 50)
    print("テスト結果:")
    print(f"汎用タグフィルタリング: {'✅ PASS' if filter_test_passed else '❌ FAIL'}")
    print(f"二段階処理: {'✅ PASS' if processing_test_passed else '❌ FAIL'}")
    
    if filter_test_passed and processing_test_passed:
        print("\n🎉 全テストが成功しました！")
        print("「4つのポイント」等の汎用タグは完全に除外されます。")
    else:
        print("\n⚠️ テストに失敗しました。修正が必要です。")

if __name__ == '__main__':
    main()