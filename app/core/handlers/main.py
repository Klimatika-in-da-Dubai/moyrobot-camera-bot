from aiogram import Bot, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.cameras.camera_stream import (
    CameraStream,
    get_input_media_photo_to_send,
)

from app.services.database.dao.user import UserDAO, get_user_from_message
from app.settings.config import Config


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """/start command handling. Adds new user to database, finish states"""
    user = get_user_from_message(message)

    userdao = UserDAO(session=session)
    if await userdao.get_by_id(user.id) is None:
        await userdao.add_user(user)

    text = (
        "Добрый день.\n\nВас приветствует МойРобот."
        "С моей помощью вы сможете увидеть очередь на мойку.\n\n"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command(commands=["queue"]))
async def cmd_queue(
    message: Message, bot: Bot, config: Config, streams: list[CameraStream]
):
    cameras = list(filter(lambda x: "queue" in x.tags, streams))
    photos = []
    for camera in cameras:
        photos.append(get_input_media_photo_to_send(camera, config))

    await bot.send_media_group(message.chat.id, photos)


@router.message(Command(commands=["stats"]))
async def cmd_stats(message: Message, session: AsyncSession):
    """
    Send table from view daily_usage

    """
    query = text("SELECT * FROM daily_usage LIMIT 12;")
    result = await session.execute(query)
    message_text = ""
    for row in result:
        message_text += f"{row[0]}\t{row[1]}\n"
    await message.answer(message_text)
