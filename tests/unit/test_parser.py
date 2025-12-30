"""LINEトーク履歴パーサーのテスト

パーサーの各機能を網羅的にテストする
"""

from datetime import datetime
from io import StringIO

import pytest

from app.services.parser import LineMessageParser, Message


class TestMessage:
    """Messageデータクラスのテスト"""

    def test_create_instance(self) -> None:
        """インスタンス生成のテスト"""
        message = Message(
            datetime=datetime(2024, 8, 1, 22, 12, 0),
            user="hoge山fuga太郎",
            content="おはようございます",
        )
        assert message.datetime == datetime(2024, 8, 1, 22, 12, 0)
        assert message.user == "hoge山fuga太郎"
        assert message.content == "おはようございます"


class TestLineMessageParser:
    """LineMessageParserクラスのテスト"""

    def test_parse_standard_format(self) -> None:
        """標準的なトーク履歴の解析テスト"""
        content = """[LINE] サンプルグループのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	おはようございます
22:14	piyo田	こんにちは
22:16	foo子	よろしくお願いします
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        assert len(messages) == 3
        assert messages[0].user == "hoge山fuga太郎"
        assert messages[0].content == "おはようございます"
        assert messages[0].datetime == datetime(2024, 8, 1, 22, 12, 0)
        assert messages[1].user == "piyo田"
        assert messages[2].user == "foo子"

    def test_parse_with_fixture_file(self) -> None:
        """フィクスチャファイルを使用した解析テスト"""
        with open("tests/fixtures/sample_talk.txt", encoding="utf-8") as f:
            parser = LineMessageParser()
            messages = parser.parse(f)

        # スタンプ、写真、システムメッセージを除外した18件（改行メッセージ2件と連続名詞テスト用3件を含む）
        assert len(messages) == 18
        assert messages[0].content == "おはようございます"
        # 改行メッセージが正しく解析されているか確認
        multiline_messages = [m for m in messages if "\n" in m.content]
        assert len(multiline_messages) == 2

    def test_exclude_system_messages(self) -> None:
        """システムメッセージの除外テスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:13		piyo田が参加しました。
22:14	piyo田	こんにちは
22:15		foo子が退出しました。
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # システムメッセージは除外される
        assert len(messages) == 1
        assert messages[0].content == "こんにちは"

    def test_exclude_stamps_and_photos(self) -> None:
        """スタンプ・写真の除外テスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	こんにちは
22:13	hoge山fuga太郎	[スタンプ]
22:14	piyo田	[写真]
22:15	foo子	よろしく
22:16	hoge山fuga太郎	[動画]
22:17	piyo田	[ファイル]
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # スタンプ、写真、動画、ファイルは除外される
        assert len(messages) == 2
        assert messages[0].content == "こんにちは"
        assert messages[1].content == "よろしく"

    def test_parse_multiple_dates(self) -> None:
        """複数日付にまたがるデータのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	1日目のメッセージ
23:30	piyo田	深夜です

2024/08/02(金)
08:00	foo子	2日目のメッセージ
12:00	hoge山fuga太郎	お昼です
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        assert len(messages) == 4
        assert messages[0].datetime.day == 1
        assert messages[0].datetime.hour == 22
        assert messages[2].datetime.day == 2
        assert messages[2].datetime.hour == 8

    def test_parse_special_characters_in_username(self) -> None:
        """特殊文字を含むユーザー名のテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	山田@太郎	テストメッセージ1
22:13	田中★花子	テストメッセージ2
22:14	佐藤(次郎)	テストメッセージ3
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        assert len(messages) == 3
        assert messages[0].user == "山田@太郎"
        assert messages[1].user == "田中★花子"
        assert messages[2].user == "佐藤(次郎)"

    def test_parse_special_characters_in_message(self) -> None:
        """特殊文字を含むメッセージのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	こんにちは😊
22:13	piyo田	今日は良い天気
22:14	foo子	100%満足！
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        assert len(messages) == 3
        assert "😊" in messages[0].content
        assert messages[1].content == "今日は良い天気"
        assert messages[2].content == "100%満足！"

    def test_parse_empty_file(self) -> None:
        """空ファイルのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

"""
        file = StringIO(content)
        parser = LineMessageParser()

        with pytest.raises(ValueError, match="有効なメッセージが見つかりませんでした"):
            parser.parse(file)

    def test_parse_only_one_message(self) -> None:
        """1メッセージのみのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	唯一のメッセージ
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        assert len(messages) == 1
        assert messages[0].content == "唯一のメッセージ"

    def test_parse_invalid_time_format(self) -> None:
        """不正な時刻フォーマットのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
