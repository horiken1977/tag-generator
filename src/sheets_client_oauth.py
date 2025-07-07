"""
Google Sheets OAuth認証クライアント
サービスアカウントの代わりにOAuth認証を使用
"""

import os
import json
import re
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests


class SheetsClientOAuth:
    """Google Sheets OAuth認証クライアント"""
    
    def __init__(self):
        """初期化"""
        self.service = None
        self.drive_service = None
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        # OAuth設定（実際の値は環境変数から取得）
        self.client_config = {
            "web": {
                "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8501"]
            }
        }
    
    def get_auth_url(self) -> str:
        """
        OAuth認証URLを生成
        
        Returns:
            認証URL
        """
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri="http://localhost:8501"
            )
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            return auth_url
            
        except Exception as e:
            st.error(f"認証URL生成エラー: {str(e)}")
            return ""
    
    def authenticate_with_code(self, auth_code: str) -> bool:
        """
        認証コードを使用してトークンを取得
        
        Args:
            auth_code: Google認証で取得したコード
            
        Returns:
            認証成功可否
        """
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri="http://localhost:8501"
            )
            
            flow.fetch_token(code=auth_code)
            
            # サービスを初期化
            self.service = build('sheets', 'v4', credentials=flow.credentials)
            self.drive_service = build('drive', 'v3', credentials=flow.credentials)
            
            # セッションに認証情報を保存
            st.session_state.google_credentials = flow.credentials
            
            return True
            
        except Exception as e:
            st.error(f"認証エラー: {str(e)}")
            return False
    
    def authenticate_with_saved_credentials(self) -> bool:
        """
        保存された認証情報を使用
        
        Returns:
            認証成功可否
        """
        try:
            if 'google_credentials' not in st.session_state:
                return False
            
            creds = st.session_state.google_credentials
            
            # トークンが期限切れの場合は更新
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                st.session_state.google_credentials = creds
            
            # サービスを初期化
            self.service = build('sheets', 'v4', credentials=creds)
            self.drive_service = build('drive', 'v3', credentials=creds)
            
            return True
            
        except Exception as e:
            st.error(f"保存済み認証情報の読み込みエラー: {str(e)}")
            return False
    
    def is_authenticated(self) -> bool:
        """
        認証状態をチェック
        
        Returns:
            認証済みかどうか
        """
        return self.service is not None
    
    def extract_spreadsheet_id(self, url: str) -> Optional[str]:
        """
        URLからスプレッドシートIDを抽出
        
        Args:
            url: GoogleスプレッドシートのURL
            
        Returns:
            スプレッドシートID
        """
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def read_spreadsheet(self, url: str, sheet_name: str = None) -> Optional[pd.DataFrame]:
        """
        スプレッドシートを読み込み
        
        Args:
            url: スプレッドシートURL
            sheet_name: シート名（省略時は最初のシート）
            
        Returns:
            データフレーム
        """
        try:
            # 認証チェック
            if not self.is_authenticated():
                if not self.authenticate_with_saved_credentials():
                    st.error("Google認証が必要です")
                    return None
            
            # スプレッドシートIDを抽出
            spreadsheet_id = self.extract_spreadsheet_id(url)
            if not spreadsheet_id:
                st.error("無効なスプレッドシートURLです")
                return None
            
            # シート名が指定されていない場合は最初のシートを取得
            if not sheet_name:
                spreadsheet = self.service.spreadsheets().get(
                    spreadsheetId=spreadsheet_id
                ).execute()
                
                sheets = spreadsheet.get('sheets', [])
                if not sheets:
                    st.error("シートが見つかりません")
                    return None
                
                sheet_name = sheets[0]['properties']['title']
            
            # データを取得
            range_spec = f"'{sheet_name}'"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_spec,
                valueRenderOption='UNFORMATTED_VALUE'
            ).execute()
            
            values = result.get('values', [])
            if not values:
                st.error("データが見つかりません")
                return pd.DataFrame()
            
            # ヘッダー行を取得
            headers = values[0] if values else []
            data_rows = values[1:] if len(values) > 1 else []
            
            # データフレームを作成
            df = pd.DataFrame(data_rows, columns=headers)
            
            # 空の列を削除
            df = df.dropna(axis=1, how='all')
            
            return df
            
        except HttpError as e:
            if e.resp.status == 403:
                st.error("スプレッドシートへのアクセス権限がありません。共有設定を確認してください。")
            else:
                st.error(f"スプレッドシート読み込みエラー: {str(e)}")
            return None
        except Exception as e:
            st.error(f"予期しないエラー: {str(e)}")
            return None
    
    def get_available_sheets(self, url: str) -> List[str]:
        """
        スプレッドシート内の利用可能なシート一覧を取得
        
        Args:
            url: スプレッドシートURL
            
        Returns:
            シート名のリスト
        """
        try:
            if not self.is_authenticated():
                return []
            
            spreadsheet_id = self.extract_spreadsheet_id(url)
            if not spreadsheet_id:
                return []
            
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            return [sheet['properties']['title'] for sheet in sheets]
            
        except Exception as e:
            st.error(f"シート一覧取得エラー: {str(e)}")
            return []
    
    def test_spreadsheet_access(self, url: str) -> bool:
        """
        スプレッドシートへのアクセスをテスト
        
        Args:
            url: スプレッドシートURL
            
        Returns:
            アクセス可能かどうか
        """
        try:
            if not self.is_authenticated():
                return False
            
            spreadsheet_id = self.extract_spreadsheet_id(url)
            if not spreadsheet_id:
                return False
            
            # 基本情報のみ取得してテスト
            self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields='properties.title'
            ).execute()
            
            return True
            
        except Exception:
            return False


