from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database.models.command_usage import CommandUsage
from app.services.database.dao.base import BaseDAO


class CommandUsageDAO(BaseDAO[CommandUsage]):
    """ORM queries for commands_usages table"""

    def __init__(self, session: AsyncSession):
        super().__init__(CommandUsage, session)

    async def add_command_usage(self, command_usage: CommandUsage) -> None:
        await self._session.merge(command_usage)
        await self._session.commit()
