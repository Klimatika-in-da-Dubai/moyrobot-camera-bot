from aiogram.fsm.state import StatesGroup, State


class SendPromo(StatesGroup):
    text_promo_message = State()
    send_promo_message = State()


class GetPhone(StatesGroup):
    get_phone = State()


class GetFeedback(StatesGroup):
    get_feedback = State()
    get_measurable_feedback = State()


class Client(StatesGroup):
    feedback_conversation = State()


class Reviewer(StatesGroup):
    feedback_conversation = State()
