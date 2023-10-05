from sqlalchemy.ext.asyncio import AsyncSession
from app.services.database.dao.base import BaseDAO
from app.services.database.models.washings import Washing


class WashingDAO(BaseDAO[Washing]):
    """ORM queries for washings table"""

    def __init__(self, session: AsyncSession):
        super().__init__(Washing, session)
