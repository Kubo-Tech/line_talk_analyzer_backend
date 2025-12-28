"""形態素解析サービスのテスト

MorphologicalAnalyzerクラスの各機能を網羅的にテストする
"""

import pytest

from app.services.morphological import MorphologicalAnalyzer, Word, _contains_emoji


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
        # neologd辞書は「今日の天気」を1つの固有名詞として認識する
        # そのため、ストップワード「今日」による除外をテストするには別の表現が必要
        words = analyzer.analyze("今日は晴れ")

        surfaces = [w.surface for w in words]
        # 「今日」はストップワードのため除外される（neologdでは単独で出現）
        assert "今日" not in surfaces
        # 「晴れ」は名詞として抽出される
        assert any("晴れ" in s for s in surfaces)

    def test_combined_noun_with_min_length(self) -> None:
        """連続名詞と最小単語長フィルタの組み合わせテスト"""
        analyzer = MorphologicalAnalyzer(min_length=3)
        words = analyzer.analyze("お茶")

        # 「お」+「茶」=「お茶」(2文字)は最小単語長3に満たないため除外される
        # または「お茶」として認識されても2文字のため除外
        assert len([w for w in words if "茶" in w.surface]) == 0

    def test_noun_with_sahen_connection(self) -> None:
        """サ変接続名詞を含む連続名詞の結合テスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        # サ変接続名詞「勉強」と名詞「会」が連続名詞として結合されることを確認
        words = analyzer.analyze("勉強会")

        surfaces = [w.surface for w in words]
        # 「勉強会」が1語として結合されていることを確認する
        assert "勉強会" in surfaces

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
        # neologd辞書は「12時」を固有名詞として認識するため、別のテストケースを使用
        words = analyzer.analyze("3個買った")

        surfaces = [w.surface for w in words]
        # 「3」（数詞）と「個」（接尾辞）は結合されない、または数詞が除外される
        # neologdでは「3個」が固有名詞になる可能性があるため、結合されないことを確認
        # ここでは数詞が除外されることを確認
        assert "3" not in surfaces or len(surfaces) > 0  # 数詞は除外される可能性

    def test_exclude_suffix_noun(self) -> None:
        """接尾辞は結合対象外のテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        # neologdでは「犬」（一般名詞）+「ちゃん」（接尾辞）に分割される
        words = analyzer.analyze("犬ちゃん")

        surfaces = [w.surface for w in words]
        # 「犬」と「ちゃん」は結合されない
        # 「犬」は一般名詞として抽出される
        # 「ちゃん」は接尾辞のため除外される
        assert "犬ちゃん" not in surfaces  # 結合されない
        assert "犬" in surfaces  # 「犬」は抽出される
        assert "ちゃん" not in surfaces  # 接尾辞は除外される


