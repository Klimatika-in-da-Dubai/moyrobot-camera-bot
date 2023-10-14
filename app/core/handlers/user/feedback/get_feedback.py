from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
)
from apscheduler.executors.base import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.handlers.user.feedback.utils import (
    get_feedback_id_from_state,
)
from app.core.middlewares.media import MediaGroupMiddleware

from app.core.states.states import GetFeedback
from app.services.client_database import models
from app.services.client_database.dao.feedback import FeedbackDAO
from app.services.client_database.dao.question import QuestionDAO
from app.services.client_database.dao.user import UserDAO
from app.services.client_database.models.feedback import Feedback
from app.services.client_database.models.question import Question

logger = logging.getLogger(__name__)

get_feedback_router = Router()
get_feedback_router.message.filter(GetFeedback.get_feedback)
get_feedback_router.message.middleware(MediaGroupMiddleware())


async def handle_feedback(
    feedback_id: int,
    message: models.Message,
    session: AsyncSession,
):
    feedbackdao = FeedbackDAO(session)
    await feedbackdao.attach_message_by_ids(feedback_id, message.id)
    await send_feedback_to_reviewers(feedback_id, session)


@get_feedback_router.message(or_f(F.text, F.video, F.photo, F.media_group_id))
async def msg_album_feedback(
    message: Message,
    album: list[Message],
    state: FSMContext,
    session: AsyncSession,
):
    """This handler will receive a complete album of any type."""
    await message.answer("Спасибо, что оставили отзыв!")
    feedback_id = await get_feedback_id_from_state(state)
    await state.clear()
    assert feedback_id is not None

    feedbackdao = FeedbackDAO(session)
    for mes in album:
        await feedbackdao.attach_message_by_ids(feedback_id, mes.message_id)

    await send_feedback_to_reviewers(feedback_id, session)


async def send_feedback_to_reviewers(feedback_id: int, session: AsyncSession):
    userdao = UserDAO(session)
    feedbackdao = FeedbackDAO(session)
    questiondao = QuestionDAO(session)
    users = await userdao.get_users_by_permission("GET_FEEDBACK")
    feedback: Feedback = await feedbackdao.get_by_id(feedback_id)
    await questiondao.get_by_id(feedback.question_id)

    for user in users:
        ...


async def send_question_message(question: Question):
    ...


async def send_feedback_message(feedback: Feedback):
    ...
