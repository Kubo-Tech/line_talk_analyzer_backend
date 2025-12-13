"""API v1 ルーター

全てのv1エンドポイントを統合する
"""

from fastapi import APIRouter

from app.api.v1.endpoints import analyze, health

router = APIRouter(prefix="/api/v1")

# エンドポイントを登録
router.include_router(health.router, tags=["health"])
router.include_router(analyze.router, tags=["analyze"])
