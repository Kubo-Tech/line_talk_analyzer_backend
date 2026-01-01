# 実装計画

このドキュメントは、LINEトーク解析APIバックエンドの実装計画を詳細に記述したものです。各フェーズごとにPR単位でタスクを分割し、目的、タスク内容、テスト計画、依存関係を明確にしています。

## PRマージ前のチェックリスト

1. `/app/doc/PR/PRxx.md`ファイルを作成（xxはPR番号）
   - 実装内容、テスト結果、修正内容などを詳細に記載
2. 本書（PLAN.md）の該当PRのタスクチェックボックスにチェック（`[ ]` → `[x]`）を入れる

## Phase 1: プロジェクト基盤構築（並列実行可能）

### PR#1: Docker環境セットアップ
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

### PR#2: コード品質ツールのセットアップ
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

## Phase 2: データ層の実装（並列実行可能）

### PR#3: データモデル定義
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

### PR#4: LINEトーク履歴パーサーの実装
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

### PR#5: 形態素解析サービスの実装
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

## Phase 3: ビジネスロジック層の実装（PR#4, PR#5完了後）

### PR#6: 単語カウンターの実装
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

### PR#7: 統合解析サービスの実装
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

## Phase 4: API層の実装（PR#7完了後）

### PR#8: FastAPIアプリケーション構築
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

## Phase 5: 総合テストとドキュメント（全PR完了後）

### PR#9: E2Eテストと最終調整
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

## Phase 6: デプロイと公開（PR#9完了後）

### PR#10: Renderへのデプロイ
**目的**: バックエンドAPIを本番環境に公開

**タスク**:
- [x] Renderアカウントの作成
  - https://render.com でGitHubアカウントを使用してサインアップ
- [x] Web Serviceの作成
  - Dashboard → "New" → "Web Service"
  - GitHubリポジトリ `line_talk_analyzer_backend` を接続
  - Root Directoryを `.` に設定
- [x] デプロイ設定
  ```yaml
  Name: line-talk-analyzer-api
  Environment: Docker
  Region: Singapore (最寄りのアジアリージョン)
  Branch: main
  Dockerfile Path: ./Dockerfile
  Docker Build Context Directory: ./
  Plan: Free
  ```
- [x] 環境変数の設定
  ```
  PORT=8001
  ALLOWED_ORIGINS=http://localhost:3000,https://<vercel-url>.vercel.app
  ```
  ※ Vercelデプロイ後にURLを追加更新
- [x] デプロイの実行
  - "Create Web Service" をクリック
  - 自動的にDockerビルド＆デプロイが開始
  - URLが発行される（例: `https://line-talk-analyzer-api.onrender.com`）
- [x] 動作確認
  - ヘルスチェック: `https://<your-url>.onrender.com/api/v1/health`
  - レスポンスが返ることを確認
- [x] 注意事項の文書化
  - 無料プランは15分アイドルでスリープ
  - 初回アクセス時は起動に30秒程度かかる
  - 月750時間制限（実質24/7稼働可能）

**テスト計画**:
- [x] デプロイ成功の確認
- [x] ヘルスチェックエンドポイントの動作確認
- [x] 解析エンドポイントの動作確認（curl/Postmanで実行）
- [x] CORS設定の動作確認
- [x] スリープからの復帰テスト（15分以上放置後にアクセス）

**依存**: PR#9（E2Eテストと最終調整）

**完了**: ✅

## 将来の拡張案

- 時系列グラフ用のデータ出力
- 感情分析の追加
- ユーザー別統計情報
- ワードクラウド用データ生成
- LLMでの要約生成
- 去年のランキングとの比較