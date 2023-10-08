from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database.models.user import User
from app.services.database.dao.base import BaseDAO
from app.utils.phone import phone_to_text


class UserDAO(BaseDAO[User]):
    """ORM queries for users table"""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def add_user(self, user: User) -> None:
        """
        Add user to database if not added yet. If added, tries to update parameters.
        :param user: Telegram user.
        """

        await self._session.merge(user)
        await self._session.commit()

    async def add_phone(self, user_id: int, phone: str) -> None:
        user: User | None = await self.get_by_id(user_id)
        if user is None:
            raise ValueError("user should not be None")

        user.phone = phone_to_text(phone)
        await self.commit()


def get_user_from_message(message: Message) -> User:
    """
    Creates User model from telegram message
    """
    return User(
        id=message.from_user.id,  # pyright: ignore
        first_name=message.from_user.first_name,  # pyright: ignore
        last_name=message.from_user.last_name,  # pyright: ignore
        username=message.from_user.username,  # pyright: ignore
    )
