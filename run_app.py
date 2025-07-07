#!/usr/bin/env python3
"""
Tag Generator Application Launcher
さくらインターネット本番環境用のランチャースクリプト
"""

import sys
import os
import subprocess
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_requirements():
    """必要な環境変数とパッケージをチェック"""
    logger.info("環境チェックを開始...")
    
    # 必要な環境変数
    required_env_vars = [
        'GOOGLE_PROJECT_ID',
        'GOOGLE_CLIENT_EMAIL', 
        'GOOGLE_PRIVATE_KEY'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        logger.info("さくらインターネットサーバーの.envファイルに必要なAPIキーを設定してください。")
        return False
    
    # Streamlitがインストールされているかチェック
    try:
        import streamlit
        logger.info(f"Streamlit バージョン: {streamlit.__version__}")
    except ImportError:
        logger.error("Streamlitがインストールされていません。requirements.txtからインストールしてください。")
        return False
    
    # 他の主要パッケージのチェック
    try:
        import pandas
        import google.auth
        import openai
        import anthropic
        logger.info("必要なパッケージがすべてインストールされています。")
    except ImportError as e:
        logger.error(f"必要なパッケージがインストールされていません: {str(e)}")
        return False
    
    logger.info("✅ 環境チェック完了")
    return True


def run_streamlit_app():
    """Streamlitアプリケーションを起動"""
    logger.info("Streamlitアプリケーションを起動中...")
    
    # Streamlitアプリのパス
    app_path = os.path.join(os.path.dirname(__file__), 'ui', 'streamlit_app.py')
    
    if not os.path.exists(app_path):
        logger.error(f"アプリケーションファイルが見つかりません: {app_path}")
        return False
    
    try:
        # Streamlitを起動
        cmd = [
            sys.executable, '-m', 'streamlit', 'run', app_path,
            '--server.port=8501',
            '--server.address=0.0.0.0',
            '--browser.gatherUsageStats=false'
        ]
        
        logger.info("アプリケーションを起動しています...")
        logger.info("ブラウザで http://localhost:8501 にアクセスしてください")
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        logger.info("アプリケーションを停止しました。")
    except Exception as e:
        logger.error(f"アプリケーション起動エラー: {str(e)}")
        return False
    
    return True


def main():
    """メイン処理"""
    print("=" * 60)
    print("🏷️  Video Tag Generator Application")
    print("   動画タグ生成ツール - Streamlit版")
    print("=" * 60)
    print()
    
    # 環境チェック
    if not check_requirements():
        print("\n❌ 環境設定に問題があります。上記のエラーを修正してから再実行してください。")
        sys.exit(1)
    
    print("\n🚀 アプリケーションを起動します...")
    print("   ブラウザで http://localhost:8501 にアクセスしてください")
    print("   停止するには Ctrl+C を押してください")
    print()
    
    # アプリケーション起動
    if not run_streamlit_app():
        print("\n❌ アプリケーションの起動に失敗しました。")
        sys.exit(1)


if __name__ == "__main__":
    main()