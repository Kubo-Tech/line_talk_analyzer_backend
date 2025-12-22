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
[LINE] サンプルグループのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	おはようございます
22:13		piyo田が参加しました。
22:14	piyo田	こんにちは
22:15	hoge山fuga太郎	[スタンプ]
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
1. テキストファイルを読み込み、ヘッダーと保存日時行をスキップ
2. 行ごとに読み込み
3. 日付行（`YYYY/MM/DD(曜日)`形式）を検出して現在の日付を更新
4. メッセージ行をタブ文字で分割して解析（時刻、ユーザー名、メッセージ本文）
5. システムメッセージ（ユーザー名が空）、画像（`[写真]`）、スタンプ（`[スタンプ]`）等は除外
6. 構造化データ（リスト）として返却

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
   - 例: 「それな」を含む「それな；；」をカウント
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

**重要**: 各PRの作業が完了したら、以下を必ず実施すること：
1. `/app/doc/PR/PRxx.md`ファイルを作成（xxはPR番号）
   - 実装内容、テスト結果、修正内容などを詳細に記載
   - 既存のPR01.md、PR03.md、PR04.mdを参考にする
2. 本仕様書（SPEC.md）の該当PRのタスクチェックボックスにチェック（`[ ]` → `[x]`）を入れる

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
- [x] mypy.iniの作成（既存があれば確認）
- [x] .vscode/settings.jsonの確認・更新
- [x] .vscode/extensions.jsonの確認・更新
- [x] requirements-ci.txtの確認・更新
  - pytest
  - pytest-cov
  - pytest-asyncio
  - black
  - isort
  - flake8
  - mypy
- [x] .github/workflows/ci.ymlの確認・更新

**テスト計画**:
- 各ツールが正常に動作すること
- サンプルコードでリント・フォーマットが実行されること

**依存**: なし

---

### Phase 2: データ層の実装（並列実行可能）

#### PR#3: データモデル定義
**目的**: APIのリクエスト/レスポンスモデルの定義

**タスク**:
- [x] `app/models/request.py`の実装
  - `AnalyzeRequest`モデル
  - バリデーション定義
- [x] `app/models/response.py`の実装
  - `AnalysisResult`モデル
  - `WordAnalysisResult`モデル
  - `MessageAnalysisResult`モデル
  - `ErrorResponse`モデル
- [x] 型アノテーション完備
- [x] Docstring完備

**テスト計画**:
- 単体テスト: `tests/unit/test_models.py`
  - [x] 各モデルのインスタンス化
  - [x] バリデーションエラーのテスト
  - [x] JSONシリアライズ/デシリアライズのテスト

**依存**: PR#2（コード品質ツール）

---

#### PR#4: LINEトーク履歴パーサーの実装
**目的**: トーク履歴の構造化

**タスク**:
- [x] `app/services/parser.py`の実装
  - `Message`データクラス
  - `LineMessageParser`クラス
    - `parse()`メソッド: ファイルを読み込んで構造化
    - `_parse_date_line()`メソッド: 日付行の解析
    - `_parse_message_line()`メソッド: メッセージ行の解析
- [x] 正規表現パターンの定義
- [x] エラーハンドリング
- [x] テスト用サンプルデータ作成: `tests/fixtures/sample_talk.txt`

**テスト計画**:
- 単体テスト: `tests/unit/test_parser.py`
  - [x] 正常系: 標準的なトーク履歴の解析
  - [x] 異常系: 不正なフォーマット
  - [x] 境界値: 空ファイル、1メッセージのみ
  - [x] 画像・スタンプ行の除外確認
  - [x] 複数日付にまたがるデータ
  - [x] 特殊文字を含むユーザー名・メッセージ

**依存**: PR#2（コード品質ツール）

---

#### PR#5: 形態素解析サービスの実装
**目的**: MeCabによる単語抽出

**タスク**:
- [x] `app/services/morphological.py`の実装
  - `MorphologicalAnalyzer`クラス
    - `analyze()`メソッド: テキストを単語に分解
    - `_filter_by_pos()`メソッド: 品詞フィルタリング
    - `_filter_by_length()`メソッド: 文字数フィルタリング
- [x] MeCab初期化処理
- [x] 品詞マッピングの定義
- [x] エラーハンドリング

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
- [x] `app/services/word_counter.py`の実装
  - `WordCounter`クラス
    - `count_morphological_words()`メソッド: 形態素解析結果の集計
    - `count_full_messages()`メソッド: メッセージ全文の集計
    - `_find_partial_matches()`メソッド: 部分一致検索
- [x] カウント結果のデータ構造定義
- [x] 出現情報の記録処理

**テスト計画**:
- 単体テスト: `tests/unit/test_word_counter.py`
  - [x] 形態素解析結果のカウント
  - [x] メッセージ全文の完全一致カウント
  - [x] メッセージ全文の部分一致カウント
  - [x] 同一単語が複数のメッセージに出現するケース
  - [x] 1メッセージ内に対象文字列が複数回出現するケース（非重複カウント）
  - [x] 空のデータセット
  - [x] 大量データでのパフォーマンス（オプション）

