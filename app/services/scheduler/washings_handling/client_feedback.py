from datetime import datetime, timedelta
import random
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.handlers.user.feedback.get_static_questions_feedback import (
    send_static_question_feedback_message,
)
from app.core.keyboards.measurable_category import get_measurable_category_keyboard
from app.core.keyboards.yes_no import get_yes_no_reply_ketboard
from app.services.client_database.dao.user import UserDAO
from app.services.client_database.models.user import User
from app.services.client_database.models.washing import Washing


async def create_send_feedback_request_jobs(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    washings: list[Washing],
    session: AsyncSession,
    state_storage: BaseStorage,
):
    userdao = UserDAO(session)
    for washing in washings:
        users: list[User] = await userdao.get_users_by_phone(washing.phone)
        for user in users:
            date = generate_datetime(
                datetime.now(), timedelta(minutes=15), timedelta(hours=1)
            )
            state = FSMContext(state_storage, key=create_storage_key(bot, user))
            scheduler.add_job(
                func=send_feedback_request,
                trigger="date",
                run_date=date,
                args=(bot, user, washing, session, state),
                name=f"Getting feedback from user {user.phone}",
            )


def generate_datetime(
    since: datetime, min_delay: timedelta, max_delay: timedelta
) -> datetime:
    start = int(min_delay.total_seconds())
    end = int(max_delay.total_seconds())
    return since + timedelta(seconds=random.randint(start, end))


async def send_feedback_request(
    bot: Bot,
    client: User,
    washing: Washing,
    session: AsyncSession,
    state: FSMContext,
):
    start_question_id = 39
    await send_feedback_request_hello_message(bot, client)
    await send_static_question_feedback_message(
        bot, client.id, washing.id, start_question_id, state, session
    )


async def send_feedback_request_hello_message(bot: Bot, user: User):
    text = (
        "Вы недавно посещали МойРобот!\n"
        "Ответьте пожалуйста на наш вопрос, мы будем очень благодарны ;)\n"
    )
    await bot.send_message(user.id, text=text)


def create_storage_key(bot: Bot, user: User) -> StorageKey:
    return StorageKey(
        bot_id=bot.id,
        chat_id=user.id,
        user_id=user.id,
    )
