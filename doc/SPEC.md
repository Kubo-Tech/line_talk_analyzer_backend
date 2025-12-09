# LINEトーク履歴解析バックエンド 仕様書

## 1. 概要

本プロジェクトは、LINEのトーク履歴を解析し、1年間の流行語大賞を表示するスマホ用Webアプリケーションのバックエンドです。

### 1.1 主な機能

- LINEトーク履歴ファイル（.txt形式）のアップロードと解析
- 形態素解析による単語の抽出と集計
- メッセージ全文を単語としてカウントする機能
- 集計結果をJSON形式で返すRESTful API
- フロントエンドとのCORS対応

### 1.2 技術スタック

- **言語**: Python 3.11+
- **Webフレームワーク**: FastAPI
- **形態素解析**: MeCab + mecab-python3
- **辞書**: mecab-ipadic-neologd（新語対応）
- **テストフレームワーク**: pytest
- **コンテナ**: Docker + Docker Compose
- **コード品質**: Black, isort, flake8, mypy

---

## 2. システムアーキテクチャ

```
[フロントエンド] ←→ [FastAPI] ←→ [LINEトーク解析エンジン]
                                        ↓
                                   [形態素解析(MeCab)]
```

### 2.1 ディレクトリ構成

```
line_talk_analyzer_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPIアプリケーションのエントリポイント
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── analyze.py    # 解析エンドポイント
│   │   │   │   └── health.py     # ヘルスチェック
│   │   │   └── router.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # 設定管理
│   │   └── cors.py                # CORS設定
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py             # リクエストモデル
│   │   └── response.py            # レスポンスモデル
│   ├── services/
│   │   ├── __init__.py
│   │   ├── parser.py              # LINEトーク履歴パーサー
│   │   ├── morphological.py      # 形態素解析
│   │   ├── word_counter.py       # 単語カウンター
│   │   └── analyzer.py            # 統合解析サービス
│   └── utils/
│       ├── __init__.py
│       └── validators.py          # バリデーション関数
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # pytest設定
│   ├── fixtures/
│   │   └── sample_talk.txt        # テスト用サンプルデータ
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_parser.py
│   │   ├── test_morphological.py
│   │   ├── test_word_counter.py
│   │   └── test_analyzer.py
│   └── integration/
│       ├── __init__.py
│       └── test_api.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-ci.txt
├── mypy.ini
├── .dockerignore
├── .gitignore
└── README.md
```

---

## 3. データ形式

### 3.1 入力データ形式（LINEトーク履歴）

```
2024.08.01 木曜日
22:12 hoge山fuga太郎 眠い
22:12 hoge山fuga太郎 おうち帰りたい
22:13 hoge山fuga太郎 働きたくないでござる
```

**フォーマット**:
- 日付行: `YYYY.MM.DD 曜日`
- メッセージ行: `HH:MM ユーザー名 メッセージ本文`
- 画像/スタンプ等: `HH:MM ユーザー名 画像` または `HH:MM ユーザー名 スタンプ`

### 3.2 APIレスポンス形式

#### 3.2.1 解析結果レスポンス

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
          "part_of_speech": "名詞",
          "appearances": [
            {
              "date": "2024-08-01T22:12:00",
              "user": "hoge山fuga太郎",
              "message": "おうち帰りたい"
            }
          ]
        }
      ]
    },
    "full_message_analysis": {
      "top_messages": [
        {
          "message": "おうち帰りたい",
          "exact_count": 15,
          "partial_count": 8,
          "total_count": 23,
          "appearances": [
            {
              "date": "2024-08-01T22:12:00",
              "user": "hoge山fuga太郎",
              "message": "おうち帰りたい",
              "match_type": "exact"
            },
            {
              "date": "2024-08-01T22:20:00",
              "user": "hoge山fuga太郎",
              "message": "おうち帰りたいよー",
              "match_type": "partial"
            }
          ]
        }
      ]
    }
  }
}
```

#### 3.2.2 エラーレスポンス

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_FILE_FORMAT",
    "message": "アップロードされたファイルの形式が無効です"
  }
}
```

---

## 4. API仕様

### 4.1 エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/health` | ヘルスチェック |
| POST | `/api/v1/analyze` | トーク履歴解析 |

### 4.2 詳細仕様

#### 4.2.1 ヘルスチェック

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

#### 4.2.2 トーク履歴解析

```
POST /api/v1/analyze
```

**リクエスト** (multipart/form-data):
- `file`: LINEトーク履歴ファイル（.txt形式）
- `top_n`: 取得する上位単語数（オプション、デフォルト: 50）
- `min_word_length`: 最小単語長（オプション、デフォルト: 1）
- `exclude_parts`: 除外品詞（オプション、カンマ区切り）

