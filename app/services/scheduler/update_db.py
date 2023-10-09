from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.services.client_database.dao.client_bonus import ClientBonusDAO

from app.services.client_database.dao.washing import WashingDAO
from app.services.client_database.models.client_bonus import ClientBonus
from app.services.client_database.models.washing import Washing
from app.services.parser.washings_parser import WashingsParser

from app.services.terminal.session import TerminalSession


def setup_update_db_job(
    scheduler: AsyncIOScheduler,
    terminal_sessions: list[TerminalSession],
    session: async_sessionmaker,
):
    scheduler.add_job(
        func=update_db,
        trigger="cron",
        minute="*/1",
        args=(terminal_sessions, session),
        name="Update database job",
    )


async def update_db(
    terminal_sessions: list[TerminalSession], sessionmaker: async_sessionmaker
):
    parser = WashingsParser(terminal_sessions)
    washings = await parser.get_washings()

    async with sessionmaker() as session:
        await update_bonuses(washings, session)
        await update_washings(washings, session)


async def update_bonuses(washings: list[Washing], session: AsyncSession):
    washingdao = WashingDAO(session)
    clientbonusdao = ClientBonusDAO(session)
    for washing in washings:
        if await washingdao.get_by_id(washing.id) is not None:
            continue

        if washing.phone is None or washing.bonuses is None:
            continue

        if await clientbonusdao.get_by_phone(washing.phone) is None:
            await clientbonusdao.add(
                ClientBonus(
                    phone=washing.phone,
                )
            )

        await clientbonusdao.add_bonuses(washing.phone, washing.bonuses)


async def update_washings(washings: list[Washing], session: AsyncSession):
    washingdao = WashingDAO(session)
    for washing in washings:
        await washingdao.add(washing)
