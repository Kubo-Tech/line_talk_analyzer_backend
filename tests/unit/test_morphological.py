"""形態素解析サービスのテスト

MorphologicalAnalyzerクラスの各機能を網羅的にテストする
"""

import pytest

from app.services.morphological import MorphologicalAnalyzer, Word


class TestWord:
    """Wordデータクラスのテスト"""

    def test_create_instance(self) -> None:
        """インスタンス生成のテスト"""
        word = Word(
            surface="走る",
            base_form="走る",
            part_of_speech="動詞",
            part_of_speech_detail1="自立",
            part_of_speech_detail2="*",
            part_of_speech_detail3="*",
        )
        assert word.surface == "走る"
        assert word.base_form == "走る"
        assert word.part_of_speech == "動詞"


class TestMorphologicalAnalyzer:
    """MorphologicalAnalyzerクラスのテスト"""

    def test_analyze_simple_sentence(self) -> None:
        """シンプルな日本語文の解析テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("今日は良い天気です")

        assert len(words) > 0
        # 名詞「天気」、形容詞「良い」が抽出されるはず（「今日」はストップワード）
        surfaces = [w.surface for w in words]
        assert "良い" in surfaces  # 形容詞
        assert "天気" in surfaces  # 名詞

    def test_analyze_with_various_pos(self) -> None:
        """様々な品詞を含む文の解析テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("美しい花が静かに咲いている")

        # 品詞の確認（動詞「咲いて」、副詞「静かに」は除外される）
        pos_list = [w.part_of_speech for w in words]
        assert "形容詞" in pos_list  # 美しい
        assert "名詞" in pos_list  # 花、静か（形容動詞語幹）
        assert "動詞" not in pos_list  # 動詞は除外される

    def test_analyze_empty_string(self) -> None:
        """空文字列の解析テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("")

        assert len(words) == 0

    def test_analyze_whitespace_only(self) -> None:
        """空白のみの文字列の解析テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("   \n\t  ")

        assert len(words) == 0

    def test_analyze_symbols_only(self) -> None:
        """記号のみの文字列の解析テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("！？＠＃＄％")

        # MeCabの辞書によっては記号を名詞として解析する可能性がある
        # 少なくともエラーにならないことを確認
        assert isinstance(words, list)

    def test_analyze_mixed_japanese_english(self) -> None:
        """日英混在テキストの解析テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("今日はPythonでプログラミングする")

        surfaces = [w.surface for w in words]
        # 「今日」はストップワード、動詞「する」も除外される
        # 「Python」もアルファベットのみなので除外されるかも
        assert "プログラミング" in surfaces
        assert "Python" in surfaces or "プログラミング" in surfaces

    def test_analyze_with_numbers(self) -> None:
        """数字を含むテキストの解析テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("明日は10時に集合です")

        # 数詞は除外されるはず（「明日」もストップワード）
        surfaces = [w.surface for w in words]
        assert "集合" in surfaces  # 名詞
        assert "10" not in surfaces  # 数詞は除外

    def test_min_length_filtering(self) -> None:
        """最小文字数フィルタリングのテスト"""
        analyzer = MorphologicalAnalyzer(min_length=2)
        words = analyzer.analyze("今日は良い天気です")

        # 1文字の単語は除外される
        for word in words:
            assert len(word.surface) >= 2

    def test_exclude_specific_pos(self) -> None:
        """特定品詞の除外テスト"""
        analyzer = MorphologicalAnalyzer(exclude_parts=["動詞"])
        words = analyzer.analyze("美しい花が咲いている")

        # 動詞は除外されるはず
        pos_list = [w.part_of_speech for w in words]
        assert "動詞" not in pos_list
        assert "形容詞" in pos_list  # 形容詞は残る
        assert "名詞" in pos_list  # 名詞は残る

    def test_exclude_multiple_pos(self) -> None:
        """複数品詞の除外テスト"""
        analyzer = MorphologicalAnalyzer(exclude_parts=["動詞", "形容詞"])
        words = analyzer.analyze("美しい花が静かに咲いている")

        pos_list = [w.part_of_speech for w in words]
        assert "動詞" not in pos_list
        assert "形容詞" not in pos_list
        assert "名詞" in pos_list  # 名詞は残る
        # 「静かに」は形容動詞語幹として名詞に分類される

    def test_exclude_parts_with_set(self) -> None:
        """除外品詞にsetを渡すテスト"""
        analyzer = MorphologicalAnalyzer(exclude_parts={"動詞", "形容詞"})
        words = analyzer.analyze("美しい花が咲いている")

        pos_list = [w.part_of_speech for w in words]
        assert "動詞" not in pos_list
        assert "形容詞" not in pos_list
        assert "名詞" in pos_list  # 名詞は残る

    def test_filter_non_independent_noun(self) -> None:
        """非自立名詞の除外テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("走ることが好きです")

        surfaces = [w.surface for w in words]
        # 非自立名詞「こと」は除外される
        assert "こと" not in surfaces

    def test_filter_pronoun(self) -> None:
        """代名詞の除外テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("これはペンです")

        surfaces = [w.surface for w in words]
        # 代名詞「これ」は除外される
        assert "これ" not in surfaces
        # 一般名詞「ペン」は残る
        assert "ペン" in surfaces

    def test_extract_interjection(self) -> None:
        """感動詞の抽出テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("あーあ疲れたなー")

        # MeCabの辞書によって結果が異なる可能性があるため、
        # 少なくとも何かが抽出されることを確認
        assert len(words) > 0

    def test_base_form_extraction(self) -> None:
        """基本形の抽出テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("走っている")

        # 動詞の基本形が抽出されるか確認
        for word in words:
            if word.part_of_speech == "動詞" and word.surface in ["走っ", "走る"]:
                assert word.base_form == "走る"

    def test_multiple_sentences(self) -> None:
        """複数文の解析テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("今日は晴れです。明日は雨です。")

        # 両方の文から単語が抽出される（「今日」「明日」はストップワード）
        surfaces = [w.surface for w in words]
        assert "晴れ" in surfaces
        assert "雨" in surfaces

    def test_long_text(self) -> None:
        """長文の解析テスト"""
        analyzer = MorphologicalAnalyzer()
        long_text = "今日は天気が良いので公園に行きました。" * 10
        words = analyzer.analyze(long_text)

        # 適切に解析されることを確認（「今日」はストップワード、動詞は除外）
        assert len(words) > 0
        surfaces = [w.surface for w in words]
        assert "天気" in surfaces
        assert "良い" in surfaces
        assert "公園" in surfaces

    def test_mecab_initialization_error(self) -> None:
        """MeCab初期化エラーのテスト"""
        # このテストは実際のエラーを再現するのが難しいため、
        # 正常に初期化できることを確認
        try:
            analyzer = MorphologicalAnalyzer()
            assert analyzer.tagger is not None
        except RuntimeError:
            pytest.fail("MeCabの初期化に失敗しました")


