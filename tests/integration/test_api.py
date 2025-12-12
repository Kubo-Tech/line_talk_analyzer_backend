"""APIエンドポイントの統合テスト

FastAPI TestClientを使用してエンドポイントをテストする
"""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """ヘルスチェックエンドポイントのテスト"""

    def test_health_check(self) -> None:
        """ヘルスチェックエンドポイントのテスト"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestRootEndpoint:
    """ルートエンドポイントのテスト"""

    def test_root(self) -> None:
        """ルートエンドポイントのテスト"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestAnalyzeEndpoint:
    """解析エンドポイントのテスト"""

    @pytest.fixture
    def sample_talk_file(self) -> BytesIO:
        """サンプルトーク履歴ファイル

        Returns:
            BytesIO: サンプルトーク履歴
        """
        content = """[LINE] テストグループのトーク履歴
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	おはよう
10:01	ユーザーB	おはよう
10:02	ユーザーA	今日は良い天気だね
10:03	ユーザーB	本当に良い天気だね
10:04	ユーザーA	天気が良いと気分がいい
"""
        return BytesIO(content.encode("utf-8"))

    def test_analyze_success(self, sample_talk_file: BytesIO) -> None:
        """正常系: 解析が成功することを確認"""
        response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.txt", sample_talk_file, "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["total_messages"] > 0
        assert data["data"]["total_users"] > 0

    def test_analyze_with_parameters(self, sample_talk_file: BytesIO) -> None:
        """パラメータ指定ありの解析テスト"""
        response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.txt", sample_talk_file, "text/plain")},
            data={"top_n": 10, "min_word_length": 2, "min_message_length": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_analyze_with_date_range(self, sample_talk_file: BytesIO) -> None:
        """期間指定ありの解析テスト"""
        response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.txt", sample_talk_file, "text/plain")},
            data={"start_date": "2024-01-01", "end_date": "2024-01-31 23:59:59"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_analyze_no_file(self) -> None:
        """異常系: ファイルなし"""
        response = client.post("/api/v1/analyze")

        assert response.status_code == 422  # Validation Error

    def test_analyze_invalid_file_extension(self) -> None:
        """異常系: 不正なファイル拡張子"""
        fake_file = BytesIO(b"test content")
        response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.pdf", fake_file, "application/pdf")},
        )

        assert response.status_code == 400
        assert "ファイル形式が無効" in response.json()["detail"]

    def test_analyze_empty_file(self) -> None:
        """異常系: 空ファイル"""
        empty_file = BytesIO(b"")
        response = client.post(
            "/api/v1/analyze", files={"file": ("test.txt", empty_file, "text/plain")}
        )

        assert response.status_code == 400
        assert "ファイルが空" in response.json()["detail"]

    def test_analyze_invalid_encoding(self) -> None:
        """異常系: 不正なエンコーディング"""
        # Shift-JISでエンコードされたファイル
        content = "テスト".encode("shift-jis")
        invalid_file = BytesIO(content)

        response = client.post(
            "/api/v1/analyze", files={"file": ("test.txt", invalid_file, "text/plain")}
        )

        # UTF-8でデコードできないため400エラー
        assert response.status_code == 400
        assert "エンコーディング" in response.json()["detail"]

    def test_analyze_invalid_date_format(self, sample_talk_file: BytesIO) -> None:
        """異常系: 不正な日時形式"""
        response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.txt", sample_talk_file, "text/plain")},
            data={"start_date": "invalid-date"},
        )

        assert response.status_code == 400
        assert "日時の形式が無効" in response.json()["detail"]

    def test_analyze_large_file(self) -> None:
        """異常系: ファイルサイズ超過"""
        # 51MBのダミーファイル（MAX_FILE_SIZE_MB=50を超える）
        large_content = b"a" * (51 * 1024 * 1024)
        large_file = BytesIO(large_content)

        response = client.post(
            "/api/v1/analyze", files={"file": ("test.txt", large_file, "text/plain")}
        )

        assert response.status_code == 413
        assert "ファイルサイズが大きすぎます" in response.json()["detail"]


class TestCORS:
    """CORS設定のテスト"""

    def test_cors_headers(self) -> None:
        """CORSヘッダーが設定されていることを確認"""
        # 実際のリクエストでCORSヘッダーをチェック
        response = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})

        # CORSミドルウェアが正しく設定されていればaccess-control-allow-originヘッダーが返される
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
