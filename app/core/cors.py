"""CORS設定

Cross-Origin Resource Sharing (CORS) の設定を提供する
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings


def setup_cors(app: FastAPI, settings: Settings) -> None:
    """CORSミドルウェアを設定する

    フロントエンドからのクロスオリジンリクエストを許可する

    Args:
        app (FastAPI): FastAPIアプリケーション
        settings (Settings): アプリケーション設定
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