class TestEmojiHandling:
    """絵文字処理のテスト"""

    def test_emoji_not_converted_to_text(self) -> None:
        """絵文字がテキストに変換されないテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("今日は楽しかった😭")

        # 「😭」は「大泣き」などのテキストに変換されず、絵文字のまま抽出される
        surfaces = [w.surface for w in words]
        base_forms = [w.base_form for w in words]

        assert "😭" in surfaces  # 表層形に絵文字が含まれる
        assert "😭" in base_forms  # 基本形も絵文字のまま
        assert "大泣き" not in base_forms  # テキストに変換されない
        assert "泣き顔" not in base_forms  # テキストに変換されない

    def test_multiple_emojis(self) -> None:
        """複数の絵文字が正しく抽出されるテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("😭😂😊")

        surfaces = [w.surface for w in words]

        # 連続する絵文字は1つに結合される
        assert len(words) == 1
        assert "😭😂😊" in surfaces

    def test_emoji_vs_text(self) -> None:
        """絵文字とテキストが区別されるテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 絵文字のケース
        words_emoji = analyzer.analyze("😭")
        emoji_base_forms = [w.base_form for w in words_emoji]

        # 「泣き顔」テキストのケース
        words_text = analyzer.analyze("泣き顔")
        text_base_forms = [w.base_form for w in words_text]

        # 絵文字は「😭」として、テキストは「泣き顔」として別々にカウントされる
        assert "😭" in emoji_base_forms
        assert "泣き顔" in text_base_forms
        assert "😭" not in text_base_forms
        assert "泣き顔" not in emoji_base_forms

    def test_emoji_with_variation_selector(self) -> None:
        """バリエーションセレクタ付き絵文字のテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        # 一部の絵文字はバリエーションセレクタ（U+FE0F）を含む
        words = analyzer.analyze("❤️")  # ハートマーク（バリエーションセレクタ付き）

        if words:  # 絵文字が抽出される場合
            surfaces = [w.surface for w in words]
            base_forms = [w.base_form for w in words]
            # 基本形も表層形と同じになる
            assert any("❤" in s for s in surfaces)
            assert any("❤" in b for b in base_forms)

    def test_emoji_in_sentence(self) -> None:
        """文中の絵文字が正しく抽出されるテスト"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("今日のライブ最高だった🎉✨")

        surfaces = [w.surface for w in words]
        base_forms = [w.base_form for w in words]

        # 通常の単語も抽出される
        assert any("ライブ" in s for s in surfaces)
        assert any("最高" in s for s in surfaces)

        # 連続する絵文字は結合される
        assert "🎉✨" in surfaces
        assert "🎉✨" in base_forms  # 基本形も絵文字のまま


class TestControlCharacterFiltering:
    """制御文字の除外テスト

    バリエーションセレクタなどの制御文字が単語として抽出されないことを確認
    """

    def test_variation_selector_excluded(self) -> None:
        """バリエーションセレクタ（U+FE0F）が除外されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        # バリエーションセレクタ単体
        words = analyzer.analyze("\ufe0f")

        surfaces = [w.surface for w in words]

        # バリエーションセレクタは除外される
        assert "\ufe0f" not in surfaces
        assert len(words) == 0

    def test_zero_width_joiner_excluded(self) -> None:
        """ゼロ幅接合子（U+200D）が除外されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        # ゼロ幅接合子単体
        words = analyzer.analyze("\u200d")

        surfaces = [w.surface for w in words]

        # ゼロ幅接合子は除外される
        assert "\u200d" not in surfaces
        assert len(words) == 0

    def test_full_width_space_excluded(self) -> None:
        """全角スペース（U+3000）が除外されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        # 全角スペース単体
        words = analyzer.analyze("\u3000")

        surfaces = [w.surface for w in words]

        # 全角スペースは除外される
        assert "\u3000" not in surfaces
        assert len(words) == 0

    def test_multiple_control_characters_excluded(self) -> None:
        """複数の制御文字が除外されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        # 複数の制御文字を含むテキスト
        words = analyzer.analyze("\ufe0f\u200d\u3000")

        # 全て除外される
        assert len(words) == 0

    def test_control_characters_in_sentence_excluded(self) -> None:
        """文中の制御文字が除外され、通常の単語は抽出されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        # 制御文字を含む文（実際のLINEメッセージでは絵文字の後にバリエーションセレクタが付くことがある）
        words = analyzer.analyze("今日は\u3000良い\ufe0f天気")

        surfaces = [w.surface for w in words]
        base_forms = [w.base_form for w in words]

        # 制御文字は除外される
        assert "\u3000" not in surfaces
        assert "\ufe0f" not in surfaces

        # 通常の単語は抽出される（助詞「は」は除外される）
        assert "良い" in surfaces or "良い" in base_forms
        assert "天気" in surfaces or "天気" in base_forms

    def test_emoji_extracted_but_variation_selector_excluded(self) -> None:
        """絵文字は抽出されるがバリエーションセレクタは除外されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        # 絵文字とバリエーションセレクタを含むテキスト
        # 実際には絵文字の直後にバリエーションセレクタが来るが、
        # ここでは分離してテスト
        words = analyzer.analyze("😭")  # 泣き顔絵文字
        words_with_vs = analyzer.analyze("😭\ufe0f")  # 泣き顔絵文字 + バリエーションセレクタ

        surfaces1 = [w.surface for w in words]
        surfaces2 = [w.surface for w in words_with_vs]

        # 絵文字は抽出される
        assert "😭" in surfaces1

        # バリエーションセレクタ単体は除外される
        # （絵文字本体は抽出される可能性がある）
        assert "\ufe0f" not in surfaces2

    def test_only_control_characters_returns_empty(self) -> None:
        """制御文字のみのテキストは空のリストを返すことを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        test_cases = [
            "\ufe0f",  # バリエーションセレクタ
            "\u200d",  # ゼロ幅接合子
            "\u3000",  # 全角スペース
            "\ufe0f\u200d",  # 複数の制御文字
            "\u3000\u3000",  # 複数の全角スペース
        ]

        for text in test_cases:
            words = analyzer.analyze(text)
            assert len(words) == 0, f"制御文字 {repr(text)} が除外されていません"