**依存**: PR#4（パーサー）、PR#5（形態素解析）

**完了**: ✅

---

#### PR#7: 統合解析サービスの実装
**目的**: 全処理を統合

**タスク**:
- [x] `app/services/analyzer.py`の実装
  - `TalkAnalyzer`クラス
    - `analyze()`メソッド: 統合解析処理
    - `_format_response()`メソッド: レスポンス整形
    - `_filter_by_period()`メソッド: 期間フィルタリング
- [x] 各サービスの連携処理
- [x] ソート・上位N件抽出
- [x] エラーハンドリング
- [x] 期間指定機能（start_date/end_date）の実装

**テスト計画**:
- 単体テスト: `tests/unit/test_analyzer.py`
  - [x] エンドツーエンドの解析処理
  - [x] 上位N件の取得確認
  - [x] 期間の計算確認
  - [x] 統計情報の正確性
  - [x] 期間指定機能のテスト（6件）
- 統合テスト（次Phaseに含む）

**依存**: PR#6（単語カウンター）

**完了**: ✅

---

### Phase 4: API層の実装（PR#7完了後）

#### PR#8: FastAPIアプリケーション構築
**目的**: REST APIの提供

**タスク**:
- [x] `app/main.py`の実装
  - FastAPIアプリケーションの初期化
  - CORSミドルウェアの設定
  - ルーターの登録
- [x] `app/core/config.py`の実装
  - 環境変数読み込み
  - 設定クラス定義
- [x] `app/core/cors.py`の実装
  - CORS設定
- [x] `app/api/v1/router.py`の実装
  - APIルーターの統合
- [x] `app/api/v1/endpoints/health.py`の実装
  - ヘルスチェックエンドポイント
- [x] `app/api/v1/endpoints/analyze.py`の実装
  - 解析エンドポイント
  - ファイルアップロード処理
  - バリデーション
  - エラーハンドリング

**テスト計画**:
- 統合テスト: `tests/integration/test_api.py`
  - [x] ヘルスチェックエンドポイント
  - [x] 解析エンドポイントの正常系
  - [x] 解析エンドポイントの異常系
    - [x] ファイルなし
    - [x] 不正なファイル形式
    - [x] ファイルサイズ超過
  - [x] CORS設定の確認
  - [x] 各種パラメータの動作確認

**依存**: PR#7（統合解析サービス）

**完了**: ✅

---

### Phase 5: 総合テストとドキュメント（全PR完了後）

#### PR#9: E2Eテストと最終調整
**目的**: 本番環境への準備

**タスク**:
- [x] E2Eテストの実装
  - 実際のLINEトーク履歴を使用した解析
    - talk/sample.txtの2025年分を解析
    - 結果を簡易的に表示、確認
  - レスポンス時間の測定
    - sample.txtは約18MB。解析に10秒以内を目標
    - メモリ使用量の監視
- [x] パフォーマンス最適化
    - 部分一致検索のO(N²)問題を発見（387秒 → 2.5秒に154倍高速化）
    - 部分一致検索を完全削除してコードをシンプル化
- [x] 流行語品質の改善
    - 最小単語長を2文字に変更（1文字ノイズ除外）
    - ストップワード機能実装（67単語除外）
    - 基本形表示に統一（活用形 → 辞書形）
- [x] README.mdの完成
  - API仕様の詳細
  - 使用例（curl、Python、JavaScript）
  - ストップワード機能の説明
  - パフォーマンス情報
  - トラブルシューティング

**テスト計画**:
- [x] 全ての単体テストをパス（125テスト）
- [x] 全ての統合テストをパス（16テスト）
- [x] E2Eテスト（2テスト）
  - 2025年分: 2.48秒、41,539メッセージ ✅
  - 全期間: 9.82秒、272,878メッセージ ✅
- [x] 実際のトーク履歴で動作確認

**依存**: PR#1〜PR#8すべて

**完了**: ✅

---

### Phase 6: デプロイと公開（PR#9完了後）

#### PR#10: Renderへのデプロイ
**目的**: バックエンドAPIを本番環境に公開

**タスク**:
- [ ] Renderアカウントの作成
  - https://render.com でGitHubアカウントを使用してサインアップ
- [ ] Web Serviceの作成
  - Dashboard → "New" → "Web Service"
  - GitHubリポジトリ `line_talk_analyzer_backend` を接続
  - Root Directoryを `.` に設定
- [ ] デプロイ設定
  ```yaml
  Name: line-talk-analyzer-api
  Environment: Docker
  Region: Singapore (最寄りのアジアリージョン)
  Branch: main
  Dockerfile Path: ./Dockerfile
  Docker Build Context Directory: ./
  Plan: Free
  ```
- [ ] 環境変数の設定
  ```
  PORT=8001
  ALLOWED_ORIGINS=http://localhost:3000,https://<vercel-url>.vercel.app
  ```
  ※ Vercelデプロイ後にURLを追加更新