**レスポンス**: 3.2.1参照

**エラーコード**:
- `400`: ファイルが指定されていない、ファイル形式が無効
- `413`: ファイルサイズが大きすぎる（上限: 50MB）
- `500`: サーバー内部エラー

---

## 5. 解析処理の詳細

### 5.1 LINEトーク履歴パーサー (`services/parser.py`)

**責務**:
- LINEトーク履歴ファイルを読み込み、構造化データに変換

**処理フロー**:
1. テキストファイルを行ごとに読み込み
2. 日付行を検出して現在の日付を更新
3. メッセージ行を正規表現で解析（時刻、ユーザー名、メッセージ本文）
4. 画像・スタンプ等のメタメッセージは除外
5. 構造化データ（リスト）として返却

**データ構造**:
```python
@dataclass
class Message:
    datetime: datetime
    user: str
    content: str
```

### 5.2 形態素解析サービス (`services/morphological.py`)

**責務**:
- MeCabを使用して単語に分解し、品詞情報を付与

**処理フロー**:
1. メッセージ本文をMeCabで形態素解析
2. 品詞情報を抽出
3. 除外品詞（助詞、助動詞など）をフィルタリング
4. 最小単語長でフィルタリング
5. 単語リストを返却

**抽出対象品詞**（デフォルト）:
- 名詞（一般、固有名詞、サ変接続など）
- 動詞（自立）
- 形容詞（自立）
- 副詞
- 感動詞

### 5.3 単語カウンター (`services/word_counter.py`)

**責務**:
- 形態素解析結果とメッセージ全文の集計

#### 5.3.1 形態素解析結果のカウント

1. 各単語の出現回数を集計
2. 単語ごとに出現したメッセージ情報を記録
3. 品詞情報を保持

#### 5.3.2 メッセージ全文のカウント

1. 各メッセージを1単語として扱う
2. 完全一致カウント: 同一メッセージの出現回数
3. 部分一致カウント: そのメッセージを部分文字列として含む他のメッセージ
   - 例: 「まーん」を含む「まーん；；」をカウント
4. 両方の出現情報を記録

### 5.4 統合解析サービス (`services/analyzer.py`)

**責務**:
- 上記サービスを統合し、API向けのレスポンスを生成

**処理フロー**:
1. パーサーでトーク履歴を構造化
2. 形態素解析で単語抽出
3. 単語カウンターで集計
4. 上位N件を抽出してソート
5. APIレスポンス形式に整形

---

## 6. CORS設定

フロントエンドからのアクセスを許可するため、以下の設定を行う：

- **許可オリジン**: 環境変数 `ALLOWED_ORIGINS` で設定（デフォルト: `["http://localhost:3000"]`）
- **許可メソッド**: `["GET", "POST"]`
- **許可ヘッダー**: `["*"]`
- **クレデンシャル**: `True`

---

## 7. 設定管理

環境変数を使用して設定を管理（`core/config.py`）:

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `APP_NAME` | "LINE Talk Analyzer" | アプリケーション名 |
| `APP_VERSION` | "1.0.0" | バージョン |
| `ALLOWED_ORIGINS` | "http://localhost:3000" | CORS許可オリジン（カンマ区切り） |
| `MAX_FILE_SIZE_MB` | 50 | 最大ファイルサイズ（MB） |
| `DEFAULT_TOP_N` | 50 | デフォルト上位取得数 |
| `MIN_WORD_LENGTH` | 1 | 最小単語長 |

---

## 8. 実装計画

### Phase 1: プロジェクト基盤構築（並列実行可能）

#### PR#1: Docker環境セットアップ
**目的**: 開発環境のコンテナ化

**タスク**:
- [x] Dockerfileの作成
  - Python 3.11ベースイメージ
  - MeCabとmecab-ipadic-neologdのインストール
  - 依存パッケージのインストール
- [x] docker-compose.ymlの作成
  - APIサーバーコンテナ定義
  - ポートマッピング（8000:8000）
  - ボリュームマウント
- [x] .dockerignoreの作成
- [x] requirements.txtの更新
  - fastapi
  - uvicorn[standard]
  - mecab-python3
  - python-multipart
- [x] README.mdの更新（環境構築手順）

**テスト計画**:
- コンテナのビルドが成功すること
- コンテナ起動後にMeCabが使用可能なこと
- `docker-compose up`でサーバーが起動すること

**依存**: なし

---

