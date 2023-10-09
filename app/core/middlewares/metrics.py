from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any

from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.services.client_database.dao.command_usage import CommandUsageDAO

from app.services.client_database.models.command_usage import CommandUsage


class UsageMetricsMiddleware(BaseMiddleware):
    def __init__(self, session: async_sessionmaker) -> None:
        super().__init__()
        self.session_pool = session

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any],
    ) -> Any:
        if message.text:
            await self.insert_command_usage_metric(message)
        return await handler(message, data)

    async def insert_command_usage_metric(self, message: Message) -> None:
        command_usage = CommandUsage(user_id=message.from_user.id, command=message.text)  # type: ignore

        async with self.session_pool() as session:
            dao = CommandUsageDAO(session)
            await dao.add_command_usage(command_usage)
