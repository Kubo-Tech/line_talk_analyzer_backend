"""解析エンドポイント

LINEトーク履歴ファイルをアップロードして解析する
"""

import logging
from datetime import datetime
from typing import cast

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.core.config import get_settings
from app.models.response import AnalysisResult, WordAnalysisResult
from app.services.analyzer import TalkAnalyzer
from app.services.demo_service import DemoService

router = APIRouter()
logger = logging.getLogger(__name__)

# デモサービスのシングルトンインスタンス
demo_service = DemoService()


def get_analyzer(request: Request) -> TalkAnalyzer:
    """TalkAnalyzerインスタンスを取得する

    アプリケーション起動時に初期化されたシングルトンインスタンスを返す

    Args:
        request (Request): FastAPIリクエストオブジェクト

    Returns:
        TalkAnalyzer: 解析器のシングルトンインスタンス
    """
    return cast(TalkAnalyzer, request.app.state.analyzer)


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_talk(
    file: UploadFile = File(..., description="LINEトーク履歴ファイル（.txt形式）"),
    top_n: int = Form(default=None, description="取得する上位単語数"),
    min_word_length: int = Form(default=None, description="最小単語長"),
    max_word_length: int | None = Form(default=None, description="最大単語長"),
    min_message_length: int = Form(default=None, description="最小メッセージ長"),
    max_message_length: int | None = Form(default=None, description="最大メッセージ長"),
    min_word_count: int = Form(default=None, description="最小単語出現回数"),
    min_message_count: int = Form(default=None, description="最小メッセージ出現回数"),
    start_date: str | None = Form(
        default=None, description="解析開始日時（YYYY-MM-DD HH:MM:SS形式）"
    ),
    end_date: str | None = Form(
        default=None, description="解析終了日時（YYYY-MM-DD HH:MM:SS形式）"
    ),
    analyzer: TalkAnalyzer = Depends(get_analyzer),
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
        min_word_count (int): 最小単語出現回数（デフォルト: 2）
        min_message_count (int): 最小メッセージ出現回数（デフォルト: 2）
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
    min_word_length = (
        min_word_length if min_word_length is not None else settings.MIN_WORD_LENGTH
    )
    min_message_length = (
        min_message_length
        if min_message_length is not None
        else settings.MIN_MESSAGE_LENGTH
    )
    min_word_count = min_word_count if min_word_count is not None else 2
    min_message_count = min_message_count if min_message_count is not None else 2

    # ファイルの検証
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイルが指定されていません")

    # デモファイル判定
    if demo_service.is_demo_file(file.filename):
        logger.info(f"[DEMO MODE] Demo file detected: {file.filename}")
        # デモレスポンスを生成（遅延付き）
        demo_data_dict = await demo_service.generate_demo_response(
            delay_seconds=settings.DEMO_RESPONSE_DELAY_SECONDS
        )
        # dictからPydanticモデルに変換
        demo_data = WordAnalysisResult(**demo_data_dict)
        return AnalysisResult(status="success", data=demo_data)

    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="ファイル形式が無効です。.txt形式のファイルを指定してください",
        )

    # ファイルをチャンク単位で読み込み、サイズチェック
    chunk_size = 1024 * 1024  # 1MB
    content_chunks: list[bytes] = []
    file_size = 0

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break

        file_size += len(chunk)

        # サイズ制限を超えた時点で処理を中断
        if file_size > settings.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"ファイルサイズが大きすぎます。上限: {settings.MAX_FILE_SIZE_MB}MB",
            )

        content_chunks.append(chunk)

    # 空ファイルチェック
    if file_size == 0:
        raise HTTPException(status_code=400, detail="ファイルが空です")

    # すべてのチャンクを結合
    content = b"".join(content_chunks)

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

    # 解析を実行（注入されたanalyzerを使用）
    try:
        result = analyzer.analyze(
            text_content,
            top_n=top_n,
            min_word_length=min_word_length,
            max_word_length=max_word_length,
            min_message_length=min_message_length,
            max_message_length=max_message_length,
            min_word_count=min_word_count,
            min_message_count=min_message_count,
            start_date=start_datetime,
            end_date=end_datetime,
        )
        return result
    except ValueError as e:
        # ユーザー入力エラー: ログに記録し、一般的なメッセージを返す
        logger.warning(
            "解析処理でバリデーションエラーが発生しました: %s", str(e), exc_info=True
        )
        raise HTTPException(
            status_code=400,
            detail="トーク履歴の形式が正しくありません。LINEからエクスポートされた.txtファイルを使用してください。",
        )
    except Exception as e:
        # 予期しないエラー: 詳細をログに記録し、一般的なメッセージを返す
        logger.error(
            "解析処理で予期しないエラーが発生しました: %s", str(e), exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="サーバー内部エラーが発生しました。しばらく時間をおいて再度お試しください。",
        )


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
