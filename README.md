# LINE Talk Analyzer Backend

LINEトーク履歴を解析して、1年間の流行語大賞を表示するWebアプリケーションのバックエンドです。

## 概要

本システムは、LINEトーク履歴ファイルをアップロードすることで、以下の解析を行います：

- **形態素解析による単語抽出**: MeCabを使用して、トーク履歴から意味のある単語を抽出・集計
  - **抽出対象品詞**: 名詞、形容詞、感動詞（動詞・副詞は除外し、より具体的な流行語を抽出）
- **メッセージ全文の集計**: よく使われるフレーズやメッセージを完全一致でカウント
- **期間指定フィルタ**: 特定期間のトーク履歴のみを解析可能
- **ストップワード機能**: 一般的すぎる単語を除外して、より意味のある流行語を抽出
- **REST API**: JSON形式で解析結果を返却

### 主な機能

- ✅ 最大50MBのトーク履歴ファイルに対応
- ✅ 高速処理（約27万メッセージを10秒以内で解析）
- ✅ ユーザー別流行語ランキング（全体とユーザーごとの両方を同時に出力）
- ✅ 品詞フィルタリング（名詞・形容詞・感動詞のみ抽出、動詞・副詞は除外）
- ✅ 基本形でのグループ化（「行く」「行っ」「行った」を「行く」として集計）
- ✅ カスタマイズ可能なストップワード辞書
- ✅ CORS対応でフロントエンドから直接利用可能

## 技術スタック

- **言語**: Python 3.11+
- **Webフレームワーク**: FastAPI 0.104+
- **形態素解析**: MeCab + mecab-python3
- **辞書**: mecab-ipadic-neologd（新語対応）
- **テストフレームワーク**: pytest
- **コンテナ**: Docker + Docker Compose
- **コード品質**: Black, isort, flake8, mypy

## 環境構築

### 必要な環境

- Docker
- Docker Compose

### セットアップ手順

1. リポジトリをクローン

```bash
git clone https://github.com/Kubo-Tech/line_talk_analyzer_backend.git
cd line_talk_analyzer_backend
```

2. Dockerコンテナをビルド・起動

```bash
docker-compose up --build
```

3. APIサーバーが起動します

- URL: `http://localhost:8000`
- APIドキュメント: `http://localhost:8000/docs`

### MeCabの動作確認

コンテナに入ってMeCabが正しくインストールされているか確認：

```bash
docker-compose exec api bash
echo "すもももももももものうち" | mecab
```

## 開発方法

### コンテナに入る

```bash
docker-compose exec api bash
```

### コンテナの停止

```bash
docker-compose down
```

### コンテナの再起動

```bash
docker-compose restart
```

### ログの確認

```bash
docker-compose logs -f api
```

## プロジェクト構造

```
line_talk_analyzer_backend/
├── app/                    # アプリケーションコード
│   ├── main.py            # FastAPIエントリポイント
│   ├── api/               # APIエンドポイント
│   ├── core/              # 設定・CORS
│   ├── models/            # データモデル
│   ├── services/          # ビジネスロジック
│   └── utils/             # ユーティリティ
├── tests/                 # テストコード
├── docker-compose.yml     # Docker Compose設定
├── Dockerfile             # Dockerイメージ定義
├── requirements.txt       # Python依存パッケージ
└── README.md             # このファイル
```

## API仕様

### エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/health` | ヘルスチェック |
| POST | `/api/v1/analyze` | トーク履歴解析 |

### 1. ヘルスチェック

サーバーの稼働状態を確認します。

```http
GET /api/v1/health
```

**レスポンス例**:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### 2. トーク履歴解析

LINEトーク履歴ファイルをアップロードして解析します。

```http
POST /api/v1/analyze
Content-Type: multipart/form-data
```

**リクエストパラメータ**:

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|------|------|-----------|------|
| `file` | File | ✅ | - | LINEトーク履歴ファイル（.txt形式） |
| `top_n` | int | ❌ | 50 | 取得する上位単語数（1〜1000） |
| `min_word_length` | int | ❌ | 2 | 最小単語長（1〜100） |
| `max_word_length` | int | ❌ | null | 最大単語長 |
| `min_message_length` | int | ❌ | 2 | 最小メッセージ長 |
| `max_message_length` | int | ❌ | null | 最大メッセージ長 |
| `start_date` | string | ❌ | null | 解析開始日時（YYYY-MM-DD HH:MM:SS） |
| `end_date` | string | ❌ | null | 解析終了日時（YYYY-MM-DD HH:MM:SS） |

