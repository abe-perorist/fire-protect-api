#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手動で炎上事例データを入力するツール
対話形式でデータを入力
"""

import sqlite3
import os
from datetime import datetime

def add_incident_manually(db_path: str = "enjo_cases.db"):
    """手動で炎上事例を追加する"""
    
    print("=== 炎上事例データ 手動入力ツール ===")
    print()
    
    # データベース接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        while True:
            print("新しい炎上事例を入力してください（終了するには 'quit' を入力）")
            print("-" * 50)
            
            # 必須フィールドの入力
            title = input("タイトル: ").strip()
            if title.lower() == 'quit':
                break
            
            incident_text = input("炎上した投稿・発言の全文: ").strip()
            if not incident_text:
                print("炎上した投稿・発言は必須です")
                continue
            
            incident_date = input("炎上日（YYYY-MM-DD形式）: ").strip()
            if not incident_date:
                print("炎上日は必須です")
                continue
            
            # 原因カテゴリの選択
            print("\n原因カテゴリを選択してください:")
            categories = [
                "差別的表現", "誹謗中傷", "個人情報漏洩", "労働問題",
                "社会的責任の欠如", "情報隠蔽", "不適切な表現", 
                "不謹慎な表現", "社会問題への偏見", "趣味嗜好への差別"
            ]
            
            for i, category in enumerate(categories, 1):
                print(f"{i}. {category}")
            
            try:
                category_choice = int(input("選択番号: ")) - 1
                if 0 <= category_choice < len(categories):
                    cause_category = categories[category_choice]
                else:
                    print("無効な選択です")
                    continue
            except ValueError:
                print("数値を入力してください")
                continue
            
            reasoning_text = input("炎上の理由（なぜ炎上したのか）: ").strip()
            if not reasoning_text:
                print("炎上の理由は必須です")
                continue
            
            # オプションフィールドの入力
            company_info = input("企業名・個人名（任意）: ").strip() or None
            media_url = input("関連ニュースURL（任意）: ").strip() or None
            response_text = input("企業の対応・謝罪文（任意）: ").strip() or None
            outcome = input("対応結果（任意）: ").strip() or None
            
            # データの確認
            print("\n入力内容を確認してください:")
            print(f"タイトル: {title}")
            print(f"炎上投稿: {incident_text[:50]}...")
            print(f"炎上日: {incident_date}")
            print(f"原因カテゴリ: {cause_category}")
            print(f"炎上の理由: {reasoning_text[:50]}...")
            print(f"企業: {company_info or '未入力'}")
            print(f"対応結果: {outcome or '未入力'}")
            
            confirm = input("\nこの内容で保存しますか？ (y/n): ").strip().lower()
            if confirm == 'y':
                # データベースに挿入
                insert_sql = """
                INSERT INTO enjo_cases (
                    title, incident_text, incident_date, cause_category, 
                    reasoning_text, company_info, media_url, response_text, outcome
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_sql, (
                    title, incident_text, incident_date, cause_category,
                    reasoning_text, company_info, media_url, response_text, outcome
                ))
                
                conn.commit()
                print("✅ データを保存しました")
            else:
                print("❌ 保存をキャンセルしました")
            
            print("\n" + "="*50)
            
    except KeyboardInterrupt:
        print("\n\n入力が中断されました")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        conn.close()
    
    print("手動入力ツールを終了します")

def main():
    """メイン処理"""
    add_incident_manually()

if __name__ == "__main__":
    main()

