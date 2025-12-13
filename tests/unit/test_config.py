"""config.pyのユニットテスト"""

import os
import warnings
from unittest import mock

from app.core.config import Settings, get_settings


class TestSettings:
    """Settingsクラスのテスト"""

    def test_default_values(self) -> None:
        """デフォルト値が正しく設定されることを確認"""
        settings = Settings()
        assert settings.APP_NAME == "LINE Talk Analyzer"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.ALLOWED_ORIGINS == ["http://localhost:3000"]
        assert settings.MAX_FILE_SIZE_MB == 50
        assert settings.MAX_FILE_SIZE_BYTES == 50 * 1024 * 1024
        assert settings.DEFAULT_TOP_N == 50
        assert settings.MIN_WORD_LENGTH == 1
        assert settings.MIN_MESSAGE_LENGTH == 2

    def test_custom_env_values(self) -> None:
        """環境変数からカスタム値が読み込まれることを確認"""
        with mock.patch.dict(
            os.environ,
            {
                "APP_NAME": "Custom App",
                "APP_VERSION": "2.0.0",
                "ALLOWED_ORIGINS": "http://example.com,http://test.com",
                "MAX_FILE_SIZE_MB": "100",
                "DEFAULT_TOP_N": "100",
                "MIN_WORD_LENGTH": "2",
                "MIN_MESSAGE_LENGTH": "5",
            },
        ):
            settings = Settings()
            assert settings.APP_NAME == "Custom App"
            assert settings.APP_VERSION == "2.0.0"
            assert settings.ALLOWED_ORIGINS == ["http://example.com", "http://test.com"]
            assert settings.MAX_FILE_SIZE_MB == 100
            assert settings.MAX_FILE_SIZE_BYTES == 100 * 1024 * 1024
            assert settings.DEFAULT_TOP_N == 100
            assert settings.MIN_WORD_LENGTH == 2
            assert settings.MIN_MESSAGE_LENGTH == 5

    def test_invalid_int_env_values(self) -> None:
        """無効な整数値が設定された場合にデフォルト値が使用されることを確認"""
        with mock.patch.dict(
            os.environ,
            {
                "MAX_FILE_SIZE_MB": "invalid",
                "DEFAULT_TOP_N": "abc",
                "MIN_WORD_LENGTH": "1.5",
                "MIN_MESSAGE_LENGTH": "xyz",
            },
        ):
            with warnings.catch_warnings(record=True) as warning_list:
                warnings.simplefilter("always")
                settings = Settings()

                # デフォルト値が使用される
                assert settings.MAX_FILE_SIZE_MB == 50
                assert settings.DEFAULT_TOP_N == 50
                assert settings.MIN_WORD_LENGTH == 1
                assert settings.MIN_MESSAGE_LENGTH == 2

                # 警告が発生する
                assert len(warning_list) == 4
                assert "MAX_FILE_SIZE_MB" in str(warning_list[0].message)
                assert "invalid" in str(warning_list[0].message)
                assert "DEFAULT_TOP_N" in str(warning_list[1].message)
                assert "abc" in str(warning_list[1].message)
                assert "MIN_WORD_LENGTH" in str(warning_list[2].message)
                assert "1.5" in str(warning_list[2].message)
                assert "MIN_MESSAGE_LENGTH" in str(warning_list[3].message)
                assert "xyz" in str(warning_list[3].message)

    def test_parse_origins_with_spaces(self) -> None:
        """スペースを含むオリジン文字列が正しく解析されることを確認"""
        with mock.patch.dict(
            os.environ,
            {"ALLOWED_ORIGINS": " http://example.com , http://test.com , "},
        ):
            settings = Settings()
            assert settings.ALLOWED_ORIGINS == ["http://example.com", "http://test.com"]

    def test_parse_origins_empty_string(self) -> None:
        """空文字列やスペースのみのオリジンが除外されることを確認"""
        with mock.patch.dict(os.environ, {"ALLOWED_ORIGINS": "http://example.com, , ,"}):
            settings = Settings()
            assert settings.ALLOWED_ORIGINS == ["http://example.com"]


class TestGetSettings:
    """get_settings関数のテスト"""

    def test_singleton(self) -> None:
        """get_settings()が同じインスタンスを返すことを確認"""
        # キャッシュをクリア
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
