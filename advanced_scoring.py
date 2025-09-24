#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高度なスコアリングシステム
複数の要素を組み合わせた詳細なリスク分析
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class RiskScore:
    """詳細なリスクスコア"""
    overall_score: int  # 総合スコア（0-100）
    content_risk: int   # コンテンツリスク（0-100）
    legal_risk: int     # 法的リスク（0-100）
    brand_risk: int     # ブランドリスク（0-100）
    social_risk: int    # 社会的リスク（0-100）
    category: str       # 原因カテゴリ
    confidence: float   # 分析の信頼度（0.0-1.0）

class AdvancedScoringSystem:
    """高度なスコアリングシステム"""
    
    def __init__(self):
        # リスクパターンの重み付け
        self.risk_patterns = {
            # 高リスクパターン（重み: 3.0）
            'high_risk': {
                'patterns': [
                    r'クソ|くそ|最悪|ひどい|ダメ|だめ|やばい',
                    r'女性|男性|男|女|性別|結婚|妊娠',
                    r'パクリ|盗作|コピー|真似',
                    r'住所|電話|個人情報|名前|メール',
                    r'残業|給料|労働|働く|従業員',
                    r'完璧|問題ない|デマ|嘘|隠蔽'
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
                    r'競合|他社|ライバル|対抗'
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
            '差別禁止法': ['女性', '男性', '男', '女', '性別', '結婚', '妊娠'],
            '名誉毀損': ['パクリ', '盗作', 'コピー', '真似', '卑劣']
        }
        
        # ブランドリスク要因
        self.brand_risk_factors = {
            '企業イメージ': ['クソ', 'くそ', '最悪', 'ひどい', 'ダメ', 'だめ'],
            '顧客信頼': ['嘘', 'デマ', '隠蔽', '問題ない', '完璧'],
            '社会的責任': ['環境', '地球', '温暖化', 'CO2', 'エコ']
        }
        
        # 社会的リスク要因
        self.social_risk_factors = {
            '炎上拡散': ['やばい', '最悪', 'ひどい', '問題'],
            '批判集中': ['差別', '誹謗', '中傷', '攻撃'],
            '社会問題': ['税金', '政治', '政府', '国', '社会']
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
            '差別的表現': ['女性', '男性', '男', '女', '性別', '結婚', '妊娠'],
            '誹謗中傷': ['パクリ', '盗作', 'コピー', '真似', '卑劣'],
            '個人情報漏洩': ['住所', '電話', '個人情報', '名前', 'メール'],
            '労働問題': ['残業', '給料', '労働', '働く', '従業員'],
            '不適切な表現': ['クソ', 'くそ', '最悪', 'ひどい', 'ダメ', 'だめ'],
            '情報隠蔽': ['完璧', '問題ない', 'デマ', '嘘', '隠蔽'],
            '社会的責任の欠如': ['環境', '地球', '温暖化', 'CO2', 'エコ'],
            '社会問題への偏見': ['税金', '政治', '政府', '国', '社会'],
            '趣味嗜好への差別': ['アニメ', 'ゲーム', '趣味', '文化', '遅れ']
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

    def get_risk_level(self, score: int) -> str:
        """スコアからリスクレベルを判定"""
        if score >= 80:
            return "極めて高リスク"
        elif score >= 60:
            return "高リスク"
        elif score >= 40:
            return "中リスク"
        elif score >= 20:
            return "低リスク"
        else:
            return "極めて低リスク"

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

# 使用例
if __name__ == "__main__":
    scoring_system = AdvancedScoringSystem()
    
    test_text = "弊社の新商品は本当にクソみたいな仕上がりでした。でもお客様には最高の商品としてお届けします！"
    
    result = scoring_system.analyze_text(test_text)
    
    print(f"総合スコア: {result.overall_score}")
    print(f"コンテンツリスク: {result.content_risk}")
    print(f"法的リスク: {result.legal_risk}")
    print(f"ブランドリスク: {result.brand_risk}")
    print(f"社会的リスク: {result.social_risk}")
    print(f"原因カテゴリ: {result.category}")
    print(f"信頼度: {result.confidence}")
    print(f"リスクレベル: {scoring_system.get_risk_level(result.overall_score)}")
    
    recommendations = scoring_system.get_recommendations(result)
    print("推奨事項:")
    for rec in recommendations:
        print(f"- {rec}")

