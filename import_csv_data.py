#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSVファイルから炎上事例データをインポートするスクリプト
スプレッドシートをCSV形式でエクスポートして使用
"""

import csv
import sqlite3
import os
from datetime import datetime

def import_csv_to_database(csv_file_path: str, db_path: str = "enjo_cases.db"):
    """CSVファイルからデータベースにデータをインポートする"""
    
    if not os.path.exists(csv_file_path):
        print(f"エラー: CSVファイル '{csv_file_path}' が見つかりません")
        return False
    
    # データベース接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            # CSVファイルの読み込み
            reader = csv.DictReader(csvfile)
            
            # 必要なカラムをチェック
            required_columns = ['title', 'incident_text', 'incident_date', 'cause_category', 'reasoning_text']
            if not all(col in reader.fieldnames for col in required_columns):
                print(f"エラー: 必要なカラムが不足しています。")
                print(f"必要なカラム: {required_columns}")
                print(f"実際のカラム: {reader.fieldnames}")
                return False
            
            imported_count = 0
            for row in reader:
                # データの準備
                data = {
                    'title': row['title'].strip(),
                    'incident_text': row['incident_text'].strip(),
                    'incident_date': row['incident_date'].strip(),
                    'cause_category': row['cause_category'].strip(),
                    'reasoning_text': row['reasoning_text'].strip(),
                    'company_info': row.get('company_info', '').strip() or None,
                    'media_url': row.get('media_url', '').strip() or None,
                    'response_text': row.get('response_text', '').strip() or None,
                    'outcome': row.get('outcome', '').strip() or None
                }
                
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
            print(f"\n✅ {imported_count}件のデータをインポートしました")
            
            # 統計情報を表示
            cursor.execute("SELECT COUNT(*) FROM enjo_cases")
            total_count = cursor.fetchone()[0]
            print(f"データベース総件数: {total_count}件")
            
            # カテゴリ別件数
            cursor.execute("SELECT cause_category, COUNT(*) FROM enjo_cases GROUP BY cause_category ORDER BY COUNT(*) DESC")
            categories = cursor.fetchall()
            print("\nカテゴリ別件数:")
            for category, count in categories:
                print(f"  {category}: {count}件")
            
            return True
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_sample_csv():
    """サンプルCSVファイルを作成する"""
    sample_data = [
        {
            'title': 'サンプル炎上事例1',
            'incident_text': '弊社の新商品は本当にクソみたいな仕上がりでした。でもお客様には最高の商品としてお届けします！',
            'incident_date': '2024-01-15',
            'cause_category': '不適切な表現',
            'reasoning_text': '商品に対する否定的な表現と不適切な言葉遣いにより、顧客を侮辱していると受け取られ、企業の誠実性に疑問を抱かせたため。',
            'company_info': '某食品メーカー',
            'media_url': '',
            'response_text': '不適切な表現について深くお詫び申し上げます。今後はより慎重な表現を心がけます。',
            'outcome': '謝罪により早期沈静化'
        },
        {
            'title': 'サンプル炎上事例2',
            'incident_text': '女性社員は結婚したら辞めるから昇進させない方が良い。男性の方が長期的に使える。',
            'incident_date': '2024-02-20',
            'cause_category': '差別的表現',
            'reasoning_text': '性別による差別的発言が含まれており、男女平等の観点から多くの批判を招いたため。',
            'company_info': '某IT企業',
            'media_url': '',
            'response_text': '性別による差別は決して許されません。社内教育を徹底し、再発防止に努めます。',
            'outcome': '炎上拡大、ブランドイメージ低下'
        }
    ]
    
    csv_filename = 'sample_data.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'incident_text', 'incident_date', 'cause_category', 
                     'reasoning_text', 'company_info', 'media_url', 'response_text', 'outcome']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for data in sample_data:
            writer.writerow(data)
    
    print(f"サンプルCSVファイル '{csv_filename}' を作成しました")
    print("このファイルを参考に、あなたのスプレッドシートデータを同じ形式でCSVにエクスポートしてください")

def main():
    """メイン処理"""
    print("=== 炎上事例データ CSVインポートツール ===")
    print()
    
    # サンプルCSVファイルの作成
    create_sample_csv()
    print()
    
    # ユーザーにCSVファイルのパスを入力してもらう
    csv_file = input("インポートするCSVファイルのパスを入力してください: ").strip()
    
    if not csv_file:
        print("CSVファイルのパスが入力されませんでした")
        return
    
    # インポート実行
    success = import_csv_to_database(csv_file)
    
    if success:
        print("\n🎉 データのインポートが完了しました！")
        print("APIサーバーを再起動して、新しいデータで分析を試してみてください。")
    else:
        print("\n❌ データのインポートに失敗しました")

if __name__ == "__main__":
    main()

