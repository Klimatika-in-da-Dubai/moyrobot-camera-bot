from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.database.dao.base import BaseDAO
from app.services.database.models.client_bonus import ClientBonus


class ClientBonusDAO(BaseDAO[ClientBonus]):
    def __init__(self, session: AsyncSession):
        super().__init__(ClientBonus, session)

    async def add_bonuses(self, phone: str, bonus_amount: int):
        client_bonus: Optional[ClientBonus] = await self.get_by_phone(phone)
        if client_bonus is None:
            await self.add(
                ClientBonus(
                    phone=phone, actual_amount=bonus_amount, alltime_amount=bonus_amount
                )
            )
            return

        client_bonus.actual_amount += bonus_amount
        if bonus_amount > 0:
            client_bonus.alltime_amount += bonus_amount

        await self.commit()

    async def get_by_phone(self, phone: str) -> Optional[ClientBonus]:
        result = await self._session.execute(
            select(self._model).where(self._model.phone == phone)
        )
        return result.scalar_one_or_none()