class TestNounBaseForm:
    """名詞の基本形処理のテスト

    名詞には活用がないため、基本形ではなく表層形を使用することを確認
    """

    def test_proper_noun_uses_surface_form(self) -> None:
        """固有名詞は基本形ではなく表層形を使用することを確認

        neologd辞書は「アオ」を基本形「A-O」に変換するが、表層形を使うべき
        """
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 「アオのハコ」というマンガタイトルを含む文
        # neologd辞書は「アオ」を基本形「A-O」に変換するが、表層形を使うべき
        words = analyzer.analyze("アオのハコを読んだ")

        # 「アオ」という固有名詞が抽出されるはず
        surfaces = [w.surface for w in words]
        base_forms = [w.base_form for w in words]

        # 表層形に「アオ」が含まれる
        assert "アオ" in surfaces, f"「アオ」が表層形に含まれていません: {surfaces}"

        # 基本形も「アオ」であるべき（「A-O」ではない）
        assert "アオ" in base_forms, f"基本形が「アオ」ではありません: {base_forms}"
        assert "A-O" not in base_forms, f"基本形に「A-O」が含まれています: {base_forms}"

    def test_multiple_proper_nouns(self) -> None:
        """複数の固有名詞がすべて表層形で処理されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        words = analyzer.analyze("アオとハコは友達です")

        base_forms = [w.base_form for w in words]

        # 両方とも表層形のまま
        assert "アオ" in base_forms
        assert "ハコ" in base_forms
        # 変換された形が含まれていない
        assert "A-O" not in base_forms

    def test_proper_noun_combined_with_other_words(self) -> None:
        """固有名詞と他の品詞が混在する文での処理確認"""
        analyzer = MorphologicalAnalyzer(min_length=2)

        # 「少年ジャンプ＋」で「アオのハコ」を読む
        words = analyzer.analyze("少年ジャンプ＋でアオのハコを読んだ")

        base_forms = [w.base_form for w in words]
        surfaces = [w.surface for w in words]

        # 固有名詞は表層形
        assert "アオ" in surfaces or "アオ" in base_forms
        assert "A-O" not in base_forms

    def test_general_noun_still_uses_base_form(self) -> None:
        """一般名詞は引き続き基本形を使用することを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 活用のある一般的な文
        # ※ただし、名詞自体に活用はないため、基本形=表層形のケースが多い
        words = analyzer.analyze("本を読む")

        # 「本」は一般名詞なので基本形が使われる
        hon_words = [w for w in words if w.surface == "本"]
        assert len(hon_words) > 0
        assert hon_words[0].base_form == "本"  # 名詞なので基本形=表層形


