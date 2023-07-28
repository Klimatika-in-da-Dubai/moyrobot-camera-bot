from aiogram.fsm.state import StatesGroup, State


class SendPromo(StatesGroup):
    text_promo_message = State()
    send_promo_message = State()
