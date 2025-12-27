"""デモサービス

デモ・宣伝用のモックレスポンスを提供する
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DemoService:
    """デモサービスクラス

    デモファイル判定、モックレスポンスの生成を行う
    """

    def __init__(self) -> None:
        """デモサービスを初期化する"""
        self.settings = get_settings()
        self.demo_data_path = (
            Path(__file__).parent.parent / "data" / "demo_response.json"
        )

    def is_demo_file(self, filename: str | None) -> bool:
        """デモファイルかどうかを判定する

        Args:
            filename (str | None): ファイル名

        Returns:
            bool: デモファイルの場合True
        """
        if not filename:
            return False

        # デモモードが無効化されている場合はFalse
        if not self.settings.ENABLE_DEMO_MODE:
            return False

        # ファイル名が一致するか確認（大文字小文字を区別）
        return filename == self.settings.DEMO_TRIGGER_FILENAME

    def load_demo_response(self) -> dict[str, Any]:
        """モックレスポンスをJSONファイルから読み込む

        Returns:
            dict[str, Any]: モックレスポンスデータ

        Raises:
            FileNotFoundError: JSONファイルが見つからない場合
        """
        logger.info(f"Loading demo response from {self.demo_data_path}")

        if not self.demo_data_path.exists():
            raise FileNotFoundError(
                f"Demo response file not found: {self.demo_data_path}"
            )

        with open(self.demo_data_path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        return data

    async def generate_demo_response(self, delay_seconds: float) -> dict[str, Any]:
        """遅延付きでモックレスポンスを生成する

        実際の解析と同様の遅延時間を設けることで、
        リアルなユーザー体験を提供する

        Args:
            delay_seconds (float): 遅延時間（秒）

        Returns:
            dict[str, Any]: モックレスポンスデータ
        """
        logger.info(
            f"[DEMO MODE] Generating demo response with {delay_seconds} seconds delay"
        )

        # 遅延を設ける
        await asyncio.sleep(delay_seconds)

        # モックレスポンスを読み込み
        data = self.load_demo_response()

        logger.info("[DEMO MODE] Demo response returned for promotional purposes")

        return data
