# LINE Talk Analyzer Backend

LINEトーク履歴を解析して、1年間の流行語大賞を表示するWebアプリケーションのバックエンドです。

## 概要

- LINEトーク履歴ファイル（.txt形式）をアップロード
- 形態素解析（MeCab）で単語を抽出・集計
- メッセージ全文も1つの単語として集計
- REST APIで解析結果をJSON形式で返却

## 技術スタック

- **言語**: Python 3.11
- **Webフレームワーク**: FastAPI
- **形態素解析**: MeCab + mecab-ipadic-neologd
- **コンテナ**: Docker + Docker Compose

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

詳細な仕様は `doc/SPEC.md` を参照してください。

### 主なエンドポイント

- `GET /api/v1/health` - ヘルスチェック
- `POST /api/v1/analyze` - トーク履歴解析

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