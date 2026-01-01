# LINE Talk Analyzer Backend

LINEのトーク履歴を解析し、1年間の流行語大賞を表示するWebアプリケーションのバックエンドです。

## 概要

### 主な機能

- LINEトーク履歴ファイル（.txt形式）のアップロードと解析
- 形態素解析による単語の抽出と集計
- メッセージ全文の集計
- ユーザー別流行語ランキング
- 期間指定フィルタ
- ストップワード機能
- REST API（JSON形式）
- CORS対応

### 技術スタック

- **言語**: Python 3.11+
- **Webフレームワーク**: FastAPI 0.104+
- **形態素解析**: MeCab + mecab-python3
- **辞書**: mecab-ipadic-neologd（新語対応）
- **テストフレームワーク**: pytest
- **コンテナ**: Docker + Docker Compose
- **コード品質**: Black, isort, flake8, mypy

## 環境構築

### 前提条件

- Docker
- Docker Compose

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/Kubo-Tech/line_talk_analyzer_backend.git
cd line_talk_analyzer_backend

# Dockerコンテナをビルド・起動
docker-compose up --build
```

APIサーバーが起動します：
- URL: http://localhost:8001
- APIドキュメント: http://localhost:8001/docs

### 環境変数の設定

環境変数の設定は**オプション**です。設定しない場合、デフォルト値が使用されます。

変更したい場合は`.env.example`をコピーして`.env`ファイルを作成してください：

```bash
cp .env.example .env
# .envファイルを編集
```

**注意**:
- `.env`ファイルはGit管理対象外です（機密情報の保護）
- アプリケーション名とバージョンは`app/__version__.py`から自動取得されます
- 環境変数で上書きしない限り、デフォルト値が使用されます

詳細は[CONFIG.md](doc/CONFIG.md)を参照してください。

## 開発

### 利用可能なコマンド

| コマンド | 説明 |
|---------|------|
| `docker-compose up` | サーバーを起動 |
| `docker-compose down` | サーバーを停止 |
| `docker-compose restart` | サーバーを再起動 |
| `docker-compose logs -f api` | ログを表示 |
| `docker-compose exec api bash` | コンテナに入る |

### コンテナ内でのコマンド

```bash
# コンテナに入る
docker-compose exec api bash

# テスト実行
pytest

# カバレッジ付きテスト
pytest --cov=app --cov-report=html

# リント/フォーマットチェック
isort --profile=black --line-length=100 --check-only app/
flake8 app/
mypy app/ --config-file=mypy.ini
```

## API使用例

### curlでの使用例

```bash
# 基本的な解析
curl -X POST "http://localhost:8001/api/v1/analyze" \
  -F "file=@talk_history.txt"

# パラメータ指定
curl -X POST "http://localhost:8001/api/v1/analyze" \
  -F "file=@talk_history.txt" \
  -F "top_n=100" \
  -F "min_word_length=2" \
  -F "start_date=2025-01-01 00:00:00" \
  -F "end_date=2025-12-31 23:59:59"
```

### Pythonでの使用例

```python
import requests

url = "http://localhost:8001/api/v1/analyze"
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

fetch('http://localhost:8001/api/v1/analyze', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => console.log('解析結果:', data));
```

## トラブルシューティング

### MeCabが動作しない

**症状**: `RuntimeError: MeCab initialization failed`

**対処法**:
```bash
# コンテナを再ビルド
docker-compose down
docker-compose up --build
```

### ファイルアップロードでエラー

**症状**: `413 Request Entity Too Large`

**対処法**:
- ファイルサイズが50MBを超えていないか確認
- 環境変数`MAX_FILE_SIZE_MB`で上限を変更可能

### 解析結果に不要な単語が含まれる

**症状**: 「する」「ある」などの一般的な単語が上位に来る

**対処法**:
- `app/data/stopwords.json`に除外したい単語を追加

### 特定期間のデータが取得できない

**症状**: `start_date`/`end_date`を指定してもデータが0件

**対処法**:
- 日時形式を確認: `YYYY-MM-DD HH:MM:SS`
- トーク履歴ファイルの日付形式が正しいか確認

## ドキュメント

- [API仕様](./doc/API.md)
- [システムアーキテクチャ](./doc/ARCHITECTURE.md)
- [設定管理](./doc/CONFIG.md)
- [ディレクトリ構成](./doc/DIRECTORY.md)
- [テスト戦略](./doc/TEST.md)
- [コーディング規約](./doc/CODING_RULE.md)
- [単語カウントルール](./doc/WORD_COUNT_RULE.md)
- [PRドキュメント](./doc/PR/)
- [Issue対応履歴](./doc/ISSUE/)

## 参考文献

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [MeCab公式サイト](https://taku910.github.io/mecab/)
- [mecab-ipadic-neologd](https://github.com/neologd/mecab-ipadic-neologd)

## ライセンス

MIT

