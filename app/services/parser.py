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
        line_number = 0

        for line in file:
            line_number += 1
            line = line.rstrip("\n")

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
                message = self._parse_message_line(line, current_date)
                if message:
                    messages.append(message)

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

    def _parse_message_line(self, line: str, current_date: datetime) -> Message | None:
        """メッセージ行を解析

        Args:
            line (str): 解析対象の行
            current_date (datetime): 現在の日付

        Returns:
            Message | None: 解析されたメッセージ、無効な行の場合はNone
        """
        # タブ文字で分割（最大3分割：時刻、ユーザー名、メッセージ本文）
        parts = line.split("\t", maxsplit=2)

        # 最低でも3つの要素が必要（時刻、ユーザー名、メッセージ）
        if len(parts) < 3:
            return None

        time_str = parts[0].strip()
        user = parts[1].strip()
        content = parts[2].strip()

        # 時刻の解析
        time_match = re.match(r"^(\d{1,2}):(\d{2})$", time_str)
        if not time_match:
            return None

        hour = int(time_match.group(1))
        minute = int(time_match.group(2))

        # システムメッセージ（ユーザー名が空）を除外
        if not user:
            return None

        # メッセージが空の場合は除外
        if not content:
            return None

        # メタメッセージを除外
        if self._meta_pattern.search(content):
            return None

        # datetimeオブジェクトを作成
        try:
            message_datetime = current_date.replace(hour=hour, minute=minute)
        except ValueError:
            # 不正な時刻（25:00など）の場合はNoneを返す
            return None

        return Message(datetime=message_datetime, user=user, content=content)
