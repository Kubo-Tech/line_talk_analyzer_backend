"""レスポンスモデル

APIレスポンスのデータモデルを定義する
"""

from typing import Literal

from pydantic import BaseModel, Field

# NOTE: Issue#01でappearancesフィールドを削除しました（レスポンスサイズ削減: 4MB → 0.05MB）
# 削除前の実装や将来の拡張方法については、以下を参照してください：
# - doc/ISSUE/ISSUE01.md: 削除理由と将来の拡張アプローチ


class TopWord(BaseModel):
    """上位単語情報

    Attributes:
        word (str): 単語
        count (int): 出現回数
        part_of_speech (str): 品詞
    """

    word: str = Field(description="単語")
    count: int = Field(ge=1, description="出現回数")
    part_of_speech: str = Field(description="品詞")


class MorphologicalAnalysis(BaseModel):
    """形態素解析結果

    Attributes:
        top_words (list[TopWord]): 上位単語のリスト
    """

    top_words: list[TopWord] = Field(default_factory=list, description="上位単語のリスト")


class TopMessage(BaseModel):
    """上位メッセージ情報

    Attributes:
        message (str): メッセージ本文
        count (int): 出現回数
    """

    message: str = Field(description="メッセージ本文")
    count: int = Field(ge=1, description="出現回数")


class MessageAnalysisResult(BaseModel):
    """メッセージ全文解析結果

    Attributes:
        top_messages (list[TopMessage]): 上位メッセージのリスト
    """

    top_messages: list[TopMessage] = Field(
        default_factory=list, description="上位メッセージのリスト"
    )


class UserWordAnalysis(BaseModel):
    """ユーザー別の単語解析結果

    Attributes:
        user (str): ユーザー名
        top_words (list[TopWord]): 上位単語のリスト
    """

    user: str = Field(description="ユーザー名")
    top_words: list[TopWord] = Field(default_factory=list, description="上位単語のリスト")


class UserMessageAnalysis(BaseModel):
    """ユーザー別のメッセージ解析結果

    Attributes:
        user (str): ユーザー名
        top_messages (list[TopMessage]): 上位メッセージのリスト
    """

    user: str = Field(description="ユーザー名")
    top_messages: list[TopMessage] = Field(
        default_factory=list, description="上位メッセージのリスト"
    )


class UserAnalysis(BaseModel):
    """ユーザー別の解析結果

    Attributes:
        word_analysis (list[UserWordAnalysis]): ユーザー別単語解析結果
        message_analysis (list[UserMessageAnalysis]): ユーザー別メッセージ解析結果
    """

    word_analysis: list[UserWordAnalysis] = Field(
        default_factory=list, description="ユーザー別単語解析結果"
    )
    message_analysis: list[UserMessageAnalysis] = Field(
        default_factory=list, description="ユーザー別メッセージ解析結果"
    )


class AnalysisPeriod(BaseModel):
    """解析期間

    Attributes:
        start_date (str): 開始日（YYYY-MM-DD形式）
        end_date (str): 終了日（YYYY-MM-DD形式）
    """

    start_date: str = Field(description="開始日（YYYY-MM-DD形式）")
    end_date: str = Field(description="終了日（YYYY-MM-DD形式）")


class WordAnalysisResult(BaseModel):
    """単語解析結果データ

    Attributes:
        analysis_period (AnalysisPeriod): 解析期間
        total_messages (int): 総メッセージ数
        total_users (int): 総ユーザー数
        morphological_analysis (MorphologicalAnalysis): 形態素解析結果
        full_message_analysis (MessageAnalysisResult): メッセージ全文解析結果
        user_analysis (UserAnalysis | None): ユーザー別解析結果（オプション）
    """

    analysis_period: AnalysisPeriod = Field(description="解析期間")
    total_messages: int = Field(ge=0, description="総メッセージ数")
    total_users: int = Field(ge=0, description="総ユーザー数")
    morphological_analysis: MorphologicalAnalysis = Field(description="形態素解析結果")
    full_message_analysis: MessageAnalysisResult = Field(description="メッセージ全文解析結果")
    user_analysis: UserAnalysis | None = Field(
        default=None, description="ユーザー別解析結果（オプション）"
    )


class AnalysisResult(BaseModel):
    """解析結果レスポンス

    Attributes:
        status (Literal["success"]): ステータス
        data (WordAnalysisResult): 解析結果データ
    """

    status: Literal["success"] = Field(default="success", description="ステータス")
    data: WordAnalysisResult = Field(description="解析結果データ")


class ErrorDetail(BaseModel):
    """エラー詳細

    Attributes:
        code (str): エラーコード
        message (str): エラーメッセージ
    """

    code: str = Field(description="エラーコード")
    message: str = Field(description="エラーメッセージ")


class ErrorResponse(BaseModel):
    """エラーレスポンス

    Attributes:
        status (Literal["error"]): ステータス
        error (ErrorDetail): エラー詳細
    """

    status: Literal["error"] = Field(default="error", description="ステータス")
    error: ErrorDetail = Field(description="エラー詳細")
