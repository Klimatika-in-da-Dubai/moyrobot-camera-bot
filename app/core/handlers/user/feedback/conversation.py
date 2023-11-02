from aiogram import F, Bot, Router
from aiogram.types import Message
from app.core.middlewares.feedback_conversation import (
    FeedbackConversationMiddleware,
    FeedbackConversationStateData,
)
from app.core.middlewares.media import MediaGroupMiddleware
from app.core.states.states import Client


feedback_conversation_router = Router()
feedback_conversation_router.message.middleware(FeedbackConversationMiddleware())
feedback_conversation_router.message.middleware(MediaGroupMiddleware())


@feedback_conversation_router.message(Client.feedback_conversation, F.text)
async def feedback_conversation_text(
    message: Message,
    feedback_conversation: FeedbackConversationStateData,
    bot: Bot,
):
    assert message.text is not None

    client_id = await feedback_conversation.get_client_id()
    await bot.send_message(client_id, text=message.text)


@feedback_conversation_router.message(Client.feedback_conversation, F.photo)
async def feedback_conversation_photo(
    message: Message,
    feedback_conversation: FeedbackConversationStateData,
    bot: Bot,
):
    assert message.photo is not None

    client_id = await feedback_conversation.get_client_id()
    await bot.send_photo(
        client_id, photo=message.photo[-1].file_id, caption=message.caption
    )


@feedback_conversation_router.message(Client.feedback_conversation, F.video)
async def feedback_conversation_video(
    message: Message,
    feedback_conversation: FeedbackConversationStateData,
    bot: Bot,
):
    assert message.video is not None

    client_id = await feedback_conversation.get_client_id()
    await bot.send_video(
        client_id, video=message.video.file_id, caption=message.caption
    )