25:00	hoge山fuga太郎	不正な時刻
22:12	piyo田	正常なメッセージ
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # 不正な時刻の行はスキップされる
        assert len(messages) == 1
        assert messages[0].content == "正常なメッセージ"

    def test_parse_without_tab_separator(self) -> None:
        """タブ区切りでない行のテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12 hoge山fuga太郎 スペース区切り
22:13	piyo田	タブ区切り
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # タブ区切りでない行はスキップされる
        assert len(messages) == 1
        assert messages[0].content == "タブ区切り"

    def test_parse_date_line(self) -> None:
        """日付行解析メソッドのテスト"""
        parser = LineMessageParser()

        # 正常な日付行
        date1 = parser._parse_date_line("2024/08/01(木)")
        assert date1 == datetime(2024, 8, 1)

        date2 = parser._parse_date_line("2024/12/31(火)")
        assert date2 == datetime(2024, 12, 31)

        # 1桁の月・日
        date3 = parser._parse_date_line("2024/1/5(金)")
        assert date3 == datetime(2024, 1, 5)

        # 不正な形式
        assert parser._parse_date_line("2024-08-01(木)") is None
        assert parser._parse_date_line("2024/08/01") is None
        assert parser._parse_date_line("普通の文字列") is None

        # 無効な日付（正規表現にはマッチするが日付として無効）
        assert parser._parse_date_line("2024/13/01(月)") is None  # 月が範囲外
        assert parser._parse_date_line("2024/02/30(金)") is None  # 日が範囲外
        assert parser._parse_date_line("2024/00/15(土)") is None  # 月が0

    def test_parse_message_line(self) -> None:
        """メッセージ行解析メソッドのテスト"""
        parser = LineMessageParser()
        current_date = datetime(2024, 8, 1)
        empty_lines: list[str] = []

        # 正常なメッセージ行
        message, consumed = parser._parse_message_line(
            "22:12\thoge山fuga太郎\tこんにちは", current_date, empty_lines, 0
        )
        assert message is not None
        assert message.datetime == datetime(2024, 8, 1, 22, 12, 0)
        assert message.user == "hoge山fuga太郎"
        assert message.content == "こんにちは"
        assert consumed == 0

        # システムメッセージ（ユーザー名が空）
        message, consumed = parser._parse_message_line(
            "22:13\t\tシステムメッセージ", current_date, empty_lines, 0
        )
        assert message is None

        # スタンプ
        message, consumed = parser._parse_message_line(
            "22:14\tpiyo田\t[スタンプ]", current_date, empty_lines, 0
        )
        assert message is None

        # 不正な形式
        message, consumed = parser._parse_message_line(
            "22:12 スペース区切り", current_date, empty_lines, 0
        )
        assert message is None

    def test_parse_multiline_message(self) -> None:
        """改行を含むメッセージのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	1行目
22:13	piyo田	通常メッセージ
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # LINEのエクスポート形式では改行は別の行として扱われる
        assert len(messages) == 2

    def test_parse_two_line_multiline_message(self) -> None:
        """2行の改行メッセージのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	"1行目
2行目"
22:13	piyo田	通常メッセージ
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        assert len(messages) == 2
        assert messages[0].content == "1行目\n2行目"
        assert messages[0].user == "hoge山fuga太郎"
        assert messages[1].content == "通常メッセージ"

    def test_parse_three_line_multiline_message(self) -> None:
        """3行以上の改行メッセージのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	"1行目
2行目
3行目"
22:13	piyo田	次のメッセージ
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        assert len(messages) == 2
        assert messages[0].content == "1行目\n2行目\n3行目"
        assert "\n" in messages[0].content

    def test_parse_multiline_message_with_empty_lines(self) -> None:
        """連続する改行を含むメッセージのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	"1行目

3行目"
22:13	piyo田	通常メッセージ
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        assert len(messages) == 2
        assert messages[0].content == "1行目\n\n3行目"

    def test_parse_mixed_normal_and_multiline_messages(self) -> None:
        """通常メッセージと改行メッセージが混在するテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	通常メッセージ1
22:13	piyo田	"改行あり
2行目"
22:14	foo子	通常メッセージ2
22:15	hoge山fuga太郎	"また改行
2行目
3行目"
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        assert len(messages) == 4
        assert messages[0].content == "通常メッセージ1"
        assert messages[1].content == "改行あり\n2行目"
        assert messages[2].content == "通常メッセージ2"
        assert messages[3].content == "また改行\n2行目\n3行目"

    def test_parse_multiline_message_without_closing_quote(self) -> None:
        """閉じ"がない改行メッセージのテスト（次のメッセージで終了）"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	"1行目
2行目
22:13	piyo田	次のメッセージ
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # 閉じ"がなくても次のメッセージ行で終了
        assert len(messages) == 2
        assert messages[0].content == "1行目\n2行目"
        assert messages[1].content == "次のメッセージ"

    def test_parse_empty_multiline_message(self) -> None:
        """改行のみのメッセージのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	"空の内容
