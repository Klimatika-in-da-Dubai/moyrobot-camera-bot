from enum import IntEnum, auto
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class YesNoChoice(IntEnum):
    YES = auto()
    NO = auto()


class YesNoCB(CallbackData, prefix="yes_no"):
    choice: YesNoChoice


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="Нет", callback_data=YesNoCB(choice=YesNoChoice.NO).pack()
        ),
        InlineKeyboardButton(
            text="Да", callback_data=YesNoCB(choice=YesNoChoice.YES).pack()
        ),
    )

    return builder.as_markup()
