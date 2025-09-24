#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
炎上事例データベースのセットアップスクリプト（改良版）
より詳細なスキーマでSQLiteデータベースを作成し、豊富な初期データを挿入する
"""

import sqlite3
import os
from datetime import datetime

def create_database():
    """SQLiteデータベースとテーブルを作成する"""
    
    # データベースファイルのパス
    db_path = "enjo_cases.db"
    
    # 既存のデータベースファイルがある場合は削除
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"既存のデータベースファイル {db_path} を削除しました")
    
    # データベース接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 新しいテーブル作成
    create_table_sql = """
    CREATE TABLE enjo_cases (
        incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        incident_text TEXT NOT NULL,
        incident_date TEXT NOT NULL,
        cause_category TEXT NOT NULL,
        reasoning_text TEXT NOT NULL,
        company_info TEXT,
        media_url TEXT,
        response_text TEXT,
        outcome TEXT
    )
    """
    
    cursor.execute(create_table_sql)
    print("enjo_casesテーブルを作成しました（改良版スキーマ）")
    
    return conn, cursor

def insert_sample_data(cursor):
    """サンプルデータを挿入する"""
    
    sample_data = [
        {
            "title": "カレー店の差別的投稿",
            "incident_text": "弊社の新商品は本当にクソみたいな仕上がりでした。でもお客様には最高の商品としてお届けします！",
            "incident_date": "2024-01-15",
            "cause_category": "不適切な表現",
            "reasoning_text": "商品に対する否定的な表現と不適切な言葉遣いにより、顧客を侮辱していると受け取られ、企業の誠実性に疑問を抱かせたため。",
            "company_info": "某食品メーカー",
            "media_url": "",
            "response_text": "不適切な表現について深くお詫び申し上げます。今後はより慎重な表現を心がけます。",
            "outcome": "謝罪により早期沈静化"
        },
        {
            "title": "女性社員への差別的発言",
            "incident_text": "女性社員は結婚したら辞めるから昇進させない方が良い。男性の方が長期的に使える。",
            "incident_date": "2024-02-20",
            "cause_category": "差別的表現",
            "reasoning_text": "性別による差別的発言が含まれており、男女平等の観点から多くの批判を招いたため。",
            "company_info": "某IT企業",
            "media_url": "",
            "response_text": "性別による差別は決して許されません。社内教育を徹底し、再発防止に努めます。",
            "outcome": "炎上拡大、ブランドイメージ低下"
        },
        {
            "title": "競合他社への誹謗中傷",
            "incident_text": "A社の商品は完全にパクリです。我々の技術を盗んだ卑劣な会社です。絶対に買わないでください。",
            "incident_date": "2024-03-10",
            "cause_category": "誹謗中傷",
            "reasoning_text": "競合他社への根拠のない誹謗中傷により、業界全体の信頼性を損なう発言として批判されたため。",
            "company_info": "某製造業",
            "media_url": "",
            "response_text": "不適切な発言について謝罪いたします。競合他社への敬意を払い、健全な競争を心がけます。",
            "outcome": "法的措置の検討、ブランドイメージ低下"
        },
        {
            "title": "災害を軽視したハッシュタグ使用",
            "incident_text": "新商品発売記念！ #コロナ #災害 #不謹慎 でも安いから買ってね！",
            "incident_date": "2024-04-05",
            "cause_category": "不謹慎な表現",
            "reasoning_text": "災害や社会問題を軽視したハッシュタグの使用により、社会的責任を欠く発言として批判されたため。",
            "company_info": "某小売業",
            "media_url": "",
            "response_text": "災害を軽視するような表現について深くお詫び申し上げます。社会的責任を重く受け止めます。",
            "outcome": "早期沈静化"
        },
        {
            "title": "個人情報の不適切な公開",
            "incident_text": "お客様の田中様（住所：東京都渋谷区...）から素晴らしいお声をいただきました！",
            "incident_date": "2024-05-12",
            "cause_category": "個人情報漏洩",
            "reasoning_text": "顧客の個人情報を許可なく公開したため、プライバシー保護の観点から重大な問題として批判されたため。",
            "company_info": "某サービス業",
            "media_url": "",
            "response_text": "個人情報の取り扱いについて重大な問題が発生しました。管理体制を全面的に見直します。",
            "outcome": "法的措置、管理体制見直し"
        },
        {
            "title": "アニメファンへの差別的発言",
            "incident_text": "人気アニメ見てないやつ、文化遅れすぎててやばくない？",
            "incident_date": "2024-06-08",
            "cause_category": "趣味嗜好への差別",
            "reasoning_text": "特定の趣味嗜好を持たない人を「文化遅れ」と断じる差別的発言により、多様性を否定する発言として批判されたため。",
            "company_info": "某エンターテイメント企業",
            "media_url": "",
            "response_text": "多様性を尊重し、すべての趣味嗜好を認める姿勢を大切にします。",
            "outcome": "早期沈静化"
        },
        {
            "title": "社会問題への不用意な言及",
            "incident_text": "正直、努力しない人に税金使うのって無駄だと思うんだけど",
            "incident_date": "2024-07-15",
            "cause_category": "社会問題への偏見",
            "reasoning_text": "特定の属性の人々を「努力しない人」と一括りにし、社会問題への偏見を含む発言として批判されたため。",
            "company_info": "某コンサルティング企業",
            "media_url": "",
            "response_text": "社会問題について慎重に発言し、多様性を尊重する姿勢を大切にします。",
            "outcome": "炎上拡大、社会的責任への疑問"
        },
        {
            "title": "商品の品質問題を隠蔽",
            "incident_text": "当社の新商品は完璧です。品質に問題があるという噂は根拠のないデマです。",
            "incident_date": "2024-08-22",
            "cause_category": "情報隠蔽",
            "reasoning_text": "実際に品質問題があったにも関わらず、それを隠蔽し、批判を「デマ」と一蹴したため、信頼性を大きく損なったため。",
            "company_info": "某自動車メーカー",
            "media_url": "",
            "response_text": "品質問題について適切に情報開示し、お客様の安全を最優先に取り組みます。",
            "outcome": "大規模リコール、ブランドイメージ大幅低下"
        },
        {
            "title": "従業員への不適切な発言",
            "incident_text": "残業代を払うのがもったいないから、サービス残業で頑張ってもらおう。",
            "incident_date": "2024-09-10",
            "cause_category": "労働問題",
            "reasoning_text": "労働基準法に違反する可能性のある発言により、労働者の権利を軽視する発言として批判されたため。",
            "company_info": "某建設業",
            "media_url": "",
            "response_text": "労働基準法を遵守し、従業員の権利を尊重します。",
            "outcome": "労働基準監督署の調査、法的措置"
        },
        {
            "title": "環境問題への無関心",
            "incident_text": "環境なんてどうでもいい。利益が一番大事。",
            "incident_date": "2024-10-05",
            "cause_category": "社会的責任の欠如",
            "reasoning_text": "環境問題への無関心を露骨に表現し、社会的責任を軽視する発言として批判されたため。",
            "company_info": "某製造業",
            "media_url": "",
            "response_text": "環境問題は重要な課題です。持続可能な経営に取り組みます。",
            "outcome": "ESG投資家からの批判、株価下落"
        }
    ]
    
    # データ挿入
    insert_sql = """
    INSERT INTO enjo_cases (
        title, incident_text, incident_date, cause_category, 
        reasoning_text, company_info, media_url, response_text, outcome
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    for data in sample_data:
        cursor.execute(insert_sql, (
            data["title"],
            data["incident_text"],
            data["incident_date"],
            data["cause_category"],
            data["reasoning_text"],
            data["company_info"],
            data["media_url"],
            data["response_text"],
            data["outcome"]
        ))
    
    print(f"{len(sample_data)}件のサンプルデータを挿入しました")

def main():
    """メイン処理"""
    print("炎上事例データベースのセットアップを開始します（改良版）...")
    
    try:
        # データベースとテーブル作成
        conn, cursor = create_database()
        
        # サンプルデータ挿入
        insert_sample_data(cursor)
        
        # 変更をコミット
        conn.commit()
        
        # データ確認
        cursor.execute("SELECT COUNT(*) FROM enjo_cases")
        count = cursor.fetchone()[0]
        print(f"データベースに {count} 件のレコードが登録されました")
        
        # カテゴリ別の件数確認
        cursor.execute("SELECT cause_category, COUNT(*) FROM enjo_cases GROUP BY cause_category")
        categories = cursor.fetchall()
        print("\nカテゴリ別件数:")
        for category, count in categories:
            print(f"  {category}: {count}件")
        
        # 接続を閉じる
        conn.close()
        
        print("\nデータベースのセットアップが完了しました！")
        print("新しいスキーマにより、より詳細な分析が可能になりました。")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
