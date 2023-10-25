from aiogram import F, Bot, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
)
from apscheduler.executors.base import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.handlers.user.feedback.utils import (
    get_feedback_id_from_state,
    send_feedback_to_reviewers,
)
from app.core.keyboards.menu import get_user_menu_reply_keyboard
from app.core.middlewares.media import MediaGroupMiddleware

from app.core.states.states import GetFeedback
from app.services.client_database import models
from app.services.client_database.dao.feedback import FeedbackDAO

logger = logging.getLogger(__name__)

get_feedback_router = Router()
get_feedback_router.message.filter(GetFeedback.get_feedback)
get_feedback_router.message.middleware(MediaGroupMiddleware())


async def handle_feedback(
    feedback_id: int,
    message: models.Message,
    session: AsyncSession,
    bot: Bot,
):
    feedbackdao = FeedbackDAO(session)
    await feedbackdao.attach_message_by_ids(feedback_id, message.id)
    await send_feedback_to_reviewers(bot, feedback_id, session)


@get_feedback_router.message(F.media_group_id)
async def msg_album_feedback(
    message: Message,
    album: list[Message],
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
):
    """This handler will receive a complete album of any type."""
    await message.answer(
        "Спасибо, что оставили отзыв!",
        reply_markup=await get_user_menu_reply_keyboard(message.chat.id, session),
    )
    feedback_id = await get_feedback_id_from_state(state)
    await state.clear()
    assert feedback_id is not None

    feedbackdao = FeedbackDAO(session)
    for mes in album:
        await feedbackdao.attach_message_by_ids(feedback_id, mes.message_id)

    await send_feedback_to_reviewers(bot, feedback_id, session)


@get_feedback_router.message(or_f(F.text, F.video, F.photo))
async def msg_feedback(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
):
    """This handler will receive a complete album of any type."""
    await message.answer(
        "Спасибо, что оставили отзыв!",
        reply_markup=await get_user_menu_reply_keyboard(message.chat.id, session),
    )
    feedback_id = await get_feedback_id_from_state(state)
    await state.clear()
    assert feedback_id is not None

    feedbackdao = FeedbackDAO(session)
    await feedbackdao.attach_message_by_ids(feedback_id, message.message_id)
    await send_feedback_to_reviewers(bot, feedback_id, session)
