from aiogram import Bot
from apscheduler.executors.base import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler, asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.services.client_database.dao.client_bonus import ClientBonusDAO
from app.services.client_database.dao.user import UserDAO

from app.services.client_database.dao.washing import WashingDAO
from app.services.client_database.models.client_bonus import ClientBonus
from app.services.client_database.models.user import User
from app.services.client_database.models.washing import Washing
from app.services.parser.washings_parser import WashingsParser

from app.services.terminal.session import TerminalSession

SEND_NOTIFICATION_DELAY = 0.06


def setup_parser_job(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    terminal_sessions: list[TerminalSession],
    session: async_sessionmaker,
):
    scheduler.add_job(
        func=do_parser_work,
        trigger="cron",
        minute="*/1",
        args=(bot: Bot, terminal_sessions, session),
        name="Update database job",
    )


async def do_parser_work(
    bot: Bot, terminal_sessions: list[TerminalSession], sessionmaker: async_sessionmaker
):
    parser = WashingsParser(terminal_sessions)
    washings = await parser.get_washings()
    async with sessionmaker() as session:
        await update_bonuses(washings, session)
        await send_bonus_notifications(bot, washings, session)
        await update_washings(washings, session)


async def filter_new_washings_with_bonuses(
    washings: list[Washing], session: AsyncSession
) -> list[Washing]:
    return [
        washing
        for washing in await filter_new_washings(washings, session)
        if washing.phone is not None and washing.bonuses is not None
    ]


async def filter_new_washings(
    washings: list[Washing], session: AsyncSession
) -> list[Washing]:
    washingdao = WashingDAO(session)
    return [
        washing
        for washing in washings
        if not await washingdao.is_washing_exists(washing)
    ]


async def update_bonuses(washings: list[Washing], session: AsyncSession):
    clientbonusdao = ClientBonusDAO(session)
    new_washings = await filter_new_washings_with_bonuses(washings, session)
    for washing in new_washings:
        if await clientbonusdao.get_by_phone(washing.phone) is None:
            await clientbonusdao.add(
                ClientBonus(
                    phone=washing.phone,
                )
            )

        await clientbonusdao.add_bonuses(washing.phone, washing.bonuses)


async def send_bonus_notifications(
    bot: Bot, washings: list[Washing], session: AsyncSession
):
    userdao = UserDAO(session)
    clientbonusdao = ClientBonusDAO(session)
    new_washings = await filter_new_washings_with_bonuses(washings, session)
    for washing in new_washings:
        users: list[User] = await userdao.get_users_by_phone(washing.phone)
        bonus_balance: ClientBonus = await clientbonusdao.get_by_phone(washing.phone)

        if bonus_balance is None:
            continue

        text = (
            "Начисление бонусов за мойку!\n"
            f"Количество: {washing.bonuses}\n"
            f"Текущий баланс: {bonus_balance.actual_amount}\n"
        )

        for user in users:
            try:
                await bot.send_message(user.id, text=text)
            except Exception as e:
                logging.error(e)

            await asyncio.sleep(SEND_NOTIFICATION_DELAY)


async def update_washings(washings: list[Washing], session: AsyncSession):
    washingdao = WashingDAO(session)
    for washing in washings:
        await washingdao.add(washing)
