from aiogram import Bot
from aiogram.fsm.context import FSMContext
from apscheduler.executors.base import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.client_database.dao.feedback import FeedbackDAO
from app.services.client_database.dao.question import QuestionDAO
from app.services.client_database.dao.user import UserDAO

from app.services.client_database.models.feedback import Feedback
from app.services.client_database.models.message import Message
from app.services.client_database.models.question import MEASURABLE_CATEGORY, Question
from app.services.client_database.models.user import User


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


async def send_feedback_message(
    bot: Bot, user: User, feedback_id: int, session: AsyncSession
):
    feedbackdao = FeedbackDAO(session)
    questiondao = QuestionDAO(session)
    feedback: Feedback = await feedbackdao.get_by_id(feedback_id)
    question: Question = await questiondao.get_by_id(feedback.question_id)
    messages: list[Message] = await feedbackdao.get_feedback_messages(feedback_id)

    categories = [
        c.name for c in await questiondao.get_question_categories(question.id)
    ]
    if MEASURABLE_CATEGORY in categories:
        mark = int(messages[0].text)
        answer = "⭐" * mark
    else:
        answer = messages[0].text
    text = "Получен отзыв от клиента!\n" f"Вопрос: {question.text}\n" f"Ответ: {answer}"
    await bot.send_message(user.id, text)