**レスポンス例**:
```json
{
  "status": "success",
  "data": {
    "analysis_period": {
      "start_date": "2025-01-01T00:00:00",
      "end_date": "2025-12-31T23:59:59"
    },
    "total_messages": 15000,
    "total_users": 3,
    "morphological_analysis": {
      "top_words": [
        {
          "word": "アニメ",
          "count": 450,
          "part_of_speech": "名詞",
          "appearances": [
            {
              "date": "2025-01-15T10:30:00",
              "user": "ユーザーA",
              "message": "アニメ見た"
            }
          ]
        },
        {
          "word": "美味しい",
          "count": 380,
          "part_of_speech": "形容詞",
          "appearances": [
            {
              "date": "2025-02-20T12:00:00",
              "user": "ユーザーB",
              "message": "これ美味しい"
            }
          ]
        }
      ]
    },
    "full_message_analysis": {
      "top_messages": [
        {
          "message": "おつかれ",
          "count": 250,
          "appearances": [
            {
              "date": "2025-01-10T18:00:00",
              "user": "ユーザーA",
              "message": "おつかれ",
              "match_type": "exact"
            }
          ]
        },
        {
          "message": "ありがとう",
          "count": 180,
          "appearances": [
            {
              "date": "2025-03-05T14:30:00",
              "user": "ユーザーC",
              "message": "ありがとう",
              "match_type": "exact"
            }
          ]
        }
      ]
    },
    "user_analysis": {
      "word_analysis": [
        {
          "user": "ユーザーA",
          "top_words": [
            {
              "word": "アニメ",
              "count": 200,
              "part_of_speech": "名詞"
            },
            {
              "word": "楽しい",
              "count": 150,
              "part_of_speech": "形容詞"
            }
          ]
        }
      ],
      "message_analysis": [
        {
          "user": "ユーザーA",
          "top_messages": [
            {
              "message": "おつかれ",
              "count": 120
            },
            {
              "message": "おはよう",
              "count": 95
            }
          ]
        }
      ]
    }
  }
}
```

**エラーレスポンス例**:
```json
{
  "detail": "アップロードされたファイルの形式が無効です"
}
```

## 使用例

### curlでの使用例

```bash
# 基本的な解析
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@talk_history.txt"

# パラメータ指定
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@talk_history.txt" \
  -F "top_n=100" \
  -F "min_word_length=2" \
  -F "start_date=2025-01-01 00:00:00" \
  -F "end_date=2025-12-31 23:59:59"
```

### Pythonでの使用例

```python
import requests

# ファイルをアップロードして解析
url = "http://localhost:8000/api/v1/analyze"
files = {"file": open("talk_history.txt", "rb")}
data = {
    "top_n": 100,
    "min_word_length": 2,
    "start_date": "2025-01-01 00:00:00",
    "end_date": "2025-12-31 23:59:59"
}

response = requests.post(url, files=files, data=data)
result = response.json()

# 上位10単語を表示
for word in result["data"]["morphological_analysis"]["top_words"][:10]:
    print(f"{word['word']}: {word['count']}回")
```

### JavaScriptでの使用例

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('top_n', 100);
formData.append('min_word_length', 2);
formData.append('start_date', '2025-01-01 00:00:00');
formData.append('end_date', '2025-12-31 23:59:59');

fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => {
    console.log('解析結果:', data);
  });
```

## ストップワード機能

一般的すぎる単語（「する」「ある」「そう」など）を解析結果から除外できます。

### ストップワード辞書の編集

`app/data/stopwords.json` を編集して、除外する単語を追加・削除できます：

```json
{
  "stop_words": [
    "する",
    "ある",
    "いる",
    "なる"
  ]
}
```

**注意**: 単語は基本形（辞書形）で記載してください。
- ❌ 「なっ」「なり」（活用形）
- ✅ 「なる」（基本形）

### ストップワードの動作

- 形態素解析時に基本形でフィルタリング
- 動詞、形容詞の活用形も自動的に除外
- デフォルトで67単語が登録済み

## パフォーマンス

実際のトーク履歴（約18MB、27万メッセージ）での測定結果：

| 期間 | メッセージ数 | 解析時間 | メモリ使用量 |
|------|------------|---------|------------|
| 1年分 | 41,539 | 2.5秒 | 141 MB |
| 全期間（8年） | 272,878 | 10秒 | 150 MB |

**最適化ポイント**:
- 品詞フィルタリング（名詞・形容詞・感動詞のみ）により、具体的な流行語を抽出
- 基本形でのグループ化により、活用形を統一して集計
- ストップワードによる不要な単語の除外
- 効率的なカウント処理

## トラブルシューティング

### 1. MeCabが動作しない

**症状**: `RuntimeError: MeCab initialization failed`

**対処法**:
```bash
# コンテナを再ビルド
docker-compose down
docker-compose up --build
```

### 2. ファイルアップロードでエラーが出る

**症状**: `413 Request Entity Too Large`

**対処法**: 
- ファイルサイズが50MBを超えていないか確認
- 環境変数 `MAX_FILE_SIZE_MB` で上限を変更可能

### 3. 解析結果に意図しない単語が含まれる

**症状**: 「する」「ある」などの一般的な単語が上位に来る

**対処法**:
- `app/data/stopwords.json` に除外したい単語を追加
- 単語は基本形で記載すること

### 4. 特定期間のデータが取得できない

**症状**: `start_date`/`end_date`を指定してもデータが0件

**対処法**:
- 日時形式を確認: `YYYY-MM-DD HH:MM:SS`
- トーク履歴ファイルの日付形式が正しいか確認
- タイムゾーンの違いに注意

### 5. 解析が遅い

**症状**: 大量のメッセージで10秒以上かかる

**対処法**:
- `min_word_length=2` または `3` に設定して1文字単語を除外
- `top_n` を減らす（デフォルト50）
- ストップワードを充実させて処理対象を減らす

## 詳細仕様

詳細な仕様は以下のドキュメントを参照してください：

- [仕様書（SPEC.md）](doc/SPEC.md) - システム全体の仕様
- [コーディング規約](doc/コーディング規約.md) - 開発時のルール
- [PRドキュメント](doc/PR/) - 各機能の実装記録

## コーディング規約

本プロジェクトは `doc/コーディング規約.md` に従って開発されています。

- PEP8準拠
- Black でフォーマット
- flake8 でリント
- mypy で型チェック
- Google Style Docstring

## ライセンス

MIT License

## 開発者

Kubo-Tech