"""統合解析サービス

LINEトーク履歴の解析処理を統合し、API向けのレスポンスを生成する
"""

from datetime import datetime
from io import StringIO
from typing import Any, TextIO

from app.models.response import (
    AnalysisPeriod,
    AnalysisResult,
    MessageAnalysisResult,
    MessageAppearance,
    MorphologicalAnalysis,
    TopMessage,
    TopWord,
    WordAnalysisResult,
    WordAppearance,
)
from app.services.morphological import MorphologicalAnalyzer
from app.services.parser import LineMessageParser, Message
from app.services.word_counter import MessageCount, WordCount, WordCounter


class TalkAnalyzer:
    """トーク解析統合クラス

    パーサー、形態素解析、単語カウンターを統合し、
    解析結果をAPI向けのレスポンス形式に整形する
    """

    def __init__(self) -> None:
        """初期化処理

        各サービスのインスタンスを生成する
        """
        self.parser = LineMessageParser()
        self.morphological_analyzer = MorphologicalAnalyzer()
        self.word_counter = WordCounter()

    def analyze(
        self,
        file: TextIO | str,
        top_n: int = 50,
        min_word_length: int = 2,
        max_word_length: int | None = None,
        min_message_length: int = 2,
        max_message_length: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> AnalysisResult:
        """トーク履歴を解析する

        LINEトーク履歴ファイルを解析し、単語とメッセージの集計を行い、
        API向けのレスポンス形式に整形する

        Args:
            file (TextIO | str): LINEトーク履歴ファイルまたは文字列
            top_n (int): 取得する上位単語数（デフォルト: 50）
            min_word_length (int): 最小単語長（デフォルト: 2）
            max_word_length (int | None): 最大単語長（デフォルト: None）
            min_message_length (int): 最小メッセージ長（デフォルト: 2）
            max_message_length (int | None): 最大メッセージ長（デフォルト: None）
            start_date (datetime | None): 解析開始日時（デフォルト: None）
            end_date (datetime | None): 解析終了日時（デフォルト: None）


        Returns:
            AnalysisResult: 解析結果

        Raises:
            ValueError: パラメータが無効な場合
        """
        # パラメータのバリデーション
        if top_n <= 0:
            raise ValueError(f"top_nは1以上である必要があります: {top_n}")
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValueError(
                f"start_dateはend_date以前である必要があります: "
                f"start_date={start_date}, end_date={end_date}"
            )

        # 文字列の場合はStringIOに変換
        if isinstance(file, str):
            file = StringIO(file)

        # 1. パーサーでトーク履歴を構造化
        try:
            messages = self.parser.parse(file)
        except ValueError:
            # 有効なメッセージが見つからない場合は空の結果を返す
            return self._create_empty_result()

        # メッセージが空の場合は空の結果を返す
        if not messages:
            return self._create_empty_result()

        # 期間でフィルタリング
        messages = self._filter_by_period(messages, start_date, end_date)

        # フィルタリング後にメッセージが空の場合は空の結果を返す
        if not messages:
            return self._create_empty_result()

        # 2. 形態素解析で単語抽出
        words_by_message = [self.morphological_analyzer.analyze(msg.content) for msg in messages]

        # 3. 単語カウンターで集計
        word_counts = self.word_counter.count_morphological_words(
            messages, words_by_message, min_word_length, max_word_length
        )
        message_counts = self.word_counter.count_full_messages(
            messages, min_message_length, max_message_length
        )

        # 4. 上位N件を抽出してソート
        top_words = self._get_top_words(word_counts, top_n)
        top_messages = self._get_top_messages(message_counts, top_n)

        # 4.5. ユーザー別集計
        # word_countsとmessage_countsのuser_countsからユーザー別ランキングを生成
        user_word_analysis = self._format_user_word_analysis(word_counts, top_n)
        user_message_analysis = self._format_user_message_analysis(message_counts, top_n)

        # 5. APIレスポンス形式に整形
        return self._format_response(
            messages, top_words, top_messages, user_word_analysis, user_message_analysis
        )

    def _filter_by_period(
        self,
        messages: list[Message],
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> list[Message]:
        """メッセージを期間でフィルタリングする

        Args:
            messages (list[Message]): メッセージのリスト
            start_date (datetime | None): 開始日時（Noneの場合はフィルタリングしない）
            end_date (datetime | None): 終了日時（Noneの場合はフィルタリングしない）

        Returns:
            list[Message]: フィルタリング後のメッセージリスト
        """
        filtered_messages = messages

        # 開始日時でフィルタリング
        if start_date is not None:
            filtered_messages = [msg for msg in filtered_messages if msg.datetime >= start_date]

        # 終了日時でフィルタリング
        if end_date is not None:
            filtered_messages = [msg for msg in filtered_messages if msg.datetime <= end_date]

        return filtered_messages

    def _get_top_words(self, word_counts: list[WordCount], top_n: int) -> list[WordCount]:
        """上位N件の単語を取得する

        Args:
            word_counts (list[WordCount]): 単語カウントのリスト
            top_n (int): 取得する上位件数

        Returns:
            list[WordCount]: 上位N件の単語カウントのリスト（カウント降順）
        """
        # カウント数でソート（降順）し、上位N件を取得
        sorted_words = sorted(word_counts, key=lambda x: x.count, reverse=True)
        return sorted_words[:top_n]

    def _get_top_messages(
        self, message_counts: list[MessageCount], top_n: int
    ) -> list[MessageCount]:
        """上位N件のメッセージを取得する

        Args:
            message_counts (list[MessageCount]): メッセージカウントのリスト
            top_n (int): 取得する上位件数

        Returns:
            list[MessageCount]: 上位N件のメッセージカウントのリスト（カウント降順）
        """
        # カウント数でソート（降順）し、上位N件を取得
        sorted_messages = sorted(message_counts, key=lambda x: x.count, reverse=True)
        return sorted_messages[:top_n]

    def _format_response(
        self,
        messages: list[Message],
        top_words: list[WordCount],
        top_messages: list[MessageCount],
        user_word_analysis: list[Any] | None = None,
        user_message_analysis: list[Any] | None = None,
    ) -> AnalysisResult:
        """APIレスポンス形式に整形する

        Args:
            messages (list[Message]): 全メッセージのリスト
            top_words (list[WordCount]): 上位単語のリスト
            top_messages (list[MessageCount]): 上位メッセージのリスト

        Returns:
            AnalysisResult: 整形された解析結果
        """
        # 解析期間を計算
        start_date = min(msg.datetime for msg in messages)
        end_date = max(msg.datetime for msg in messages)
        analysis_period = AnalysisPeriod(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        # 総ユーザー数を計算
        unique_users = len(set(msg.user for msg in messages))

        # 形態素解析結果を整形
        morphological_analysis = self._format_morphological_analysis(top_words)

        # メッセージ全文解析結果を整形
        full_message_analysis = self._format_message_analysis(top_messages)

        # レスポンスを生成
        # ユーザー別解析結果の作成
        from app.models.response import UserAnalysis

        user_analysis = None
        if user_word_analysis is not None or user_message_analysis is not None:
            user_analysis = UserAnalysis(
                word_analysis=user_word_analysis or [],
                message_analysis=user_message_analysis or [],
            )

        return AnalysisResult(
            status="success",
            data=WordAnalysisResult(
                analysis_period=analysis_period,
                total_messages=len(messages),
                total_users=unique_users,
                morphological_analysis=morphological_analysis,
                full_message_analysis=full_message_analysis,
                user_analysis=user_analysis,
            ),
        )

    def _format_morphological_analysis(self, top_words: list[WordCount]) -> MorphologicalAnalysis:
        """形態素解析結果を整形する

        Args:
            top_words (list[WordCount]): 上位単語のリスト

        Returns:
            MorphologicalAnalysis: 整形された形態素解析結果
        """
        top_word_models = []
        for word_count in top_words:
            appearances = [
                WordAppearance(
                    date=msg.datetime,
                    user=msg.user,
                    message=msg.content,
                )
                for msg in word_count.appearances
            ]
            top_word_models.append(
                TopWord(
                    word=word_count.word,
                    count=word_count.count,
                    part_of_speech=word_count.part_of_speech,
                    appearances=appearances,
                )
            )
        return MorphologicalAnalysis(top_words=top_word_models)

    def _format_message_analysis(self, top_messages: list[MessageCount]) -> MessageAnalysisResult:
        """メッセージ全文解析結果を整形する

        Args:
            top_messages (list[MessageCount]): 上位メッセージのリスト

        Returns:
            MessageAnalysisResult: 整形されたメッセージ全文解析結果
        """
        top_message_models = []
        for message_count in top_messages:
            appearances = [
                MessageAppearance(
                    date=msg.datetime,
                    user=msg.user,
                    message=msg.content,
                    match_type="exact",
                )
                for msg in message_count.appearances
            ]

            top_message_models.append(
                TopMessage(
                    message=message_count.message,
                    count=message_count.count,
                    appearances=appearances,
                )
            )

        return MessageAnalysisResult(top_messages=top_message_models)

    def _create_empty_result(self) -> AnalysisResult:
        """空の解析結果を生成する

        メッセージが存在しない場合の結果を返す

        Returns:
            AnalysisResult: 空の解析結果
        """
        # 現在の日付を使用
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")

        return AnalysisResult(
            status="success",
            data=WordAnalysisResult(
                analysis_period=AnalysisPeriod(
                    start_date=date_str,
                    end_date=date_str,
                ),
                total_messages=0,
                total_users=0,
                morphological_analysis=MorphologicalAnalysis(top_words=[]),
                full_message_analysis=MessageAnalysisResult(top_messages=[]),
            ),
        )

    def _format_user_word_analysis(self, word_counts: list[WordCount], top_n: int) -> list[Any]:
        """ユーザー別の単語解析結果を整形する

        Args:
            word_counts (list[WordCount]): 単語カウントのリスト（user_countsを含む）
            top_n (int): 各ユーザーの上位N件

        Returns:
            list[Any]: ユーザー別単語解析結果
        """
        from app.models.response import UserWordAnalysis

        # ユーザーごとに単語カウントを集約
        user_word_dict: dict[str, list[tuple[WordCount, int]]] = {}
        for wc in word_counts:
            for user, count in wc.user_counts.items():
                if user not in user_word_dict:
                    user_word_dict[user] = []
                user_word_dict[user].append((wc, count))

        # 各ユーザーの上位N件を取得
        user_analysis_list = []
        for user, word_list in user_word_dict.items():
            # カウント順でソート
            sorted_words = sorted(word_list, key=lambda x: x[1], reverse=True)[:top_n]

            # レスポンス形式に整形
            top_words_response = [
                TopWord(
                    word=wc.base_form,
                    count=user_count,
                    part_of_speech=wc.part_of_speech,
                    appearances=[
                        WordAppearance(
                            date=msg.datetime,
                            user=msg.user,
                            message=msg.content,
                        )
                        for msg in wc.appearances
                        if msg.user == user  # そのユーザーの発言のみ
                    ][
                        :5
                    ],  # 上位5件の出現情報
                )
                for wc, user_count in sorted_words
            ]
            user_analysis_list.append(
                UserWordAnalysis(
                    user=user,
                    top_words=top_words_response,
                )
            )
        return user_analysis_list

    def _format_user_message_analysis(
        self, message_counts: list[MessageCount], top_n: int
    ) -> list[Any]:
        """ユーザー別のメッセージ解析結果を整形する

        Args:
            message_counts (list[MessageCount]): メッセージカウントのリスト（user_countsを含む）
            top_n (int): 各ユーザーの上位N件

        Returns:
            list[Any]: ユーザー別メッセージ解析結果
        """
        from app.models.response import UserMessageAnalysis

        # ユーザーごとにメッセージカウントを集約
        user_message_dict: dict[str, list[tuple[MessageCount, int]]] = {}
        for mc in message_counts:
            for user, count in mc.user_counts.items():
                if user not in user_message_dict:
                    user_message_dict[user] = []
                user_message_dict[user].append((mc, count))

        # 各ユーザーの上位N件を取得
        user_analysis_list = []
        for user, message_list in user_message_dict.items():
            # カウント順でソート
            sorted_messages = sorted(message_list, key=lambda x: x[1], reverse=True)[:top_n]

            # レスポンス形式に整形
            top_messages_response = [
                TopMessage(
                    message=mc.message,
                    count=user_count,
                    appearances=[
                        MessageAppearance(
                            date=msg.datetime,
                            user=msg.user,
                            message=msg.content,
                            match_type="exact",
                        )
                        for msg in mc.appearances
                        if msg.user == user  # そのユーザーの発言のみ
                    ][
                        :5
                    ],  # 上位5件の出現情報
                )
                for mc, user_count in sorted_messages
            ]
            user_analysis_list.append(
                UserMessageAnalysis(
                    user=user,
                    top_messages=top_messages_response,
                )
            )
        return user_analysis_list
