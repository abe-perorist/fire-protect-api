#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
炎上リスク分析API
SQLiteデータベースから類似事例を検索し、Gemini APIでリスク分析を行う
多要素スコアリングシステム統合版
"""

import os
import sqlite3
import re
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="炎上リスク分析API",
    description="投稿テキストの炎上リスクを分析するAPI（多要素スコアリング対応）",
    version="2.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini APIの設定
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY環境変数が設定されていません")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# データベースファイルのパス
DB_PATH = "enjo_cases.db"

# 多要素スコアリングシステム
class RiskScore(BaseModel):
    """詳細なリスクスコア"""
    overall_score: int = Field(..., ge=0, le=100, description="総合スコア（0-100）")
    content_risk: int = Field(..., ge=0, le=100, description="コンテンツリスク（0-100）")
    legal_risk: int = Field(..., ge=0, le=100, description="法的リスク（0-100）")
    brand_risk: int = Field(..., ge=0, le=100, description="ブランドリスク（0-100）")
    social_risk: int = Field(..., ge=0, le=100, description="社会的リスク（0-100）")
    category: str = Field(..., description="原因カテゴリ")
    confidence: float = Field(..., ge=0.0, le=1.0, description="分析の信頼度（0.0-1.0）")

# Pydanticモデル
class AnalyzeRequest(BaseModel):
    """分析リクエストのモデル"""
    text: str = Field(..., description="分析対象のテキスト", min_length=1, max_length=1000)

class RelatedCase(BaseModel):
    """関連事例のモデル"""
    incident_id: int
    title: str
    incident_text: str
    incident_date: str
    cause_category: str
    reasoning_text: str
    company_info: str = None
    media_url: str = None
    response_text: str = None
    outcome: str = None

class AnalyzeResponse(BaseModel):
    """分析結果のモデル（多要素スコアリング対応）"""
    input_text: str
    risk_score: RiskScore  # 詳細なスコア情報
    analysis_text: str
    related_cases: List[RelatedCase]
    recommendations: List[str] = Field(default_factory=list, description="推奨事項")

# 多要素スコアリングシステム
class AdvancedScoringSystem:
    """高度なスコアリングシステム"""
    
    def __init__(self):
        # リスクパターンの重み付け
        self.risk_patterns = {
            # 極めて高リスクパターン（重み: 4.0）
            'extreme_risk': {
                'patterns': [
                    r'殺害|殺す|死ね|死ぬ|殺人|殺し|殺して|殺せ',
                    r'老人|高齢者|年寄り|お年寄り',
                    r'障害者|障がい者|身体障害|知的障害',
                    r'外国人|移民|在日|朝鮮|中国|韓国',
                    r'女性|男性|男|女|性別|結婚|妊娠|LGBT|ゲイ|レズ',
                    r'暴力|暴行|殴る|蹴る|叩く|痛めつける',
                    r'差別|偏見|見下す|馬鹿|アホ|バカ|クズ|ゴミ'
                ],
                'weight': 4.0,
                'base_score': 95
            },
            # 高リスクパターン（重み: 3.0）
            'high_risk': {
                'patterns': [
                    r'クソ|くそ|最悪|ひどい|ダメ|だめ|やばい',
                    r'パクリ|盗作|コピー|真似',
                    r'住所|電話|個人情報|名前|メール',
                    r'残業|給料|労働|働く|従業員',
                    r'完璧|問題ない|デマ|嘘|隠蔽',
                    r'うざい|うっとうしい|邪魔|迷惑',
                    r'消えろ|消えて|出て行け|帰れ'
                ],
                'weight': 3.0,
                'base_score': 80
            },
            # 中リスクパターン（重み: 2.0）
            'medium_risk': {
                'patterns': [
                    r'環境|地球|温暖化|CO2|エコ',
                    r'税金|政治|政府|国|社会',
                    r'アニメ|ゲーム|趣味|文化|遅れ',
                    r'競合|他社|ライバル|対抗',
                    r'宗教|信仰|信者|信教',
                    r'民族|人種|肌の色|出身'
                ],
                'weight': 2.0,
                'base_score': 50
            },
            # 低リスクパターン（重み: 1.0）
            'low_risk': {
                'patterns': [
                    r'すごい|素晴らしい|最高|良い',
                    r'お客様|顧客|ユーザー',
                    r'品質|サービス|商品'
                ],
                'weight': 1.0,
                'base_score': 20
            }
        }
        
        # 法的リスク要因
        self.legal_risk_factors = {
            '労働基準法': ['残業', '給料', '労働', '働く', '従業員'],
            '個人情報保護法': ['住所', '電話', '個人情報', '名前', 'メール'],
            '差別禁止法': ['女性', '男性', '男', '女', '性別', '結婚', '妊娠', '老人', '高齢者', '障害者', '外国人', '移民'],
            '名誉毀損': ['パクリ', '盗作', 'コピー', '真似', '卑劣'],
            '脅迫罪': ['殺害', '殺す', '死ね', '死ぬ', '殺人', '暴力', '暴行', '殴る', '蹴る'],
            '侮辱罪': ['馬鹿', 'アホ', 'バカ', 'クズ', 'ゴミ', 'うざい', 'うっとうしい']
        }
        
        # ブランドリスク要因
        self.brand_risk_factors = {
            '企業イメージ': ['クソ', 'くそ', '最悪', 'ひどい', 'ダメ', 'だめ', '殺害', '殺す', '死ね', '暴力'],
            '顧客信頼': ['嘘', 'デマ', '隠蔽', '問題ない', '完璧', '差別', '偏見'],
            '社会的責任': ['環境', '地球', '温暖化', 'CO2', 'エコ', '老人', '高齢者', '障害者', '外国人'],
            '人権問題': ['差別', '偏見', '見下す', '馬鹿', 'アホ', 'バカ', 'クズ', 'ゴミ']
        }
        
        # 社会的リスク要因
        self.social_risk_factors = {
            '炎上拡散': ['やばい', '最悪', 'ひどい', '問題', '殺害', '殺す', '死ね', '暴力'],
            '批判集中': ['差別', '誹謗', '中傷', '攻撃', '老人', '高齢者', '障害者', '外国人'],
            '社会問題': ['税金', '政治', '政府', '国', '社会', '差別', '偏見', '人権'],
            '人権侵害': ['老人', '高齢者', '障害者', '外国人', '移民', '女性', '男性', 'LGBT']
        }

    def analyze_text(self, text: str) -> RiskScore:
        """テキストを詳細分析してリスクスコアを算出"""
        
        # 各要素のスコアを算出
        content_risk = self._calculate_content_risk(text)
        legal_risk = self._calculate_legal_risk(text)
        brand_risk = self._calculate_brand_risk(text)
        social_risk = self._calculate_social_risk(text)
        
        # 総合スコアを算出（重み付け平均）
        overall_score = self._calculate_overall_score(
            content_risk, legal_risk, brand_risk, social_risk
        )
        
        # 原因カテゴリを特定
        category = self._identify_category(text)
        
        # 信頼度を算出
        confidence = self._calculate_confidence(text)
        
        return RiskScore(
            overall_score=overall_score,
            content_risk=content_risk,
            legal_risk=legal_risk,
            brand_risk=brand_risk,
            social_risk=social_risk,
            category=category,
            confidence=confidence
        )

    def _calculate_content_risk(self, text: str) -> int:
        """コンテンツリスクを算出"""
        score = 0
        total_matches = 0
        
        for risk_level, config in self.risk_patterns.items():
            for pattern in config['patterns']:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                if matches > 0:
                    score += matches * config['weight'] * config['base_score']
                    total_matches += matches
        
        if total_matches == 0:
            return 10  # デフォルト値
        
        return min(100, int(score / total_matches))

    def _calculate_legal_risk(self, text: str) -> int:
        """法的リスクを算出"""
        legal_score = 0
        
        for law, keywords in self.legal_risk_factors.items():
            for keyword in keywords:
                if keyword in text:
                    legal_score += 20  # 各法的リスク要因で20点追加
        
        return min(100, legal_score)

    def _calculate_brand_risk(self, text: str) -> int:
        """ブランドリスクを算出"""
        brand_score = 0
        
        for risk_type, keywords in self.brand_risk_factors.items():
            for keyword in keywords:
                if keyword in text:
                    brand_score += 15  # 各ブランドリスク要因で15点追加
        
        return min(100, brand_score)

    def _calculate_social_risk(self, text: str) -> int:
        """社会的リスクを算出"""
        social_score = 0
        
        for risk_type, keywords in self.social_risk_factors.items():
            for keyword in keywords:
                if keyword in text:
                    social_score += 10  # 各社会的リスク要因で10点追加
        
        return min(100, social_score)

    def _calculate_overall_score(self, content: int, legal: int, brand: int, social: int) -> int:
        """総合スコアを算出（重み付け平均）"""
        # 重み付け: コンテンツ40%, 法的30%, ブランド20%, 社会的10%
        weights = [0.4, 0.3, 0.2, 0.1]
        scores = [content, legal, brand, social]
        
        weighted_score = sum(score * weight for score, weight in zip(scores, weights))
        return int(weighted_score)

    def _identify_category(self, text: str) -> str:
        """原因カテゴリを特定"""
        category_scores = {}
        
        categories = {
            '極めて危険な表現': ['殺害', '殺す', '死ね', '死ぬ', '殺人', '暴力', '暴行'],
            '差別的表現': ['女性', '男性', '男', '女', '性別', '結婚', '妊娠', '老人', '高齢者', '障害者', '外国人', '移民', 'LGBT'],
            '誹謗中傷': ['パクリ', '盗作', 'コピー', '真似', '卑劣', '馬鹿', 'アホ', 'バカ', 'クズ', 'ゴミ'],
            '個人情報漏洩': ['住所', '電話', '個人情報', '名前', 'メール'],
            '労働問題': ['残業', '給料', '労働', '働く', '従業員'],
            '不適切な表現': ['クソ', 'くそ', '最悪', 'ひどい', 'ダメ', 'だめ', 'うざい', 'うっとうしい'],
            '情報隠蔽': ['完璧', '問題ない', 'デマ', '嘘', '隠蔽'],
            '社会的責任の欠如': ['環境', '地球', '温暖化', 'CO2', 'エコ'],
            '社会問題への偏見': ['税金', '政治', '政府', '国', '社会'],
            '趣味嗜好への差別': ['アニメ', 'ゲーム', '趣味', '文化', '遅れ'],
            '人権侵害': ['差別', '偏見', '見下す', '老人', '高齢者', '障害者', '外国人']
        }
        
        for category, keywords in categories.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            category_scores[category] = score
        
        # 最もスコアの高いカテゴリを返す
        if category_scores:
            return max(category_scores, key=category_scores.get)
        return 'その他'

    def _calculate_confidence(self, text: str) -> float:
        """分析の信頼度を算出"""
        # テキストの長さとキーワードの多さに基づいて信頼度を算出
        text_length = len(text)
        keyword_count = sum(len(re.findall(pattern, text, re.IGNORECASE)) 
                           for config in self.risk_patterns.values() 
                           for pattern in config['patterns'])
        
        # 信頼度の計算（0.0-1.0）
        length_factor = min(1.0, text_length / 100)  # 100文字で1.0
        keyword_factor = min(1.0, keyword_count / 5)  # 5個のキーワードで1.0
        
        confidence = (length_factor + keyword_factor) / 2
        return round(confidence, 2)

    def get_recommendations(self, risk_score: RiskScore) -> List[str]:
        """リスクスコアに基づく推奨事項を生成"""
        recommendations = []
        
        if risk_score.legal_risk >= 60:
            recommendations.append("法的リスクが高いため、法務部門との相談を推奨")
        
        if risk_score.brand_risk >= 60:
            recommendations.append("ブランドイメージへの影響が大きいため、広報戦略の見直しが必要")
        
        if risk_score.social_risk >= 60:
            recommendations.append("社会的影響が予想されるため、SNS監視体制の強化を推奨")
        
        if risk_score.content_risk >= 80:
            recommendations.append("コンテンツの全面的な見直しが必要")
        
        if risk_score.confidence < 0.5:
            recommendations.append("分析の信頼度が低いため、より詳細な分析を推奨")
        
        return recommendations

# グローバルスコアリングシステムインスタンス
scoring_system = AdvancedScoringSystem()

def get_database_connection():
    """データベース接続を取得する"""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="データベースファイルが見つかりません")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 辞書形式で結果を取得
    return conn

def search_related_cases(text: str, limit: int = 3) -> List[Dict[str, Any]]:
    """入力テキストに関連する炎上事例を検索する（改良版）"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # キーワードを抽出（改良版）
    keywords = extract_keywords_advanced(text)
    
    # 関連事例を検索（改良版）
    search_conditions = []
    search_params = []
    
    for keyword in keywords:
        search_conditions.append("(title LIKE ? OR incident_text LIKE ? OR cause_category LIKE ? OR reasoning_text LIKE ?)")
        search_params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
    
    if search_conditions:
        where_clause = " OR ".join(search_conditions)
        sql = f"""
        SELECT incident_id, title, incident_text, incident_date, cause_category, 
               reasoning_text, company_info, media_url, response_text, outcome
        FROM enjo_cases
        WHERE {where_clause}
        ORDER BY 
            CASE cause_category 
                WHEN '差別的表現' THEN 5
                WHEN '誹謗中傷' THEN 5
                WHEN '個人情報漏洩' THEN 5
                WHEN '労働問題' THEN 4
                WHEN '社会的責任の欠如' THEN 4
                WHEN '情報隠蔽' THEN 4
                WHEN '不適切な表現' THEN 3
                WHEN '不謹慎な表現' THEN 3
                WHEN '社会問題への偏見' THEN 3
                WHEN '趣味嗜好への差別' THEN 2
                ELSE 1
            END DESC,
            incident_date DESC
        LIMIT ?
        """
        search_params.append(limit)
    else:
        # キーワードが見つからない場合は最新の事例を返す
        sql = """
        SELECT incident_id, title, incident_text, incident_date, cause_category, 
               reasoning_text, company_info, media_url, response_text, outcome
        FROM enjo_cases
        ORDER BY incident_date DESC
        LIMIT ?
        """
        search_params = [limit]
    
    cursor.execute(sql, search_params)
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]

