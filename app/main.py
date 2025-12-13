"""FastAPIアプリケーションのエントリポイント

LINE Talk Analyzer Backendのメインアプリケーション
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.cors import setup_cors
from app.services.analyzer import TalkAnalyzer

# 設定を取得
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """アプリケーションのライフサイクル管理

    起動時に重い初期化処理を実行し、終了時にクリーンアップする

    Args:
        app (FastAPI): FastAPIアプリケーション

    Yields:
        None
    """
    # 起動時: TalkAnalyzerをシングルトンとして初期化（MeCabの初期化を1度だけ実行）
    app.state.analyzer = TalkAnalyzer()
    yield
    # 終了時: 必要に応じてクリーンアップ処理を追加


# FastAPIアプリケーションを初期化
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LINEトーク履歴を解析し、流行語を抽出するバックエンドAPI",
    lifespan=lifespan,
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
