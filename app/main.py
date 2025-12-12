"""FastAPIアプリケーションのエントリポイント

LINE Talk Analyzer Backendのメインアプリケーション
"""

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.cors import setup_cors

# 設定を取得
settings = get_settings()

# FastAPIアプリケーションを初期化
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LINEトーク履歴を解析し、流行語を抽出するバックエンドAPI",
)

# CORSミドルウェアを設定
setup_cors(app, settings)

# ルーターを登録
app.include_router(v1_router)


@app.get("/")
def read_root() -> dict[str, str]:
    """ルートエンドポイント

    APIの基本情報を返す

    Returns:
        dict[str, str]: 基本情報
    """
    return {
        "message": "Welcome to LINE Talk Analyzer API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
