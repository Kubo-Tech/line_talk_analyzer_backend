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

    # 連続名詞結合の対象となる名詞の細分類
    COMBINABLE_NOUN_DETAILS = {
        "一般",  # 一般名詞（例: 「プラモデル」「アニメ」）
        "固有名詞",  # 固有名詞（例: 「ガンダム」「東京」）
        "サ変接続",  # サ変接続（例: 「ストア」「センター」） ※固有名詞の一部として使われることが多い
    }

    # 連続名詞結合から除外する名詞の細分類
    NON_COMBINABLE_NOUN_DETAILS = {
        "非自立",  # 非自立名詞（「もの」「こと」など）
        "代名詞",  # 代名詞（「これ」「それ」など）
        "数",  # 数詞（「1」「2」「十」など）
        "接尾",  # 接尾辞（「さん」「円」「個」など）
        "形容動詞語幹",  # 形容動詞語幹（「綺麗」「元気」など）
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
            # neologd辞書を使用（新語・固有名詞の認識精度向上）
            self.tagger = MeCab.Tagger(
                "-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd"
            )
        except Exception as e:
            raise RuntimeError(f"MeCabの初期化に失敗しました: {e}") from e

        self.min_length = min_length
        self.exclude_parts = set(exclude_parts) if exclude_parts else set()

        # ストップワードの読み込み
        self.stop_words = self._load_stop_words()

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

        # 全ての形態素を一旦リストに格納（フィルタリング前）
        all_morphemes: list[Word] = []

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

                # 絵文字の場合は基本形ではなく表層形（絵文字そのまま）を使用
                # neologd辞書は絵文字を日本語テキストに変換するため
                # 例: 😭 -> 「大泣き」、😂 -> 「嬉し涙」
                if _contains_emoji(node.surface):
                    base_form = node.surface

                # 名詞の場合は基本形ではなく表層形を使用
                # 理由1: 名詞には活用がないため、基本形を使う意味がない
                # 理由2: neologd辞書が固有名詞をローマ字等に正規化することがある
                #       例: 「アオ」-> 「A-O」、「ひろゆき」-> 「西村博之」
                # 理由3: ユーザーが実際に使った言葉そのままをカウントすべき
                if pos == "名詞":
                    base_form = node.surface

                word = Word(
                    surface=node.surface,
                    base_form=base_form,
                    part_of_speech=pos,
                    part_of_speech_detail1=pos_detail1,
                    part_of_speech_detail2=pos_detail2,
                    part_of_speech_detail3=pos_detail3,
                )

                all_morphemes.append(word)

            node = node.next

        # 連続する名詞を結合
        combined_morphemes = self._combine_consecutive_nouns(all_morphemes)

        # フィルタリングして最終結果を作成
        words: list[Word] = []
        for word in combined_morphemes:
            if self._should_include(word):
                words.append(word)

        return words

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

        # 絵文字を含む記号は特別に許可（表層形に絵文字が含まれる場合）
        if pos == "記号" and _contains_emoji(word.surface):
            return True

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

    def _is_combinable_noun(self, word: Word) -> bool:
        """連続名詞結合の対象となる名詞かどうかを判定

        Args:
            word (Word): チェック対象の単語

        Returns:
            bool: 結合対象の名詞ならTrue
        """
        # 品詞が名詞でない場合は対象外
        if word.part_of_speech != "名詞":
            return False

        # 除外する名詞の細分類に該当する場合は対象外
        if word.part_of_speech_detail1 in self.NON_COMBINABLE_NOUN_DETAILS:
            return False

        # 結合対象の名詞の細分類に該当する場合は対象
        if word.part_of_speech_detail1 in self.COMBINABLE_NOUN_DETAILS:
            return True

        return False

    def _combine_consecutive_nouns(self, words: list[Word]) -> list[Word]:
        """連続する名詞を1つの単語に結合

        Args:
            words (list[Word]): 形態素解析結果の単語リスト

        Returns:
            list[Word]: 連続名詞を結合した単語リスト
        """
        if not words:
            return []

        combined_words: list[Word] = []
        i = 0

        while i < len(words):
            current_word = words[i]

            # 結合可能な名詞の場合、連続する名詞を探す
            if self._is_combinable_noun(current_word):
                # 連続する名詞を収集
                noun_group = [current_word]
                j = i + 1

                while j < len(words) and self._is_combinable_noun(words[j]):
                    noun_group.append(words[j])
                    j += 1

                # 2つ以上の名詞が連続している場合は結合
                if len(noun_group) > 1:
                    # 表層形を連結
                    combined_surface = "".join(word.surface for word in noun_group)

                    # 結合された単語を作成（基本形も表層形と同じにする）
                    combined_word = Word(
                        surface=combined_surface,
                        base_form=combined_surface,
                        part_of_speech="名詞",
                        part_of_speech_detail1="一般",
                        part_of_speech_detail2="*",
                        part_of_speech_detail3="*",
                    )
                    combined_words.append(combined_word)
                    i = j  # 次の単語へ
                else:
                    # 1つだけの場合はそのまま追加
                    combined_words.append(current_word)
                    i += 1
            else:
                # 名詞以外はそのまま追加
                combined_words.append(current_word)
                i += 1

        return combined_words


def _contains_emoji(text: str) -> bool:
    """テキストに絵文字が含まれるかをチェック

    バリエーションセレクタなどの制御文字は絵文字とみなさない

    Args:
        text (str): チェック対象のテキスト

    Returns:
        bool: 絵文字が含まれる場合True
    """
    import unicodedata

    # テキストが空または空白のみの場合は絵文字ではない
    if not text or not text.strip():
        return False

    # 全ての文字をチェック
    for char in text:
        category = unicodedata.category(char)

        # 制御文字（Cc, Cf）や非スペーシング記号（Mn）は除外
        if category in ("Cc", "Cf", "Mn"):
            continue

        # 絵文字の範囲をチェック
        code_point = ord(char)

        # 主要な絵文字ブロック
        if (
            (0x1F600 <= code_point <= 0x1F64F)  # 顔文字
            or (0x1F300 <= code_point <= 0x1F5FF)  # その他の記号と絵文字
            or (0x1F680 <= code_point <= 0x1F6FF)  # 交通と地図記号
            or (0x1F1E0 <= code_point <= 0x1F1FF)  # 国旗
            or (0x2600 <= code_point <= 0x26FF)  # その他の記号
            or (0x2700 <= code_point <= 0x27BF)  # 装飾記号
            or (0x1F900 <= code_point <= 0x1F9FF)  # 補助絵文字
            or (0x1FA00 <= code_point <= 0x1FA6F)  # 拡張絵文字
            or (0x2300 <= code_point <= 0x23FF)  # その他の技術記号
        ):
            return True

    return False
