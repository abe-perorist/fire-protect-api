#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
炎上リスク分析API - Vercel互換版
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
    text: str = Field(..., min_length=1, max_length=1000)

class RiskScore(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class RelatedCase(BaseModel):
    incident_id: int
    title: str
    incident_text: str
    incident_date: str
    cause_category: str
    reasoning_text: str

class AnalyzeResponse(BaseModel):
    input_text: str
    risk_score: RiskScore
    analysis_text: str
    related_cases: List[RelatedCase]

def get_database_connection():
    """データベース接続を取得する"""
    try:
        if not os.path.exists(DB_PATH):
            return None
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None

def calculate_risk_score(text: str) -> RiskScore:
    """リスクスコア計算"""
    score = 10
    category = "その他"
    
    # 高リスクパターン
    if re.search(r'殺害|殺す|死ね|死ぬ|殺人', text, re.IGNORECASE):
        score += 40
        category = "極めて危険な表現"
    elif re.search(r'女性|男性|男|女|性別', text, re.IGNORECASE):
        score += 30
        category = "差別的表現"
    elif re.search(r'差別|偏見|見下す', text, re.IGNORECASE):
        score += 30
        category = "差別的表現"
    elif re.search(r'暴力|暴行|殴る|蹴る', text, re.IGNORECASE):
        score += 35
        category = "暴力的表現"
    elif re.search(r'クソ|くそ|最悪|ひどい', text, re.IGNORECASE):
        score += 25
        category = "不適切な表現"
    elif re.search(r'残業|給料|労働', text, re.IGNORECASE):
        score += 20
        category = "労働問題"
    elif re.search(r'環境|地球|温暖化', text, re.IGNORECASE):
        score += 15
        category = "社会的責任"
    elif re.search(r'税金|政治|政府', text, re.IGNORECASE):
        score += 15
        category = "社会問題"
    
    score = min(100, max(0, score))
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
        keywords = [word for word in text.split() if len(word) >= 2][:5]
        
        if keywords:
            conditions = []
            params = []
            for keyword in keywords:
                conditions.append("(title LIKE ? OR incident_text LIKE ? OR cause_category LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
            
            where_clause = " OR ".join(conditions)
            sql = f"""
            SELECT incident_id, title, incident_text, incident_date, cause_category, reasoning_text
            FROM enjo_cases
            WHERE {where_clause}
            ORDER BY incident_date DESC
            LIMIT ?
            """
            params.append(limit)
        else:
            sql = """
            SELECT incident_id, title, incident_text, incident_date, cause_category, reasoning_text
            FROM enjo_cases
            ORDER BY incident_date DESC
            LIMIT ?
            """
            params = [limit]
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        return [dict(row) for row in results]
        
    except Exception:
        return []
    finally:
        conn.close()

@app.get("/")
async def root():
    return {
        "message": "炎上リスク分析API",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
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
                "database_connected": False
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    try:
        risk_score = calculate_risk_score(request.text)
        related_cases_data = search_related_cases(request.text, limit=3)
        
        risk_level = "高リスク" if risk_score.overall_score >= 70 else "中リスク" if risk_score.overall_score >= 40 else "低リスク"
        
        analysis_text = f"""分析結果:
総合リスクスコア: {risk_score.overall_score}/100
原因カテゴリ: {risk_score.category}
信頼度: {risk_score.confidence}
リスク評価: {risk_level}
関連事例: {len(related_cases_data)}件"""
        
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
    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)