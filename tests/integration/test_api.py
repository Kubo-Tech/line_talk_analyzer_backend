"""APIエンドポイントの統合テスト

FastAPI TestClientを使用してエンドポイントをテストする
"""

from io import BytesIO
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.analyzer import TalkAnalyzer

# TestClientはlifespanイベントをサポートしているが、明示的にwith文を使用する必要がある
# ただし、グローバルclientとしてwithを使えないため、app.state.analyzerを手動で初期化
app.state.analyzer = TalkAnalyzer()

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
            data={
                "top_n": "10",
                "min_word_length": "2",
                "min_message_length": "3",
                "min_word_count": "3",
                "min_message_count": "2",
            },
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

    def test_analyze_file_at_size_limit(self) -> None:
        """境界値: ちょうど50MBのファイル"""
        # ちょうど50MBのダミーファイル
        content_50mb = b"a" * (50 * 1024 * 1024)
        file_50mb = BytesIO(content_50mb)

        response = client.post(
            "/api/v1/analyze", files={"file": ("test.txt", file_50mb, "text/plain")}
        )

        # 50MBちょうどなので413エラーにならず、正常に処理される
        # （内容が不正でもサイズチェックはパスする）
        assert response.status_code in [200, 400]
        # 413（サイズ超過）ではないことを確認
        assert response.status_code != 413

    def test_analyze_chunked_reading(self) -> None:
        """正常系: チャンク読み込みが正しく動作すること"""
        # 5MBのLINEトーク履歴風ファイル
        sample_talk = """[LINE] テストグループのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12\tユーザー1\tこんにちは
22:13\tユーザー2\tよろしく
"""
        # 5MBになるまで繰り返し
        large_talk = sample_talk * (5 * 1024 * 1024 // len(sample_talk.encode("utf-8")))
        large_file = BytesIO(large_talk.encode("utf-8"))

        response = client.post(
            "/api/v1/analyze", files={"file": ("test.txt", large_file, "text/plain")}
        )

        # チャンク読み込みでも正常に解析できることを確認
        assert response.status_code == 200

    def test_analyze_server_error(self, sample_talk_file: BytesIO) -> None:
        """異常系: サーバー内部エラー（予期しない例外）"""
        # TalkAnalyzer.analyzeをモックして予期しない例外を発生させる
        with mock.patch.object(
            TalkAnalyzer, "analyze", side_effect=RuntimeError("予期しないエラー")
        ):
            response = client.post(
                "/api/v1/analyze",
                files={"file": ("test.txt", sample_talk_file, "text/plain")},
            )

            assert response.status_code == 500
            # 一般的なエラーメッセージが返されることを確認（詳細は含まれない）
            assert "サーバー内部エラーが発生しました" in response.json()["detail"]
            # セキュリティのため、内部エラーの詳細は露出されない
            assert "予期しないエラー" not in response.json()["detail"]
            assert "RuntimeError" not in response.json()["detail"]

    def test_analyze_value_error(self, sample_talk_file: BytesIO) -> None:
        """異常系: ValueError（解析エラー）"""
        # TalkAnalyzer.analyzeをモックしてValueErrorを発生させる
        with mock.patch.object(
            TalkAnalyzer, "analyze", side_effect=ValueError("不正なトーク履歴形式")
        ):
            response = client.post(
                "/api/v1/analyze",
                files={"file": ("test.txt", sample_talk_file, "text/plain")},
            )

            assert response.status_code == 400
            # 一般的なエラーメッセージが返されることを確認（詳細は含まれない）
            assert "トーク履歴の形式が正しくありません" in response.json()["detail"]
            # セキュリティのため、内部エラーの詳細は露出されない
            assert "不正なトーク履歴形式" not in response.json()["detail"]

    def test_analyze_with_min_count_filters(self) -> None:
        """最小出現回数フィルタのテスト"""
        content = """[LINE] 最小出現回数テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	りんごとバナナとみかん
10:01	ユーザーB	りんごとバナナ
10:02	ユーザーC	りんご
10:03	ユーザーA	おはよう
10:04	ユーザーB	おはよう
10:05	ユーザーC	こんにちは
"""
        file = BytesIO(content.encode("utf-8"))

        response = client.post(
            "/api/v1/analyze",
            files={"file": ("test.txt", file, "text/plain")},
            data={"min_word_count": "2", "min_message_count": "2"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # 2回以上出現する単語のみ含まれる
        words = [w["word"] for w in data["data"]["morphological_analysis"]["top_words"]]
        assert "りんご" in words  # 3回出現
        assert "バナナ" in words  # 2回出現
        # 「みかん」は1回のみなので含まれない

        # 2回以上出現するメッセージのみ含まれる
        messages = [
            m["message"] for m in data["data"]["full_message_analysis"]["top_messages"]
        ]
        assert "おはよう" in messages  # 2回出現
        assert "こんにちは" not in messages  # 1回のみ


class TestCORS:
    """CORS設定のテスト"""

    def test_cors_headers(self) -> None:
        """CORSヘッダーが設定されていることを確認"""
        # 実際のリクエストでCORSヘッダーをチェック
        response = client.get(
            "/api/v1/health", headers={"Origin": "http://localhost:3000"}
        )

        # CORSミドルウェアが正しく設定されていればaccess-control-allow-originヘッダーが返される
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
