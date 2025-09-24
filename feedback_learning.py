#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
フィードバック学習システム
ユーザーの評価を学習してスコアリング精度を向上
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class FeedbackLearningSystem:
    """フィードバック学習システム"""
    
    def __init__(self, db_path: str = "enjo_cases.db"):
        self.db_path = db_path
        self.feedback_file = "feedback_data.json"
        self.learning_data = self._load_feedback_data()
    
    def _load_feedback_data(self) -> Dict:
        """フィードバックデータを読み込み"""
        if os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'feedback_count': 0,
            'accuracy_history': [],
            'user_corrections': [],
            'pattern_weights': {}
        }
    
    def _save_feedback_data(self):
        """フィードバックデータを保存"""
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(self.learning_data, f, ensure_ascii=False, indent=2)
    
    def add_feedback(self, text: str, predicted_score: int, user_score: int, 
                    user_comment: str = "") -> bool:
        """ユーザーフィードバックを追加"""
        
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'text': text,
            'predicted_score': predicted_score,
            'user_score': user_score,
            'user_comment': user_comment,
            'score_difference': abs(predicted_score - user_score)
        }
        
        self.learning_data['user_corrections'].append(feedback)
        self.learning_data['feedback_count'] += 1
        
        # 精度を計算
        accuracy = self._calculate_accuracy()
        self.learning_data['accuracy_history'].append({
            'timestamp': datetime.now().isoformat(),
            'accuracy': accuracy,
            'feedback_count': self.learning_data['feedback_count']
        })
        
        # パターンの重みを更新
        self._update_pattern_weights(text, predicted_score, user_score)
        
        self._save_feedback_data()
        
        print(f"フィードバックを記録しました（精度: {accuracy:.1f}%）")
        return True
    
    def _calculate_accuracy(self) -> float:
        """現在の精度を計算"""
        if not self.learning_data['user_corrections']:
            return 0.0
        
        total_difference = sum(feedback['score_difference'] 
                             for feedback in self.learning_data['user_corrections'])
        total_feedback = len(self.learning_data['user_corrections'])
        
        # 平均誤差を計算（0-100スケール）
        average_error = total_difference / total_feedback
        accuracy = max(0, 100 - average_error)
        
        return accuracy
    
    def _update_pattern_weights(self, text: str, predicted_score: int, user_score: int):
        """パターンの重みを更新"""
        # 簡単なパターン抽出
        patterns = self._extract_patterns(text)
        
        for pattern in patterns:
            if pattern not in self.learning_data['pattern_weights']:
                self.learning_data['pattern_weights'][pattern] = 1.0
            
            # 重みを調整
            score_diff = user_score - predicted_score
            if score_diff > 0:  # ユーザーの方が高いスコア
                self.learning_data['pattern_weights'][pattern] *= 1.1
            elif score_diff < 0:  # ユーザーの方が低いスコア
                self.learning_data['pattern_weights'][pattern] *= 0.9
            
            # 重みの範囲を制限
            self.learning_data['pattern_weights'][pattern] = max(0.1, 
                min(3.0, self.learning_data['pattern_weights'][pattern]))
    
    def _extract_patterns(self, text: str) -> List[str]:
        """テキストからパターンを抽出"""
        import re
        
        patterns = []
        
        # 危険な表現のパターン
        dangerous_words = ['クソ', 'くそ', '最悪', 'ひどい', 'ダメ', 'だめ', 'やばい']
        for word in dangerous_words:
            if word in text:
                patterns.append(f"dangerous_{word}")
        
        # 差別的表現のパターン
        discriminatory_words = ['女性', '男性', '男', '女', '性別']
        for word in discriminatory_words:
            if word in text:
                patterns.append(f"discriminatory_{word}")
        
        # 感情表現のパターン
        emotion_words = ['怒', '悲', '喜', '驚', '恐', '嫌']
        for word in emotion_words:
            if word in text:
                patterns.append(f"emotion_{word}")
        
        return patterns
    
    def get_learning_statistics(self) -> Dict:
        """学習統計を取得"""
        if not self.learning_data['user_corrections']:
            return {
                'total_feedback': 0,
                'current_accuracy': 0.0,
                'improvement_trend': 0.0,
                'top_patterns': []
            }
        
        # 精度の改善傾向を計算
        accuracy_history = self.learning_data['accuracy_history']
        if len(accuracy_history) >= 2:
            recent_accuracy = accuracy_history[-1]['accuracy']
            older_accuracy = accuracy_history[0]['accuracy']
            improvement = recent_accuracy - older_accuracy
        else:
            improvement = 0.0
        
        # 重要なパターンを取得
        pattern_weights = self.learning_data['pattern_weights']
        sorted_patterns = sorted(pattern_weights.items(), key=lambda x: x[1], reverse=True)
        top_patterns = sorted_patterns[:10]
        
        return {
            'total_feedback': self.learning_data['feedback_count'],
            'current_accuracy': self._calculate_accuracy(),
            'improvement_trend': improvement,
            'top_patterns': top_patterns
        }
    
    def get_recommendations(self) -> List[str]:
        """学習に基づく推奨事項を生成"""
        recommendations = []
        
        stats = self.get_learning_statistics()
        
        if stats['total_feedback'] < 10:
            recommendations.append("より多くのフィードバックを収集して精度を向上させましょう")
        
        if stats['current_accuracy'] < 70:
            recommendations.append("現在の精度が低いため、モデルの再学習を推奨します")
        
        if stats['improvement_trend'] < 0:
            recommendations.append("精度が低下傾向にあります。パターンの重み調整が必要です")
        
        # 重要なパターンに基づく推奨事項
        for pattern, weight in stats['top_patterns'][:3]:
            if weight > 2.0:
                recommendations.append(f"パターン '{pattern}' の重みが高すぎます。調整を検討してください")
            elif weight < 0.5:
                recommendations.append(f"パターン '{pattern}' の重みが低すぎます。調整を検討してください")
        
        return recommendations

# 使用例
if __name__ == "__main__":
    feedback_system = FeedbackLearningSystem()
    
    # フィードバックを追加
    feedback_system.add_feedback(
        text="弊社の新商品は本当にクソみたいな仕上がりでした",
        predicted_score=85,
        user_score=90,
        user_comment="もう少し高いスコアが適切だと思います"
    )
    
    # 統計を表示
    stats = feedback_system.get_learning_statistics()
    print("学習統計:")
    print(f"総フィードバック数: {stats['total_feedback']}")
    print(f"現在の精度: {stats['current_accuracy']:.1f}%")
    print(f"改善傾向: {stats['improvement_trend']:.1f}%")
    
    # 推奨事項を表示
    recommendations = feedback_system.get_recommendations()
    print("\n推奨事項:")
    for rec in recommendations:
        print(f"- {rec}")

