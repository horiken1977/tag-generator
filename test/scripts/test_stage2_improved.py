#!/usr/bin/env python3
"""
改良版Stage2プロンプトの動作テストスクリプト
"""

import json
import sys
import os
from typing import List, Dict, Any

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from staged_tag_processor import StagedTagProcessor
from ai_api_handler import AIAPIHandler

def create_test_video_data() -> List[Dict[str, Any]]:
    """テスト用の動画データを作成"""
    return [
        {
            'title': '効果的なプレゼンテーション技法',
            'skill': 'コミュニケーション',
            'description': '聴衆を惹きつけるプレゼンテーション技法を学ぶ',
            'summary': 'プレゼンテーションの基本構成と効果的な伝達方法について解説',
            'transcript': 'プレゼンテーションにおいて最も重要なのは、聴衆との信頼関係の構築です。まず、オープニングで注意を惹きつけ、明確な構成を示すことが大切です。ボディパートでは論理的な流れを保ち、具体的な事例やデータを活用して説得力を高めます。視覚的資料は補助として使用し、アイコンタクトと身振り手振りで聴衆と繋がります。質疑応答では冷静に対応し、分からない場合は正直に伝えることも重要です。'
        },
        {
            'title': 'デジタルマーケティング基礎',
            'skill': 'マーケティング',
            'description': 'SEOとSNS活用による効果的なデジタルマーケティング戦略',
            'summary': 'デジタル時代のマーケティング手法と実践方法を学習',
            'transcript': 'デジタルマーケティングの核心は顧客との接点を最大化することです。Google Analytics を使用してユーザー行動を分析し、SEO対策でオーガニック検索からの流入を増やします。Facebook 広告やInstagram 広告を活用したペイドメディア戦略も重要です。コンバージョン率を向上させるためにA/Bテストを実施し、LTV（顧客生涯価値）を最大化するリテンション施策を展開します。ROI計算による効果測定も欠かせません。'
        },
        {
            'title': 'Excel関数とピボットテーブル活用術',
            'skill': 'データ分析',
            'description': 'VLOOKUP、SUMIFS等の高度なExcel関数とピボットテーブルの実践的活用法',
            'summary': '業務効率化のためのExcel関数とピボットテーブルをマスター',
            'transcript': 'Excelの関数を使いこなすことで業務効率が大幅に向上します。VLOOKUP関数は別シートからデータを検索する際に使用し、SUMIFS関数は複数条件での集計に活用します。INDEX関数とMATCH関数を組み合わせることで、より柔軟な検索が可能になります。ピボットテーブルは大量データの集計と分析に威力を発揮し、スライサーを使用することで動的なフィルタリングが実現できます。Power Query を使用すれば外部データとの連携も可能です。'
        },
        {
            'title': 'Salesforce CRM導入と運用最適化',
            'skill': 'CRM管理',
            'description': 'Salesforce の基本設定から高度なカスタマイズまでの包括的導入ガイド',
            'summary': 'Salesforce CRMシステムの効果的な導入と運用方法を習得',
            'transcript': 'Salesforce CRMの導入では、まず組織の営業プロセスを整理することから始めます。リードの取り込みから商談の進捗管理、顧客のライフサイクル管理まで一元化します。カスタムオブジェクトを作成して独自のデータ構造を構築し、ワークフローを設定して業務の自動化を実現します。Salesforce Einstein を活用した予測分析機能により、営業の成約確率や顧客のチャーン予測が可能になります。APIを使用して他システムとの連携も重要です。'
        },
        {
            'title': 'Google Analytics 4とGoogle Tag Manager設定',
            'skill': 'Webアナリティクス',
            'description': 'GA4の新機能と GTM を使用したイベント トラッキングの実装方法',
            'summary': 'Google Analytics 4 とタグマネージャーを使用したウェブ解析の実践',
            'transcript': 'Google Analytics 4では従来のページビューベースからイベントベースの計測に変更されました。Google Tag Manager を使用してカスタムイベントを設定し、ユーザーの行動を詳細に追跡します。コンバージョンイベントの設定により、ゴール達成の測定が可能になります。Enhanced Ecommerce機能では購入ファネルの分析ができ、カスタムディメンションで独自の分析軸を追加できます。BigQuery との連携により大量データの高度な分析も実現します。データスタジオでの可視化も重要な要素です。'
        }
    ]