"
22:13	piyo田	通常メッセージ
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # 改行を含むメッセージは、末尾の空行が削除される
        assert len(messages) == 2
        assert messages[0].content == "空の内容"
        assert messages[1].content == "通常メッセージ"

    def test_parse_message_with_url(self) -> None:
        """URLを含むメッセージの除外テスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	これは便利 https://example.com/page
22:13	piyo田	チェックして http://test.com
22:14	foo子	https://animestore.docomo.ne.jp/animestore/cd?partId=12345
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # URLが除外されていることを確認
        # 3つ目のメッセージはURLのみのため空になり除外される
        assert len(messages) == 2
        assert messages[0].content == "これは便利"
        assert messages[1].content == "チェックして"

    def test_parse_message_with_hashtag_and_params(self) -> None:
        """ハッシュタグを含むメッセージのテスト（実際のdアニメストアメッセージ形式）"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	"機動戦士ガンダム 第34話を視聴しました！#dアニメストア
https://animestore.docomo.ne.jp/animestore/cd?partId=20230034&ref=line"
22:13	piyo田	見てね #アニメ
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # URLが除外され、ハッシュタグは残る
        assert len(messages) == 2
        assert messages[0].content == "機動戦士ガンダム 第34話を視聴しました！#dアニメストア"
        assert messages[1].content == "見てね #アニメ"

    def test_parse_message_with_mixed_content(self) -> None:
        """テキストとURLが混在するメッセージのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
22:12	hoge山fuga太郎	今日の記事 https://example.com/article とても良かった
22:13	piyo田	明日は https://test.com に行く予定
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # URLが除外され、テキスト部分のみ残る
        assert len(messages) == 2
        assert messages[0].content == "今日の記事 とても良かった"
        assert messages[1].content == "明日は に行く予定"

    def test_parse_exclude_call_messages(self) -> None:
        """通話関連のシステムメッセージが除外されることをテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
13:49	太郎	☎ 不在着信
13:55	花子	☎ 通話に応答がありませんでした
13:56	太郎	☎ 通話時間 0:38
14:00	太郎	通常のメッセージ
19:34	花子	☎ 通話をキャンセルしました
20:05	りんな	[ボイスメッセージ]
21:24	次郎	☎ グループ通話が開始されました。
21:30	花子	こんばんは
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # 通話関連メッセージとボイスメッセージが除外され、通常のメッセージのみ残る
        assert len(messages) == 2
        assert messages[0].content == "通常のメッセージ"
        assert messages[0].user == "太郎"
        assert messages[1].content == "こんばんは"
        assert messages[1].user == "花子"

    def test_parse_call_messages_variations(self) -> None:
        """様々な通話時間パターンのテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
13:49	ユーザー1	☎ 通話時間 0:05
13:50	ユーザー2	☎ 通話時間 1:23
13:51	ユーザー3	☎ 通話時間 12:45
13:52	ユーザー4	通話終わりました
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # 様々な通話時間パターンが除外され、通常のメッセージのみ残る
        assert len(messages) == 1
        assert messages[0].content == "通話終わりました"
        assert messages[0].user == "ユーザー4"

    def test_parse_android_call_messages(self) -> None:
        """Android版の通話関連メッセージが除外されることをテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
00:18	太郎	不在着信
00:19	太郎	通話に応答がありませんでした
00:20	太郎	通話時間 2:49
00:21	太郎	通話をキャンセルしました。
00:22	太郎	通常のメッセージ1
00:23	太郎	グループ音声通話が開始されました。
00:24	太郎	グループビデオ通話が開始されました。
00:25	太郎	グループ通話が終了しました。
00:26	太郎	通常のメッセージ2
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # Android版の通話関連メッセージが除外され、通常のメッセージのみ残る
        assert len(messages) == 2
        assert messages[0].content == "通常のメッセージ1"
        assert messages[0].user == "太郎"
        assert messages[1].content == "通常のメッセージ2"
        assert messages[1].user == "太郎"

    def test_parse_mixed_iphone_android_call_messages(self) -> None:
        """iPhone版とAndroid版の通話メッセージが混在する場合のテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
00:18	太郎	☎ 不在着信
00:19	花子	不在着信
00:20	次郎	☎ 通話時間 1:23
00:21	太郎	通話時間 2:49
00:22	花子	通常のメッセージ1
00:23	次郎	☎ グループ通話が開始されました。
00:24	太郎	グループ音声通話が開始されました。
00:25	花子	グループビデオ通話が開始されました。
00:26	次郎	グループ通話が終了しました。
00:27	太郎	通常のメッセージ2
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # iPhone版・Android版どちらの通話メッセージも除外される
        assert len(messages) == 2
        assert messages[0].content == "通常のメッセージ1"
        assert messages[0].user == "花子"
        assert messages[1].content == "通常のメッセージ2"
        assert messages[1].user == "太郎"

    def test_parse_group_call_end_without_user(self) -> None:
        """iPhone版のグループ通話終了メッセージ（発言者なし）のテスト"""
        content = """[LINE] テストのトーク履歴
保存日時：2024/08/01 00:00

2024/08/01(木)
01:39	太郎	☎ グループ通話が開始されました。
01:40		グループ通話が終了しました。
01:41	花子	終わったね
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        # ユーザー名が空のメッセージはシステムメッセージとして除外される
        # グループ通話開始メッセージも除外される
        assert len(messages) == 1
        assert messages[0].content == "終わったね"
        assert messages[0].user == "花子"
