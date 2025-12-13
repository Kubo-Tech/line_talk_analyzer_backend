"""形態素解析サービス

MeCabを使用してテキストを単語に分解し、品詞情報を付与する
"""

import json
from dataclasses import dataclass
from pathlib import Path

import MeCab


@dataclass
class Word:
    """単語データ

    Attributes:
        surface (str): 表層形（実際の単語）
        base_form (str): 基本形（原形）
        part_of_speech (str): 品詞
        part_of_speech_detail1 (str): 品詞細分類1
        part_of_speech_detail2 (str): 品詞細分類2
        part_of_speech_detail3 (str): 品詞細分類3
    """

    surface: str
    base_form: str
    part_of_speech: str
    part_of_speech_detail1: str
    part_of_speech_detail2: str
    part_of_speech_detail3: str


class MorphologicalAnalyzer:
    """形態素解析器

    MeCabを使用してテキストを形態素解析し、単語のリストに変換する
    """

    # 抽出対象の品詞（デフォルト）
    DEFAULT_TARGET_POS = {
        "名詞",  # 名詞全般
        "形容詞",  # 形容詞全般
        "感動詞",  # 感動詞
    }

    # 除外する名詞の細分類
    EXCLUDED_NOUN_DETAILS = {
        "非自立",  # 非自立名詞（「こと」「もの」など）
        "代名詞",  # 代名詞（「これ」「あれ」など）
        "数",  # 数詞
    }

    # 除外する形容詞の細分類
    EXCLUDED_ADJ_DETAILS = {
        "非自立",  # 非自立形容詞
        "接尾",  # 接尾辞
    }

    def __init__(
        self, min_length: int = 1, exclude_parts: set[str] | list[str] | None = None
    ) -> None:
        """形態素解析器の初期化

        Args:
            min_length (int): 最小単語長（デフォルト: 1）
            exclude_parts (set[str] | list[str] | None): 除外する品詞のリストまたはセット（デフォルト: None）

        Raises:
            RuntimeError: MeCabの初期化に失敗した場合
        """
        try:
            self.tagger = MeCab.Tagger()
        except Exception as e:
            raise RuntimeError(f"MeCabの初期化に失敗しました: {e}") from e

        self.min_length = min_length
        self.exclude_parts = set(exclude_parts) if exclude_parts else set()

        # ストップワードの読み込み
        self.stop_words = self._load_stop_words()

    def _load_stop_words(self) -> set[str]:
        """ストップワードをJSONファイルから読み込む

        Returns:
            set[str]: ストップワードのセット
        """
        stopwords_path = Path(__file__).parent.parent / "data" / "stopwords.json"

        try:
            with open(stopwords_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("stop_words", []))
        except FileNotFoundError:
            # ファイルが見つからない場合は空のセットを返す
            return set()
        except json.JSONDecodeError as e:
            # JSON解析エラーの場合は警告して空のセットを返す
            print(f"警告: stopwords.jsonの読み込みに失敗しました: {e}")
            return set()

    def analyze(self, text: str) -> list[Word]:
        """テキストを形態素解析

        Args:
            text (str): 解析対象のテキスト

        Returns:
            list[Word]: 解析された単語のリスト

        Raises:
            RuntimeError: 形態素解析に失敗した場合
        """
        if not text or not text.strip():
            return []

        # MeCabで解析
        try:
            node = self.tagger.parseToNode(text)
        except Exception as e:
            raise RuntimeError(f"形態素解析に失敗しました: {e}") from e

        words: list[Word] = []

        while node:
            # EOSノード（文末）はスキップ
            if node.surface:
                features = node.feature.split(",")

                # 品詞情報を取得（足りない場合は空文字列で埋める）
                pos = features[0] if len(features) > 0 else ""
                pos_detail1 = features[1] if len(features) > 1 else ""
                pos_detail2 = features[2] if len(features) > 2 else ""
                pos_detail3 = features[3] if len(features) > 3 else ""
                base_form = features[6] if len(features) > 6 else node.surface

                word = Word(
                    surface=node.surface,
                    base_form=base_form,
                    part_of_speech=pos,
                    part_of_speech_detail1=pos_detail1,
                    part_of_speech_detail2=pos_detail2,
                    part_of_speech_detail3=pos_detail3,
                )

                # フィルタリング
                if self._should_include(word):
                    words.append(word)

            node = node.next

        return words

    def _should_include(self, word: Word) -> bool:
        """単語を結果に含めるべきかチェック

        Args:
            word (Word): チェック対象の単語

        Returns:
            bool: 含めるべきならTrue
        """
        # 最小文字数チェック
        if not self._filter_by_length(word):
            return False

        # 品詞チェック
        if not self._filter_by_pos(word):
            return False

        # ストップワードチェック（基本形で判定）
        if word.base_form in self.stop_words:
            return False

        return True

    def _filter_by_length(self, word: Word) -> bool:
        """文字数でフィルタリング

        Args:
            word (Word): チェック対象の単語

        Returns:
            bool: 条件を満たす場合True
        """
        return len(word.surface) >= self.min_length

    def _filter_by_pos(self, word: Word) -> bool:
        """品詞でフィルタリング

        Args:
            word (Word): チェック対象の単語

        Returns:
            bool: 条件を満たす場合True
        """
        pos = word.part_of_speech
        pos_detail1 = word.part_of_speech_detail1

        # 除外品詞リストに含まれている場合は除外
        if pos in self.exclude_parts:
            return False

        # デフォルト対象品詞に含まれていない場合は除外
        if pos not in self.DEFAULT_TARGET_POS:
            return False

        # 名詞の細分類チェック
        if pos == "名詞" and pos_detail1 in self.EXCLUDED_NOUN_DETAILS:
            return False

        # 形容詞の細分類チェック
        if pos == "形容詞" and pos_detail1 in self.EXCLUDED_ADJ_DETAILS:
            return False

        return True
