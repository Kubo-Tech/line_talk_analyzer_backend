"""ヘルスチェックエンドポイント

APIの稼働状態を確認するためのエンドポイント
"""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    """ヘルスチェック

    APIが正常に稼働しているかを確認する

    Returns:
        dict[str, str]: ステータスとバージョン情報
    """
    settings = get_settings()
    return {"status": "ok", "version": settings.APP_VERSION}
