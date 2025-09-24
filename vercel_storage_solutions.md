# Vercel環境でのストレージ解決策

## 問題の詳細

### 現在の制限
- **読み取り専用**: 既存の `enjo_cases.db` ファイルは読み取り可能
- **書き込み不可**: 新しいデータの追加や更新はできない
- **一時的**: ファイルシステムの変更は次のリクエストで失われる

### 影響を受ける機能
- ✅ **動作する**: 炎上リスク分析（既存データの検索）
- ❌ **動作しない**: 新しい炎上事例の追加
- ❌ **動作しない**: データベースの更新・削除

## 解決策

### 1. 外部データベースサービス（推奨）

#### A. PlanetScale (MySQL)
```python
import mysql.connector
import os

def get_database_connection():
    return mysql.connector.connect(
        host=os.getenv('PLANETSCALE_HOST'),
        user=os.getenv('PLANETSCALE_USER'),
        password=os.getenv('PLANETSCALE_PASSWORD'),
        database=os.getenv('PLANETSCALE_DATABASE'),
        ssl_ca='/etc/ssl/certs/ca-certificates.crt'
    )
```

#### B. Supabase (PostgreSQL)
```python
import psycopg2
import os

def get_database_connection():
    return psycopg2.connect(
        host=os.getenv('SUPABASE_HOST'),
        user=os.getenv('SUPABASE_USER'),
        password=os.getenv('SUPABASE_PASSWORD'),
        database=os.getenv('SUPABASE_DATABASE'),
        port=os.getenv('SUPABASE_PORT', 5432)
    )
```

#### C. MongoDB Atlas
```python
from pymongo import MongoClient
import os

def get_database_connection():
    client = MongoClient(os.getenv('MONGODB_URI'))
    return client[os.getenv('MONGODB_DATABASE')]
```

### 2. クラウドストレージサービス

#### A. AWS S3 + Lambda
```python
import boto3
import json

def get_cases_from_s3():
    s3 = boto3.client('s3')
    response = s3.get_object(
        Bucket=os.getenv('S3_BUCKET'),
        Key='enjo_cases.json'
    )
    return json.loads(response['Body'].read())
```

#### B. Google Cloud Storage
```python
from google.cloud import storage
import json

def get_cases_from_gcs():
    client = storage.Client()
    bucket = client.bucket(os.getenv('GCS_BUCKET'))
    blob = bucket.blob('enjo_cases.json')
    return json.loads(blob.download_as_text())
```

### 3. 一時的な解決策（現在のまま）

#### メリット
- ✅ 既存のコードを変更不要
- ✅ 読み取り専用の分析機能は完全に動作
- ✅ デプロイが簡単

#### デメリット
- ❌ 新しいデータの追加ができない
- ❌ データの更新ができない
- ❌ 動的な学習機能が使えない

## 推奨実装

### 段階的移行プラン

#### Phase 1: 現在のままデプロイ（即座に可能）
```python
# main.py はそのまま使用
# 読み取り専用の分析機能のみ提供
```

#### Phase 2: 外部データベース導入（将来的）
```python
# 環境変数でデータベースタイプを切り替え
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')

def get_database_connection():
    if DATABASE_TYPE == 'sqlite':
        return sqlite3.connect(DB_PATH)
    elif DATABASE_TYPE == 'postgresql':
        return get_postgresql_connection()
    elif DATABASE_TYPE == 'mysql':
        return get_mysql_connection()
```

## 現在の状況での対応

### 1. データ更新が必要な場合
- ローカル環境でデータを更新
- 更新された `enjo_cases.db` をGitにコミット
- Vercelに再デプロイ

### 2. 新しいデータの追加
```bash
# ローカルでデータを追加
python3 manual_input.py

# 変更をコミット
git add enjo_cases.db
git commit -m "Update database with new cases"
git push origin main

# Vercelが自動的に再デプロイ
```

## 結論

**現在の状況**: 読み取り専用の分析APIとして完全に動作
**将来の拡張**: 外部データベースサービスを導入してフル機能を実現

まずは現在のコードでデプロイし、必要に応じて段階的に外部データベースを導入することを推奨します。