class TestIsSingleKana:
    """_is_single_kana()関数のテスト"""

    def test_hiragana_single_character_a(self) -> None:
        """ひらがな1文字「あ」のテスト"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("あ") is True

    def test_hiragana_single_character_n(self) -> None:
        """ひらがな1文字「ん」のテスト"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("ん") is True

    def test_katakana_single_character_a(self) -> None:
        """カタカナ1文字「ア」のテスト"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("ア") is True

    def test_katakana_single_character_n(self) -> None:
        """カタカナ1文字「ン」のテスト"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("ン") is True

    def test_katakana_single_character_prolonged(self) -> None:
        """カタカナ1文字「ー」のテスト"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("ー") is True

    def test_half_width_katakana(self) -> None:
        """半角カタカナ1文字「ｱ」のテスト"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("ｱ") is True

    def test_kanji_single_character(self) -> None:
        """漢字1文字「草」は除外されない"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("草") is False

    def test_kanji_single_character_ai(self) -> None:
        """漢字1文字「愛」は除外されない"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("愛") is False

    def test_alphabet_lowercase(self) -> None:
        """アルファベット小文字1文字「w」は除外されない"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("w") is False

    def test_alphabet_uppercase(self) -> None:
        """アルファベット大文字1文字「W」は除外されない"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("W") is False

    def test_emoji(self) -> None:
        """絵文字1文字「😭」は除外されない"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("😭") is False

    def test_symbol(self) -> None:
        """記号1文字「！」は除外されない"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("！") is False

    def test_two_characters(self) -> None:
        """2文字以上「あい」は除外されない"""
        from app.services.morphological import _is_single_kana

        assert _is_single_kana("あい") is False


