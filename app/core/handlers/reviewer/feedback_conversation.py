from aiogram import F, Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.keyboards.cancel import CancelCB, get_cancel_keyboard

from app.core.keyboards.answer_feedback import AnswerFeedbackCB
from app.core.keyboards.close_conversation import CLOSE_CONVERSATION_BUTTON_TEXT
from app.core.keyboards.menu import get_menu_reply_keyboard
from app.core.middlewares.feedback_conversation import (
    FeedbackConversationMiddleware,
    FeedbackConversationStateData,
)
from app.core.middlewares.media import MediaGroupMiddleware
from app.core.states.states import Client, Reviewer
from app.services.client_database.dao.feedback import FeedbackDAO
from app.services.client_database.dao.user import UserDAO
from app.services.client_database.models.feedback import (
    ConversationStatus,
    Feedback,
)
from app.services.client_database.models.user import User
from app.services.scheduler.washings_handling.client_feedback import create_storage_key


feedback_conversation_router = Router()
feedback_conversation_router.message.middleware(FeedbackConversationMiddleware())
feedback_conversation_router.message.middleware(MediaGroupMiddleware())


@feedback_conversation_router.callback_query(AnswerFeedbackCB.filter())
async def cb_feedback_conversation(
    cb: CallbackQuery,
    callback_data: AnswerFeedbackCB,
    bot: Bot,
    fsm_storage: RedisStorage,
    state: FSMContext,
    session: AsyncSession,
):
    feedbackdao = FeedbackDAO(session)
    userdao = UserDAO(session)

    if await feedbackdao.is_feedback_conversation_active(callback_data.feedback_id):
        await cb.answer(text="Отзыв уже обрабатывается!", show_alert=True)
        return

    await cb.answer()
    feedback: Feedback = await feedbackdao.get_by_id(callback_data.feedback_id)
    client: User = await userdao.get_by_id(feedback.user_id)
    await feedbackdao.create_conversation(feedback.id, client.id)

    client_storage_key = create_storage_key(bot, client)
    client_state = FSMContext(fsm_storage, client_storage_key)

    await state.set_state(Reviewer.feedback_conversation)
    await client_state.set_state(Client.feedback_conversation)

    await FeedbackConversationStateData(state).init(
        feedback_id=feedback.id, client_id=client.id, reviewer_id=cb.from_user.id
    )
    await FeedbackConversationStateData(client_state).init(
        feedback_id=feedback.id, client_id=client.id, reviewer_id=cb.from_user.id
    )
    await cb.message.answer(
        "Чтобы обащаться с клиентом просто пишите сообщения боту, они будут перенаправлятся.\nВы также можете прикрепить фото или видео",
        reply_markup=get_cancel_keyboard(),
    )


@feedback_conversation_router.callback_query(
    Reviewer.feedback_conversation, CancelCB.filter()
)
async def cancel_conversation(
    cb: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    feedback_conversation: FeedbackConversationStateData,
):
    feedbackdao = FeedbackDAO(session)
    await cb.message.delete()
    client_id = await feedback_conversation.get_client_id()
    reviewer_id = await feedback_conversation.get_reviewer_id()
    await feedbackdao.update_conversation_status(
        client_id, reviewer_id, ConversationStatus.CANCELED
    )

    await state.clear()


@feedback_conversation_router.message(
    Reviewer.feedback_conversation, F.text == CLOSE_CONVERSATION_BUTTON_TEXT
)
async def close_conversation(
    message: Message,
    feedback_conversation: FeedbackConversationStateData,
    bot: Bot,
    state: FSMContext,
    fsm_storage: RedisStorage,
    session: AsyncSession,
):
    userdao = UserDAO(session)
    feedbackdao = FeedbackDAO(session)
    client_id = await feedback_conversation.get_client_id()
    reviewer_id = await feedback_conversation.get_reviewer_id()
    await feedbackdao.update_conversation_status(
        client_id, reviewer_id, ConversationStatus.CLOSED
    )
    client: User = await userdao.get_by_id(client_id)

    client_storage_key = create_storage_key(bot, client)
    client_state = FSMContext(fsm_storage, client_storage_key)

    await state.clear()
    await client_state.clear()

    await bot.send_message(
        client_id,
        text="Беседа закрыта. Удачного дня!",
        reply_markup=get_menu_reply_keyboard(),
    )

    await message.answer(
        "Вы прекратили разговор с клиентом", reply_markup=get_menu_reply_keyboard()
    )


@feedback_conversation_router.message(Reviewer.feedback_conversation, F.text)
async def feedback_conversation_text(
    message: Message,
    feedback_conversation: FeedbackConversationStateData,
    bot: Bot,
):
    assert message.text is not None

    client_id = await feedback_conversation.get_client_id()
    await bot.send_message(
        client_id, text=message.text, reply_markup=get_cancel_keyboard()
    )


@feedback_conversation_router.message(Reviewer.feedback_conversation, F.photo)
async def feedback_conversation_photo(
    message: Message,
    feedback_conversation: FeedbackConversationStateData,
    bot: Bot,
):
    assert message.photo is not None

    client_id = await feedback_conversation.get_client_id()
    await bot.send_photo(
        client_id,
        photo=message.photo[-1].file_id,
        caption=message.caption,
        reply_markup=get_cancel_keyboard(),
    )


@feedback_conversation_router.message(Reviewer.feedback_conversation, F.video)
async def feedback_conversation_video(
    message: Message,
    feedback_conversation: FeedbackConversationStateData,
    bot: Bot,
):
    assert message.video is not None

    client_id = await feedback_conversation.get_client_id()
    await bot.send_video(
        client_id,
        video=message.video.file_id,
        caption=message.caption,
        reply_markup=get_cancel_keyboard(),
    )
