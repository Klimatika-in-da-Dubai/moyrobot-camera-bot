from typing import List
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
)
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.middlewares.media import MediaGroupMiddleware

from app.core.states.states import GetFeedback


get_feedback_router = Router()
get_feedback_router.message.filter(GetFeedback.get_feedback)
get_feedback_router.message.middleware(MediaGroupMiddleware())


@get_feedback_router.message(F.media_group_id)
async def msg_album_feedback(
    message: Message, album: List[Message], state: FSMContext, session: AsyncSession
):
    """This handler will receive a complete album of any type."""

    media = MediaGroupBuilder(caption=message.text)

    for element in album:
        caption_kwargs = {
            "caption": element.caption,
            "caption_entities": element.caption_entities,
        }
        if element.photo:
            media.add_photo(media=element.photo[-1].file_id, **caption_kwargs)
        elif element.video:
            media.add_video(media=element.video.file_id, **caption_kwargs)
        else:
            return message.answer("This media type isn't supported!")

    return message.answer_media_group(media.build())


@get_feedback_router.message(F.text)
async def msg_text_feedback(message: Message, state: FSMContext, session: AsyncSession):
    await message.answer(message.text)  # type: ignore


@get_feedback_router.message(F.photo)
async def msg_photo_feedback(
    message: Message, state: FSMContext, session: AsyncSession
):
    await message.answer_photo(message.photo[0].file_id)  # type: ignore


@get_feedback_router.message(F.video)
async def msg_video_feedback(
    message: Message, state: FSMContext, session: AsyncSession
):
    await message.answer_video(message.video.file_id)  # type: ignore
