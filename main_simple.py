#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
炎上リスク分析API - シンプル版
Vercelデプロイ用の最小構成
"""

import os
import sqlite3
import re
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="炎上リスク分析API",
    description="投稿テキストの炎上リスクを分析するAPI",
    version="2.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データベースファイルのパス
DB_PATH = "enjo_cases.db"

# Pydanticモデル
class AnalyzeRequest(BaseModel):
    """分析リクエストのモデル"""
    text: str = Field(..., description="分析対象のテキスト", min_length=1, max_length=1000)

class RiskScore(BaseModel):
    """リスクスコア"""
    overall_score: int = Field(..., ge=0, le=100, description="総合スコア（0-100）")
    category: str = Field(..., description="原因カテゴリ")
    confidence: float = Field(..., ge=0.0, le=1.0, description="分析の信頼度（0.0-1.0）")

class RelatedCase(BaseModel):
    """関連事例のモデル"""
    incident_id: int
    title: str
    incident_text: str
    incident_date: str
    cause_category: str
    reasoning_text: str

class AnalyzeResponse(BaseModel):
    """分析結果のモデル"""
    input_text: str
    risk_score: RiskScore
    analysis_text: str
    related_cases: List[RelatedCase]

def get_database_connection():
    """データベース接続を取得する"""
    try:
        if not os.path.exists(DB_PATH):
            print(f"データベースファイルが見つかりません: {DB_PATH}")
            return None
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"データベース接続エラー: {e}")
        return None

def calculate_risk_score(text: str) -> RiskScore:
    """シンプルなリスクスコア計算"""
    
    # 高リスクパターン
    high_risk_patterns = [
        r'殺害|殺す|死ね|死ぬ|殺人',
        r'女性|男性|男|女|性別',
        r'差別|偏見|見下す',
        r'暴力|暴行|殴る|蹴る',
        r'クソ|くそ|最悪|ひどい'
    ]
    
    # 中リスクパターン
    medium_risk_patterns = [
        r'残業|給料|労働',
        r'環境|地球|温暖化',
        r'税金|政治|政府'
    ]
    
    # スコア計算
    score = 10  # ベーススコア
    category = "その他"
    
    for pattern in high_risk_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 30
            if "殺害" in pattern or "殺す" in pattern:
                category = "極めて危険な表現"
            elif "女性" in pattern or "男性" in pattern:
                category = "差別的表現"
            elif "差別" in pattern:
                category = "差別的表現"
            elif "暴力" in pattern:
                category = "暴力的表現"
            elif "クソ" in pattern:
                category = "不適切な表現"
            break
    
    for pattern in medium_risk_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 15
            if "残業" in pattern:
                category = "労働問題"
            elif "環境" in pattern:
                category = "社会的責任"
            elif "税金" in pattern:
                category = "社会問題"
            break
    
    # スコアを0-100の範囲に調整
    score = min(100, max(0, score))
    
    # 信頼度計算
    confidence = min(1.0, len(text) / 100)
    
    return RiskScore(
        overall_score=score,
        category=category,
        confidence=confidence
    )

def search_related_cases(text: str, limit: int = 3) -> List[Dict[str, Any]]:
    """関連事例を検索する"""
    conn = get_database_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # キーワードを抽出
        keywords = []
        for word in text.split():
            if len(word) >= 2:
                keywords.append(word)
        
        # 関連事例を検索
        if keywords:
            search_conditions = []
            search_params = []
            
            for keyword in keywords[:5]:  # 最大5個のキーワード
                search_conditions.append("(title LIKE ? OR incident_text LIKE ? OR cause_category LIKE ?)")
                search_params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
            
            where_clause = " OR ".join(search_conditions)
            sql = f"""
            SELECT incident_id, title, incident_text, incident_date, cause_category, reasoning_text
            FROM enjo_cases
            WHERE {where_clause}
            ORDER BY incident_date DESC
            LIMIT ?
            """
            search_params.append(limit)
        else:
            sql = """
            SELECT incident_id, title, incident_text, incident_date, cause_category, reasoning_text
            FROM enjo_cases
            ORDER BY incident_date DESC
            LIMIT ?
            """
            search_params = [limit]
        
        cursor.execute(sql, search_params)
        results = cursor.fetchall()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        print(f"検索エラー: {e}")
        return []
    finally:
        conn.close()

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "炎上リスク分析API",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM enjo_cases")
            count = cursor.fetchone()[0]
            conn.close()
            
            return {
                "status": "healthy",
                "database_records": count,
                "database_connected": True
            }
        else:
            return {
                "status": "unhealthy",
                "database_connected": False,
                "error": "Database connection failed"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """テキストの炎上リスクを分析する"""
    try:
        # 1. リスクスコアを計算
        risk_score = calculate_risk_score(request.text)
        
        # 2. 関連事例を検索
        related_cases_data = search_related_cases(request.text, limit=3)
        
        # 3. 分析結果を生成
        analysis_text = f"""
分析結果:
総合リスクスコア: {risk_score.overall_score}/100
原因カテゴリ: {risk_score.category}
信頼度: {risk_score.confidence}

リスク評価:
{"高リスク" if risk_score.overall_score >= 70 else "中リスク" if risk_score.overall_score >= 40 else "低リスク"}

関連事例: {len(related_cases_data)}件
        """.strip()
        
        # 4. 関連事例をモデルに変換
        related_cases = [RelatedCase(**case) for case in related_cases_data]
        
        return AnalyzeResponse(
            input_text=request.text,
            risk_score=risk_score,
            analysis_text=analysis_text,
            related_cases=related_cases
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析中にエラーが発生しました: {str(e)}")

# Vercel用のハンドラー
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    print("Mangum not available, using direct app")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
