"""解析エンドポイント

LINEトーク履歴ファイルをアップロードして解析する
"""

from datetime import datetime

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.models.response import AnalysisResult
from app.services.analyzer import TalkAnalyzer

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_talk(
    file: UploadFile = File(..., description="LINEトーク履歴ファイル（.txt形式）"),
    top_n: int = Form(None, description="取得する上位単語数"),
    min_word_length: int = Form(None, description="最小単語長"),
    max_word_length: int | None = Form(None, description="最大単語長"),
    min_message_length: int = Form(None, description="最小メッセージ長"),
    max_message_length: int | None = Form(None, description="最大メッセージ長"),
    start_date: str | None = Form(None, description="解析開始日時（YYYY-MM-DD HH:MM:SS形式）"),
    end_date: str | None = Form(None, description="解析終了日時（YYYY-MM-DD HH:MM:SS形式）"),
) -> AnalysisResult:
    """トーク履歴を解析する

    LINEトーク履歴ファイルをアップロードして、単語とメッセージの集計を行う

    Args:
        file (UploadFile): LINEトーク履歴ファイル
        top_n (int): 取得する上位単語数（デフォルト: 設定値）
        min_word_length (int): 最小単語長（デフォルト: 設定値）
        max_word_length (int | None): 最大単語長（デフォルト: None）
        min_message_length (int): 最小メッセージ長（デフォルト: 設定値）
        max_message_length (int | None): 最大メッセージ長（デフォルト: None）
        start_date (str | None): 解析開始日時
        end_date (str | None): 解析終了日時

    Returns:
        AnalysisResult: 解析結果

    Raises:
        HTTPException: ファイル関連のエラー、解析エラー
    """
    settings = get_settings()

    # デフォルト値を設定（Noneの場合のみ）
    top_n = top_n if top_n is not None else settings.DEFAULT_TOP_N
    min_word_length = min_word_length if min_word_length is not None else settings.MIN_WORD_LENGTH
    min_message_length = (
        min_message_length if min_message_length is not None else settings.MIN_MESSAGE_LENGTH
    )

    # ファイルの検証
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイルが指定されていません")

    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="ファイル形式が無効です。.txt形式のファイルを指定してください",
        )

    # ファイルサイズの検証
    content = await file.read()
    file_size = len(content)

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"ファイルサイズが大きすぎます。上限: {settings.MAX_FILE_SIZE_MB}MB",
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="ファイルが空です")

    # 日時文字列をdatetimeオブジェクトに変換
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    try:
        if start_date:
            start_datetime = _parse_datetime(start_date)
        if end_date:
            end_datetime = _parse_datetime(end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日時の形式が無効です: {str(e)}")

    # ファイル内容をデコード
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="ファイルのエンコーディングが無効です。UTF-8形式のファイルを指定してください",
        )

    # 解析を実行
    try:
        analyzer = TalkAnalyzer()
        result = analyzer.analyze(
            text_content,
            top_n=top_n,
            min_word_length=min_word_length,
            max_word_length=max_word_length,
            min_message_length=min_message_length,
            max_message_length=max_message_length,
            start_date=start_datetime,
            end_date=end_datetime,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"解析エラー: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"サーバー内部エラー: {str(e)}")


def _parse_datetime(date_str: str) -> datetime:
    """日時文字列をdatetimeオブジェクトに変換する

    Args:
        date_str (str): 日時文字列（YYYY-MM-DD HH:MM:SS形式またはYYYY-MM-DD形式）

    Returns:
        datetime: datetimeオブジェクト

    Raises:
        ValueError: 日時の形式が無効な場合
    """
    # YYYY-MM-DD HH:MM:SS形式を試す
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    # YYYY-MM-DD形式を試す
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"日時の形式が無効です: {date_str}。YYYY-MM-DD HH:MM:SSまたはYYYY-MM-DD形式で指定してください"
        )