def create_sample_approved_candidates() -> List[str]:
    """サンプルの承認済みタグ候補を作成"""
    return [
        # 具体的なツール・サービス名
        'Google Analytics', 'Google Analytics 4', 'Google Tag Manager', 'BigQuery',
        'Salesforce', 'Salesforce CRM', 'Salesforce Einstein',
        'Facebook広告', 'Instagram広告', 'Excel関数', 'VLOOKUP関数',
        'SUMIFS関数', 'INDEX関数', 'MATCH関数', 'ピボットテーブル', 'Power Query',
        
        # 測定可能な指標・KPI
        'コンバージョン率', 'LTV', 'ROI計算', 'A/Bテスト', 'チャーン予測',
        '成約確率', 'カスタムディメンション', 'Enhanced Ecommerce',
        
        # 具体的な手法・プロセス
        'SEO対策', 'リテンション施策', 'ワークフロー設定', 'API連携',
        'イベントトラッキング', 'カスタムオブジェクト', 'データスタジオ可視化',
        
        # 専門的な概念（但し具体的）
        'オーガニック検索', 'ペイドメディア戦略', '顧客ライフサイクル管理',
        'リード管理', '商談進捗管理', 'カスタムイベント設定',
        
        # 汎用的だが避けるべきタグ（比較用）
        'ビジネススキル', 'マーケティング', 'コミュニケーション', 'プレゼンテーション',
        'データ分析', 'CRM管理', 'Webアナリティクス', '営業', '効率化', '最適化'
    ]

def print_test_results(results: Dict[str, Any]) -> None:
    """テスト結果を整理して表示"""
    print(f"\n{'='*80}")
    print(f"改良版Stage2プロンプト テスト結果")
    print(f"{'='*80}")
    
    if not results.get('success'):
        print(f"❌ テスト失敗: {results.get('error', 'Unknown error')}")
        return
    
    test_results = results.get('results', [])
    statistics = results.get('statistics', {})
    
    print(f"📊 統計情報:")
    print(f"  • 処理動画数: {statistics.get('total_videos', 0)}件")
    print(f"  • 平均タグ数: {statistics.get('avg_tags_per_video', 0):.1f}個/動画")
    print(f"  • 総タグ数: {statistics.get('total_tags_assigned', 0)}個")
    print(f"  • 処理時間: {statistics.get('processing_time', 0):.2f}秒")
    
    print(f"\n🎯 個別動画結果:")
    for i, result in enumerate(test_results):
        title = result.get('title', 'Unknown')[:40]
        tags = result.get('selected_tags', [])
        confidence = result.get('confidence', 0)
        
        print(f"\n  【動画 {i+1}】 {title}")
        print(f"  信頼度: {confidence}")
        print(f"  タグ数: {len(tags)}個")
        print(f"  選定タグ: {', '.join(tags[:8])}{'...' if len(tags) > 8 else ''}")
        
        # 汎用タグをチェック
        generic_tags = ['ビジネススキル', 'マーケティング', 'コミュニケーション', 
                       'プレゼンテーション', 'データ分析', 'CRM管理', 'Webアナリティクス']
        found_generic = [tag for tag in tags if tag in generic_tags]
        if found_generic:
            print(f"  ⚠️ 汎用タグ検出: {', '.join(found_generic)}")
        else:
            print(f"  ✅ 汎用タグ回避成功")

def main():
    """メイン実行関数"""
    print("改良版Stage2プロンプトの動作テストを開始します...\n")
    
    # テストデータを準備
    test_videos = create_test_video_data()
    approved_candidates = create_sample_approved_candidates()
    
    print(f"テスト対象:")
    print(f"  • 動画データ: {len(test_videos)}件")
    print(f"  • 承認済みタグ候補: {len(approved_candidates)}個")
    
    # AIハンドラーとプロセッサーを初期化
    try:
        ai_handler = AIAPIHandler()
        processor = StagedTagProcessor(ai_handler)
        
        # Stage2テストを実行
        print(f"\n🚀 Stage2個別タグ付けテストを実行中...")
        results = processor.execute_stage2_individual_tagging(
            test_videos, 
            approved_candidates, 
            ai_engine='claude'
        )
        
        # 結果を表示
        print_test_results(results)
        
        # 結果をJSONファイルに保存
        output_file = 'stage2_test_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 詳細結果を {output_file} に保存しました")
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()