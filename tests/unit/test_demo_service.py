"""デモサービスの単体テスト"""

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.demo_service import DemoService


class TestDemoService:
    """DemoServiceクラスのテスト"""

    def test_init(self):
        """初期化処理のテスト"""
        service = DemoService()
        assert service.settings is not None
        assert service.demo_data_path.exists()

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("__DEMO__.txt", True),
            ("test.txt", False),
            ("demo.txt", False),
            ("__demo__.txt", False),  # 大文字小文字を区別
            ("__DEMO__", False),  # .txtがない
            (None, False),
            ("", False),
        ],
    )
    def test_is_demo_file(self, filename, expected):
        """デモファイル判定のテスト"""
        service = DemoService()
        assert service.is_demo_file(filename) == expected

    def test_is_demo_file_disabled(self):
        """デモモード無効化時のテスト"""
        with patch("app.services.demo_service.get_settings") as mock_settings:
            mock_settings.return_value.ENABLE_DEMO_MODE = False
            mock_settings.return_value.DEMO_TRIGGER_FILENAME = "__DEMO__.txt"

            service = DemoService()
            # デモモードが無効の場合、デモファイルでもFalseを返す
            assert service.is_demo_file("__DEMO__.txt") is False

    def test_load_demo_response(self):
        """モックレスポンス読み込みのテスト"""
        service = DemoService()
        data = service.load_demo_response()

        # 基本構造の検証
        assert "analysis_period" in data
        assert "total_messages" in data
        assert "total_users" in data
        assert "morphological_analysis" in data
        assert "full_message_analysis" in data
        assert "user_analysis" in data

        # 期間の検証
        assert data["analysis_period"]["start_date"] == "2025-01-01"
        assert data["analysis_period"]["end_date"] == "2025-12-31"

        # 統計情報の検証
        assert data["total_messages"] == 1000
        assert data["total_users"] == 3

        # 流行語ランキングの検証
        top_words = data["morphological_analysis"]["top_words"]
        assert len(top_words) == 50
        assert top_words[0]["word"] == "エッホエッホ"
        assert top_words[0]["count"] == 150
        assert top_words[0]["part_of_speech"] == "名詞"

        # 流行メッセージランキングの検証
        top_messages = data["full_message_analysis"]["top_messages"]
        assert len(top_messages) == 30
        assert top_messages[0]["message"] == "それな"
        assert top_messages[0]["count"] == 80

        # ユーザー別解析の検証
        user_analysis = data["user_analysis"]
        assert len(user_analysis["word_analysis"]) == 3
        assert len(user_analysis["message_analysis"]) == 3

        # 各ユーザーの流行語トップ10
        for user_word in user_analysis["word_analysis"]:
            assert len(user_word["top_words"]) == 10

        # 各ユーザーの流行メッセージトップ10
        for user_message in user_analysis["message_analysis"]:
            assert len(user_message["top_messages"]) == 10

    def test_load_demo_response_file_not_found(self):
        """JSONファイルが見つからない場合のテスト"""
        service = DemoService()
        service.demo_data_path = Path("/nonexistent/demo_response.json")

        with pytest.raises(FileNotFoundError):
            service.load_demo_response()

    @pytest.mark.asyncio
    async def test_generate_demo_response(self):
        """遅延付きレスポンス生成のテスト"""
        service = DemoService()
        delay_seconds = 0.1  # テスト用に短く設定

        import time

        start_time = time.time()
        data = await service.generate_demo_response(delay_seconds)
        elapsed_time = time.time() - start_time

        # 遅延時間の確認（±0.05秒の誤差を許容）
        assert abs(elapsed_time - delay_seconds) < 0.05

        # レスポンスデータの確認
        assert "analysis_period" in data
        assert data["total_messages"] == 1000

    @pytest.mark.asyncio
    async def test_generate_demo_response_zero_delay(self):
        """遅延なしのレスポンス生成のテスト"""
        service = DemoService()
        delay_seconds = 0.0

        import time

        start_time = time.time()
        data = await service.generate_demo_response(delay_seconds)
        elapsed_time = time.time() - start_time

        # 遅延なしでもレスポンスが返ること
        assert elapsed_time < 0.1
        assert data["total_messages"] == 1000

    @pytest.mark.asyncio
    async def test_generate_demo_response_concurrent(self):
        """複数回同時呼び出しのテスト"""
        service = DemoService()
        delay_seconds = 0.1

        # 3回同時に呼び出し
        tasks = [
            service.generate_demo_response(delay_seconds),
            service.generate_demo_response(delay_seconds),
            service.generate_demo_response(delay_seconds),
        ]

        results = await asyncio.gather(*tasks)

        # すべて同じレスポンスが返ること
        assert len(results) == 3
        for result in results:
            assert result["total_messages"] == 1000
            assert len(result["morphological_analysis"]["top_words"]) == 50
