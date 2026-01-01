"""実際のLINEトーク履歴を使用したE2Eテスト

talk/sample.txtを使用して実際の解析処理をテストし、パフォーマンスを測定する

実行方法：
    cd /app
    pytest tests/e2e/test_real_data.py -v -s

    オプション：
        -v: 詳細表示
        -s: print文を表示（結果のランキング表示）
        -k test_analyze_2025_data: 2025年分のみ実行
        -k test_analyze_all_period: 全期間のみ実行
"""

import time
from datetime import datetime
from pathlib import Path

import psutil
import pytest

from app.services.analyzer import TalkAnalyzer

TOP_N = 100


@pytest.mark.e2e
class TestRealDataAnalysis:
    """実際のトーク履歴を使用した解析テスト
    
    注意: このテストは実際のトーク履歴ファイル(talk/sample.txt)を必要とします。
    CI環境では`-m "not e2e"`オプションでスキップされます。
    ローカルで実行する場合は、talk/sample.txtを配置してください。
    """

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """サンプルファイルのパス

        Returns:
            Path: sample.txtのパス
        """
        return Path("/app/talk/sample.txt")

    def test_analyze_2025_data(self, sample_file_path: Path) -> None:
        """2025年分のデータを解析する

        レスポンス時間とメモリ使用量を測定し、
        パフォーマンスが許容範囲内であることを確認する
        """
        # 2025年1月1日から12月31日までを指定
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 12, 31, 23, 59, 59)

        self._analyze_and_display_results(
            sample_file_path,
            start_date=start_date,
            end_date=end_date,
            test_name="2025年分データ解析",
        )

    def test_analyze_all_period(self, sample_file_path: Path) -> None:
        """全期間のデータを解析する（期間フィルタなし）"""
        self._analyze_and_display_results(
            sample_file_path,
            start_date=None,
            end_date=None,
            test_name="全期間解析",
        )

    def _analyze_and_display_results(
        self,
        sample_file_path: Path,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        test_name: str = "解析",
    ) -> None:
        """トーク履歴を解析して結果を表示する共通処理

        Args:
            sample_file_path (Path): サンプルファイルのパス
            start_date (datetime | None): 解析開始日時
            end_date (datetime | None): 解析終了日時
            test_name (str): テスト名（表示用）
        """
        # ファイルが存在することを確認
        assert sample_file_path.exists(), "sample.txtが見つかりません"

        # メモリ使用量の初期値を取得
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # 解析開始
        start_time = time.time()

        with open(sample_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        analyzer = TalkAnalyzer()
        result = analyzer.analyze(
            content,
            top_n=TOP_N,
            min_word_length=1,
            min_message_length=2,
            start_date=start_date,
            end_date=end_date,
        )

        # 解析終了
        end_time = time.time()
        elapsed_time = end_time - start_time

        # メモリ使用量の最終値を取得
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        # 結果を表示
        print("\n" + "=" * 80)
        print(f"{test_name}結果")
        print("=" * 80)
        print(f"ファイルサイズ: {sample_file_path.stat().st_size / 1024 / 1024:.2f} MB")
        print(f"解析時間: {elapsed_time:.2f} 秒")
        print(f"メモリ使用量: {memory_used:.2f} MB")
        print(f"総メッセージ数: {result.data.total_messages}")
        print(f"総ユーザー数: {result.data.total_users}")
        period = result.data.analysis_period
        print(f"解析期間: {period.start_date} ~ {period.end_date}")
        print(f"\n形態素解析 - 上位{TOP_N}単語:")
        for i, word in enumerate(result.data.morphological_analysis.top_words[:TOP_N], 1):
            print(f"  {i}. {word.word} ({word.part_of_speech}): {word.count}回")

        print(f"\nメッセージ全文解析 - 上位{TOP_N}メッセージ:")
        for i, msg in enumerate(result.data.full_message_analysis.top_messages[:TOP_N], 1):
            print(f"  {i}. {msg.message}: {msg.count}回")

        # ユーザー別解析結果の表示
        if result.data.user_analysis:
            print("\n" + "=" * 80)
            print("ユーザー別流行語ランキング")
            print("=" * 80)
            for user_word in result.data.user_analysis.word_analysis:
                print(f"\n【{user_word.user}】の流行語トップ10:")
                for i, word in enumerate(user_word.top_words[:10], 1):
                    print(f"  {i}. {word.word} ({word.part_of_speech}): {word.count}回")

            print("\n" + "=" * 80)
            print("ユーザー別流行メッセージランキング")
            print("=" * 80)
            for user_msg in result.data.user_analysis.message_analysis:
                print(f"\n【{user_msg.user}】の流行メッセージトップ10:")
                for i, msg in enumerate(user_msg.top_messages[:10], 1):
                    print(f"  {i}. {msg.message}: {msg.count}回")

        print("=" * 80)

        # 基本的なアサーション
        assert result.status == "success", "解析が成功しませんでした"
        assert result.data.total_messages > 0, "メッセージが解析されていません"

        # 期間フィルタが指定されている場合の追加チェック
        if start_date is not None:
            assert result.data.analysis_period.start_date >= start_date.strftime(
                "%Y-%m-%d"
            ), f"開始日が指定期間より前です: {result.data.analysis_period.start_date}"
        if end_date is not None and result.data.total_messages > 0:
            # 終了日の翌日より前であることを確認
            next_day = datetime(end_date.year + 1, 1, 1) if end_date.month == 12 else end_date
            assert (
                result.data.analysis_period.end_date <= next_day.strftime("%Y-%m-%d")
                if isinstance(next_day, datetime)
                else end_date.strftime("%Y-%m-%d")
            ), f"終了日が指定期間を超えています: {result.data.analysis_period.end_date}"

        # パフォーマンスチェック
        # レスポンス時間の警告（30秒を超えたら警告）
        if elapsed_time > 30:
            pytest.fail(
                f"解析時間が長すぎます: {elapsed_time:.2f}秒 > 30秒\n"
                "パフォーマンス最適化を検討してください"
            )
        elif elapsed_time > 10:
            print(f"\n⚠️  警告: 解析時間が目標値を超えています: {elapsed_time:.2f}秒 > 10秒")

        # メモリ使用量の警告（1GB を超えたら警告）
        if memory_used > 1024:
            pytest.fail(
                f"メモリ使用量が多すぎます: {memory_used:.2f}MB > 1024MB\n"
                "メモリ最適化を検討してください"
            )
