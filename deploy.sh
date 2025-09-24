#!/bin/bash
# 炎上リスク分析API - Vercelデプロイスクリプト

echo "🚀 炎上リスク分析API - Vercelデプロイ準備"
echo "=========================================="

# 1. Gitリポジトリの確認
if [ ! -d ".git" ]; then
    echo "📁 Gitリポジトリを初期化中..."
    git init
    echo "✅ Gitリポジトリを初期化しました"
else
    echo "✅ Gitリポジトリが既に存在します"
fi

# 2. ファイルの追加
echo "📝 ファイルをGitに追加中..."
git add .
echo "✅ ファイルを追加しました"

# 3. コミット
echo "💾 変更をコミット中..."
git commit -m "Deploy to Vercel - Fire Risk Analysis API v2.0.0"
echo "✅ コミットが完了しました"

# 4. リモートリポジトリの確認
if ! git remote | grep -q origin; then
    echo "⚠️  リモートリポジトリが設定されていません"
    echo "以下のコマンドでGitHubリポジトリを追加してください："
    echo "git remote add origin https://github.com/yourusername/fire-protect-api.git"
    echo ""
    echo "その後、以下のコマンドでプッシュしてください："
    echo "git push -u origin main"
else
    echo "🔄 リモートリポジトリにプッシュ中..."
    git push origin main
    echo "✅ プッシュが完了しました"
fi

echo ""
echo "🎉 デプロイ準備が完了しました！"
echo ""
echo "次のステップ："
echo "1. GitHubリポジトリを確認"
echo "2. Vercelダッシュボードでプロジェクトを作成"
echo "3. 環境変数 GEMINI_API_KEY を設定"
echo "4. デプロイを実行"
echo ""
echo "詳細な手順は README_VERCEL.md を参照してください"
