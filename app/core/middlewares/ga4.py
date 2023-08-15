from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.client.session.aiohttp import ClientSession
from aiogram.types import Message, TelegramObject

from app.settings.ga4 import GA4


class GA4Middleware(BaseMiddleware):
    """Middleware for getting statistic from user activity in messages"""

    def __init__(self, ga4_config: GA4) -> None:
        super().__init__()
        self.ga4 = ga4_config

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any],
    ) -> Any:
        if message.text and message.text.startswith("/"):
            await self.send_analytics(
                message.from_user.id, message.from_user.language_code, message.text[1:]  # type: ignore
            )
        return await handler(message, data)

    async def send_analytics(self, user_id, user_lang_code, action_name):
        """
        Send record to Google Analytics
        """
        params = {
            "client_id": str(user_id),
            "user_id": str(user_id),
            "events": [
                {
                    "name": action_name,
                    "params": {
                        "language": user_lang_code,
                        "engagement_time_msec": "1",
                    },
                }
            ],
        }

        async with ClientSession() as session:
            await session.post(
                f"https://www.google-analytics.com/"
                f"mp/collect?measurement_id={self.ga4.measurement_id}&api_secret={self.ga4.api_secret}",
                json=params,
            )
