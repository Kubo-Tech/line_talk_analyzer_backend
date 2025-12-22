"""単語カウンターのテスト"""

from datetime import datetime

import pytest

from app.services import Message, Word
from app.services.word_counter import MessageCount, WordCount, WordCounter


class TestWordCount:
    """WordCountデータクラスのテスト"""

    def test_create_instance(self) -> None:
        """インスタンス作成テスト"""
        message = Message(
            datetime=datetime(2024, 8, 1, 22, 12),
            user="テストユーザー",
            content="テストメッセージ",
        )

        word_count = WordCount(
            word="テスト",
            base_form="テスト",
            count=5,
            part_of_speech="名詞",
            user_counts={"テストユーザー": 5},
            appearances=[message],
        )

        assert word_count.word == "テスト"
        assert word_count.base_form == "テスト"
        assert word_count.count == 5
        assert word_count.part_of_speech == "名詞"
        assert word_count.user_counts == {"テストユーザー": 5}
        assert len(word_count.appearances) == 1


class TestMessageCount:
    """MessageCountデータクラスのテスト"""

    def test_create_instance(self) -> None:
        """インスタンス作成テスト"""
        message = Message(
            datetime=datetime(2024, 8, 1, 22, 12),
            user="テストユーザー",
            content="テストメッセージ",
        )

        message_count = MessageCount(
            message="テストメッセージ",
            count=5,
            user_counts={"テストユーザー": 5},
            appearances=[message],
        )

        assert message_count.message == "テストメッセージ"
        assert message_count.count == 5
        assert message_count.user_counts == {"テストユーザー": 5}
        assert len(message_count.appearances) == 1


