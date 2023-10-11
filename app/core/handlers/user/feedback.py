from typing import List
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.middlewares.media import MediaGroupMiddleware

from app.core.states.states import GetFeedback


feedback_router = Router()
feedback_router.message.filter(GetFeedback.get_feedback)
feedback_router.message.middleware(MediaGroupMiddleware())


@feedback_router.message(F.media_group_id)
async def msg_album_feedback(
    message: Message, album: List[Message], state: FSMContext, session: AsyncSession
):
    """This handler will receive a complete album of any type."""
    group_elements = []
    for element in album:
        caption_kwargs = {
            "caption": element.caption,
            "caption_entities": element.caption_entities,
        }
        if element.photo:
            input_media = InputMediaPhoto(
                media=element.photo[-1].file_id, **caption_kwargs
            )
        elif element.video:
            input_media = InputMediaVideo(media=element.video.file_id, **caption_kwargs)
        elif element.document:
            input_media = InputMediaDocument(
                media=element.document.file_id, **caption_kwargs
            )
        elif element.audio:
            input_media = InputMediaAudio(media=element.audio.file_id, **caption_kwargs)
        else:
            return message.answer("This media type isn't supported!")

        group_elements.append(input_media)

    return message.answer_media_group(group_elements)


@feedback_router.message(F.text)
async def msg_text_feedback(message: Message, state: FSMContext, session: AsyncSession):
    await message.answer(message.text)


@feedback_router.message(F.photo)
async def msg_photo_feedback(
    message: Message, state: FSMContext, session: AsyncSession
):
    await message.answer_photo(message.photo[0].file_id)


@feedback_router.message(F.video)
async def msg_video_feedback(
    message: Message, state: FSMContext, session: AsyncSession
):
    await message.answer_video(message.video.file_id)
