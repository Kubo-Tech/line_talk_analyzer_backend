"""アプリケーション設定

環境変数を読み込み、アプリケーション全体で使用する設定を管理する
"""

import os
from functools import lru_cache


class Settings:
    """アプリケーション設定クラス

    環境変数から設定値を読み込み、デフォルト値を提供する
    """

    def __init__(self) -> None:
        """設定を初期化する"""
        # アプリケーション基本情報
        self.APP_NAME: str = os.getenv("APP_NAME", "LINE Talk Analyzer")
        self.APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

        # CORS設定
        self.ALLOWED_ORIGINS: list[str] = self._parse_origins(
            os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        )

        # ファイルアップロード設定
        self.MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
        self.MAX_FILE_SIZE_BYTES: int = self.MAX_FILE_SIZE_MB * 1024 * 1024

        # 解析設定
        self.DEFAULT_TOP_N: int = int(os.getenv("DEFAULT_TOP_N", "50"))
        self.MIN_WORD_LENGTH: int = int(os.getenv("MIN_WORD_LENGTH", "1"))
        self.MIN_MESSAGE_LENGTH: int = int(os.getenv("MIN_MESSAGE_LENGTH", "2"))

    def _parse_origins(self, origins_str: str) -> list[str]:
        """カンマ区切りのオリジン文字列をリストに変換する

        Args:
            origins_str (str): カンマ区切りのオリジン文字列

        Returns:
            list[str]: オリジンのリスト
        """
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得する

    lru_cacheによりインスタンスがキャッシュされ、
    アプリケーション全体で同じインスタンスが使用される

    Returns:
        Settings: 設定インスタンス
    """
    return Settings()
