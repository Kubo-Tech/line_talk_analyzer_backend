"""LINEトーク履歴パーサー

LINEのトーク履歴ファイルを読み込み、構造化データに変換する
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import TextIO


@dataclass
class Message:
    """メッセージデータ

    Attributes:
        datetime (datetime): メッセージの日時
        user (str): ユーザー名
        content (str): メッセージ本文
    """

    datetime: datetime
    user: str
    content: str


class LineMessageParser:
    """LINEトーク履歴パーサー

    LINEのトーク履歴ファイルを解析し、メッセージのリストに変換する
    """

    # 日付行の正規表現: YYYY/MM/DD(曜日)
    DATE_PATTERN = re.compile(r"^(\d{4})/(\d{1,2})/(\d{1,2})\([月火水木金土日]\)$")

    # メタメッセージ（除外対象）のパターン
    META_PATTERNS = [
        r"^\[スタンプ\]$",
        r"^\[写真\]$",
        r"^\[動画\]$",
        r"^\[ファイル\]$",
        r"^\[アルバム\]$",
        r"^\[ノート\]$",
        r"^\[通話\]",
        r"が参加しました。$",
        r"が退出しました。$",
        r"がメンバーを追加しました。$",
        r"がメンバーを削除しました。$",
    ]

    def __init__(self) -> None:
        """パーサーの初期化"""
        self._meta_pattern = re.compile("|".join(self.META_PATTERNS))

    def parse(self, file: TextIO) -> list[Message]:
        """トーク履歴ファイルを解析

        Args:
            file (TextIO): トーク履歴ファイルオブジェクト

        Returns:
            list[Message]: 解析されたメッセージのリスト

        Raises:
            ValueError: ファイル形式が不正な場合
        """
        messages: list[Message] = []
        current_date: datetime | None = None

        # ファイル全体を行リストとして読み込む（改行メッセージ対応のため）
        lines = [line.rstrip("\r\n") for line in file]

        i = 0
        line_number = 0

        while i < len(lines):
            line = lines[i]
            line_number += 1
            i += 1

            # 空行をスキップ
            if not line:
                continue

            # ヘッダー行をスキップ（1行目）
            if line_number == 1 and line.startswith("[LINE]"):
                continue

            # 保存日時行をスキップ（2行目）
            if line_number == 2 and line.startswith("保存日時："):
                continue

            # 日付行の解析
            date_match = self._parse_date_line(line)
            if date_match:
                current_date = date_match
                continue

            # メッセージ行の解析
            if current_date is not None:
                # 改行メッセージの可能性をチェック
                message, lines_consumed = self._parse_message_line(line, current_date, lines, i)
                if message:
                    messages.append(message)
                # 複数行読み込んだ場合、インデックスを進める
                i += lines_consumed
                line_number += lines_consumed

        if not messages:
            raise ValueError("有効なメッセージが見つかりませんでした")

        return messages

    def _parse_date_line(self, line: str) -> datetime | None:
        """日付行を解析

        Args:
            line (str): 解析対象の行

        Returns:
            datetime | None: 解析された日付、日付行でない場合はNone
        """
        match = self.DATE_PATTERN.match(line)
        if match:
            try:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                return datetime(year, month, day)
            except ValueError:
                # 無効な日付（例：2024/13/32）の場合はNoneを返す
                return None
        return None

    def _parse_message_line(
        self, line: str, current_date: datetime, lines: list[str], current_index: int
    ) -> tuple[Message | None, int]:
        """メッセージ行を解析

        Args:
            line (str): 解析対象の行
            current_date (datetime): 現在の日付
            lines (list[str]): 全行のリスト
            current_index (int): 現在の行の次のインデックス

        Returns:
            tuple[Message | None, int]: (解析されたメッセージ, 消費した追加行数)
        """
        # タブ文字で分割（最大3分割：時刻、ユーザー名、メッセージ本文）
        parts = line.split("\t", maxsplit=2)

        # 最低でも3つの要素が必要（時刻、ユーザー名、メッセージ）
        if len(parts) < 3:
            return None, 0

        time_str = parts[0].strip()
        user = parts[1].strip()
        content = parts[2].strip()

        # 時刻の解析
        time_match = re.match(r"^(\d{1,2}):(\d{2})$", time_str)
        if not time_match:
            return None, 0

        hour = int(time_match.group(1))
        minute = int(time_match.group(2))

        # システムメッセージ（ユーザー名が空）を除外
        if not user:
            return None, 0

        # メッセージが空の場合は除外
        if not content:
            return None, 0

        # 改行メッセージのチェック
        if self._is_multiline_message_start(content):
            # 複数行メッセージを読み込む
            full_content, lines_consumed = self._read_multiline_message(
                content, lines, current_index
            )
            content = full_content
        else:
            lines_consumed = 0

        # メッセージが空になった場合は除外（改行のみのメッセージなど）
        if not content:
            return None, lines_consumed

        # メタメッセージを除外
        if self._meta_pattern.search(content):
            return None, lines_consumed

        # datetimeオブジェクトを作成
        try:
            message_datetime = current_date.replace(hour=hour, minute=minute)
        except ValueError:
            # 不正な時刻（25:00など）の場合はNoneを返す
            return None, lines_consumed

        return (
            Message(datetime=message_datetime, user=user, content=content),
            lines_consumed,
        )

    def _is_multiline_message_start(self, content: str) -> bool:
        """改行メッセージの開始かどうかを判定

        Args:
            content (str): メッセージ本文

        Returns:
            bool: 改行メッセージの場合True
        """
        # 1文字目が"で、末尾が"ではない場合、改行メッセージの開始
        return content.startswith('"') and not content.endswith('"')

    def _is_message_line(self, line: str) -> bool:
        """メッセージ行の形式かどうかを判定

        Args:
            line (str): 判定対象の行

        Returns:
            bool: メッセージ行の形式の場合True
        """
        # HH:MM\t で始まるかチェック
        parts = line.split("\t", maxsplit=1)
        if len(parts) < 2:
            return False

        time_str = parts[0].strip()
        return bool(re.match(r"^(\d{1,2}):(\d{2})$", time_str))

    def _read_multiline_message(
        self, first_line: str, lines: list[str], start_index: int
    ) -> tuple[str, int]:
        """複数行メッセージを読み込む

        Args:
            first_line (str): 1行目（"で始まる行）
            lines (list[str]): 全行のリスト
            start_index (int): 読み込み開始インデックス

        Returns:
            tuple[str, int]: (結合されたメッセージ本文, 消費した行数)
        """
        # 1行目の先頭の"を除去
        content_lines = [first_line[1:]]
        lines_consumed = 0

        # 次の行から順次読み込む
        i = start_index
        while i < len(lines):
            line = lines[i]
            lines_consumed += 1
            i += 1

            # 空行の場合も改行として保持
            if not line:
                content_lines.append("")
                continue

            # 次のメッセージ行が出現した場合、改行メッセージが不正な形式
            # （閉じ"がない）として、ここまでを返す
            if self._is_message_line(line):
                # 最後の行を消費しなかったことにする
                lines_consumed -= 1
                break

            # 末尾が"の場合、改行メッセージの終了
            if line.endswith('"'):
                content_lines.append(line[:-1])  # 末尾の"を除去
                break
            else:
                content_lines.append(line)

        # 改行で結合
        full_content = "\n".join(content_lines)

        return full_content, lines_consumed