def extract_keywords_advanced(text: str) -> List[str]:
    """テキストからキーワードを抽出する（改良版）"""
    keywords = []
    
    # 高リスクパターン（重み付け）
    high_risk_patterns = {
        r'クソ|くそ|最悪|ひどい|ダメ|だめ|やばい': '不適切な表現',
        r'女性|男性|男|女|性別|結婚|妊娠': '差別的表現',
        r'パクリ|盗作|コピー|真似': '誹謗中傷',
        r'住所|電話|個人情報|名前|メール': '個人情報漏洩',
        r'残業|給料|労働|働く|従業員': '労働問題',
        r'環境|地球|温暖化|CO2|エコ': '社会的責任',
        r'税金|政治|政府|国|社会': '社会問題',
        r'アニメ|ゲーム|趣味|文化|遅れ': '趣味嗜好',
        r'競合|他社|ライバル|対抗': '競合関係',
        r'完璧|問題ない|デマ|嘘|隠蔽': '情報隠蔽'
    }
    
    # パターンマッチング
    for pattern, category in high_risk_patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.extend(matches)
        keywords.append(category)  # カテゴリも追加
    
    # 感情表現の抽出
    emotion_patterns = [
        r'怒|悲|喜|驚|恐|嫌|愛|恨|妬|嫉',
        r'すごい|やばい|ひどい|最悪|最高|素晴らしい',
        r'絶対|絶対に|絶対だ|絶対です',
        r'絶対に|絶対|絶対だ|絶対です'
    ]
    
    for pattern in emotion_patterns:
        matches = re.findall(pattern, text)
        keywords.extend(matches)
    
    # 否定表現の抽出
    negation_patterns = [
        r'ない|無い|だめ|ダメ|禁止|禁止する',
        r'やめて|やめろ|やめるな',
        r'買うな|買わない|買わないで'
    ]
    
    for pattern in negation_patterns:
        matches = re.findall(pattern, text)
        keywords.extend(matches)
    
    # 一般的な名詞の抽出（2文字以上）
    words = re.findall(r'[ぁ-んァ-ヶ一-龯]{2,}', text)
    keywords.extend([word for word in words if len(word) >= 2])
    
    # 重複除去と優先度付け
    unique_keywords = list(set(keywords))
    
    # 高リスクキーワードを優先
    priority_keywords = []
    normal_keywords = []
    
    for keyword in unique_keywords:
        if any(risk in keyword for risk in ['不適切', '差別', '誹謗', '個人情報', '労働', '社会', '隠蔽']):
            priority_keywords.append(keyword)
        else:
            normal_keywords.append(keyword)
    
    # 優先度の高いキーワードを先に、最大15個まで
    result = priority_keywords[:10] + normal_keywords[:5]
    return result[:15]

