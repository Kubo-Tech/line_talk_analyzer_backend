"""単語カウンターサービス

形態素解析結果とメッセージ全文の集計を行う
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from app.services.morphological import Word
from app.services.parser import Message


@dataclass
class WordCount:
    """単語のカウント情報

    Attributes:
        word (str): 単語（表層形）
        base_form (str): 基本形
        count (int): 出現回数（全体）
        part_of_speech (str): 品詞
        user_counts (dict[str, int]): 発言者ごとの出現回数
        appearances (list[Message]): 出現したメッセージのリスト（時系列データ用）
    """

    word: str
    base_form: str
    count: int
    part_of_speech: str
    user_counts: dict[str, int]
    appearances: list[Message]


@dataclass
class MessageCount:
    """メッセージのカウント情報

    Attributes:
        message (str): メッセージ本文
        count (int): 出現回数（全体）
        user_counts (dict[str, int]): 発言者ごとの出現回数
        appearances (list[Message]): 出現したメッセージのリスト（時系列データ用）
    """

    message: str
    count: int
    user_counts: dict[str, int]
    appearances: list[Message]


class WordCounter:
    """単語カウンター

    形態素解析結果とメッセージ全文の集計を行う
    """

    def count_morphological_words(
        self,
        messages: list[Message],
        words_by_message: list[list[Word]],
        min_word_length: int = 2,
        max_word_length: int | None = None,
    ) -> list[WordCount]:
        """形態素解析結果の集計

        Args:
            messages (list[Message]): メッセージのリスト
            words_by_message (list[list[Word]]): メッセージごとの単語リスト（messagesと同じ順序）
            min_word_length (int): 集計対象の最小文字数（デフォルト: 2）
            max_word_length (int | None): 集計対象の最大文字数（デフォルト: None=無制限）

        Returns:
            list[WordCount]: 単語カウント結果のリスト

        Raises:
            ValueError: messagesとwords_by_messageの長さが一致しない場合
            ValueError: min_word_lengthが負の値の場合
            ValueError: max_word_lengthが負の値の場合
            ValueError: min_word_length > max_word_lengthの場合
        """
        # min_word_lengthとmax_word_lengthの検証
        if min_word_length < 0:
            raise ValueError(f"min_word_lengthは0以上である必要があります: {min_word_length}")
        if max_word_length is not None and max_word_length < 0:
            raise ValueError(f"max_word_lengthは0以上である必要があります: {max_word_length}")
        if max_word_length is not None and min_word_length > max_word_length:
            raise ValueError(
                f"min_word_lengthはmax_word_length以下である必要があります: "
                f"min={min_word_length}, max={max_word_length}"
            )

        # messagesとwords_by_messageの長さが一致することを検証
        if len(messages) != len(words_by_message):
            raise ValueError(
                f"messagesとwords_by_messageの長さが一致しません: "
                f"messages={len(messages)}, words_by_message={len(words_by_message)}"
            )

        # 基本形をキーとして単語をグループ化
        word_dict: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "surface": "",
                "base_form": "",
                "count": 0,
                "part_of_speech": "",
                "user_counts": defaultdict(int),
                "appearances": [],
            }
        )

        for i, words in enumerate(words_by_message):
            message = messages[i]
            for word in words:
                # 文字数チェック
                word_length = len(word.surface)
                if word_length < min_word_length:
                    continue
                if max_word_length is not None and word_length > max_word_length:
                    continue

                key = word.base_form
                entry = word_dict[key]

                # 初回登録時は基本形と品詞を設定
                if entry["count"] == 0:
                    entry["surface"] = word.base_form  # 基本形を表示用にも使用
                    entry["base_form"] = word.base_form
                    entry["part_of_speech"] = word.part_of_speech

                entry["count"] += 1
                entry["user_counts"][message.user] += 1  # 発言者ごとのカウント
                entry["appearances"].append(message)

        # WordCountオブジェクトのリストに変換
        word_counts = [
            WordCount(
                word=data["surface"],
                base_form=data["base_form"],
                count=data["count"],
                part_of_speech=data["part_of_speech"],
                user_counts=dict(data["user_counts"]),  # defaultdictをdictに変換
                appearances=data["appearances"],
            )
            for data in word_dict.values()
        ]

        return word_counts

    def count_full_messages(
        self,
        messages: list[Message],
        min_message_length: int = 2,
        max_message_length: int | None = None,
    ) -> list[MessageCount]:
        """メッセージ全文の集計

        Args:
            messages (list[Message]): メッセージのリスト
            min_message_length (int): 集計対象の最小文字数（デフォルト: 2）
            max_message_length (int | None): 集計対象の最大文字数（デフォルト: None=無制限）

        Returns:
            list[MessageCount]: メッセージカウント結果のリスト

        Raises:
            ValueError: min_message_lengthが負の値の場合
            ValueError: max_message_lengthが負の値の場合
            ValueError: min_message_length > max_message_lengthの場合
        """
        # min_message_lengthとmax_message_lengthの検証
        if min_message_length < 0:
            raise ValueError(f"min_message_lengthは0以上である必要があります: {min_message_length}")
        if max_message_length is not None and max_message_length < 0:
            raise ValueError(f"max_message_lengthは0以上である必要があります: {max_message_length}")
        if max_message_length is not None and min_message_length > max_message_length:
            raise ValueError(
                f"min_message_lengthはmax_message_length以下である必要があります: "
                f"min={min_message_length}, max={max_message_length}"
            )

        # メッセージ本文をキーとして集計
        message_dict: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "user_counts": defaultdict(int),
                "appearances": [],
            }
        )

        # 完全一致のカウント
        for message in messages:
            content = message.content

            # 文字数チェック
            content_length = len(content)
            if content_length < min_message_length:
                continue
            if max_message_length is not None and content_length > max_message_length:
                continue

            message_dict[content]["count"] += 1
            message_dict[content]["user_counts"][message.user] += 1  # 発言者ごとのカウント
            message_dict[content]["appearances"].append(message)

        # MessageCountオブジェクトのリストに変換
        message_counts = [
            MessageCount(
                message=content,
                count=data["count"],
                user_counts=dict(data["user_counts"]),  # defaultdictをdictに変換
                appearances=data["appearances"],
            )
            for content, data in message_dict.items()
        ]

        return message_counts