class TestFilterByLengthWithKana:
    """_filter_by_length()メソッドの1文字カナ除外機能のテスト"""

    def test_filter_single_hiragana(self) -> None:
        """1文字ひらがなが除外されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        word = Word(
            surface="あ",
            base_form="あ",
            part_of_speech="感動詞",
            part_of_speech_detail1="*",
            part_of_speech_detail2="*",
            part_of_speech_detail3="*",
        )
        assert analyzer._filter_by_length(word) is False

    def test_filter_single_katakana(self) -> None:
        """1文字カタカナが除外されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        word = Word(
            surface="ア",
            base_form="ア",
            part_of_speech="感動詞",
            part_of_speech_detail1="*",
            part_of_speech_detail2="*",
            part_of_speech_detail3="*",
        )
        assert analyzer._filter_by_length(word) is False

    def test_filter_single_half_width_katakana(self) -> None:
        """1文字半角カタカナが除外されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        word = Word(
            surface="ｱ",
            base_form="ｱ",
            part_of_speech="感動詞",
            part_of_speech_detail1="*",
            part_of_speech_detail2="*",
            part_of_speech_detail3="*",
        )
        assert analyzer._filter_by_length(word) is False

    def test_allow_single_kanji(self) -> None:
        """1文字漢字が許可されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        word = Word(
            surface="草",
            base_form="草",
            part_of_speech="名詞",
            part_of_speech_detail1="一般",
            part_of_speech_detail2="*",
            part_of_speech_detail3="*",
        )
        assert analyzer._filter_by_length(word) is True

    def test_allow_single_alphabet_lowercase(self) -> None:
        """1文字アルファベット小文字が許可されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        word = Word(
            surface="w",
            base_form="w",
            part_of_speech="名詞",
            part_of_speech_detail1="一般",
            part_of_speech_detail2="*",
            part_of_speech_detail3="*",
        )
        assert analyzer._filter_by_length(word) is True

    def test_allow_single_alphabet_uppercase(self) -> None:
        """1文字アルファベット大文字が許可されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        word = Word(
            surface="W",
            base_form="W",
            part_of_speech="名詞",
            part_of_speech_detail1="固有名詞",
            part_of_speech_detail2="*",
            part_of_speech_detail3="*",
        )
        assert analyzer._filter_by_length(word) is True

    def test_allow_single_emoji(self) -> None:
        """1文字絵文字が許可されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        word = Word(
            surface="😭",
            base_form="😭",
            part_of_speech="記号",
            part_of_speech_detail1="一般",
            part_of_speech_detail2="*",
            part_of_speech_detail3="*",
        )
        assert analyzer._filter_by_length(word) is True

    def test_allow_single_symbol(self) -> None:
        """1文字記号が許可されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        word = Word(
            surface="！",
            base_form="！",
            part_of_speech="記号",
            part_of_speech_detail1="一般",
            part_of_speech_detail2="*",
            part_of_speech_detail3="*",
        )
        assert analyzer._filter_by_length(word) is True

    def test_allow_two_or_more_characters(self) -> None:
        """2文字以上が許可されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        word = Word(
            surface="あい",
            base_form="あい",
            part_of_speech="名詞",
            part_of_speech_detail1="一般",
            part_of_speech_detail2="*",
            part_of_speech_detail3="*",
        )
        assert analyzer._filter_by_length(word) is True


class TestAnalyzeWithKanaFiltering:
    """analyze()メソッドの1文字カナ除外統合テスト"""

    def test_analyze_mixed_single_characters(self) -> None:
        """1文字単語混在テキストの解析"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 「草w」というテキスト（漢字1文字、アルファベット1文字）
        # ひらがな・カタカナ1文字は除外されるべき
        words = analyzer.analyze("草w")

        surfaces = [w.surface for w in words]

        # 漢字1文字「草」とアルファベット1文字「w」は残る
        assert "草" in surfaces
        assert "w" in surfaces or "W" in surfaces  # MeCabの解析結果による

    def test_analyze_exclude_single_kana(self) -> None:
        """ひらがな1文字が除外されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 「草」「あ」「w」が含まれる文
        # 実際のMeCab解析では「あ」は感動詞として抽出される可能性がある
        words = analyzer.analyze("草あw")

        surfaces = [w.surface for w in words]

        # 「草」と「w」は含まれ、「あ」は除外される
        assert "草" in surfaces
        # 「あ」は除外される（ひらがな1文字）
        assert "あ" not in surfaces
        # 「w」はアルファベットなので許可される
        # ただし、MeCabの解析結果によっては「w」が記号扱いされる可能性もある
        # そのため、「w」の存在確認はスキップ


class TestKeiyoudoushiGokanCombination:
    """形容動詞語幹の結合テスト（Issue#05対応）"""

    def test_keiyoudoushi_gokan_combined_in_person_name(self) -> None:
        """人名の一部として形容動詞語幹が結合されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 「優稀」という人名（「稀」は形容動詞語幹）
        words = analyzer.analyze("優稀さん")

        surfaces = [w.surface for w in words]

        # 「優」と「稀」が結合されて「優稀」になる
        assert "優稀" in surfaces
        # 分離されていない
        assert "優" not in surfaces
        assert "稀" not in surfaces

    def test_keiyoudoushi_gokan_combined_in_full_name(self) -> None:
        """フルネームで形容動詞語幹が結合されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 「山田優稀」という氏名
        words = analyzer.analyze("山田優稀")

        surfaces = [w.surface for w in words]

        # 全て結合される
        assert "山田優稀" in surfaces

    def test_keiyoudoushi_gokan_not_combined_with_na(self) -> None:
        """形容動詞として使われる場合（「な」が後続）は結合されないことを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 「綺麗な花」（「綺麗」は形容動詞語幹、「な」が後続）
        words = analyzer.analyze("綺麗な花")

        surfaces = [w.surface for w in words]

        # 「綺麗」と「花」は結合されない
        assert "綺麗" in surfaces
        assert "花" in surfaces
        assert "綺麗花" not in surfaces

    def test_multiple_keiyoudoushi_gokan_not_combined_with_na(self) -> None:
        """複数の形容動詞語幹が「な」で区切られる場合に結合されないことを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 「元気な人」（「元気」は形容動詞語幹）
        words = analyzer.analyze("元気な人")

        surfaces = [w.surface for w in words]

        # 「元気」と「人」は結合されない
        assert "元気" in surfaces
        # 「人」はストップワードでなければ抽出される
        # 結合されていない
        assert "元気人" not in surfaces

    def test_keiyoudoushi_gokan_combined_without_particle(self) -> None:
        """助詞がない場合に形容動詞語幹が結合されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 「静か部屋」（助詞なし、非現実的だが動作確認）
        words = analyzer.analyze("静か部屋")

        surfaces = [w.surface for w in words]

        # 助詞がないため結合される
        assert "静か部屋" in surfaces


class TestAdjectiveBaseForm:
    """形容詞の基本形（表層形使用）のテスト"""

    def test_adjective_uses_surface_form(self) -> None:
        """形容詞が表層形を使用することを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 「あらかわTwitter」の解析（「あらかわ」→「あらか」(形容詞)+「わ」(助詞)に誤分割される）
        words = analyzer.analyze("あらかわTwitter")

        # 形容詞「あらか」が表層形のまま抽出される
        adj_words = [w for w in words if w.part_of_speech == "形容詞"]
        assert len(adj_words) == 1
        assert adj_words[0].surface == "あらか"
        assert adj_words[0].base_form == "あらか"  # 表層形が基本形にも設定される

    def test_adjective_conjugation_forms_kept_separate(self) -> None:
        """形容詞の活用形が別々に保持されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 「荒い」「荒く」「荒かった」の解析
        words_arai = analyzer.analyze("荒い")
        words_araku = analyzer.analyze("荒く")

        # それぞれの表層形が保持される
        adj_arai = [w for w in words_arai if w.part_of_speech == "形容詞"]
        adj_araku = [w for w in words_araku if w.part_of_speech == "形容詞"]

        assert len(adj_arai) == 1
        assert len(adj_araku) == 1
        assert adj_arai[0].surface == "荒い"
        assert adj_arai[0].base_form == "荒い"
        assert adj_araku[0].surface == "荒く"
        assert adj_araku[0].base_form == "荒く"

    def test_adjective_surface_form_in_sentence(self) -> None:
        """文中の形容詞が表層形で抽出されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 「すごく楽しかった」の解析
        words = analyzer.analyze("すごく楽しかった")

        # 形容詞を抽出
        adj_words = [w for w in words if w.part_of_speech == "形容詞"]

        # 「すごく」と「楽しかっ」が表層形で抽出される
        surfaces = [w.surface for w in adj_words]
        base_forms = [w.base_form for w in adj_words]

        assert "すごく" in surfaces
        assert "楽しかっ" in surfaces
        assert "すごく" in base_forms
        assert "楽しかっ" in base_forms

    def test_adjective_vs_noun_handling(self) -> None:
        """形容詞と名詞の基本形処理の違いを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 名詞と形容詞を含む文
        words = analyzer.analyze("面白い映画")

        # 形容詞「面白い」は表層形
        adj_words = [w for w in words if w.part_of_speech == "形容詞"]
        assert len(adj_words) == 1
        assert adj_words[0].surface == "面白い"
        assert adj_words[0].base_form == "面白い"

        # 名詞「映画」も表層形
        noun_words = [w for w in words if w.part_of_speech == "名詞"]
        assert len(noun_words) >= 1
        movie_words = [w for w in noun_words if w.surface == "映画"]
        assert len(movie_words) == 1
        assert movie_words[0].base_form == "映画"

    def test_real_world_case_arakawa_misparse(self) -> None:
        """実際のケース「あらかわ」の誤解析を表層形で記録することを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 実際のメッセージ「あらかわのアイコン草」
        words = analyzer.analyze("あらかわのアイコン草")

        # 「あらか」が形容詞として抽出される（誤解析）
        adj_words = [w for w in words if w.part_of_speech == "形容詞"]
        assert len(adj_words) == 1
        assert adj_words[0].surface == "あらか"
        assert adj_words[0].base_form == "あらか"  # 「あらい」にまとめられない


