#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheetsから直接データをインポートするスクリプト
Google Sheets APIを使用
"""

import sqlite3
import os
from datetime import datetime

def import_from_google_sheets(sheet_id: str, sheet_name: str = "Sheet1", db_path: str = "enjo_cases.db"):
    """Google Sheetsから直接データをインポートする"""
    
    try:
        # Google Sheets APIのライブラリをインポート
        import gspread
        from google.oauth2.service_account import Credentials
        
        print("Google Sheets APIを使用してデータをインポートします...")
        
        # 認証情報の設定（サービスアカウントキーファイルが必要）
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        # サービスアカウントキーファイルのパス
        creds_file = 'service_account_key.json'
        if not os.path.exists(creds_file):
            print(f"エラー: サービスアカウントキーファイル '{creds_file}' が見つかりません")
            print("Google Cloud Consoleでサービスアカウントを作成し、キーファイルをダウンロードしてください")
            return False
        
        creds = Credentials.from_service_account_file(creds_file, scopes=scope)
        client = gspread.authorize(creds)
        
        # スプレッドシートを開く
        sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
        
        # データを取得
        records = sheet.get_all_records()
        
        if not records:
            print("スプレッドシートにデータが見つかりません")
            return False
        
        # データベース接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        imported_count = 0
        for record in records:
            # データの準備
            data = {
                'title': record.get('title', '').strip(),
                'incident_text': record.get('incident_text', '').strip(),
                'incident_date': record.get('incident_date', '').strip(),
                'cause_category': record.get('cause_category', '').strip(),
                'reasoning_text': record.get('reasoning_text', '').strip(),
                'company_info': record.get('company_info', '').strip() or None,
                'media_url': record.get('media_url', '').strip() or None,
                'response_text': record.get('response_text', '').strip() or None,
                'outcome': record.get('outcome', '').strip() or None
            }
            
            # 必須フィールドのチェック
            if not all([data['title'], data['incident_text'], data['incident_date'], 
                       data['cause_category'], data['reasoning_text']]):
                print(f"スキップ: 必須フィールドが不足しています - {data['title']}")
                continue
            
            # データベースに挿入
            insert_sql = """
            INSERT INTO enjo_cases (
                title, incident_text, incident_date, cause_category, 
                reasoning_text, company_info, media_url, response_text, outcome
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_sql, (
                data['title'],
                data['incident_text'],
                data['incident_date'],
                data['cause_category'],
                data['reasoning_text'],
                data['company_info'],
                data['media_url'],
                data['response_text'],
                data['outcome']
            ))
            
            imported_count += 1
            print(f"インポート完了: {data['title']}")
        
        # 変更をコミット
        conn.commit()
        conn.close()
        
        print(f"\n✅ {imported_count}件のデータをGoogle Sheetsからインポートしました")
        return True
        
    except ImportError:
        print("エラー: 必要なライブラリがインストールされていません")
        print("以下のコマンドでインストールしてください:")
        print("pip install gspread google-auth")
        return False
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

def main():
    """メイン処理"""
    print("=== Google Sheets データインポートツール ===")
    print()
    
    # スプレッドシートIDの入力
    sheet_id = input("Google SheetsのスプレッドシートIDを入力してください: ").strip()
    if not sheet_id:
        print("スプレッドシートIDが入力されませんでした")
        return
    
    # シート名の入力（オプション）
    sheet_name = input("シート名を入力してください（デフォルト: Sheet1）: ").strip()
    if not sheet_name:
        sheet_name = "Sheet1"
    
    # インポート実行
    success = import_from_google_sheets(sheet_id, sheet_name)
    
    if success:
        print("\n🎉 データのインポートが完了しました！")
    else:
        print("\n❌ データのインポートに失敗しました")

if __name__ == "__main__":
    main()

