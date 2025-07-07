"""
Google Sheets API連携モジュール
スプレッドシートの読み込み、コピー、書き込み機能を提供
"""

import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st

# .envファイルを読み込み
load_dotenv()


class SheetsClient:
    """Google Sheets API クライアント"""
    
    def __init__(self, config_path: str = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path or "config/settings.json"
        self.service = None
        self.drive_service = None
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
    def authenticate(self) -> bool:
        """
        Google API認証（.envファイルから認証情報を取得）
        
        Returns:
            認証成功可否
        """
        try:
            creds = None
            
            # .envファイルからサービスアカウント情報を取得
            service_account_info = {
                "type": "service_account",
                "project_id": os.getenv('GOOGLE_PROJECT_ID'),
                "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
                "private_key": os.getenv('GOOGLE_PRIVATE_KEY', '').replace('\\n', '\n'),
                "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
                "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv('GOOGLE_CLIENT_X509_CERT_URL')
            }
            
            # 必須フィールドをチェック
            required_fields = ['project_id', 'private_key', 'client_email']
            if all(service_account_info.get(field) for field in required_fields):
                creds = ServiceCredentials.from_service_account_info(
                    service_account_info, scopes=self.scopes
                )
            else:
                # ファイルパスから読み込みを試行
                service_account_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
                if service_account_path and os.path.exists(service_account_path):
                    creds = ServiceCredentials.from_service_account_file(
                        service_account_path, scopes=self.scopes
                    )
            
            if creds:
                self.service = build('sheets', 'v4', credentials=creds)
                self.drive_service = build('drive', 'v3', credentials=creds)
                return True
            else:
                st.error("Google認証情報が設定されていません。.envファイルを確認してください。")
                return False
                
        except Exception as e:
            st.error(f"Google認証エラー: {str(e)}")
            return False
    
    def extract_spreadsheet_id(self, url: str) -> Optional[str]:
        """
        スプレッドシートURLからIDを抽出
        
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
    
    def get_spreadsheet_info(self, spreadsheet_id: str) -> Optional[Dict]:
        """
        スプレッドシート情報を取得
        
        Args:
            spreadsheet_id: スプレッドシートID
            
        Returns:
            スプレッドシート情報
        """
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            return {
                'title': spreadsheet.get('properties', {}).get('title', 'Unknown'),
                'sheets': [
                    {
                        'title': sheet['properties']['title'],
                        'id': sheet['properties']['sheetId'],
                        'grid_properties': sheet['properties'].get('gridProperties', {})
                    }
                    for sheet in spreadsheet.get('sheets', [])
                ]
            }
        except HttpError as e:
            st.error(f"スプレッドシート情報取得エラー: {str(e)}")
            return None
    
    def get_sheet_data(self, spreadsheet_id: str, sheet_name: str, 
                      range_name: str = None) -> Optional[pd.DataFrame]:
        """
        シートデータを取得
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            range_name: 範囲指定（例: 'A1:Z1000'）
            
        Returns:
            データフレーム
        """
        try:
            if range_name:
                range_spec = f"'{sheet_name}'!{range_name}"
            else:
                range_spec = f"'{sheet_name}'"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_spec,
                valueRenderOption='UNFORMATTED_VALUE'
            ).execute()
            
            values = result.get('values', [])
            if not values:
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
            st.error(f"シートデータ取得エラー: {str(e)}")
            return None
    
    def get_column_headers(self, spreadsheet_id: str, sheet_name: str) -> List[str]:
        """
        列ヘッダーを取得
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            
        Returns:
            列ヘッダーのリスト
        """
        try:
            range_spec = f"'{sheet_name}'!1:1"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_spec
            ).execute()
            
            values = result.get('values', [])
            return values[0] if values else []
            
        except HttpError as e:
            st.error(f"列ヘッダー取得エラー: {str(e)}")
            return []
    
    def copy_spreadsheet(self, source_id: str, new_title: str) -> Optional[str]:
        """
        スプレッドシートをコピー
        
        Args:
            source_id: コピー元スプレッドシートID
            new_title: 新しいタイトル
            
        Returns:
            コピー先スプレッドシートID
        """
        try:
            # ファイルをコピー
            copy_request = {
                'name': new_title
            }
            
            copied_file = self.drive_service.files().copy(
                fileId=source_id,
                body=copy_request
            ).execute()
            
            return copied_file.get('id')
            
        except HttpError as e:
            st.error(f"スプレッドシートコピーエラー: {str(e)}")
            return None
    
    def add_tags_column(self, spreadsheet_id: str, sheet_name: str, 
                       column_name: str = "Generated_Tags") -> bool:
        """
        タグ列を追加
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            column_name: 追加する列名
            
        Returns:
            成功可否
        """
        try:
            # 現在の列ヘッダーを取得
            headers = self.get_column_headers(spreadsheet_id, sheet_name)
            
            if column_name not in headers:
                # 新しい列ヘッダーを追加
                new_column_index = len(headers)
                range_spec = f"'{sheet_name}'!{chr(65 + new_column_index)}1"
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_spec,
                    valueInputOption='RAW',
                    body={'values': [[column_name]]}
                ).execute()
                
            return True
            
        except HttpError as e:
            st.error(f"列追加エラー: {str(e)}")
            return False
    
    def write_tags(self, spreadsheet_id: str, sheet_name: str, 
                  tags_data: List[List[str]], start_row: int = 2,
                  column_name: str = "Generated_Tags") -> bool:
        """
        タグデータを書き込み
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            tags_data: タグデータのリスト
            start_row: 開始行（1ベース）
            column_name: タグ列名
            
        Returns:
            成功可否
        """
        try:
            # 列ヘッダーを取得して、タグ列のインデックスを特定
            headers = self.get_column_headers(spreadsheet_id, sheet_name)
            
            try:
                column_index = headers.index(column_name)
            except ValueError:
                st.error(f"列 '{column_name}' が見つかりません")
                return False
            
            # 範囲を指定してデータを書き込み
            column_letter = chr(65 + column_index)  # A, B, C...
            end_row = start_row + len(tags_data) - 1
            range_spec = f"'{sheet_name}'!{column_letter}{start_row}:{column_letter}{end_row}"
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_spec,
                valueInputOption='RAW',
                body={'values': tags_data}
            ).execute()
            
            return True
            
        except HttpError as e:
            st.error(f"タグ書き込みエラー: {str(e)}")
            return False
    
    def get_spreadsheet_url(self, spreadsheet_id: str) -> str:
        """
        スプレッドシートのURLを生成
        
        Args:
            spreadsheet_id: スプレッドシートID
            
        Returns:
            スプレッドシートURL
        """
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    
    def create_copy_with_tags(self, original_url: str, 
                             video_data_with_tags: pd.DataFrame, 
                             final_tags_df: pd.DataFrame) -> Optional[str]:
        """
        タグ付きデータで新しいスプレッドシートを作成
        
        Args:
            original_url: 元のスプレッドシートURL
            video_data_with_tags: タグ列を含む動画データ
            final_tags_df: 最終タグセットのデータフレーム
            
        Returns:
            新しいスプレッドシートのURL
        """
        try:
            # 認証確認
            if not self.authenticate():
                return None
            
            # 元のスプレッドシートIDを取得
            original_id = self.extract_spreadsheet_id(original_url)
            if not original_id:
                st.error("無効なスプレッドシートURLです")
                return None
            
            # タイムスタンプ付きの新しいタイトル
            import time
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            new_title = f"Video_Tags_Generated_{timestamp}"
            
            # スプレッドシートをコピー
            new_id = self.copy_spreadsheet(original_id, new_title)
            if not new_id:
                return None
            
            # メインシートにタグデータを書き込み
            main_sheet_name = "Sheet1"  # デフォルト、実際のシート名を取得したい場合は改良
            
            # まず元データを全て書き込み
            self._write_dataframe_to_sheet(new_id, main_sheet_name, video_data_with_tags)
            
            # 最終タグセット用の新しいシートを作成
            self._create_new_sheet(new_id, "Optimized_Tags")
            self._write_dataframe_to_sheet(new_id, "Optimized_Tags", final_tags_df)
            
            # 新しいスプレッドシートのURLを返す
            new_url = self.get_spreadsheet_url(new_id)
            return new_url
            
        except Exception as e:
            st.error(f"スプレッドシート作成エラー: {str(e)}")
            return None
    
    def _write_dataframe_to_sheet(self, spreadsheet_id: str, sheet_name: str, 
                                 df: pd.DataFrame) -> bool:
        """
        データフレームをシートに書き込み
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: シート名
            df: データフレーム
            
        Returns:
            成功可否
        """
        try:
            # データフレームを値のリストに変換
            headers = df.columns.tolist()
            data_rows = df.fillna('').values.tolist()
            
            # ヘッダーとデータを結合
            all_data = [headers] + data_rows
            
            # 範囲を指定して書き込み
            range_spec = f"'{sheet_name}'!A1"
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_spec,
                valueInputOption='RAW',
                body={'values': all_data}
            ).execute()
            
            return True
            
        except HttpError as e:
            st.error(f"データフレーム書き込みエラー: {str(e)}")
            return False
    
    def _create_new_sheet(self, spreadsheet_id: str, sheet_name: str) -> bool:
        """
        新しいシートを作成
        
        Args:
            spreadsheet_id: スプレッドシートID
            sheet_name: 新しいシート名
            
        Returns:
            成功可否
        """
        try:
            request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=request_body
            ).execute()
            
            return True
            
        except HttpError as e:
            st.error(f"シート作成エラー: {str(e)}")
            return False