#### PR#2: コード品質ツールのセットアップ
**目的**: コーディング規約の適用

**タスク**:
- [ ] mypy.iniの作成（既存があれば確認）
- [ ] .vscode/settings.jsonの確認・更新
- [ ] .vscode/extensions.jsonの確認・更新
- [ ] requirements-ci.txtの更新
  - pytest
  - pytest-cov
  - pytest-asyncio
  - black
  - isort
  - flake8
  - mypy
- [ ] GitHub Actions用CI設定ファイル作成（オプション）

**テスト計画**:
- 各ツールが正常に動作すること
- サンプルコードでリント・フォーマットが実行されること

**依存**: なし

---

### Phase 2: データ層の実装（並列実行可能）

#### PR#3: データモデル定義
**目的**: APIのリクエスト/レスポンスモデルの定義

**タスク**:
- [ ] `app/models/request.py`の実装
  - `AnalyzeRequest`モデル
  - バリデーション定義
- [ ] `app/models/response.py`の実装
  - `AnalysisResult`モデル
  - `WordAnalysisResult`モデル
  - `MessageAnalysisResult`モデル
  - `ErrorResponse`モデル
- [ ] 型アノテーション完備
- [ ] Docstring完備

**テスト計画**:
- 単体テスト: `tests/unit/test_models.py`
  - 各モデルのインスタンス化
  - バリデーションエラーのテスト
  - JSONシリアライズ/デシリアライズのテスト

**依存**: PR#2（コード品質ツール）

---

#### PR#4: LINEトーク履歴パーサーの実装
**目的**: トーク履歴の構造化

**タスク**:
- [ ] `app/services/parser.py`の実装
  - `Message`データクラス
  - `LineMessageParser`クラス
    - `parse()`メソッド: ファイルを読み込んで構造化
    - `_parse_date_line()`メソッド: 日付行の解析
    - `_parse_message_line()`メソッド: メッセージ行の解析
- [ ] 正規表現パターンの定義
- [ ] エラーハンドリング
- [ ] テスト用サンプルデータ作成: `tests/fixtures/sample_talk.txt`

**テスト計画**:
- 単体テスト: `tests/unit/test_parser.py`
  - 正常系: 標準的なトーク履歴の解析
  - 異常系: 不正なフォーマット
  - 境界値: 空ファイル、1メッセージのみ
  - 画像・スタンプ行の除外確認
  - 複数日付にまたがるデータ
  - 特殊文字を含むユーザー名・メッセージ

**依存**: PR#2（コード品質ツール）

---

#### PR#5: 形態素解析サービスの実装
**目的**: MeCabによる単語抽出

**タスク**:
- [ ] `app/services/morphological.py`の実装
  - `MorphologicalAnalyzer`クラス
    - `analyze()`メソッド: テキストを単語に分解
    - `_filter_by_pos()`メソッド: 品詞フィルタリング
    - `_filter_by_length()`メソッド: 文字数フィルタリング
- [ ] MeCab初期化処理
- [ ] 品詞マッピングの定義
- [ ] エラーハンドリング

**テスト計画**:
- 単体テスト: `tests/unit/test_morphological.py`
  - 正常系: 一般的な日本語文の解析
  - 各品詞の抽出確認
  - フィルタリング機能の確認
  - 空文字列の処理
  - 記号のみの文字列
  - 英数字混在テキスト

**依存**: PR#1（Docker環境でMeCabが必要）、PR#2（コード品質ツール）

---

### Phase 3: ビジネスロジック層の実装（PR#4, PR#5完了後）

#### PR#6: 単語カウンターの実装
**目的**: 単語とメッセージの集計

**タスク**:
- [ ] `app/services/word_counter.py`の実装
  - `WordCounter`クラス
    - `count_morphological_words()`メソッド: 形態素解析結果の集計
    - `count_full_messages()`メソッド: メッセージ全文の集計
    - `_find_partial_matches()`メソッド: 部分一致検索
- [ ] カウント結果のデータ構造定義
- [ ] 出現情報の記録処理

**テスト計画**:
- 単体テスト: `tests/unit/test_word_counter.py`
  - 形態素解析結果のカウント
  - メッセージ全文の完全一致カウント
  - メッセージ全文の部分一致カウント
  - 同一単語が複数のメッセージに出現するケース
  - 空のデータセット
  - 大量データでのパフォーマンス（オプション）

**依存**: PR#4（パーサー）、PR#5（形態素解析）

---

#### PR#7: 統合解析サービスの実装
**目的**: 全処理を統合

