#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
炎上リスク分析API - Vercel API Routes版
"""

import os
import sqlite3
import re
import json
from http.server import BaseHTTPRequestHandler
from typing import List, Dict, Any

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "message": "炎上リスク分析API",
                "version": "2.0.0",
                "status": "running"
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                conn = self.get_database_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM enjo_cases")
                    count = cursor.fetchone()[0]
                    conn.close()
                    
                    response = {
                        "status": "healthy",
                        "database_records": count,
                        "database_connected": True
                    }
                else:
                    response = {
                        "status": "unhealthy",
                        "database_connected": False
                    }
            except Exception as e:
                response = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/analyze':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                text = data.get('text', '')
                if not text:
                    response = {"error": "テキストが指定されていません"}
                else:
                    risk_score = self.calculate_risk_score(text)
                    related_cases = self.search_related_cases(text, limit=3)
                    
                    risk_level = "高リスク" if risk_score['overall_score'] >= 70 else "中リスク" if risk_score['overall_score'] >= 40 else "低リスク"
                    
                    analysis_text = f"""分析結果:
総合リスクスコア: {risk_score['overall_score']}/100
原因カテゴリ: {risk_score['category']}
信頼度: {risk_score['confidence']}
リスク評価: {risk_level}
関連事例: {len(related_cases)}件"""
                    
                    response = {
                        "input_text": text,
                        "risk_score": risk_score,
                        "analysis_text": analysis_text,
                        "related_cases": related_cases
                    }
                
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                error_response = {"error": f"分析中にエラーが発生しました: {str(e)}"}
                self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def get_database_connection(self):
        """データベース接続を取得する"""
        try:
            db_path = "enjo_cases.db"
            if not os.path.exists(db_path):
                return None
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None
    
    def calculate_risk_score(self, text: str) -> Dict[str, Any]:
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
        
        return {
            "overall_score": score,
            "category": category,
            "confidence": confidence
        }
    
    def search_related_cases(self, text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """関連事例を検索する"""
        conn = self.get_database_connection()
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