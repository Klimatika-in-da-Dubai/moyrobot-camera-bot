from aiogram import F, Bot, Router
from aiogram.fsm.context import FSMContext
from apscheduler.executors.base import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.handlers.user.feedback.utils import (
    get_feedback_id_from_state,
    send_feedback_to_reviewers,
)
import re
from app.core.keyboards.menu import get_user_menu_reply_keyboard

from app.core.states.states import GetFeedback
from app.services.client_database.dao.feedback import FeedbackDAO
from app.services.client_database.dao.message import MessageDAO
from app.services.client_database.models.message import Message

logger = logging.getLogger(__name__)

get_measurable_feedback_router = Router()
get_measurable_feedback_router.message.filter(GetFeedback.get_measurable_feedback)

pattern = re.compile(r"[1-5] ⭐", re.UNICODE)


@get_measurable_feedback_router.message(F.text)
async def msg_measurable_feedback(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
):
    """This handler will receive a complete album of any type."""
    if not pattern.match(message.text):
        await message.answer("Выберите рейтинг из клавиатуры!")
        return

    await message.answer(
        "Спасибо, что оставили отзыв!",
        reply_markup=await get_user_menu_reply_keyboard(message.chat.id, session),
    )
    feedback_id = await get_feedback_id_from_state(state)
    await state.clear()

    mark = message.text.split()[0]
    assert feedback_id is not None

    feedbackdao = FeedbackDAO(session)
    messagedao = MessageDAO(session)
    await feedbackdao.attach_message_by_ids(feedback_id, message.message_id)
    await messagedao.change_message(message.message_id, mark)

    await send_feedback_to_reviewers(bot, feedback_id, session)
