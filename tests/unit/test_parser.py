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

        # スタンプ、写真、システムメッセージを除外した11件
        assert len(messages) == 11
        assert messages[0].content == "おはようございます"
        assert messages[-1].content == "よろしくお願いします"

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
22:13	piyo田	今日は\t良い天気
22:14	foo子	100%満足！
"""
        file = StringIO(content)
        parser = LineMessageParser()
        messages = parser.parse(file)

        assert len(messages) == 3
        assert "😊" in messages[0].content
        assert messages[1].content == "今日は\t良い天気"  # タブ文字を含むメッセージ
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

        # 正常なメッセージ行
        message = parser._parse_message_line("22:12\thoge山fuga太郎\tこんにちは", current_date)
        assert message is not None
        assert message.datetime == datetime(2024, 8, 1, 22, 12, 0)
        assert message.user == "hoge山fuga太郎"
        assert message.content == "こんにちは"

        # システムメッセージ（ユーザー名が空）
        message = parser._parse_message_line("22:13\t\tシステムメッセージ", current_date)
        assert message is None

        # スタンプ
        message = parser._parse_message_line("22:14\tpiyo田\t[スタンプ]", current_date)
        assert message is None

        # 不正な形式
        message = parser._parse_message_line("22:12 スペース区切り", current_date)
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
