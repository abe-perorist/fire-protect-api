# 炎上リスク分析API - Vercelデプロイガイド

## 🚀 Vercelへのデプロイ手順

### 1. 前提条件
- Vercelアカウント（[vercel.com](https://vercel.com)で無料登録）
- GitHubアカウント
- Google Gemini APIキー

### 2. リポジトリの準備
```bash
# Gitリポジトリを初期化（まだの場合）
git init
git add .
git commit -m "Initial commit for Vercel deployment"

# GitHubにプッシュ
git remote add origin https://github.com/yourusername/fire-protect-api.git
git push -u origin main
```

### 3. Vercelでのデプロイ
1. [Vercel Dashboard](https://vercel.com/dashboard)にアクセス
2. "New Project"をクリック
3. GitHubリポジトリを選択
4. プロジェクト設定：
   - **Framework Preset**: Other
   - **Root Directory**: `./` (デフォルト)
   - **Build Command**: 空白のまま
   - **Output Directory**: 空白のまま

### 4. 環境変数の設定
Vercelダッシュボードで以下の環境変数を設定：

```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

**設定手順：**
1. プロジェクトの "Settings" タブ
2. "Environment Variables" セクション
3. 以下の変数を追加：
   - **Name**: `GEMINI_API_KEY`
   - **Value**: あなたのGemini APIキー
   - **Environment**: Production, Preview, Development すべてにチェック

### 5. デプロイの実行
- "Deploy" ボタンをクリック
- デプロイが完了するまで待機（通常2-3分）

### 6. 動作確認
デプロイ完了後、以下のエンドポイントでテスト：

```bash
# ヘルスチェック
curl https://your-project-name.vercel.app/health

# 分析テスト
curl -X POST https://your-project-name.vercel.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "この商品は素晴らしいです！"}'
```

## 📁 プロジェクト構造
```
fire-protect/
├── main.py              # メインAPIファイル
├── vercel.json          # Vercel設定ファイル
├── requirements.txt     # Python依存関係
├── enjo_cases.db       # SQLiteデータベース
├── README_VERCEL.md    # このファイル
└── .gitignore          # Git除外設定
```

## 🔧 設定ファイルの説明

### vercel.json
- **builds**: Pythonアプリケーションとして認識
- **routes**: すべてのリクエストをmain.pyにルーティング
- **env**: 環境変数の参照設定
- **functions**: タイムアウト設定（30秒）

### requirements.txt
- FastAPI、Google Generative AI、Mangum等の依存関係
- Vercel用にMangumを追加（AWS Lambda互換ハンドラー）

## ⚠️ 注意事項

1. **データベースファイル**: `enjo_cases.db`はGitリポジトリに含める必要があります
2. **APIキー**: 本番環境では必ず環境変数で設定してください
3. **タイムアウト**: Vercelの無料プランでは10秒の制限があります
4. **ストレージ**: サーバーレス環境では永続的なファイル書き込みはできません

## 🐛 トラブルシューティング

### よくある問題と解決方法

1. **デプロイエラー**
   - `requirements.txt`の依存関係を確認
   - Pythonバージョンの互換性を確認

2. **環境変数エラー**
   - Vercelダッシュボードで環境変数が正しく設定されているか確認
   - 再デプロイが必要な場合があります

3. **データベースエラー**
   - `enjo_cases.db`がリポジトリに含まれているか確認
   - ファイルパスが正しいか確認

4. **タイムアウトエラー**
   - 複雑な分析処理でタイムアウトが発生する場合があります
   - より単純なテストケースで試してください

## 📊 API仕様

### エンドポイント
- `GET /` - ルート情報
- `GET /health` - ヘルスチェック
- `POST /analyze` - テキスト分析

### 分析リクエスト例
```json
{
  "text": "分析したいテキスト"
}
```

### 分析レスポンス例
```json
{
  "input_text": "分析したいテキスト",
  "risk_score": {
    "overall_score": 50,
    "content_risk": 60,
    "legal_risk": 40,
    "brand_risk": 30,
    "social_risk": 20,
    "category": "不適切な表現",
    "confidence": 0.8
  },
  "analysis_text": "詳細な分析結果...",
  "related_cases": [...],
  "recommendations": [...]
}
```

## 🎉 デプロイ完了後

デプロイが成功すると、以下のようなURLでAPIにアクセスできます：
`https://your-project-name.vercel.app`

このAPIを使って、Webアプリケーションやモバイルアプリから炎上リスク分析機能を利用できます！