class TestWordCounter:
    """WordCounterクラスのテスト"""

    @pytest.fixture
    def sample_messages(self) -> list[Message]:
        """テスト用メッセージ"""
        return [
            Message(
                datetime=datetime(2024, 8, 1, 22, 12),
                user="ユーザーA",
                content="今日は良い天気です",
            ),
            Message(
                datetime=datetime(2024, 8, 1, 22, 15),
                user="ユーザーB",
                content="今日も良い天気ですね",
            ),
            Message(
                datetime=datetime(2024, 8, 1, 22, 20),
                user="ユーザーA",
                content="明日も天気が良いといいな",
            ),
        ]

    @pytest.fixture
    def sample_words_by_message(self) -> list[list[Word]]:
        """テスト用の形態素解析結果"""
        return [
            [
                Word("今日", "今日", "名詞", "副詞可能", "*", "*"),
                Word("良い", "良い", "形容詞", "自立", "*", "*"),
                Word("天気", "天気", "名詞", "一般", "*", "*"),
            ],
            [
                Word("今日", "今日", "名詞", "副詞可能", "*", "*"),
                Word("良い", "良い", "形容詞", "自立", "*", "*"),
                Word("天気", "天気", "名詞", "一般", "*", "*"),
            ],
            [
                Word("明日", "明日", "名詞", "副詞可能", "*", "*"),
                Word("天気", "天気", "名詞", "一般", "*", "*"),
                Word("良い", "良い", "形容詞", "自立", "*", "*"),
            ],
        ]

    def test_count_morphological_words(
        self,
        sample_messages: list[Message],
        sample_words_by_message: list[list[Word]],
    ) -> None:
        """形態素解析結果のカウントテスト"""
        counter = WordCounter()
        word_counts = counter.count_morphological_words(sample_messages, sample_words_by_message)

        # 単語数の確認
        assert len(word_counts) == 4  # 今日、良い、天気、明日

        # 各単語のカウント確認
        word_count_dict = {wc.base_form: wc for wc in word_counts}

        assert "今日" in word_count_dict
        assert word_count_dict["今日"].count == 2
        assert word_count_dict["今日"].part_of_speech == "名詞"

        assert "良い" in word_count_dict
        assert word_count_dict["良い"].count == 3

        assert "天気" in word_count_dict
        assert word_count_dict["天気"].count == 3

        assert "明日" in word_count_dict
        assert word_count_dict["明日"].count == 1

    def test_count_morphological_words_with_same_base_form(self) -> None:
        """同じ基本形を持つ単語のカウントテスト"""
        messages = [
            Message(
                datetime=datetime(2024, 8, 1, 22, 12),
                user="ユーザーA",
                content="走る",
            ),
            Message(
                datetime=datetime(2024, 8, 1, 22, 15),
                user="ユーザーB",
                content="走った",
            ),
        ]

        words_by_message = [
            [Word("走る", "走る", "動詞", "自立", "*", "*")],
            [Word("走っ", "走る", "動詞", "自立", "*", "*")],
        ]

        counter = WordCounter()
        word_counts = counter.count_morphological_words(messages, words_by_message)

        # 基本形が同じなので1つの単語としてカウント
        assert len(word_counts) == 1
        assert word_counts[0].base_form == "走る"
        assert word_counts[0].count == 2

    def test_count_morphological_words_empty(self) -> None:
        """空のデータセットのテスト"""
        counter = WordCounter()
        word_counts = counter.count_morphological_words([], [])

        assert len(word_counts) == 0

    def test_count_morphological_words_with_length_filter(self) -> None:
        """文字数フィルタリングのテスト"""
        messages = [
            Message(
                datetime=datetime(2024, 8, 1, 22, 12),
                user="ユーザーA",
                content="あ天気",
            ),
        ]

        words_by_message = [
            [
                Word("あ", "あ", "名詞", "一般", "*", "*"),  # 1文字
                Word("天気", "天気", "名詞", "一般", "*", "*"),  # 2文字
            ]
        ]

        counter = WordCounter()

        # 最小文字数2文字でフィルタ
        word_counts = counter.count_morphological_words(
            messages, words_by_message, min_word_length=2
        )
        assert len(word_counts) == 1
        assert word_counts[0].word == "天気"

        # 最大文字数1文字でフィルタ（デフォルトmin_word_length=2なので、両方を指定）
        word_counts = counter.count_morphological_words(
            messages, words_by_message, min_word_length=1, max_word_length=1
        )
        assert len(word_counts) == 1
        assert word_counts[0].word == "あ"

        # 範囲指定（2文字以上2文字以下）
        word_counts = counter.count_morphological_words(
            messages, words_by_message, min_word_length=2, max_word_length=2
        )
        assert len(word_counts) == 1
        assert word_counts[0].word == "天気"

    def test_count_morphological_words_length_mismatch(self) -> None:
        """messagesとwords_by_messageの長さが一致しない場合のテスト"""
        messages = [
            Message(
                datetime=datetime(2024, 8, 1, 22, 12),
                user="ユーザーA",
                content="今日は良い天気です",
            ),
            Message(
                datetime=datetime(2024, 8, 1, 22, 15),
                user="ユーザーB",
                content="今日も良い天気ですね",
            ),
        ]

        # messagesより少ないwords_by_message
        words_by_message_short = [
            [Word("今日", "今日", "名詞", "副詞可能", "*", "*")],
        ]

        # messagesより多いwords_by_message
        words_by_message_long = [
            [Word("今日", "今日", "名詞", "副詞可能", "*", "*")],
            [Word("今日", "今日", "名詞", "副詞可能", "*", "*")],
            [Word("明日", "明日", "名詞", "副詞可能", "*", "*")],
        ]

        counter = WordCounter()

        # 長さが一致しない場合はValueErrorが発生
        with pytest.raises(ValueError) as excinfo:
            counter.count_morphological_words(messages, words_by_message_short)
        assert "messagesとwords_by_messageの長さが一致しません" in str(excinfo.value)
        assert "messages=2" in str(excinfo.value)
        assert "words_by_message=1" in str(excinfo.value)

        with pytest.raises(ValueError) as excinfo:
            counter.count_morphological_words(messages, words_by_message_long)
        assert "messagesとwords_by_messageの長さが一致しません" in str(excinfo.value)
        assert "messages=2" in str(excinfo.value)
        assert "words_by_message=3" in str(excinfo.value)

    def test_count_morphological_words_invalid_parameters(self) -> None:
        """count_morphological_wordsのパラメータ検証テスト"""
        messages = [
            Message(
                datetime=datetime(2024, 8, 1, 22, 12),
                user="ユーザーA",
                content="今日は良い天気です",
            ),
        ]
        words_by_message = [
            [Word("今日", "今日", "名詞", "副詞可能", "*", "*")],
        ]

        counter = WordCounter()

        # min_word_lengthが負の値
        with pytest.raises(ValueError) as excinfo:
            counter.count_morphological_words(messages, words_by_message, min_word_length=-1)
        assert "min_word_lengthは0以上である必要があります" in str(excinfo.value)

        # max_word_lengthが負の値
        with pytest.raises(ValueError) as excinfo:
            counter.count_morphological_words(messages, words_by_message, max_word_length=-1)
        assert "max_word_lengthは0以上である必要があります" in str(excinfo.value)

        # min_word_length > max_word_length
        with pytest.raises(ValueError) as excinfo:
            counter.count_morphological_words(
                messages, words_by_message, min_word_length=10, max_word_length=5
            )
        assert "min_word_lengthはmax_word_length以下である必要があります" in str(excinfo.value)
        assert "min=10" in str(excinfo.value)
        assert "max=5" in str(excinfo.value)

    def test_count_full_messages_exact_match(self) -> None:
        """メッセージ全文の完全一致カウントテスト"""
        messages = [
            Message(
                datetime=datetime(2024, 8, 1, 22, 12),
                user="ユーザーA",
                content="おはよう",
            ),
            Message(
                datetime=datetime(2024, 8, 1, 22, 15),
                user="ユーザーB",
                content="おはよう",
            ),
            Message(
                datetime=datetime(2024, 8, 1, 22, 20),
                user="ユーザーC",
                content="こんにちは",
            ),
        ]

        counter = WordCounter()
        message_counts = counter.count_full_messages(messages)

        # メッセージ種類数の確認
        assert len(message_counts) == 2  # おはよう、こんにちは

        # 各メッセージのカウント確認
        message_count_dict = {mc.message: mc for mc in message_counts}

        assert "おはよう" in message_count_dict
        assert message_count_dict["おはよう"].count == 2

        assert "こんにちは" in message_count_dict
        assert message_count_dict["こんにちは"].count == 1

    def test_count_full_messages_empty(self) -> None:
        """空のメッセージリストのテスト"""
        counter = WordCounter()
        message_counts = counter.count_full_messages([])

        assert len(message_counts) == 0

    def test_count_full_messages_with_length_filter(self) -> None:
        """メッセージ全文カウントの文字数フィルタリングテスト"""
        messages = [
            Message(
                datetime=datetime(2024, 8, 1, 22, 12),
                user="ユーザーA",
                content="短",  # 1文字
            ),
            Message(
                datetime=datetime(2024, 8, 1, 22, 13),
                user="ユーザーB",
                content="中間",  # 2文字
            ),
            Message(
                datetime=datetime(2024, 8, 1, 22, 14),
                user="ユーザーC",
                content="これは長い",  # 5文字
            ),
            Message(
                datetime=datetime(2024, 8, 1, 22, 15),
                user="ユーザーD",
                content="短中間",  # "短"と"中間"を含む
            ),
        ]

        counter = WordCounter()

        # 最小文字数2文字：「短」は集計対象外
        message_counts = counter.count_full_messages(messages, min_message_length=2)
        message_count_dict = {mc.message: mc for mc in message_counts}

        # 「短」は1文字なので集計されない
        assert "短" not in message_count_dict
        # 「中間」は2文字なので集計される
        assert "中間" in message_count_dict
        assert message_count_dict["中間"].count == 1

        # 最大文字数2文字：「これは長い」は集計対象外
        message_counts = counter.count_full_messages(
            messages, min_message_length=1, max_message_length=2
        )
        message_count_dict = {mc.message: mc for mc in message_counts}

        # 「これは長い」は5文字なので集計されない
        assert "これは長い" not in message_count_dict
        # 「短」「中間」は集計される
        assert "短" in message_count_dict
        assert "中間" in message_count_dict

    def test_count_full_messages_invalid_parameters(self) -> None:
        """count_full_messagesのパラメータ検証テスト"""
        messages = [
            Message(
                datetime=datetime(2024, 8, 1, 22, 12),
                user="ユーザーA",
                content="テスト",
            ),
        ]

        counter = WordCounter()

        # min_message_lengthが負の値
        with pytest.raises(ValueError) as excinfo:
            counter.count_full_messages(messages, min_message_length=-1)
        assert "min_message_lengthは0以上である必要があります" in str(excinfo.value)

        # max_message_lengthが負の値
        with pytest.raises(ValueError) as excinfo:
            counter.count_full_messages(messages, max_message_length=-1)
        assert "max_message_lengthは0以上である必要があります" in str(excinfo.value)

        # min_message_length > max_message_length
        with pytest.raises(ValueError) as excinfo:
            counter.count_full_messages(messages, min_message_length=10, max_message_length=5)
        assert "min_message_lengthはmax_message_length以下である必要があります" in str(
            excinfo.value
        )
        assert "min=10" in str(excinfo.value)
        assert "max=5" in str(excinfo.value)

    # NOTE: Issue#01でappearancesフィールドはレスポンスから削除されましたが、
    # 内部データ構造(WordCount, MessageCount)のappearancesフィールドは保持されています。
    # 将来の時系列解析機能実装時に内部データが正しく記録されていることを保証するため、
    # 以下のテストは引き続き実行します。
    def test_word_appearances_recorded(
        self,
        sample_messages: list[Message],
        sample_words_by_message: list[list[Word]],
    ) -> None:
        """単語の出現情報が正しく記録されているかのテスト"""
        counter = WordCounter()
        word_counts = counter.count_morphological_words(sample_messages, sample_words_by_message)
        word_count_dict = {wc.base_form: wc for wc in word_counts}
        # "今日"が出現したメッセージの確認
        today_appearances = word_count_dict["今日"].appearances
        assert len(today_appearances) == 2
        assert all(msg in sample_messages[:2] for msg in today_appearances)

    def test_message_appearances_recorded(self) -> None:
        """メッセージの出現情報が正しく記録されているかのテスト"""
        messages = [
            Message(
                datetime=datetime(2024, 8, 1, 22, 12),
                user="ユーザーA",
                content="test",
            ),
            Message(
                datetime=datetime(2024, 8, 1, 22, 15),
                user="ユーザーB",
                content="test",
            ),
            Message(
                datetime=datetime(2024, 8, 1, 22, 20),
                user="ユーザーC",
                content="test123",
            ),
        ]
        counter = WordCounter()
        message_counts = counter.count_full_messages(messages)
        message_count_dict = {mc.message: mc for mc in message_counts}
        # "test"の出現情報
        test_appearances = message_count_dict["test"].appearances
        assert len(test_appearances) == 2
        assert all(msg.content == "test" for msg in test_appearances)
