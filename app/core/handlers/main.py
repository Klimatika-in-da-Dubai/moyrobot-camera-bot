from typing import Optional
from aiogram import F, Bot, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.keyboards.menu import (
    GET_BONUSES_BUTTON_TEXT,
    PHONE_BUTTON_TEXT,
    SEE_QUEUE_BUTTON_TEXT,
    get_menu_reply_keyboard,
)
from app.core.states.states import GetPhone
from app.services.cameras.camera_stream import (
    CameraStream,
    get_input_media_photo_to_send,
)
from app.services.client_database.dao.client_bonus import ClientBonusDAO

from app.services.client_database.dao.user import UserDAO
from app.services.client_database.models.client_bonus import ClientBonus
from app.services.client_database.models.user import User
from app.settings.config import Config
from app.utils.phone import format_phone, is_phone_correct, phone_to_text


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """/start command handling. Adds new user to client_database finish states"""

    userdao = UserDAO(session=session)
    user: User = await userdao.get_by_id(message.chat.id)

    text = (
        "Добрый день.\n\nВас приветствует МойРобот."
        "С моей помощью вы сможете увидеть очередь на мойку.\n\n"
    )
    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_menu_reply_keyboard(user.phone),
    )


@router.message(F.text == SEE_QUEUE_BUTTON_TEXT)
async def queue(
    message: Message,
    state: FSMContext,
    bot: Bot,
    config: Config,
    streams: list[CameraStream],
):
    await state.clear()
    cameras = list(filter(lambda x: "queue" in x.tags, streams))
    photos = []
    for camera in cameras:
        photos.append(get_input_media_photo_to_send(camera, config))

    await bot.send_media_group(message.chat.id, photos)


@router.message(F.text == GET_BONUSES_BUTTON_TEXT)
async def msg_get_bonuses(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()
    userdao = UserDAO(session=session)

    user: User = await userdao.get_by_id(message.chat.id)

    if user.phone is None:
        await msg_phone(message, state)
        return

    clientbonusdao = ClientBonusDAO(session=session)
    clientbonus: Optional[ClientBonus] = await clientbonusdao.get_by_phone(user.phone)
    if clientbonus is None:
        clientbonus = ClientBonus(phone=user.phone)
        await clientbonusdao.add(clientbonus)

    await message.answer(
        "Ваш текущий баланс:\n"
        f"Телефон: {format_phone(clientbonus.phone)}\n"
        f"Бонусы: {clientbonus.actual_amount}"
    )


@router.message(F.text.startswith(PHONE_BUTTON_TEXT))
async def msg_phone(message: Message, state: FSMContext):
    await message.answer("Введите пожалуйста новый номер телефона")
    await state.set_state(GetPhone.get_phone)


@router.message(GetPhone.get_phone, F.text)
async def msg_get_phone(message: Message, state: FSMContext, session: AsyncSession):
    text = message.text
    if text is None:
        raise ValueError("Text in message is None")

    if not is_phone_correct(text):
        await message.answer("Некорретный номер телефона")
        return
    phone = phone_to_text(text)

    userdao = UserDAO(session)
    await userdao.add_phone(message.chat.id, phone)

    clientbonusdao = ClientBonusDAO(session)
    await clientbonusdao.add_bonuses(phone, 0)

    await message.answer(
        f"Вы сменили номер телефона!\n" f"Новый номер: {format_phone(phone)}",
        reply_markup=get_menu_reply_keyboard(phone),
    )
    await state.clear()


@router.message(Command(commands=["queue", "photo"]))
async def cmd_deprecated_photo_commands(message: Message):
    await message.answer(
        "Данная команда больше не работает :(\nВы можете посмотреть очередь через меню",
        reply_markup=get_menu_reply_keyboard(),
    )
