"""アプリケーション設定

環境変数を読み込み、アプリケーション全体で使用する設定を管理する
"""

import os
import warnings
from functools import lru_cache

from app.__version__ import __app_name__, __version__


class Settings:
    """アプリケーション設定クラス

    環境変数から設定値を読み込み、デフォルト値を提供する
    """

    def __init__(self) -> None:
        """設定を初期化する"""
        # アプリケーション基本情報
        self.APP_NAME: str = os.getenv("APP_NAME", __app_name__)
        self.APP_VERSION: str = os.getenv("APP_VERSION", __version__)

        # CORS設定
        self.ALLOWED_ORIGINS: list[str] = self._parse_origins(
            os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        )

        # ファイルアップロード設定
        self.MAX_FILE_SIZE_MB: int = self._get_int_env("MAX_FILE_SIZE_MB", 50)
        self.MAX_FILE_SIZE_BYTES: int = self.MAX_FILE_SIZE_MB * 1024 * 1024

        # 解析設定
        self.DEFAULT_TOP_N: int = self._get_int_env("DEFAULT_TOP_N", 50)
        self.MIN_WORD_LENGTH: int = self._get_int_env("MIN_WORD_LENGTH", 1)
        self.MIN_MESSAGE_LENGTH: int = self._get_int_env("MIN_MESSAGE_LENGTH", 2)

        # デモモード設定
        self.ENABLE_DEMO_MODE: bool = os.getenv("ENABLE_DEMO_MODE", "true").lower() in (
            "true",
            "1",
            "yes",
        )
        self.DEMO_TRIGGER_FILENAME: str = os.getenv(
            "DEMO_TRIGGER_FILENAME", "__DEMO__.txt"
        )
        self.DEMO_RESPONSE_DELAY_SECONDS: float = self._get_float_env(
            "DEMO_RESPONSE_DELAY_SECONDS", 3.0
        )

    def _get_int_env(self, key: str, default: int) -> int:
        """環境変数から整数値を安全に取得する

        環境変数の値が整数に変換できない場合は、デフォルト値を使用し、
        警告メッセージを表示する

        Args:
            key (str): 環境変数のキー
            default (int): デフォルト値

        Returns:
            int: 環境変数の値またはデフォルト値
        """
        value_str = os.getenv(key)
        if value_str is None:
            return default

        try:
            return int(value_str)
        except ValueError:
            warnings.warn(
                f"環境変数 {key} の値 '{value_str}' は整数に変換できません。"
                f"デフォルト値 {default} を使用します。",
                UserWarning,
                stacklevel=2,
            )
            return default

    def _get_float_env(self, key: str, default: float) -> float:
        """環境変数から浮動小数点数値を安全に取得する

        環境変数の値が浮動小数点数に変換できない場合は、デフォルト値を使用し、
        警告メッセージを表示する

        Args:
            key (str): 環境変数のキー
            default (float): デフォルト値

        Returns:
            float: 環境変数の値またはデフォルト値
        """
        value_str = os.getenv(key)
        if value_str is None:
            return default

        try:
            return float(value_str)
        except ValueError:
            warnings.warn(
                f"環境変数 {key} の値 '{value_str}' は浮動小数点数に変換できません。"
                f"デフォルト値 {default} を使用します。",
                UserWarning,
                stacklevel=2,
            )
            return default

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