def extract_keywords(text: str) -> List[str]:
    """後方互換性のための関数"""
    return extract_keywords_advanced(text)

def generate_gemini_prompt_advanced(input_text: str, related_cases: List[Dict[str, Any]], risk_score: RiskScore) -> str:
    """Gemini API用のプロンプトを生成する（多要素スコアリング対応版）"""
    
    cases_text = ""
    for i, case in enumerate(related_cases, 1):
        cases_text += f"""
事例{i}:
タイトル: {case['title']}
炎上投稿: {case['incident_text']}
炎上日: {case['incident_date']}
原因カテゴリ: {case['cause_category']}
炎上の理由: {case['reasoning_text']}
企業: {case.get('company_info', '不明')}
対応結果: {case.get('outcome', '不明')}
---
"""
    
    prompt = f"""
あなたは企業の炎上リスク専門家です。以下の投稿案について、提供された類似事例と多要素スコアリング結果を参考にリスクを分析し、具体的な改善点を提案してください。

【分析対象の投稿】
{input_text}

【多要素スコアリング結果】
総合スコア: {risk_score.overall_score}/100
コンテンツリスク: {risk_score.content_risk}/100
法的リスク: {risk_score.legal_risk}/100
ブランドリスク: {risk_score.brand_risk}/100
社会的リスク: {risk_score.social_risk}/100
原因カテゴリ: {risk_score.category}
分析信頼度: {risk_score.confidence}

【参考となる類似事例】
{cases_text}

【分析ガイドライン】
1. 多要素スコアリング結果を基に、各リスク要素の詳細分析を行ってください
2. 類似事例の「炎上の理由」を参考に、投稿の潜在的なリスクを特定してください
3. 原因カテゴリ（差別的表現、誹謗中傷、個人情報漏洩、労働問題、社会的責任の欠如、情報隠蔽、不適切な表現、不謹慎な表現、社会問題への偏見、趣味嗜好への差別）に基づいて分類してください
4. 企業の社会的責任、ブランドイメージ、法的リスクを考慮してください
5. 具体的で実用的な改善提案を提供してください

【分析項目】
1. 総合リスク評価（多要素スコアリング結果の解釈）
2. 各リスク要素の詳細分析
3. 原因カテゴリの特定と根拠
4. 具体的なリスク要因の分析
5. 類似事例との比較分析
6. 社会的影響の予測
7. 具体的な改善提案
8. 推奨される表現の修正案

【回答形式】
総合リスク評価: [多要素スコアリング結果の解釈]
コンテンツリスク分析: [コンテンツの詳細分析]
法的リスク分析: [法的リスクの詳細分析]
ブランドリスク分析: [ブランドリスクの詳細分析]
社会的リスク分析: [社会的リスクの詳細分析]
原因カテゴリ: [該当するカテゴリと根拠]
リスク要因: [具体的なリスク要因]
類似事例との比較: [比較分析]
社会的影響: [予測される影響]
改善提案: [具体的な改善点]
修正案: [推奨される表現]
"""
    
    return prompt