- [ ] デプロイの実行
  - "Create Web Service" をクリック
  - 自動的にDockerビルド＆デプロイが開始
  - URLが発行される（例: `https://line-talk-analyzer-api.onrender.com`）
- [ ] 動作確認
  - ヘルスチェック: `https://<your-url>.onrender.com/api/v1/health`
  - レスポンスが返ることを確認
- [ ] 注意事項の文書化
  - 無料プランは15分アイドルでスリープ
  - 初回アクセス時は起動に30秒程度かかる
  - 月750時間制限（実質24/7稼働可能）

**テスト計画**:
- [ ] デプロイ成功の確認
- [ ] ヘルスチェックエンドポイントの動作確認
- [ ] 解析エンドポイントの動作確認（curl/Postmanで実行）
- [ ] CORS設定の動作確認
- [ ] スリープからの復帰テスト（15分以上放置後にアクセス）

**依存**: PR#9（E2Eテストと最終調整）

**完了**: 

---

#### Issue#01: appearancesフィールドの削除
**目的**: レスポンスデータサイズの削減によるモバイル対応の改善

**背景**:
- デプロイ後のスマホでの動作確認で問題が発覚
- 会話量の多いトーク履歴（約27万メッセージ）の解析結果が約4MBと巨大
- フロントエンド側でセッションストレージに保存しようとすると容量制限でエラー
- 試験的に`appearances`フィールドを削除したところ、0.05MBまで削減（約80分の1）
- `appearances`はもともと時系列解析などの将来的な拡張を見越して用意したもの
- しかし、現時点でフロントエンドでは使用されておらず、データ量だけが増大している
- **教訓**: フロントエンドに渡すデータは、バックエンド側で適切に処理・集約してから最小限のデータのみを返すべき

**タスク**:
- [x] `app/models/response.py`の修正
  - `WordAnalysisResult`から`appearances`フィールドを削除
  - `MessageAnalysisResult`から`appearances`フィールドを削除
  - `UserWordAnalysisResult`から`appearances`フィールドを削除（存在する場合）
  - `UserMessageAnalysisResult`から`appearances`フィールドを削除（存在する場合）
- [x] `app/services/word_counter.py`の修正
  - `appearances`収集処理をコメントアウト
  - 将来の時系列解析のために処理ロジックは保持
  - コメントで削除理由と今後の拡張方法を明記
- [x] `app/services/analyzer.py`の修正
  - `appearances`に関する処理をコメントアウト
  - レスポンス整形時に`appearances`を含めない
  - 将来の拡張のためのコメントを追加
- [x] テストコードの修正
  - `tests/unit/test_models.py`: `appearances`の検証を削除
  - `tests/unit/test_word_counter.py`: `appearances`のテストをコメントアウト（処理は残すため）
  - `tests/unit/test_analyzer.py`: `appearances`のアサーションを削除
  - `tests/integration/test_api.py`: APIレスポンスの`appearances`チェックを削除
  - `tests/e2e/test_real_data.py`: `appearances`の検証を削除
- [x] ドキュメントの更新
  - `README.md`: レスポンス例から`appearances`を削除
  - `doc/SPEC.md`: 
    - セクション3.2.1のレスポンス例を更新
    - Issue#01の完了チェック

**将来の拡張に向けた方針**:
- 時系列解析、ユーザー行動分析などの機能を追加する際は、以下のアプローチを検討：
  1. **専用エンドポイントの追加**: `/api/v1/analyze/timeline`など、詳細データが必要な場合のみ呼び出す
  2. **ページネーション**: `appearances`を返す場合は、limit/offsetで分割取得
  3. **データベース保存**: 解析結果をDB保存し、必要に応じてクエリで取得
  4. **サマリーデータのみ返却**: 日別集計、月別集計など、集約済みデータを返す
- コメントアウトした処理は、上記実装時の参考コードとして活用

**影響範囲**:
- レスポンスモデル: 3ファイル
- サービス層: 2ファイル
- テストコード: 5ファイル
- ドキュメント: 2ファイル

**期待される効果**:
- レスポンスサイズ: 約4MB → 約0.05MB（約80倍削減）
- モバイルブラウザでのセッションストレージ保存が可能に
- ネットワーク転送速度の向上
- フロントエンドのメモリ使用量削減
- ユーザー体験の改善

**テスト計画**:
- [x] 全ての単体テストがパスすること
- [x] 全ての統合テストがパスすること
- [x] E2Eテストで実際のレスポンスサイズを確認
  - 2025年分（41,539メッセージ）: 50KB以下を目標
  - 全期間（272,878メッセージ）: 200KB以下を目標
- [x] デプロイ後、スマホでの動作確認
  - セッションストレージへの保存が成功すること
  - 解析結果の表示が正しく動作すること

**依存**: PR#9（E2Eテストと最終調整）

**完了**: ✅

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
