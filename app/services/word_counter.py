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
        count (int): 出現回数
        part_of_speech (str): 品詞
        appearances (list[Message]): 出現したメッセージのリスト
    """

    word: str
    base_form: str
    count: int
    part_of_speech: str
    appearances: list[Message]


@dataclass
class MessageCount:
    """メッセージのカウント情報

    Attributes:
        message (str): メッセージ本文
        exact_count (int): 完全一致カウント
        partial_count (int): 部分一致カウント
        total_count (int): 合計カウント
        exact_appearances (list[Message]): 完全一致したメッセージのリスト
        partial_appearances (list[Message]): 部分一致したメッセージのリスト
    """

    message: str
    exact_count: int
    partial_count: int
    total_count: int
    exact_appearances: list[Message]
    partial_appearances: list[Message]


class WordCounter:
    """単語カウンター

    形態素解析結果とメッセージ全文の集計を行う
    """

    def count_morphological_words(
        self,
        messages: list[Message],
        words_by_message: list[list[Word]],
        min_word_length: int = 1,
        max_word_length: int | None = None,
    ) -> list[WordCount]:
        """形態素解析結果の集計

        Args:
            messages (list[Message]): メッセージのリスト
            words_by_message (list[list[Word]]): メッセージごとの単語リスト（messagesと同じ順序）
            min_word_length (int): 集計対象の最小文字数（デフォルト: 1）
            max_word_length (int | None): 集計対象の最大文字数（デフォルト: None=無制限）

        Returns:
            list[WordCount]: 単語カウント結果のリスト
        """
        # 基本形をキーとして単語をグループ化
        word_dict: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "surface": "",
                "base_form": "",
                "count": 0,
                "part_of_speech": "",
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

                # 初回登録時は表層形と品詞を設定
                if entry["count"] == 0:
                    entry["surface"] = word.surface
                    entry["base_form"] = word.base_form
                    entry["part_of_speech"] = word.part_of_speech

                entry["count"] += 1
                entry["appearances"].append(message)

        # WordCountオブジェクトのリストに変換
        word_counts = [
            WordCount(
                word=data["surface"],
                base_form=data["base_form"],
                count=data["count"],
                part_of_speech=data["part_of_speech"],
                appearances=data["appearances"],
            )
            for data in word_dict.values()
        ]

        return word_counts

    def count_full_messages(
        self,
        messages: list[Message],
        min_message_length: int = 1,
        max_message_length: int | None = None,
    ) -> list[MessageCount]:
        """メッセージ全文の集計

        Args:
            messages (list[Message]): メッセージのリスト
            min_message_length (int): 部分一致検索対象の最小文字数（デフォルト: 1）
            max_message_length (int | None): 部分一致検索対象の最大文字数（デフォルト: None=無制限）

        Returns:
            list[MessageCount]: メッセージカウント結果のリスト
        """
        # メッセージ本文をキーとして集計
        message_dict: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "exact_count": 0,
                "partial_count": 0,
                "exact_appearances": [],
                "partial_appearances": [],
            }
        )

        # 完全一致のカウント
        for message in messages:
            content = message.content
            message_dict[content]["exact_count"] += 1
            message_dict[content]["exact_appearances"].append(message)

        # 部分一致のカウント
        for target_content in list(message_dict.keys()):
            # 文字数チェック: 範囲内のメッセージのみ部分一致検索を実行
            content_length = len(target_content)
            if content_length < min_message_length:
                continue
            if max_message_length is not None and content_length > max_message_length:
                continue

            partial_matches = self._find_partial_matches(target_content, messages)
            message_dict[target_content]["partial_count"] = len(partial_matches)
            message_dict[target_content]["partial_appearances"] = partial_matches

        # MessageCountオブジェクトのリストに変換
        message_counts = [
            MessageCount(
                message=content,
                exact_count=data["exact_count"],
                partial_count=data["partial_count"],
                total_count=data["exact_count"] + data["partial_count"],
                exact_appearances=data["exact_appearances"],
                partial_appearances=data["partial_appearances"],
            )
            for content, data in message_dict.items()
        ]

        return message_counts

    def _find_partial_matches(
        self, target: str, messages: list[Message]
    ) -> list[Message]:
        """部分一致検索

        対象メッセージを部分文字列として含む他のメッセージを検索する
        （完全一致は除外）
        同一メッセージ内に複数回出現する場合は、その回数分カウントする（重複なし）

        例: 「＾＾」を検索時、「それな＾＾＾＾」は2回含まれる

        Args:
            target (str): 検索対象のメッセージ本文
            messages (list[Message]): 全メッセージのリスト

        Returns:
            list[Message]: 部分一致したメッセージのリスト（複数回出現する場合は複数回追加）
        """
        partial_matches: list[Message] = []

        for message in messages:
            # 完全一致は除外
            if message.content == target:
                continue

            # 部分一致の回数をカウント（重複を考慮）
            count = self._count_occurrences(target, message.content)
            # 出現回数分だけリストに追加
            for _ in range(count):
                partial_matches.append(message)

        return partial_matches

    def _count_occurrences(self, substring: str, text: str) -> int:
        """文字列内の部分文字列の出現回数をカウント（重複なし）

        見つかった部分文字列を取り除いてから次を検索する方式
        例: 「＾＾＾＾」に「＾＾」は2回（最初の「＾＾」を取り除いて残りの「＾＾」で1回）

        Args:
            substring (str): 検索する部分文字列
            text (str): 検索対象のテキスト

        Returns:
            int: 出現回数
        """
        if not substring or not text:
            return 0

        count = 0
        start = 0

        while True:
            # 次の出現位置を検索
            pos = text.find(substring, start)
            if pos == -1:
                break
            count += 1
            # 次の検索開始位置を部分文字列の長さ分進める（重複を許さない）
            start = pos + len(substring)

        return count
