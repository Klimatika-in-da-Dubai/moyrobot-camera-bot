from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.database.dao.base import BaseDAO
from app.services.database.models.client_bonus import ClientBonus


class ClientBonusDAO(BaseDAO[ClientBonus]):
    def __init__(self, session: AsyncSession):
        super().__init__(ClientBonus, session)

    async def add_bonuses(self, phone: str, bonus_amount: int):
        client_bonus: Optional[ClientBonus] = await self.get_by_id(phone)
        if client_bonus is None:
            return

        client_bonus.actual_amount += bonus_amount
        if bonus_amount > 0:
            client_bonus.alltime_amount += bonus_amount

        await self.commit()
