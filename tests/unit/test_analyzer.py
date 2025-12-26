"""統合解析サービスのテスト

TalkAnalyzerクラスの単体テストを実施する
"""

from datetime import datetime
from io import StringIO

import pytest

from app.services.analyzer import TalkAnalyzer


class TestTalkAnalyzer:
    """TalkAnalyzerクラスのテスト"""

    @pytest.fixture
    def sample_talk_content(self) -> str:
        """サンプルトーク履歴

        Returns:
            str: サンプルトーク履歴
        """
        return """[LINE] テストグループのトーク履歴
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	おはよう
10:01	ユーザーB	おはよう
10:02	ユーザーA	今日は良い天気だね
10:03	ユーザーB	本当に良い天気だね
10:04	ユーザーA	天気が良いと気分がいい

2024/01/02(火)
11:00	ユーザーC	こんにちは
11:01	ユーザーA	こんにちは
11:02	ユーザーB	ランチどこ行く？
"""

    @pytest.fixture
    def analyzer(self) -> TalkAnalyzer:
        """TalkAnalyzerのインスタンス

        Returns:
            TalkAnalyzer: TalkAnalyzerのインスタンス
        """
        return TalkAnalyzer()

    def test_analyze_basic(
        self, analyzer: TalkAnalyzer, sample_talk_content: str
    ) -> None:
        """基本的な解析処理のテスト"""
        result = analyzer.analyze(sample_talk_content, top_n=10)

        # ステータスの確認
        assert result.status == "success"

        # 基本統計の確認
        assert result.data.total_messages == 8
        assert result.data.total_users == 3

        # 解析期間の確認
        assert result.data.analysis_period.start_date == "2024-01-01"
        assert result.data.analysis_period.end_date == "2024-01-02"

        # 形態素解析結果の確認
        assert len(result.data.morphological_analysis.top_words) > 0

        # メッセージ全文解析結果の確認
        assert len(result.data.full_message_analysis.top_messages) > 0

    def test_analyze_with_textio(
        self, analyzer: TalkAnalyzer, sample_talk_content: str
    ) -> None:
        """TextIOを使った解析処理のテスト"""
        file = StringIO(sample_talk_content)
        result = analyzer.analyze(file, top_n=10)

        assert result.status == "success"
        assert result.data.total_messages == 8

    def test_analyze_top_n(
        self, analyzer: TalkAnalyzer, sample_talk_content: str
    ) -> None:
        """上位N件の取得確認のテスト"""
        # top_n=3を指定
        result = analyzer.analyze(sample_talk_content, top_n=3)

        # 形態素解析結果は最大3件
        assert len(result.data.morphological_analysis.top_words) <= 3

        # メッセージ全文解析結果は最大3件
        assert len(result.data.full_message_analysis.top_messages) <= 3

    def test_analyze_word_sorting(
        self, analyzer: TalkAnalyzer, sample_talk_content: str
    ) -> None:
        """単語のソート順確認のテスト"""
        result = analyzer.analyze(sample_talk_content, top_n=10)

        # 単語がカウント降順でソートされていることを確認
        top_words = result.data.morphological_analysis.top_words
        for i in range(len(top_words) - 1):
            assert top_words[i].count >= top_words[i + 1].count

    def test_analyze_message_sorting(
        self, analyzer: TalkAnalyzer, sample_talk_content: str
    ) -> None:
        """メッセージのソート順確認のテスト"""
        result = analyzer.analyze(sample_talk_content, top_n=10)

        # メッセージがカウント降順でソートされていることを確認
        top_messages = result.data.full_message_analysis.top_messages
        for i in range(len(top_messages) - 1):
            assert top_messages[i].count >= top_messages[i + 1].count

    def test_analyze_with_length_filters(
        self, analyzer: TalkAnalyzer, sample_talk_content: str
    ) -> None:
        """文字数フィルタのテスト"""
        result = analyzer.analyze(
            sample_talk_content,
            top_n=10,
            min_word_length=2,
            max_word_length=5,
            min_message_length=3,
            max_message_length=10,
        )

        assert result.status == "success"

        # フィルタが適用されても結果が返されることを確認
        # （具体的な件数は形態素解析の結果に依存するため、存在確認のみ）
        assert result.data.total_messages > 0

    def test_analyze_empty_file(self, analyzer: TalkAnalyzer) -> None:
        """空ファイルのテスト"""
        empty_content = """[LINE] 空のトーク履歴
保存日時：2024/01/01 00:00

"""
        result = analyzer.analyze(empty_content)

        assert result.status == "success"
        assert result.data.total_messages == 0
        assert result.data.total_users == 0
        assert len(result.data.morphological_analysis.top_words) == 0
        assert len(result.data.full_message_analysis.top_messages) == 0

    def test_analyze_single_message(self, analyzer: TalkAnalyzer) -> None:
        """単一メッセージのテスト"""
        single_message = """[LINE] シングルメッセージ
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	こんにちは
"""
        result = analyzer.analyze(single_message)

        assert result.status == "success"
        assert result.data.total_messages == 1
        assert result.data.total_users == 1

    def test_analyze_multiple_days(self, analyzer: TalkAnalyzer) -> None:
        """複数日にまたがるデータのテスト"""
        multi_day_content = """[LINE] マルチデイトーク
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	1日目

2024/01/05(金)
15:00	ユーザーB	5日目

2024/01/10(水)
20:00	ユーザーC	10日目
"""
        result = analyzer.analyze(multi_day_content)

        assert result.status == "success"
        assert result.data.analysis_period.start_date == "2024-01-01"
        assert result.data.analysis_period.end_date == "2024-01-10"

    def test_analyze_repeated_words(self, analyzer: TalkAnalyzer) -> None:
        """同一単語が複数回出現するケースのテスト"""
        repeated_content = """[LINE] リピートテスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	テストテストテスト
10:01	ユーザーB	テスト中です
10:02	ユーザーC	テストを実行
"""
        result = analyzer.analyze(repeated_content, top_n=5)

        assert result.status == "success"

        # 「テスト」という単語が上位に来ていることを確認
        # 注: 「テストテストテスト」は1つのメッセージ内では1回とカウントされる
        top_words = result.data.morphological_analysis.top_words
        test_word = next((w for w in top_words if "テスト" in w.word), None)
        assert test_word is not None
        assert test_word.count >= 2  # 3つのメッセージに出現（重複は除外）

    def test_analyze_repeated_messages(self, analyzer: TalkAnalyzer) -> None:
        """同一メッセージが複数回出現するケースのテスト"""
        repeated_content = """[LINE] メッセージリピート
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	了解
10:01	ユーザーB	了解
10:02	ユーザーC	了解です
"""
        result = analyzer.analyze(repeated_content, top_n=5, min_message_length=1)

        assert result.status == "success"

        # 「了解」というメッセージが上位に来ていることを確認
        top_messages = result.data.full_message_analysis.top_messages
        ryoukai_message = next((m for m in top_messages if m.message == "了解"), None)
        assert ryoukai_message is not None
        assert ryoukai_message.count == 2

    def test_analyze_invalid_top_n(self, analyzer: TalkAnalyzer) -> None:
        """無効なtop_nパラメータのテスト"""
        content = """[LINE] テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	テスト
"""
        with pytest.raises(ValueError, match="top_nは1以上である必要があります"):
            analyzer.analyze(content, top_n=0)

        with pytest.raises(ValueError, match="top_nは1以上である必要があります"):
            analyzer.analyze(content, top_n=-1)

    def test_analyze_with_period_filter(self, analyzer: TalkAnalyzer) -> None:
        """期間指定のテスト"""
        content = """[LINE] 期間テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	1月1日のメッセージ
10:01	ユーザーB	1月1日のメッセージ2

2024/01/05(金)
15:00	ユーザーC	1月5日のメッセージ

2024/01/10(水)
20:00	ユーザーA	1月10日のメッセージ
"""
        # 1月1日から1月5日までのメッセージのみを解析
        result = analyzer.analyze(
            content,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5, 23, 59, 59),
        )

        assert result.status == "success"
        assert result.data.total_messages == 3  # 1/1の2件と1/5の1件
        assert result.data.analysis_period.start_date == "2024-01-01"
        assert result.data.analysis_period.end_date == "2024-01-05"

    def test_analyze_with_start_date_only(self, analyzer: TalkAnalyzer) -> None:
        """開始日のみ指定のテスト"""
        content = """[LINE] 開始日テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	1月1日

2024/01/05(金)
15:00	ユーザーB	1月5日

2024/01/10(水)
20:00	ユーザーC	1月10日
"""
        # 1月5日以降のメッセージのみを解析
        result = analyzer.analyze(content, start_date=datetime(2024, 1, 5))

        assert result.status == "success"
        assert result.data.total_messages == 2  # 1/5と1/10の2件
        assert result.data.analysis_period.start_date == "2024-01-05"
        assert result.data.analysis_period.end_date == "2024-01-10"

    def test_analyze_with_end_date_only(self, analyzer: TalkAnalyzer) -> None:
        """終了日のみ指定のテスト"""
        content = """[LINE] 終了日テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	1月1日

2024/01/05(金)
15:00	ユーザーB	1月5日

2024/01/10(水)
20:00	ユーザーC	1月10日
"""
        # 1月5日までのメッセージのみを解析
        result = analyzer.analyze(content, end_date=datetime(2024, 1, 5, 23, 59, 59))

        assert result.status == "success"
        assert result.data.total_messages == 2  # 1/1と1/5の2件
        assert result.data.analysis_period.start_date == "2024-01-01"
        assert result.data.analysis_period.end_date == "2024-01-05"

    def test_analyze_with_invalid_period(self, analyzer: TalkAnalyzer) -> None:
        """無効な期間指定のテスト"""
        content = """[LINE] テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	テスト
"""
        # 開始日が終了日より後の場合はエラー
        with pytest.raises(
            ValueError, match="start_dateはend_date以前である必要があります"
        ):
            analyzer.analyze(
                content,
                start_date=datetime(2024, 1, 10),
                end_date=datetime(2024, 1, 1),
            )

    def test_analyze_with_period_no_messages(self, analyzer: TalkAnalyzer) -> None:
        """期間内にメッセージがない場合のテスト"""
        content = """[LINE] 期間外テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	1月1日のメッセージ
"""
        # 1月10日以降を指定（該当メッセージなし）
        result = analyzer.analyze(content, start_date=datetime(2024, 1, 10))

        assert result.status == "success"
        assert result.data.total_messages == 0
        assert result.data.total_users == 0
        assert len(result.data.morphological_analysis.top_words) == 0
        assert len(result.data.full_message_analysis.top_messages) == 0

    def test_filter_by_period(self, analyzer: TalkAnalyzer) -> None:
        """_filter_by_periodメソッドのテスト"""
        from app.services.parser import Message

        messages = [
            Message(datetime(2024, 1, 1, 10, 0), "ユーザーA", "1日"),
            Message(datetime(2024, 1, 5, 15, 0), "ユーザーB", "5日"),
            Message(datetime(2024, 1, 10, 20, 0), "ユーザーC", "10日"),
        ]

        # 開始日と終了日の両方を指定
        filtered = analyzer._filter_by_period(
            messages, datetime(2024, 1, 5), datetime(2024, 1, 10, 23, 59, 59)
        )
        assert len(filtered) == 2  # 5日と10日
        assert filtered[0].content == "5日"
        assert filtered[1].content == "10日"

        # 開始日のみを指定
        filtered = analyzer._filter_by_period(messages, datetime(2024, 1, 5), None)
        assert len(filtered) == 2  # 5日と10日

        # 終了日のみを指定
        filtered = analyzer._filter_by_period(
            messages, None, datetime(2024, 1, 5, 23, 59, 59)
        )
        assert len(filtered) == 2  # 1日と5日

        # どちらも指定しない
        filtered = analyzer._filter_by_period(messages, None, None)
        assert len(filtered) == 3  # 全て

    def test_get_top_words(self, analyzer: TalkAnalyzer) -> None:
        """_get_top_wordsメソッドのテスト"""
        from app.services.parser import Message
        from app.services.word_counter import WordCount

        # テストデータの作成
        msg1 = Message(datetime(2024, 1, 1, 10, 0), "ユーザーA", "テスト1")
        msg2 = Message(datetime(2024, 1, 1, 10, 1), "ユーザーB", "テスト2")

        word_counts = [
            WordCount(
                "単語A",
                "単語A",
                5,
                "名詞",
                {"ユーザーA": 5},
                [msg1, msg1, msg1, msg1, msg1],
            ),
            WordCount(
                "単語B",
                "単語B",
                10,
                "名詞",
                {"ユーザーB": 10},
                [msg2] * 10,
            ),
            WordCount(
                "単語C",
                "単語C",
                3,
                "名詞",
                {"ユーザーA": 3},
                [msg1, msg1, msg1],
            ),
        ]

        # 上位2件を取得
        top_words = analyzer._get_top_words(word_counts, 2)

        assert len(top_words) == 2
        assert top_words[0].word == "単語B"  # 最多
        assert top_words[0].count == 10
        assert top_words[1].word == "単語A"  # 2番目
        assert top_words[1].count == 5

    def test_get_top_messages(self, analyzer: TalkAnalyzer) -> None:
        """_get_top_messagesメソッドのテスト"""
        from app.services.parser import Message
        from app.services.word_counter import MessageCount

        # テストデータの作成
        msg1 = Message(datetime(2024, 1, 1, 10, 0), "ユーザーA", "メッセージA")
        msg2 = Message(datetime(2024, 1, 1, 10, 1), "ユーザーB", "メッセージB")

        message_counts = [
            MessageCount(
                "メッセージA",
                5,
                {"ユーザーA": 5},
                [msg1] * 5,
            ),
            MessageCount(
                "メッセージB",
                8,
                {"ユーザーB": 8},
                [msg2] * 8,
            ),
            MessageCount(
                "メッセージC",
                3,
                {"ユーザーA": 3},
                [msg1] * 3,
            ),
        ]

        # 上位2件を取得
        top_messages = analyzer._get_top_messages(message_counts, 2)

        assert len(top_messages) == 2
        assert top_messages[0].message == "メッセージB"  # 8回
        assert top_messages[0].count == 8
        assert top_messages[1].message == "メッセージA"  # 5回
        assert top_messages[1].count == 5

    def test_format_response(self, analyzer: TalkAnalyzer) -> None:
        """_format_responseメソッドのテスト"""
        from app.services.parser import Message
        from app.services.word_counter import MessageCount, WordCount

        # テストデータの作成
        messages = [
            Message(datetime(2024, 1, 1, 10, 0), "ユーザーA", "テスト1"),
            Message(datetime(2024, 1, 2, 15, 0), "ユーザーB", "テスト2"),
            Message(datetime(2024, 1, 3, 20, 0), "ユーザーA", "テスト3"),
        ]

        word_counts = [
            WordCount(
                "テスト",
                "テスト",
                3,
                "名詞",
                {"ユーザーA": 2, "ユーザーB": 1},
                messages,
            ),
        ]

        message_counts = [
            MessageCount(
                "テスト1",
                1,
                {"ユーザーA": 1},
                [messages[0]],
            ),
        ]

        # レスポンスを整形
        result = analyzer._format_response(messages, word_counts, message_counts)

        # 基本情報の確認
        assert result.status == "success"
        assert result.data.total_messages == 3
        assert result.data.total_users == 2
        assert result.data.analysis_period.start_date == "2024-01-01"
        assert result.data.analysis_period.end_date == "2024-01-03"

        # 形態素解析結果の確認
        assert len(result.data.morphological_analysis.top_words) == 1
        assert result.data.morphological_analysis.top_words[0].word == "テスト"
        assert result.data.morphological_analysis.top_words[0].count == 3

        # メッセージ全文解析結果の確認
        assert len(result.data.full_message_analysis.top_messages) == 1
        assert result.data.full_message_analysis.top_messages[0].message == "テスト1"

    def test_create_empty_result(self, analyzer: TalkAnalyzer) -> None:
        """_create_empty_resultメソッドのテスト"""
        result = analyzer._create_empty_result()

        assert result.status == "success"
        assert result.data.total_messages == 0
        assert result.data.total_users == 0
        assert len(result.data.morphological_analysis.top_words) == 0
        assert len(result.data.full_message_analysis.top_messages) == 0

        # 日付は現在の日付が設定されていることを確認
        today = datetime.now().strftime("%Y-%m-%d")
        assert result.data.analysis_period.start_date == today
        assert result.data.analysis_period.end_date == today

    def test_analyze_with_min_word_count(self, analyzer: TalkAnalyzer) -> None:
        """最小単語出現回数フィルタのテスト"""
        content = """[LINE] 単語出現回数テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	りんごとバナナとみかん
10:01	ユーザーB	りんごとバナナ
10:02	ユーザーC	りんご
"""
        # min_word_count=2 の場合、2回以上出現する単語のみ取得
        result = analyzer.analyze(content, top_n=10, min_word_count=2)

        assert result.status == "success"

        # 「りんご」(3回)、「バナナ」(2回) は含まれる
        # 「みかん」(1回) は含まれない
        words = [w.word for w in result.data.morphological_analysis.top_words]
        assert "りんご" in words
        assert "バナナ" in words
        assert "みかん" not in words

    def test_analyze_with_min_message_count(self, analyzer: TalkAnalyzer) -> None:
        """最小メッセージ出現回数フィルタのテスト"""
        content = """[LINE] メッセージ出現回数テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	おはよう
10:01	ユーザーB	おはよう
10:02	ユーザーC	おはよう
10:03	ユーザーA	こんにちは
10:04	ユーザーB	こんにちは
10:05	ユーザーC	さようなら
"""
        # min_message_count=2 の場合、2回以上出現するメッセージのみ取得
        result = analyzer.analyze(content, top_n=10, min_message_count=2)

        assert result.status == "success"

        # 「おはよう」(3回)、「こんにちは」(2回) は含まれる
        # 「さようなら」(1回) は含まれない
        messages = [m.message for m in result.data.full_message_analysis.top_messages]
        assert "おはよう" in messages
        assert "こんにちは" in messages
        assert "さようなら" not in messages

    def test_analyze_with_min_count_default(self, analyzer: TalkAnalyzer) -> None:
        """最小出現回数のデフォルト値（2）のテスト"""
        content = """[LINE] デフォルト値テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	一回のみ
10:01	ユーザーB	二回目
10:02	ユーザーC	二回目
"""
        # min_word_count, min_message_countを指定しない（デフォルト=2）
        result = analyzer.analyze(content, top_n=10)

        assert result.status == "success"

        # 1回のみの単語・メッセージは除外される
        words = [w.word for w in result.data.morphological_analysis.top_words]
        messages = [m.message for m in result.data.full_message_analysis.top_messages]

        # 「一回」は1回のみなので含まれない
        assert "一回" not in words

        # 「二回目」は2回なので含まれる
        assert "二回目" in messages
        # 「一回のみ」は1回なので含まれない
        assert "一回のみ" not in messages

    def test_analyze_min_count_validation(self, analyzer: TalkAnalyzer) -> None:
        """最小出現回数のバリデーションテスト"""
        content = """[LINE] バリデーションテスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	テスト
"""
        # min_word_count が 0 以下の場合はエラー
        with pytest.raises(ValueError, match="min_word_count.*1以上"):
            analyzer.analyze(content, min_word_count=0)

        with pytest.raises(ValueError, match="min_word_count.*1以上"):
            analyzer.analyze(content, min_word_count=-1)

        # min_message_count が 0 以下の場合はエラー
        with pytest.raises(ValueError, match="min_message_count.*1以上"):
            analyzer.analyze(content, min_message_count=0)

        with pytest.raises(ValueError, match="min_message_count.*1以上"):
            analyzer.analyze(content, min_message_count=-1)
