# 設定管理

環境変数を使用して設定を管理（`core/config.py`）:

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `APP_NAME` | "LINE Talk Analyzer" | アプリケーション名 |
| `APP_VERSION` | "1.0.0" | バージョン |
| `ALLOWED_ORIGINS` | "http://localhost:3000" | CORS許可オリジン（カンマ区切り） |
| `MAX_FILE_SIZE_MB` | 50 | 最大ファイルサイズ（MB） |
| `DEFAULT_TOP_N` | 50 | デフォルト上位取得数 |
| `MIN_WORD_LENGTH` | 1 | 最小単語長 |
| `MIN_MESSAGE_LENGTH` | 2 | 最小メッセージ長 |
| `ENABLE_DEMO_MODE` | "true" | デモモードの有効化 |
| `DEMO_TRIGGER_FILENAME` | "__DEMO__.txt" | デモモードトリガーファイル名 |
| `DEMO_RESPONSE_DELAY_SECONDS` | 3.0 | デモレスポンスの遅延時間（秒） |
