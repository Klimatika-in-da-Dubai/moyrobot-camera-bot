from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder
from apscheduler.executors.base import logging
from apscheduler.schedulers.asyncio import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.client_database.dao.feedback import FeedbackDAO
from app.services.client_database.dao.question import QuestionDAO
from app.services.client_database.dao.user import UserDAO

from app.services.client_database.models.feedback import Feedback
from app.services.client_database.models.message import Message
from app.services.client_database.models.question import MEASURABLE_CATEGORY, Question
from app.services.client_database.models.user import User

SEND_FEEDBACK_DELAY = 0.05


async def get_feedback_dict_from_state(state: FSMContext) -> dict | None:
    data = await state.get_data()
    return data.get("feedback")


async def get_feedback_id_from_state(state: FSMContext) -> int | None:
    feedback = await get_feedback_dict_from_state(state)
    if feedback is None:
        return None
    return feedback.get("id")


async def get_feedback_from_state(
    state: FSMContext, session: AsyncSession
) -> Feedback | None:
    feedback_id: int | None = await get_feedback_id_from_state(state)

    feedbackdao = FeedbackDAO(session)
    if feedback_id is None:
        return None
    return await feedbackdao.get_by_id(feedback_id)


async def send_feedback_to_reviewers(bot: Bot, feedback_id: int, session: AsyncSession):
    userdao = UserDAO(session)
    reviewers = await userdao.get_users_by_permission("GET_FEEDBACK")

    for user in reviewers:
        try:
            await send_feedback_message(bot, user, feedback_id, session)
        except Exception as e:
            logging.error(e)

        await asyncio.sleep(SEND_FEEDBACK_DELAY)


async def send_feedback_message(
    bot: Bot, user: User, feedback_id: int, session: AsyncSession
):
    feedbackdao = FeedbackDAO(session)
    questiondao = QuestionDAO(session)
    feedback: Feedback = await feedbackdao.get_by_id(feedback_id)
    question: Question = await questiondao.get_by_id(feedback.question_id)
    messages: list[Message] = await feedbackdao.get_feedback_messages(feedback_id)
    attached_files = await feedbackdao.get_attached_files_to_feedback(feedback_id)
    categories = [
        c.name for c in await questiondao.get_question_categories(question.id)
    ]
    text = "Получен отзыв от клиента!\n" f"Вопрос: {question.text}\n" "Ответ: "

    match len(attached_files):
        case 0:
            if MEASURABLE_CATEGORY in categories:
                mark = int(messages[0].text)
                text += "⭐" * mark
            else:
                text += messages[0].text
            await bot.send_message(user.id, text)
        case _:
            caption = attached_files[0].caption or ""
            mediabuilder = MediaGroupBuilder(caption=text + caption)
            for file in attached_files:
                mediabuilder.add(type=file.type, media=file.id, caption=file.caption)  # type: ignore

            await bot.send_media_group(user.id, media=mediabuilder.build())