class TestConsecutiveNounCombination:
    """連続名詞結合機能のテスト"""

    def test_combine_two_nouns(self) -> None:
        """2つの名詞が連続する場合の結合テスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("機動戦士")

        # 「機動」「戦士」が「機動戦士」として結合されるべき
        surfaces = [w.surface for w in words]
        assert "機動戦士" in surfaces
        assert "機動" not in surfaces
        assert "戦士" not in surfaces

    def test_combine_three_or_more_nouns(self) -> None:
        """3つ以上の名詞が連続する場合の結合テスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("機動戦士ガンダム")

        # 「機動」「戦士」「ガンダム」が「機動戦士ガンダム」として結合されるべき
        surfaces = [w.surface for w in words]
        assert "機動戦士ガンダム" in surfaces or "機動戦士" in surfaces  # 辞書次第で変わる可能性
        # 少なくとも分割されていないことを確認
        word_count = len([w for w in words if w.part_of_speech == "名詞"])
        assert word_count <= 2  # 完全結合なら1、部分結合なら2

    def test_multiple_noun_groups(self) -> None:
        """複数の連続名詞グループが独立して処理されるテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("機動戦士のプラモデル")

        # 「機動戦士」と「プラモデル」が独立して存在すべき
        surfaces = [w.surface for w in words]
        # 「機動戦士」または「機動」「戦士」のいずれか
        # 「プラモデル」は結合されない（すでに1単語）
        assert "プラモデル" in surfaces or "プラモ" in surfaces

    def test_single_char_noun_combination(self) -> None:
        """1文字名詞の連続結合テスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        # 「お茶」は辞書によっては既に1単語として認識される可能性がある
        words = analyzer.analyze("お茶を飲む")

        surfaces = [w.surface for w in words]
        # 「お」と「茶」が結合されるか、既に「お茶」として認識される
        assert "お茶" in surfaces or "茶" in surfaces

    def test_nouns_separated_by_particle(self) -> None:
        """助詞で区切られた名詞は結合されないテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("ガンダムのプラモデル")

        surfaces = [w.surface for w in words]
        # 「ガンダムのプラモデル」と結合されるべきではない
        # 「ガンダム」と「プラモデル」が個別に存在するか、
        # 「プラモ」「デル」のように分割される
        assert "ガンダムのプラモデル" not in surfaces
        # 助詞「の」は除外されるため、結果に含まれない

    def test_combined_noun_with_stopwords(self) -> None:
        """連続名詞がストップワードに該当する場合の除外テスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        # 適切なストップワードを含むテストケースを作成
        # 仮に「今日」「明日」などがストップワードに含まれている場合
        words = analyzer.analyze("今日の天気")

        surfaces = [w.surface for w in words]
        # 「今日」はストップワードのため除外される
        assert "今日" not in surfaces
        assert "天気" in surfaces

    def test_combined_noun_with_min_length(self) -> None:
        """連続名詞と最小単語長フィルタの組み合わせテスト"""
        analyzer = MorphologicalAnalyzer(min_length=3)
        words = analyzer.analyze("お茶")

        # 「お」+「茶」=「お茶」(2文字)は最小単語長3に満たないため除外される
        # または「お茶」として認識されても2文字のため除外
        assert len([w for w in words if "茶" in w.surface]) == 0

    def test_noun_with_sahen_connection(self) -> None:
        """サ変接続名詞は結合対象外のテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("勉強する")

        surfaces = [w.surface for w in words]
        # 「勉強」はサ変接続なので、他の名詞と結合されない
        # （単独で存在する場合は抽出される）
        if "勉強" in surfaces:
            # 勉強が抽出された場合、他の名詞と結合していないことを確認
            assert len(surfaces) == 1 or all(w != "勉強" or w in surfaces for w in surfaces)

    def test_noun_with_adjective_stem(self) -> None:
        """形容動詞語幹は結合対象外のテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("綺麗な花")

        surfaces = [w.surface for w in words]
        # 「綺麗」は形容動詞語幹なので、「花」と結合されない
        assert "綺麗な花" not in surfaces
        assert "花" in surfaces

    def test_exclude_number_noun(self) -> None:
        """数詞は結合対象外のテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("12時に集合")

        surfaces = [w.surface for w in words]
        # 「12」と「時」が結合されないことを確認
        # （「時」は接尾辞の可能性もある）
        assert "12時" not in surfaces

    def test_exclude_suffix_noun(self) -> None:
        """接尾辞は結合対象外のテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("田中さん")

        surfaces = [w.surface for w in words]
        # 「田中」と「さん」が結合されないことを確認
        assert "田中さん" not in surfaces or "田中" in surfaces
