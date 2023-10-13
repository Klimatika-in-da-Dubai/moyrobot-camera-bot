from datetime import datetime, timedelta
import random
from typing import Optional
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from apscheduler.executors.base import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.states.states import GetFeedback
from app.services.client_database.dao.feedback import FeedbackDAO
from app.services.client_database.dao.question import QuestionDAO
from app.services.client_database.dao.user import UserDAO
from app.services.client_database.models.feedback import Feedback
from app.services.client_database.models.question import Category, Question
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
                datetime.now(), timedelta(minutes=30), timedelta(days=1)
            )
            state = FSMContext(state_storage, key=create_storage_key(bot, user))
            scheduler.add_job(
                func=send_client_feedback_request,
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


async def send_client_feedback_request(
    bot: Bot,
    client: User,
    washing: Washing,
    session: AsyncSession,
    state: FSMContext,
):
    try:
        question = await get_random_question(session)
    except IndexError:
        logging.error("No question was chosen")
        return
    feedback = await create_feedback(client, question, washing, session)
    await send_feedback_request_message(bot, client, feedback, question, state)


async def get_random_question(
    session: AsyncSession, category: Optional[Category] = None
) -> Optional[Question]:
    questiondao = QuestionDAO(session)

    if category is None:
        questions = await questiondao.get_all()
    else:
        questions = await questiondao.get_questions_by_category_id(category.id)
    return random.choice(questions)


async def create_feedback(
    user: User, question: Question, washing: Washing, session: AsyncSession
) -> Feedback:
    feedback = Feedback(user_id=user.id, question_id=question.id, washing_id=washing.id)
    await FeedbackDAO(session).add(feedback)
    return feedback


async def send_feedback_request_message(
    bot: Bot,
    user: User,
    feedback: Feedback,
    question: Question,
    state: FSMContext,
):
    text = (
        f" Вы недавно посещали МойРобот.\n"
        "Ответьте пожалуйста на наш вопрос.\n"
        "Мы будем очень благодарны ;)\n"
        "Если отвечать не хотите, просто проигнорируйте это сообщение\n\n"
        f"{question.text}"
    )
    await state.set_state(GetFeedback.get_feedback)
    await state.update_data(feedback={"feedback_id": feedback.id})
    await bot.send_message(user.id, text=text)


def create_storage_key(bot: Bot, user: User) -> StorageKey:
    return StorageKey(
        bot_id=bot.id,
        chat_id=user.id,
        user_id=user.id,
    )