def generate_gemini_prompt(input_text: str, related_cases: List[Dict[str, Any]]) -> str:
    """Gemini API用のプロンプトを生成する（改良版）"""
    
    cases_text = ""
    for i, case in enumerate(related_cases, 1):
        cases_text += f"""
事例{i}:
タイトル: {case['title']}
炎上投稿: {case['incident_text']}
炎上日: {case['incident_date']}
原因カテゴリ: {case['cause_category']}
炎上の理由: {case['reasoning_text']}
企業: {case.get('company_info', '不明')}
対応結果: {case.get('outcome', '不明')}
---
"""
    
    prompt = f"""
あなたは企業の炎上リスク専門家です。以下の投稿案について、提供された類似事例を参考にリスクを分析し、具体的な改善点を提案してください。

【分析対象の投稿】
{input_text}

【参考となる類似事例】
{cases_text}

【分析ガイドライン】
1. 類似事例の「炎上の理由」を参考に、投稿の潜在的なリスクを特定してください
2. 原因カテゴリ（差別的表現、誹謗中傷、個人情報漏洩、労働問題、社会的責任の欠如、情報隠蔽、不適切な表現、不謹慎な表現、社会問題への偏見、趣味嗜好への差別）に基づいて分類してください
3. 企業の社会的責任、ブランドイメージ、法的リスクを考慮してください
4. 具体的で実用的な改善提案を提供してください

【分析項目】
1. リスクスコア（0-100の数値で評価）
2. 原因カテゴリの特定
3. 具体的なリスク要因の分析
4. 類似事例との比較分析
5. 社会的影響の予測
6. 具体的な改善提案
7. 推奨される表現の修正案

【回答形式】
リスクスコア: [0-100の数値]
原因カテゴリ: [該当するカテゴリ]
分析結果: [詳細な分析]
リスク要因: [具体的なリスク要因]
類似事例との比較: [比較分析]
社会的影響: [予測される影響]
改善提案: [具体的な改善点]
修正案: [推奨される表現]
"""
    
    return prompt

