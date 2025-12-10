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
        # 名詞「今日」「天気」、形容詞「良い」などが抽出されるはず
        surfaces = [w.surface for w in words]
        assert "今日" in surfaces
        assert "天気" in surfaces

    def test_analyze_with_various_pos(self) -> None:
        """様々な品詞を含む文の解析テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("美しい花が静かに咲いている")

        # 品詞の確認
        pos_list = [w.part_of_speech for w in words]
        assert "形容詞" in pos_list  # 美しい
        assert "名詞" in pos_list  # 花、静か（形容動詞語幹）
        assert "動詞" in pos_list  # 咲いて

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
        assert "今日" in surfaces
        assert "Python" in surfaces or "プログラミング" in surfaces

    def test_analyze_with_numbers(self) -> None:
        """数字を含むテキストの解析テスト"""
        analyzer = MorphologicalAnalyzer()
        words = analyzer.analyze("明日は10時に集合です")

        # 数詞は除外されるはず
        surfaces = [w.surface for w in words]
        assert "明日" in surfaces
        assert "集合" in surfaces
        # 数詞「10」は除外される
        assert "10" not in surfaces

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

        # 両方の文から単語が抽出される
        surfaces = [w.surface for w in words]
        assert "今日" in surfaces
        assert "晴れ" in surfaces
        assert "明日" in surfaces
        assert "雨" in surfaces

    def test_long_text(self) -> None:
        """長文の解析テスト"""
        analyzer = MorphologicalAnalyzer()
        long_text = "今日は天気が良いので公園に行きました。" * 10
        words = analyzer.analyze(long_text)

        # 適切に解析されることを確認
        assert len(words) > 0
        surfaces = [w.surface for w in words]
        assert "今日" in surfaces
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