def display_oauth_ui():
    """
    OAuth認証UIを表示
    
    Returns:
        認証済みのSheetsClientOAuthインスタンス、または None
    """
    st.subheader("🔐 Google アカウント認証")
    
    # OAuth設定の確認
    if not os.getenv('GOOGLE_CLIENT_ID') or not os.getenv('GOOGLE_CLIENT_SECRET'):
        st.error("Google OAuth設定が不完全です。.envファイルにGOOGLE_CLIENT_IDとGOOGLE_CLIENT_SECRETを設定してください。")
        st.info("""
        **設定方法:**
        1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
        2. プロジェクトを作成または選択
        3. Google Sheets API と Google Drive API を有効化
        4. 認証情報 → OAuth 2.0 クライアント ID を作成
        5. .env ファイルに以下を追加:
        ```
        GOOGLE_CLIENT_ID=your-client-id
        GOOGLE_CLIENT_SECRET=your-client-secret
        ```
        """)
        return None
    
    sheets_client = SheetsClientOAuth()
    
    # 既に認証済みかチェック
    if sheets_client.authenticate_with_saved_credentials():
        st.success("✅ Google アカウント認証済み")
        return sheets_client
    
    # 認証が必要な場合
    st.info("Googleスプレッドシートにアクセスするため、Googleアカウントでの認証が必要です。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔑 Google認証を開始", type="primary"):
            auth_url = sheets_client.get_auth_url()
            if auth_url:
                st.markdown(f"### [こちらをクリックしてGoogle認証]({auth_url})")
                st.info("認証後、表示される認証コードを下記に入力してください。")
    
    with col2:
        auth_code = st.text_input(
            "認証コードを入力",
            placeholder="Google認証で取得したコードを貼り付け",
            help="Google認証ページで表示されるコードをコピーして貼り付けてください"
        )
        
        if auth_code and st.button("認証実行"):
            with st.spinner("認証中..."):
                if sheets_client.authenticate_with_code(auth_code):
                    st.success("✅ 認証成功！")
                    st.rerun()
                else:
                    st.error("❌ 認証に失敗しました。認証コードを確認してください。")
    
    return None