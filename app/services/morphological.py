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
        # 記号は絵文字のみを対象とするため、_filter_by_pos()で個別に許可
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
        "形容動詞語幹",  # 形容動詞語幹（例: 「稀」「綺麗」） ※人名の一部として使われることがある
    }

    # 連続名詞結合から除外する名詞の細分類
    NON_COMBINABLE_NOUN_DETAILS = {
        "非自立",  # 非自立名詞（「もの」「こと」など）
        "代名詞",  # 代名詞（「これ」「それ」など）
        "数",  # 数詞（「1」「2」「十」など）
        "接尾",  # 接尾辞（「さん」「円」「個」など）
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

                # 全ての品詞で表層形を使用（基本形は使用しない）
                # 理由1: ユーザーが実際に使った言葉そのままをカウントすべき
                # 理由2: 活用形の多様性を保持（「荒い」「荒く」「荒かった」を別々にカウント）
                # 理由3: 誤解析の影響を軽減（「あらかわ」→「あらか」+「わ」の誤分割を防止）
                # 理由4: neologd辞書の正規化を回避（「アオ」->「A-O」、絵文字->日本語変換など）
                base_form = node.surface

                # 絵文字を含む単語は品詞を「記号」に統一
                # 理由: MeCabが絵文字を「記号」と「名詞」で交互に認識するため
                #       品詞を統一しないと連続記号として結合できない
                if contains_emoji(node.surface):
                    pos = "記号"

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

        # 連続する絵文字（記号）を結合（名詞結合・記号フィルタリングより先に実行）
        # 重要: 絵文字が元々連続しているかを判定するため、絵文字を含まない記号を除外する前に実行
        # 例: "！😭！😭" の場合、「！」と「😭」が交互に出現しているため、
        #     「😭」は連続していない → 結合されない
        # 例: "😭😭😭" の場合、「😭」が連続している → 結合される
        combined_morphemes = self._combine_consecutive_words(all_morphemes, "記号")

        # 連続する名詞を結合
        combined_morphemes = self._combine_consecutive_words(combined_morphemes, "名詞")

        # 絵文字を含まない記号を除外
        # 理由: MeCabは句読点と絵文字を連続する記号として認識することがある
        #       例: "！！！😭😭😭" → 1つの記号として認識される
        #       絵文字のみを抽出したいため、絵文字を含まない記号を除外
        #       ※ただし、連続する絵文字の結合判定は除外前に行う
        emoji_only_morphemes: list[Word] = []
        for word in combined_morphemes:
            if word.part_of_speech == "記号":
                # 絵文字を含む記号のみを残す
                if contains_emoji(word.surface):
                    emoji_only_morphemes.append(word)
                # 絵文字を含まない記号は除外（句読点など）
            else:
                # 記号以外はそのまま残す
                emoji_only_morphemes.append(word)

        # フィルタリングして最終結果を作成
        words: list[Word] = []
        for word in emoji_only_morphemes:
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

        1文字単語の場合、ひらがな・カタカナを除外
        漢字、アルファベット、絵文字、記号を含む1文字単語は許可

        Args:
            word (Word): チェック対象の単語

        Returns:
            bool: 条件を満たす場合True
        """
        word_length = len(word.surface)

        # min_length未満は除外
        if word_length < self.min_length:
            return False

        # 1文字の場合、追加チェック
        if word_length == 1:
            # ひらがな、カタカナのみの場合は除外
            if _is_single_kana(word.surface):
                return False
            # 上記以外（漢字、アルファベット、絵文字、記号など）は許可

        return True

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

        # 記号の場合、絵文字を含む場合のみ許可（句読点などは除外）
        if pos == "記号":
            # 絵文字を含む場合は許可
            if contains_emoji(word.surface):
                return True
            # 絵文字を含まない記号は除外
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

        # 絵文字を含む単語は結合対象外（記号として処理されるべき）
        if contains_emoji(word.surface):
            return False

        # 除外する名詞の細分類に該当する場合は対象外
        if word.part_of_speech_detail1 in self.NON_COMBINABLE_NOUN_DETAILS:
            return False

        # 結合対象の名詞の細分類に該当する場合は対象
        if word.part_of_speech_detail1 in self.COMBINABLE_NOUN_DETAILS:
            return True

        return False

    def _is_target_for_combination(self, word: Word, target_pos: str) -> bool:
        """単語が指定品詞の結合対象かどうかを判定

        Args:
            word (Word): チェック対象の単語
            target_pos (str): 結合対象の品詞（例: "名詞", "記号"）

        Returns:
            bool: 結合対象ならTrue
        """
        if target_pos == "名詞":
            return self._is_combinable_noun(word)
        elif target_pos == "記号":
            # 記号の場合、絵文字を含む記号のみを結合対象とする
            # これにより「！😭！😭」のような場合に、「！」が除外された後に
            # 「😭😭」として誤結合されることを防ぐ
            return word.part_of_speech == "記号" and contains_emoji(word.surface)
        return word.part_of_speech == target_pos

    def _combine_consecutive_words(self, words: list[Word], target_pos: str) -> list[Word]:
        """連続する指定品詞の単語を1つの単語に結合

        名詞・記号など、連続する同じ品詞の単語を1つに結合します。
        結合後の単語は表層形でカウントされます。

        Args:
            words (list[Word]): 形態素解析結果の単語リスト
            target_pos (str): 結合対象の品詞（例: "名詞", "記号"）

        Returns:
            list[Word]: 連続単語を結合した単語リスト
        """
        if not words:
            return []

        combined_words: list[Word] = []
        i = 0

        while i < len(words):
            current_word = words[i]

            # 結合対象かどうかを判定
            is_target = self._is_target_for_combination(current_word, target_pos)

            # 結合対象の場合、連続する単語を探す
            if is_target:
                # 連続する単語を収集
                word_group = [current_word]
                j = i + 1

                while j < len(words):
                    next_word = words[j]
                    # 次の単語も結合対象かチェック
                    is_next_target = self._is_target_for_combination(next_word, target_pos)

                    if is_next_target:
                        word_group.append(next_word)
                        j += 1
                    else:
                        break

                # 2つ以上の単語が連続している場合は結合
                if len(word_group) > 1:
                    # 表層形を連結
                    combined_surface = "".join(word.surface for word in word_group)

                    # 結合された単語を作成（基本形も表層形と同じにする）
                    combined_word = Word(
                        surface=combined_surface,
                        base_form=combined_surface,
                        part_of_speech=target_pos,
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
                # 対象品詞以外はそのまま追加
                combined_words.append(current_word)
                i += 1

        return combined_words


def contains_emoji(text: str) -> bool:
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


def _is_single_kana(text: str) -> bool:
    """1文字のひらがな、カタカナかどうかを判定

    Args:
        text (str): 判定対象の文字列

    Returns:
        bool: 1文字のひらがな、カタカナならTrue
    """
    # 1文字でない場合はFalse
    if len(text) != 1:
        return False

    char = text[0]
    code_point = ord(char)

    # ひらがな（U+3040-U+309F）
    if 0x3040 <= code_point <= 0x309F:
        return True

    # カタカナ（U+30A0-U+30FF）
    if 0x30A0 <= code_point <= 0x30FF:
        return True

    # 半角カタカナ（U+FF65-U+FF9F）
    if 0xFF65 <= code_point <= 0xFF9F:
        return True

    return False
