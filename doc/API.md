# API仕様書

このドキュメントは、LINEトーク履歴解析バックエンドのAPI仕様を記載しています。

## データ形式

### 入力データ形式（LINEトーク履歴）

```
[LINE] サンプルグループのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge太郎	おはようございます
22:13		piyo田が参加しました。
22:14	piyo田	こんにちは
22:15	hoge太郎	[スタンプ]
22:16	foo子	よろしくお願いします
```

**フォーマット**:
- ヘッダー行（1行目）: `[LINE] <トーク名>のトーク履歴`
- 保存日時行（2行目）: `保存日時：YYYY/MM/DD HH:MM`
- 空行（3行目）
- 日付行: `YYYY/MM/DD(曜日)`
- メッセージ行: `HH:MM<TAB>ユーザー名<TAB>メッセージ本文`
  - 区切り文字はタブ文字
  - ユーザー名が空の場合もあり（システムメッセージ）
- 画像/スタンプ等: `HH:MM<TAB>ユーザー名<TAB>[スタンプ]` または `HH:MM<TAB>ユーザー名<TAB>[写真]`

### APIレスポンス形式

#### 解析結果レスポンス

```json
{
  "status": "success",
  "data": {
    "analysis_period": {
      "start_date": "2024-01-01",
      "end_date": "2024-12-31"
    },
    "total_messages": 1500,
    "total_users": 3,
    "morphological_analysis": {
      "top_words": [
        {
          "word": "おうち",
          "count": 42,
          "part_of_speech": "名詞"
        }
      ]
    },
    "full_message_analysis": {
      "top_messages": [
        {
          "message": "おうち帰りたい",
          "count": 23
        }
      ]
    },
    "user_analysis": {
      "word_analysis": [
        {
          "user": "太郎",
          "top_words": [
            {
              "word": "おうち",
              "count": 20,
              "part_of_speech": "名詞"
            }
          ]
        }
      ],
      "message_analysis": [
        {
          "user": "太郎",
          "top_messages": [
            {
              "message": "おうち帰りたい",
              "count": 10
            }
          ]
        }
      ]
    }
  }
}
```

#### エラーレスポンス

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_FILE_FORMAT",
    "message": "アップロードされたファイルの形式が無効です"
  }
}
```

## API仕様

### エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/` | ルートエンドポイント（API基本情報） |
| GET | `/api/v1/health` | ヘルスチェック |
| POST | `/api/v1/analyze` | トーク履歴解析 |

### 詳細仕様

#### ルートエンドポイント

```
GET /
```

**レスポンス**:
```json
{
  "message": "Welcome to LINE Talk Analyzer API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

#### ヘルスチェック

```
GET /api/v1/health
```

**レスポンス**:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

#### トーク履歴解析

```
POST /api/v1/analyze
```

**リクエスト** (multipart/form-data):
- `file`: LINEトーク履歴ファイル（.txt形式、必須）
- `top_n`: 取得する上位単語数（オプション、デフォルト: 50）
- `min_word_length`: 最小単語長（オプション、デフォルト: 1）
- `max_word_length`: 最大単語長（オプション、デフォルト: なし）
- `min_message_length`: 最小メッセージ長（オプション、デフォルト: 1）
- `max_message_length`: 最大メッセージ長（オプション、デフォルト: なし）
- `min_word_count`: 最小単語出現回数（オプション、デフォルト: 2）
- `min_message_count`: 最小メッセージ出現回数（オプション、デフォルト: 2）
- `start_date`: 解析開始日時（オプション、YYYY-MM-DD HH:MM:SS形式）
- `end_date`: 解析終了日時（オプション、YYYY-MM-DD HH:MM:SS形式）

**レスポンス**: 上記参照

**エラーコード**:
- `400`: ファイルが指定されていない、ファイル形式が無効
- `413`: ファイルサイズが大きすぎる（上限: 50MB）
- `500`: サーバー内部エラー

## CORS設定

フロントエンドからのアクセスを許可するため、以下の設定を行う：

- **許可オリジン**: 環境変数 `ALLOWED_ORIGINS` で設定（デフォルト: `["http://localhost:3000"]`）
- **許可メソッド**: `["GET", "POST"]`
- **許可ヘッダー**: `["*"]`
- **クレデンシャル**: `True`
