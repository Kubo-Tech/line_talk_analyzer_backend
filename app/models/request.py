"""リクエストモデル

APIリクエストのデータモデルを定義する
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    """トーク履歴解析リクエスト

    Attributes:
        top_n (int): 取得する上位単語数
        min_word_length (int): 最小単語長
        exclude_parts (Optional[str]): 除外品詞（カンマ区切り）
    """

    top_n: int = Field(default=50, ge=1, le=1000, description="取得する上位単語数")
    min_word_length: int = Field(default=1, ge=1, le=10, description="最小単語長")
    exclude_parts: Optional[str] = Field(default=None, description="除外品詞（カンマ区切り）")

    @field_validator("exclude_parts")
    @classmethod
    def validate_exclude_parts(cls, v: Optional[str]) -> Optional[str]:
        """除外品詞のバリデーション

        カンマ区切りの文字列を検証し、空白を除去する

        Args:
            v (Optional[str]): 除外品詞文字列

        Returns:
            Optional[str]: 正規化された除外品詞文字列
        """
        if v is None:
            return None
        # 空白を除去してカンマ区切りリストとして正規化
        parts_list = [part.strip() for part in v.split(",") if part.strip()]
        if not parts_list:
            return None
        return ",".join(parts_list)

    def get_exclude_parts_list(self) -> list[str]:
        """除外品詞をリストとして取得

        Returns:
            list[str]: 除外品詞のリスト
        """
        if self.exclude_parts is None:
            return []
        return [part.strip() for part in self.exclude_parts.split(",")]
