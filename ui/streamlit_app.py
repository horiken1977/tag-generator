"""
Streamlit Web UI for Tag Generator
Googleスプレッドシート動画タグ生成ツール
"""

import streamlit as st
import pandas as pd
import sys
import os
import time
import json
from typing import Dict, List, Any, Optional

# パスを追加してモジュールをインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sheets_client_oauth import SheetsClientOAuth, display_oauth_ui
from batch_processor import BatchProcessor
from tag_optimizer import TagOptimizer


def init_session_state():
    """セッション状態を初期化"""
    if 'spreadsheet_data' not in st.session_state:
        st.session_state.spreadsheet_data = None
    if 'column_mapping' not in st.session_state:
        st.session_state.column_mapping = {}
    if 'processing_results' not in st.session_state:
        st.session_state.processing_results = None
    if 'config' not in st.session_state:
        st.session_state.config = load_config()


def load_config() -> Dict[str, Any]:
    """設定ファイルを読み込み"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"設定ファイル読み込みエラー: {str(e)}")
        return {}


def validate_environment():
    """環境設定の検証"""
    # Google OAuth設定はoptional（アプリ内で認証する）
    oauth_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
    missing_oauth = [var for var in oauth_vars if not os.getenv(var)]
    
    if missing_oauth:
        st.warning(f"Google OAuth設定が不完全です: {', '.join(missing_oauth)}")
        st.info("Google認証を使用する場合は、.envファイルにGOOGLE_CLIENT_IDとGOOGLE_CLIENT_SECRETを設定してください。")
    
    return True


def load_spreadsheet_data(sheets_client: SheetsClientOAuth, url: str, sheet_name: str) -> Optional[pd.DataFrame]:
    """スプレッドシートデータを読み込み"""
    try:
        with st.spinner('スプレッドシートを読み込み中...'):
            data = sheets_client.read_spreadsheet(url, sheet_name)
            return data
    except Exception as e:
        st.error(f"スプレッドシート読み込みエラー: {str(e)}")
        return None


def display_column_mapping_ui(df: pd.DataFrame) -> Dict[str, str]:
    """列マッピングUIを表示"""
    st.subheader("🔧 列マッピング設定")
    st.write("スプレッドシートの列を以下の項目にマッピングしてください：")
    
    columns = [''] + list(df.columns)
    
    mapping = {}
    col1, col2 = st.columns(2)
    
    with col1:
        mapping['title'] = st.selectbox("📝 動画タイトル (必須)", columns, key="title_col")
        mapping['skill'] = st.selectbox("🎯 スキル/カテゴリ", columns, key="skill_col")
        mapping['description'] = st.selectbox("📄 動画説明", columns, key="desc_col")
    
    with col2:
        mapping['summary'] = st.selectbox("📋 要約", columns, key="summary_col")
        mapping['transcript'] = st.selectbox("🎙️ 音声テキスト", columns, key="transcript_col")
    
    # 必須フィールドの検証
    if not mapping['title']:
        st.warning("⚠️ 動画タイトルの列選択は必須です")
        return {}
    
    return {k: v for k, v in mapping.items() if v}


def display_ai_selection() -> str:
    """AI選択UIを表示"""
    st.subheader("🤖 AI プロバイダー選択")
    
    # バッチプロセッサーで接続テスト
    try:
        batch_processor = BatchProcessor()
        connection_status = batch_processor.test_ai_connections()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_icon = "🟢" if connection_status.get('openai', False) else "🔴"
            st.write(f"{status_icon} OpenAI GPT")
        
        with col2:
            status_icon = "🟢" if connection_status.get('claude', False) else "🔴"
            st.write(f"{status_icon} Claude")
        
        with col3:
            status_icon = "🟢" if connection_status.get('gemini', False) else "🔴"
            st.write(f"{status_icon} Google Gemini")
        
        # 利用可能なプロバイダーのみ選択肢に表示
        available_providers = [name for name, status in connection_status.items() if status]
        
        if not available_providers:
            st.error("利用可能なAIプロバイダーがありません。.envファイルのAPIキーを確認してください。")
            return ""
        
        provider_map = {
            'openai': 'OpenAI GPT',
            'claude': 'Claude',
            'gemini': 'Google Gemini'
        }
        
        provider_options = [provider_map[p] for p in available_providers]
        selected_display = st.selectbox("使用するAIプロバイダーを選択してください", provider_options)
        
        # 表示名から内部名に変換
        reverse_map = {v: k for k, v in provider_map.items()}
        return reverse_map[selected_display]
        
    except Exception as e:
        st.error(f"AI接続テストエラー: {str(e)}")
        return ""


def display_processing_settings() -> Dict[str, Any]:
    """処理設定UIを表示"""
    st.subheader("⚙️ 処理設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        batch_size = st.slider(
            "バッチサイズ（一度に処理する動画数）",
            min_value=1,
            max_value=50,
            value=10,
            help="大きくするとメモリ使用量が増加しますが、処理が早くなります"
        )
    
    with col2:
        target_tags = st.slider(
            "目標タグ数",
            min_value=100,
            max_value=300,
            value=175,
            help="最終的に出力するタグの目標数"
        )
    
    return {
        'batch_size': batch_size,
        'target_tag_count': target_tags
    }


def estimate_processing_info(total_videos: int, ai_provider: str, batch_size: int):
    """処理時間・コスト推定を表示"""
    try:
        batch_processor = BatchProcessor()
        
        # 設定を一時的に更新
        batch_processor.batch_size = batch_size
        
        time_estimate = batch_processor.estimate_processing_time(total_videos, ai_provider)
        memory_estimate = batch_processor.get_memory_usage_estimate(total_videos)
        
        st.subheader("📊 処理推定情報")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総処理時間", f"{time_estimate['total_minutes']:.1f}分")
            st.metric("バッチ数", f"{time_estimate['total_batches']}")
        
        with col2:
            st.metric("メモリ使用量", f"{memory_estimate['batch_mb']:.1f}MB")
            memory_safe = "✅ 安全" if memory_estimate['memory_safe'] else "⚠️ 要注意"
            st.metric("メモリ状況", memory_safe)
        
        with col3:
            # 概算コスト（プロバイダー別）
            cost_per_video = {'openai': 0.01, 'claude': 0.015, 'gemini': 0.005}
            estimated_cost = total_videos * cost_per_video.get(ai_provider, 0.01)
            st.metric("推定コスト", f"${estimated_cost:.2f}")
        
        if not memory_estimate['memory_safe']:
            st.warning("⚠️ メモリ使用量が制限を超える可能性があります。バッチサイズを小さくすることを推奨します。")
            
    except Exception as e:
        st.error(f"処理推定エラー: {str(e)}")


def process_videos(
    df: pd.DataFrame,
    ai_provider: str,
    column_mapping: Dict[str, str],
    processing_settings: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """動画処理を実行"""
    
    try:
        # プログレスバーとステータス表示
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress: float, current: int, total: int):
            progress_bar.progress(progress / 100)
            status_text.text(f"処理中: {current}/{total} 動画 ({progress:.1f}%)")
        
        # バッチ処理実行
        status_text.text("バッチ処理を初期化中...")
        batch_processor = BatchProcessor()
        batch_processor.batch_size = processing_settings['batch_size']
        
        status_text.text("AI処理でタグを生成中...")
        all_tags = batch_processor.process_videos_batch(
            df, ai_provider, column_mapping, progress_callback
        )
        
        status_text.text("タグ最適化を実行中...")
        progress_bar.progress(90)
        
        # タグ最適化
        tag_optimizer = TagOptimizer()
        tag_optimizer.target_tag_count = processing_settings['target_tag_count']
        
        final_tags = tag_optimizer.optimize_tags(all_tags, df, column_mapping)
        
        # 分析レポート生成
        analytics = tag_optimizer.generate_tag_analytics(final_tags, all_tags)
        
        progress_bar.progress(100)
        status_text.text("✅ 処理完了!")
        
        return {
            'all_tags': all_tags,
            'final_tags': final_tags,
            'analytics': analytics,
            'processed_data': df
        }
        
    except Exception as e:
        st.error(f"処理エラー: {str(e)}")
        return None


def display_results(results: Dict[str, Any]):
    """結果を表示"""
    st.subheader("📈 処理結果")
    
    analytics = results['analytics']
    
    # 基本統計
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("最終タグ数", analytics['total_final_tags'])
    
    with col2:
        st.metric("元タグ数", analytics['unique_original_tags'])
    
    with col3:
        st.metric("削減率", f"{analytics['reduction_ratio']:.1%}")
    
    with col4:
        st.metric("カバレッジ", f"{analytics['coverage_percentage']:.1f}%")
    
    # 最終タグ表示
    st.subheader("🏷️ 最終タグセット")
    
    # タグを3列で表示
    tags = results['final_tags']
    cols = st.columns(3)
    
    for i, tag in enumerate(tags):
        col_idx = i % 3
        with cols[col_idx]:
            st.write(f"• {tag}")
    
    # ダウンロード用データ準備
    tags_df = pd.DataFrame({'tags': tags})
    csv_data = tags_df.to_csv(index=False, encoding='utf-8-sig')
    
    st.download_button(
        label="📥 タグリストをCSVでダウンロード",
        data=csv_data,
        file_name=f"optimized_tags_{time.strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def save_to_spreadsheet(results: Dict[str, Any], original_url: str) -> Optional[str]:
    """結果をスプレッドシートに保存"""
    try:
        with st.spinner('Googleスプレッドシートに保存中...'):
            sheets_client = SheetsClient()
            
            # 元データにタグ列を追加
            df = results['processed_data'].copy()
            all_tags = results['all_tags']
            
            # 各動画のタグをカンマ区切りに変換
            tag_strings = [', '.join(tags) if tags else '' for tags in all_tags]
            df['generated_tags'] = tag_strings
            
            # 最終タグセットを別シートに
            final_tags_df = pd.DataFrame({'optimized_tags': results['final_tags']})
            
            # 新しいスプレッドシートを作成
            new_url = sheets_client.create_copy_with_tags(original_url, df, final_tags_df)
            
            return new_url
            
    except Exception as e:
        st.error(f"スプレッドシート保存エラー: {str(e)}")
        return None


def main():
    """メイン関数"""
    st.set_page_config(
        page_title="Tag Generator",
        page_icon="🏷️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏷️ 動画タグ生成ツール")
    st.markdown("---")
    
    # セッション状態初期化
    init_session_state()
    
    # 環境設定検証
    if not validate_environment():
        st.stop()
    
    # Google OAuth認証
    sheets_client = display_oauth_ui()
    
    # サイドバー
    with st.sidebar:
        st.header("📋 処理ステップ")
        st.write("0. Google認証")
        st.write("1. スプレッドシート読み込み")
        st.write("2. 列マッピング設定")
        st.write("3. AI・処理設定")
        st.write("4. タグ生成実行")
        st.write("5. 結果確認・保存")
    
    # Google認証が完了している場合のみ処理を続行
    if sheets_client is None:
        st.info("まずGoogle認証を完了してください。")
        st.stop()
    
    # Step 1: スプレッドシート読み込み
    st.header("1️⃣ スプレッドシート読み込み")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        spreadsheet_url = st.text_input(
            "GoogleスプレッドシートのURL",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="認証済みのGoogleアカウントでアクセス可能なスプレッドシートのURL"
        )
    
    with col2:
        # スプレッドシートURLが入力された場合、利用可能なシート一覧を取得
        if spreadsheet_url:
            available_sheets = sheets_client.get_available_sheets(spreadsheet_url)
            if available_sheets:
                sheet_name = st.selectbox("シート選択", available_sheets)
            else:
                sheet_name = st.text_input("シート名", value="Sheet1")
        else:
            sheet_name = st.text_input("シート名", value="Sheet1")
    
    if st.button("📊 スプレッドシート読み込み", type="primary"):
        if spreadsheet_url:
            data = load_spreadsheet_data(sheets_client, spreadsheet_url, sheet_name)
            if data is not None:
                st.session_state.spreadsheet_data = data
                st.success(f"✅ {len(data)}行のデータを読み込みました")
        else:
            st.warning("スプレッドシートのURLを入力してください")
    
    # データプレビュー
    if st.session_state.spreadsheet_data is not None:
        st.subheader("📄 データプレビュー")
        st.dataframe(st.session_state.spreadsheet_data.head(), use_container_width=True)
        
        # Step 2: 列マッピング設定
        st.header("2️⃣ 列マッピング設定")
        column_mapping = display_column_mapping_ui(st.session_state.spreadsheet_data)
        
        if column_mapping:
            st.session_state.column_mapping = column_mapping
            
            # Step 3: AI・処理設定
            st.header("3️⃣ AI・処理設定")
            
            ai_provider = display_ai_selection()
            
            if ai_provider:
                processing_settings = display_processing_settings()
                
                # 処理推定情報
                total_videos = len(st.session_state.spreadsheet_data)
                estimate_processing_info(total_videos, ai_provider, processing_settings['batch_size'])
                
                # Step 4: 処理実行
                st.header("4️⃣ タグ生成実行")
                
                if st.button("🚀 タグ生成開始", type="primary", use_container_width=True):
                    results = process_videos(
                        st.session_state.spreadsheet_data,
                        ai_provider,
                        column_mapping,
                        processing_settings
                    )
                    
                    if results:
                        st.session_state.processing_results = results
                        st.success("🎉 タグ生成が完了しました！")
    
    # Step 5: 結果表示・保存
    if st.session_state.processing_results is not None:
        st.header("5️⃣ 結果確認・保存")
        
        display_results(st.session_state.processing_results)
        
        # スプレッドシート保存
        st.subheader("💾 Googleスプレッドシートに保存")
        
        if st.button("📤 新しいスプレッドシートとして保存", type="secondary"):
            new_url = save_to_spreadsheet(st.session_state.processing_results, spreadsheet_url)
            if new_url:
                st.success("✅ 保存完了!")
                st.markdown(f"**新しいスプレッドシート:** [こちらをクリック]({new_url})")


if __name__ == "__main__":
    main()