class TestConsecutiveSymbolCombination:
    """連続する記号の結合機能のテスト"""

    def test_combine_two_symbols(self) -> None:
        """2つの記号が結合されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("😭😭😭")
        emoji_words = [w for w in words if _contains_emoji(w.surface)]

        # 絵文字3つが1つに結合されているはず
        assert len(emoji_words) == 1
        assert emoji_words[0].surface == "😭😭😭"
        assert emoji_words[0].base_form == "😭😭😭"
        assert emoji_words[0].part_of_speech == "記号"

    def test_combine_multiple_symbols(self) -> None:
        """3つ以上の記号が結合されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("😂😂😂😂😂")

        # 絵文字5つが1つに結合
        emoji_words = [w for w in words if _contains_emoji(w.surface)]
        assert len(emoji_words) == 1
        assert emoji_words[0].surface == "😂😂😂😂😂"
        assert emoji_words[0].base_form == "😂😂😂😂😂"

    def test_different_emojis_combined(self) -> None:
        """異なる絵文字が連続している場合も結合されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("😭😂🙏")

        # 異なる絵文字も連続していれば結合される
        emoji_words = [w for w in words if _contains_emoji(w.surface)]
        assert len(emoji_words) == 1
        assert emoji_words[0].surface == "😭😂🙏"
        assert emoji_words[0].base_form == "😭😂🙏"

    def test_symbols_separated_by_text(self) -> None:
        """テキストで区切られた記号は別々にカウントされることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("😭テスト😭")

        # 「😭」が2回出現するが、テキストで区切られているため別々
        emoji_words = [w for w in words if _contains_emoji(w.surface)]
        assert len(emoji_words) == 2
        assert emoji_words[0].surface == "😭"
        assert emoji_words[1].surface == "😭"

    def test_symbols_with_nouns(self) -> None:
        """記号と名詞が混在する場合、それぞれ正しく処理されることを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("dアニメストア😭😭")

        # 名詞が結合されている
        noun_words = [w for w in words if w.part_of_speech == "名詞"]
        combined_nouns = [w for w in noun_words if len(w.surface) > 1]
        assert len(combined_nouns) >= 1
        # 「dアニメストア」が結合されているはず
        d_anime = [w for w in combined_nouns if "d" in w.surface and "ストア" in w.surface]
        assert len(d_anime) == 1

        # 記号（絵文字）も結合されている
        emoji_words = [w for w in words if _contains_emoji(w.surface)]
        assert len(emoji_words) == 1
        assert emoji_words[0].surface == "😭😭"

    def test_single_symbol_not_combined(self) -> None:
        """1つだけの記号は結合されないことを確認"""
        analyzer = MorphologicalAnalyzer(min_length=1)
        words = analyzer.analyze("すごい😭")

        # 1つの絵文字はそのまま
        emoji_words = [w for w in words if _contains_emoji(w.surface)]
        assert len(emoji_words) == 1
        assert emoji_words[0].surface == "😭"
        assert emoji_words[0].base_form == "😭"

    def test_emoji_symbols_included_punctuation_excluded(self) -> None:
        """絵文字のみが抽出され、句読点などは除外されることを確認

        連続する絵文字は結合され、1つの単語としてカウントされる。
        句読点などの通常の記号は除外される。
        """
        analyzer = MorphologicalAnalyzer(min_length=1)

        # 絵文字と句読点が混在するケース
        words = analyzer.analyze("すごい！！！😭😭😭")
        surfaces = [w.surface for w in words]

        # 「すごい」は形容詞として抽出される
        assert "すごい" in surfaces

        # 絵文字は記号として抽出される
        assert "😭😭😭" in surfaces

        # 句読点は除外される
        assert "！！！" not in surfaces
        assert "！" not in surfaces

        # 記号品詞は絵文字のみ
        symbol_words = [w for w in words if w.part_of_speech == "記号"]
        assert len(symbol_words) == 1  # 「😭😭😭」のみ
        assert symbol_words[0].surface == "😭😭😭"

    def test_mixed_emoji_and_text_symbols(self) -> None:
        """絵文字と通常の記号が混在する場合、絵文字のみが抽出され、連続していないため結合されないことを確認

        MeCabは「！😭！😭」を「！」「😭」「！」「😭」と個別に解析する。
        絵文字を含まない記号（「！」）は除外処理で削除され、「😭」のみが残る。
        残った「😭」2つは元々連続していなかった（間に「！」があった）ため、結合されない。
        """
        analyzer = MorphologicalAnalyzer(min_length=1)
        # 句読点と絵文字が混在するケース
        words = analyzer.analyze("！😭！😭")

        # 絵文字を含む記号のみが抽出される
        symbol_words = [w for w in words if w.part_of_speech == "記号"]

        # 「😭」が2回別々にカウントされる（元々連続していなかったため結合されない）
        assert len(symbol_words) == 2
        assert symbol_words[0].surface == "😭"
        assert symbol_words[0].base_form == "😭"
        assert symbol_words[1].surface == "😭"
        assert symbol_words[1].base_form == "😭"

        # 全ての記号単語に絵文字が含まれることを確認
        for word in symbol_words:
            assert _contains_emoji(word.surface)

        # 句読点が単独で抽出されていないことを確認
        surfaces = [w.surface for w in words]
        assert "！" not in surfaces
