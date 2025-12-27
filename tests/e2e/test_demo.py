"""デモモードのE2Eテスト

デモモードの完全なフローをテストする
"""

import time
from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app
from app.services.analyzer import TalkAnalyzer

# TestClientの初期化
app.state.analyzer = TalkAnalyzer()
client = TestClient(app)


class TestDemoE2E:
    """デモモードのE2Eテスト"""

    def test_demo_mode_complete_flow(self) -> None:
        """デモモードの完全なフローのテスト"""
        # 1. デモファイルをアップロード
        demo_file = BytesIO(b"")

        response = client.post(
            "/api/v1/analyze",
            files={"file": ("__DEMO__.txt", demo_file, "text/plain")},
        )

        # 2. レスポンスの検証
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # 3. レスポンスデータの詳細検証
        result = data["data"]

        # 基本統計
        assert result["total_messages"] == 1000
        assert result["total_users"] == 3

        # 期間
        assert result["analysis_period"]["start_date"] == "2025-01-01"
        assert result["analysis_period"]["end_date"] == "2025-12-31"

        # 流行語ランキング（50件）
        top_words = result["morphological_analysis"]["top_words"]
        assert len(top_words) == 50

        # トップ10を確認
        expected_top_10 = [
            "エッホエッホ",
            "チャッピー",
            "ミャクミャク",
            "ぬい活",
            "ビジュイイじゃん",
            "ほいたらね",
            "オンカジ",
            "麻辣湯",
            "トランプ関税",
            "古古古米",
        ]
        for i, expected_word in enumerate(expected_top_10):
            assert top_words[i]["word"] == expected_word
            assert "count" in top_words[i]
            assert "part_of_speech" in top_words[i]

        # 流行メッセージランキング（30件）
        top_messages = result["full_message_analysis"]["top_messages"]
        assert len(top_messages) == 30

        # トップ5を確認
        expected_top_5_messages = ["それな", "わかる", "草", "まじで", "やばい"]
        for i, expected_message in enumerate(expected_top_5_messages):
            assert top_messages[i]["message"] == expected_message
            assert "count" in top_messages[i]

        # ユーザー別解析
        user_analysis = result["user_analysis"]
        assert len(user_analysis["word_analysis"]) == 3
        assert len(user_analysis["message_analysis"]) == 3

        # ユーザー名の確認
        user_names = [u["user"] for u in user_analysis["word_analysis"]]
        assert "太郎" in user_names
        assert "花子" in user_names
        assert "次郎" in user_names

        # 各ユーザーのトップ10
        for user_word in user_analysis["word_analysis"]:
            assert len(user_word["top_words"]) == 10

        for user_message in user_analysis["message_analysis"]:
            assert len(user_message["top_messages"]) == 10

        # 4. レスポンスサイズの確認（10KB以下を期待）
        import json

        response_text = json.dumps(data, ensure_ascii=False)
        response_size = len(response_text.encode("utf-8"))
        assert response_size < 10 * 1024, f"レスポンスサイズが大きすぎます: {response_size} bytes"

    def test_demo_mode_consistent_response(self) -> None:
        """複数回呼び出しでの一貫性のテスト"""
        demo_file1 = BytesIO(b"")
        demo_file2 = BytesIO(b"")
        demo_file3 = BytesIO(b"")

        response1 = client.post(
            "/api/v1/analyze",
            files={"file": ("__DEMO__.txt", demo_file1, "text/plain")},
        )
        response2 = client.post(
            "/api/v1/analyze",
            files={"file": ("__DEMO__.txt", demo_file2, "text/plain")},
        )
        response3 = client.post(
            "/api/v1/analyze",
            files={"file": ("__DEMO__.txt", demo_file3, "text/plain")},
        )

        # すべて成功すること
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        # すべて同じレスポンスが返ること
        data1 = response1.json()
        data2 = response2.json()
        data3 = response3.json()

        assert data1 == data2 == data3

        # 統計情報が一致すること
        assert data1["data"]["total_messages"] == 1000
        assert data2["data"]["total_messages"] == 1000
        assert data3["data"]["total_messages"] == 1000

    def test_demo_mode_delay_time(self) -> None:
        """遅延時間のテスト"""
        demo_file = BytesIO(b"")

        start_time = time.time()
        response = client.post(
            "/api/v1/analyze",
            files={"file": ("__DEMO__.txt", demo_file, "text/plain")},
        )
        elapsed_time = time.time() - start_time

        # レスポンスが成功すること
        assert response.status_code == 200

        # 約3秒かかること（±0.5秒の誤差を許容）
        assert 2.5 <= elapsed_time <= 3.5, f"遅延時間が想定外です: {elapsed_time}秒"

    def test_demo_mode_response_format(self) -> None:
        """レスポンス形式のテスト（フロントエンドとの互換性確認）"""
        demo_file = BytesIO(b"")

        response = client.post(
            "/api/v1/analyze",
            files={"file": ("__DEMO__.txt", demo_file, "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()

        # Pydanticモデルと互換性があることを確認
        from app.models.response import AnalysisResult

        # モデルでバリデーション
        result = AnalysisResult(**data)
        assert result.status == "success"
        assert result.data.total_messages == 1000
        assert result.data.total_users == 3
        assert len(result.data.morphological_analysis.top_words) == 50
        assert len(result.data.full_message_analysis.top_messages) == 30

        # ユーザー別解析も正しくパースされること
        assert result.data.user_analysis is not None
        assert len(result.data.user_analysis.word_analysis) == 3
        assert len(result.data.user_analysis.message_analysis) == 3