**タスク**:
- [ ] `app/services/analyzer.py`の実装
  - `TalkAnalyzer`クラス
    - `analyze()`メソッド: 統合解析処理
    - `_format_response()`メソッド: レスポンス整形
- [ ] 各サービスの連携処理
- [ ] ソート・上位N件抽出
- [ ] エラーハンドリング

**テスト計画**:
- 単体テスト: `tests/unit/test_analyzer.py`
  - エンドツーエンドの解析処理
  - 上位N件の取得確認
  - 期間の計算確認
  - 統計情報の正確性
- 統合テスト（次Phaseに含む）

**依存**: PR#6（単語カウンター）

---

### Phase 4: API層の実装（PR#7完了後）

#### PR#8: FastAPIアプリケーション構築
**目的**: REST APIの提供

**タスク**:
- [ ] `app/main.py`の実装
  - FastAPIアプリケーションの初期化
  - CORSミドルウェアの設定
  - ルーターの登録
- [ ] `app/core/config.py`の実装
  - 環境変数読み込み
  - 設定クラス定義
- [ ] `app/core/cors.py`の実装
  - CORS設定
- [ ] `app/api/v1/router.py`の実装
  - APIルーターの統合
- [ ] `app/api/v1/endpoints/health.py`の実装
  - ヘルスチェックエンドポイント
- [ ] `app/api/v1/endpoints/analyze.py`の実装
  - 解析エンドポイント
  - ファイルアップロード処理
  - バリデーション
  - エラーハンドリング

**テスト計画**:
- 統合テスト: `tests/integration/test_api.py`
  - ヘルスチェックエンドポイント
  - 解析エンドポイントの正常系
  - 解析エンドポイントの異常系
    - ファイルなし
    - 不正なファイル形式
    - ファイルサイズ超過
  - CORS設定の確認
  - 各種パラメータの動作確認

**依存**: PR#7（統合解析サービス）

---

### Phase 5: 総合テストとドキュメント（全PR完了後）

#### PR#9: E2Eテストと最終調整
**目的**: 本番環境への準備

**タスク**:
- [ ] E2Eテストの実装
  - 実際のLINEトーク履歴を使用した解析
  - レスポンス時間の測定
  - 大容量ファイルのテスト
- [ ] パフォーマンス最適化
- [ ] エラーメッセージの改善
- [ ] ログ出力の実装（オプション）
- [ ] README.mdの完成
  - API仕様の詳細
  - 使用例
  - トラブルシューティング

**テスト計画**:
- [ ] 全ての単体テストをパス
- [ ] 全ての統合テストをパス
- [ ] カバレッジ80%以上
- [ ] 実際のトーク履歴で動作確認

**依存**: PR#1〜PR#8すべて

---

## 9. テスト戦略

### 9.1 テストレベル

| レベル | ツール | カバレッジ目標 |
|--------|--------|---------------|
| 単体テスト | pytest | 80%以上 |
| 統合テスト | pytest + TestClient | 主要フロー100% |
| E2Eテスト | 実データ | 実用性確認 |

### 9.2 テストデータ

- **最小データセット**: 1日分、2ユーザー、10メッセージ
- **標準データセット**: 1ヶ月分、3ユーザー、500メッセージ
- **大規模データセット**: 1年分、5ユーザー、10000メッセージ
- **異常データセット**: 不正フォーマット、特殊文字、空ファイル

### 9.3 CI/CD

- PRごとに自動テスト実行
- コードカバレッジレポート生成
- リントとフォーマットチェック
- 型チェック（mypy）

---

## 10. 非機能要件

### 10.1 パフォーマンス

- 1万メッセージの解析を10秒以内で完了
- 最大ファイルサイズ: 50MB
- 同時リクエスト数: 10（初期）

### 10.2 セキュリティ

- ファイルアップロードのバリデーション
- ファイルサイズ制限
- タイムアウト設定（30秒）
- 悪意のあるファイル内容の検証（オプション）

### 10.3 可用性

- ヘルスチェックエンドポイントの提供
- エラーログの出力
- グレースフルシャットダウン

---

## 11. 今後の拡張案

- データベースへの解析結果保存
- ユーザー認証機能
- 複数ファイルの一括解析
- 時系列グラフ用のデータ出力
- 感情分析の追加
- ユーザー別統計情報
- ワードクラウド用データ生成

---

## 12. 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [MeCab公式サイト](https://taku910.github.io/mecab/)
- [mecab-ipadic-neologd](https://github.com/neologd/mecab-ipadic-neologd)
- [PEP8スタイルガイド](https://pep8-ja.readthedocs.io/ja/latest/)
