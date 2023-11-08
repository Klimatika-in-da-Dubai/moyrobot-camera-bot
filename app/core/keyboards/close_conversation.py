from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


CLOSE_CONVERSATION_BUTTON_TEXT = "Прекратить беседу с клиентом"


def get_close_conversation_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=CLOSE_CONVERSATION_BUTTON_TEXT)
    return builder.as_markup()
