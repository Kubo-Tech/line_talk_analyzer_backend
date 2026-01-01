# 設定管理

## 概要

アプリケーションの設定は以下の3層で管理されています：

1. **`app/__version__.py`** - バージョン情報（Git管理対象）
2. **`app/core/config.py`** - 設定ロジックとデフォルト値（Git管理対象）
3. **`.env`ファイル** - 環境固有の設定値（Git管理対象外）

## ファイル構成

| ファイル | 用途 | Git管理 | 更新頻度 |
|---------|------|---------|----------|
| `app/__version__.py` | バージョン番号・アプリ名 | ✓ | リリース毎 |
| `app/core/config.py` | 設定ロジック | ✓ | 機能追加時 |
| `.env.example` | 設定テンプレート | ✓ | 設定項目変更時 |
| `.env` | 環境固有の値 | ✗ | 環境毎 |

## 環境変数一覧

環境変数を使用して設定を管理（`app/core/config.py`）:

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `APP_NAME` | `__version__.py`から取得 | アプリケーション名 |
| `APP_VERSION` | `__version__.py`から取得 | バージョン |
| `ALLOWED_ORIGINS` | "http://localhost:3000" | CORS許可オリジン（カンマ区切り） |
| `MAX_FILE_SIZE_MB` | 50 | 最大ファイルサイズ（MB） |
| `DEFAULT_TOP_N` | 50 | デフォルト上位取得数 |
| `MIN_WORD_LENGTH` | 1 | 最小単語長 |
| `MIN_MESSAGE_LENGTH` | 2 | 最小メッセージ長 |
| `ENABLE_DEMO_MODE` | "true" | デモモードの有効化 |
| `DEMO_TRIGGER_FILENAME` | "__DEMO__.txt" | デモモードトリガーファイル名 |
| `DEMO_RESPONSE_DELAY_SECONDS` | 3.0 | デモレスポンスの遅延時間（秒） |

## 設定ファイルの使用方法

### 開発環境のセットアップ

1. `.env.example`をコピーして`.env`ファイルを作成：
   ```bash
   cp .env.example .env
   ```

2. 必要に応じて`.env`ファイルを編集：
   ```bash
   # デフォルト値のまま使用する場合は編集不要
   # 変更したい項目のみ編集する
   ```

3. Dockerコンテナを起動：
   ```bash
   docker-compose up --build
   ```

### バージョン更新の手順

バージョン情報を更新する場合は、`app/__version__.py`のみを編集してください：

```python
# app/__version__.py
__version__ = "1.1.0"  # バージョンを更新
__app_name__ = "LINE Talk Analyzer"
```

**注意**: 環境変数で`APP_VERSION`を設定している場合、そちらが優先されます。

### 環境別の設定管理

異なる環境（開発、ステージング、本番）で異なる設定を使用する場合：

```bash
# 開発環境
.env                  # Git管理対象外

# 本番環境
# 環境変数を直接設定するか、デプロイツールで管理
export ALLOWED_ORIGINS=https://your-domain.com
export MAX_FILE_SIZE_MB=100
```

## 設定の優先順位

設定値の優先順位は以下の通りです（上が優先）：

1. **環境変数** - OS環境変数または`.env`ファイル
2. **`__version__.py`** - バージョン情報のデフォルト値
3. **`config.py`** - その他のデフォルト値

例：
```python
# APP_NAMEの決定ロジック
# 1. 環境変数 APP_NAME が設定されている → それを使用
# 2. 環境変数がない → __version__.py の __app_name__ を使用
```

## よくある質問

### Q. `.env`ファイルは必須ですか？

いいえ、オプションです。`.env`ファイルがない場合、すべてデフォルト値が使用されます。

### Q. バージョン番号を変更するには？

`app/__version__.py`の`__version__`を編集してください。リリース時にこのファイルのみを更新します。

### Q. 本番環境で異なる設定を使うには？

本番環境では`.env`ファイルを使わず、環境変数を直接設定することを推奨します：

```bash
# Docker Composeの場合
docker-compose.yml の environment セクションで設定

# Kubernetesの場合
ConfigMap や Secret で管理
```

### Q. 設定を追加するには？

1. `app/core/config.py`の`Settings`クラスに新しい設定を追加
2. `.env.example`に新しい環境変数を追加（ドキュメントとして）
3. このドキュメントの環境変数一覧テーブルを更新
