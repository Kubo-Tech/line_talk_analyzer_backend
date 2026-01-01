# ディレクトリ構成

以下は、`line_talk_analyzer_backend` プロジェクトのディレクトリ構成の概要です。

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
│   ├── data/
│   │   ├── __init__.py
│   │   ├── demo_response.json     # デモレスポンスデータ
│   │   └── stopwords.json         # ストップワード定義
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py             # リクエストモデル
│   │   └── response.py            # レスポンスモデル
│   └── services/
│       ├── __init__.py
│       ├── parser.py              # LINEトーク履歴パーサー
│       ├── morphological.py      # 形態素解析
│       ├── word_counter.py       # 単語カウンター
│       ├── analyzer.py            # 統合解析サービス
│       └── demo_service.py        # デモデータサービス
├── doc/
│   ├── CODING_RULE.md             # コーディング規約
│   ├── DIRECTORY.md               # このファイル
│   ├── PLAN.md                    # 開発計画
│   ├── SPEC.md                    # 仕様書
│   ├── WORD_COUNT_RULE.md         # 単語カウントルール
│   ├── ISSUE/                     # Issue管理
│   └── PR/                        # PRドキュメント
├── talk/
│   ├── __DEMO__.txt               # デモ用トーク履歴
│   └── *.txt                      # テスト用トーク履歴ファイル
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   └── sample_talk.txt        # テスト用サンプルデータ
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_parser.py
│   │   ├── test_morphological.py
│   │   ├── test_word_counter.py
│   │   ├── test_analyzer.py
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   └── test_demo_service.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_api.py
│   └── e2e/
│       ├── __init__.py
│       ├── test_demo.py
│       └── test_real_data.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-ci.txt
├── mypy.ini
├── .dockerignore
├── .gitignore
└── README.md
```