#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
機械学習ベースのスコアリングシステム
過去の炎上事例データを学習してリスクスコアを算出
"""

import sqlite3
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
from typing import List, Dict, Tuple

class MLScoringSystem:
    """機械学習ベースのスコアリングシステム"""
    
    def __init__(self, db_path: str = "enjo_cases.db"):
        self.db_path = db_path
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,  # 日本語のストップワードは別途設定
            ngram_range=(1, 2)  # 1-gramと2-gramを使用
        )
        self.model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
        self.is_trained = False
        
    def load_training_data(self) -> Tuple[List[str], List[int]]:
        """データベースから学習データを読み込み"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 炎上事例データを取得
        cursor.execute("""
            SELECT incident_text, cause_category, reasoning_text
            FROM enjo_cases
        """)
        
        texts = []
        scores = []
        
        for row in cursor.fetchall():
            incident_text, cause_category, reasoning_text = row
            
            # テキストを結合
            combined_text = f"{incident_text} {reasoning_text}"
            texts.append(combined_text)
            
            # カテゴリに基づいてスコアを設定
            category_scores = {
                '差別的表現': 95,
                '誹謗中傷': 90,
                '個人情報漏洩': 95,
                '労働問題': 85,
                '社会的責任の欠如': 80,
                '情報隠蔽': 85,
                '不適切な表現': 75,
                '不謹慎な表現': 70,
                '社会問題への偏見': 75,
                '趣味嗜好への差別': 60
            }
            
            score = category_scores.get(cause_category, 50)
            scores.append(score)
        
        conn.close()
        return texts, scores
    
    def train_model(self):
        """モデルを学習"""
        print("学習データを読み込み中...")
        texts, scores = self.load_training_data()
        
        if len(texts) < 10:
            print("学習データが不足しています（最低10件必要）")
            return False
        
        print(f"学習データ: {len(texts)}件")
        
        # テキストをベクトル化
        print("テキストをベクトル化中...")
        X = self.vectorizer.fit_transform(texts)
        y = np.array(scores)
        
        # 学習データとテストデータに分割
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # モデルを学習
        print("モデルを学習中...")
        self.model.fit(X_train, y_train)
        
        # テストデータで評価
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"学習完了!")
        print(f"平均二乗誤差: {mse:.2f}")
        print(f"決定係数 (R²): {r2:.2f}")
        
        self.is_trained = True
        
        # モデルを保存
        self.save_model()
        
        return True
    
    def predict_risk_score(self, text: str) -> Dict:
        """テキストのリスクスコアを予測"""
        if not self.is_trained:
            print("モデルが学習されていません。先にtrain_model()を実行してください。")
            return None
        
        # テキストをベクトル化
        X = self.vectorizer.transform([text])
        
        # スコアを予測
        predicted_score = self.model.predict(X)[0]
        
        # 信頼区間を計算（簡易版）
        confidence = min(0.95, max(0.5, 1.0 - abs(predicted_score - 50) / 100))
        
        return {
            'predicted_score': int(predicted_score),
            'confidence': round(confidence, 2),
            'risk_level': self._get_risk_level(predicted_score)
        }
    
    def _get_risk_level(self, score: float) -> str:
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
    
    def save_model(self):
        """モデルを保存"""
        model_dir = "models"
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        joblib.dump(self.vectorizer, f"{model_dir}/vectorizer.pkl")
        joblib.dump(self.model, f"{model_dir}/model.pkl")
        print("モデルを保存しました")
    
    def load_model(self):
        """保存されたモデルを読み込み"""
        model_dir = "models"
        vectorizer_path = f"{model_dir}/vectorizer.pkl"
        model_path = f"{model_dir}/model.pkl"
        
        if os.path.exists(vectorizer_path) and os.path.exists(model_path):
            self.vectorizer = joblib.load(vectorizer_path)
            self.model = joblib.load(model_path)
            self.is_trained = True
            print("モデルを読み込みました")
            return True
        else:
            print("保存されたモデルが見つかりません")
            return False
    
    def get_feature_importance(self) -> Dict[str, float]:
        """特徴量の重要度を取得"""
        if not self.is_trained:
            return {}
        
        feature_names = self.vectorizer.get_feature_names_out()
        importance = self.model.feature_importances_
        
        # 重要度の高い特徴量を取得
        feature_importance = dict(zip(feature_names, importance))
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        return dict(sorted_features[:20])  # 上位20個

# 使用例
if __name__ == "__main__":
    ml_system = MLScoringSystem()
    
    # モデルを学習
    if ml_system.train_model():
        # テスト用のテキスト
        test_text = "弊社の新商品は本当にクソみたいな仕上がりでした。でもお客様には最高の商品としてお届けします！"
        
        # リスクスコアを予測
        result = ml_system.predict_risk_score(test_text)
        if result:
            print(f"予測スコア: {result['predicted_score']}")
            print(f"信頼度: {result['confidence']}")
            print(f"リスクレベル: {result['risk_level']}")
        
        # 特徴量の重要度を表示
        print("\n重要な特徴量:")
        importance = ml_system.get_feature_importance()
        for feature, score in list(importance.items())[:10]:
            print(f"{feature}: {score:.3f}")