def extract_risk_score_from_response(response: str) -> int:
    """Geminiの回答からリスクスコアを抽出する"""
    # リスクスコアを抽出する正規表現
    score_match = re.search(r'リスクスコア[：:]\s*(\d+)', response)
    if score_match:
        return int(score_match.group(1))
    
    # 数値が見つからない場合は、キーワードベースで推定
    high_risk_keywords = ['高', '危険', '炎上', '問題', '不適切', '差別', '誹謗']
    medium_risk_keywords = ['中', '注意', '慎重', '配慮']
    low_risk_keywords = ['低', '安全', '問題なし', '適切']
    
    response_lower = response.lower()
    
    for keyword in high_risk_keywords:
        if keyword in response_lower:
            return 80
    
    for keyword in medium_risk_keywords:
        if keyword in response_lower:
            return 50
    
    for keyword in low_risk_keywords:
        if keyword in response_lower:
            return 20
    
    return 50  # デフォルト値

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "炎上リスク分析API",
        "version": "2.0.0",
        "endpoints": {
            "POST /analyze": "テキストの炎上リスクを分析（多要素スコアリング対応）"
        }
    }

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM enjo_cases")
        count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "database_records": count,
            "gemini_api_configured": bool(GEMINI_API_KEY)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """
    テキストの炎上リスクを分析する（多要素スコアリング対応）
    
    - **text**: 分析対象のテキスト（1-1000文字）
    
    戻り値:
    - **input_text**: 入力されたテキスト
    - **risk_score**: 詳細なリスクスコア（総合、コンテンツ、法的、ブランド、社会的）
    - **analysis_text**: 詳細な分析結果
    - **related_cases**: 関連する炎上事例
    - **recommendations**: 推奨事項
    """
    try:
        # 1. 多要素スコアリングシステムで分析
        risk_score = scoring_system.analyze_text(request.text)
        
        # 2. 関連事例を検索
        related_cases_data = search_related_cases(request.text, limit=3)
        
        # 3. Gemini API用のプロンプトを生成（多要素スコア情報を含む）
        prompt = generate_gemini_prompt_advanced(request.text, related_cases_data, risk_score)
        
        # 4. Gemini APIを呼び出し
        response = model.generate_content(prompt)
        analysis_text = response.text
        
        # 5. 関連事例をモデルに変換
        related_cases = [RelatedCase(**case) for case in related_cases_data]
        
        # 6. 推奨事項を生成
        recommendations = scoring_system.get_recommendations(risk_score)
        
        return AnalyzeResponse(
            input_text=request.text,
            risk_score=risk_score,
            analysis_text=analysis_text,
            related_cases=related_cases,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析中にエラーが発生しました: {str(e)}")

# Vercel用のハンドラー
from mangum import Mangum
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

