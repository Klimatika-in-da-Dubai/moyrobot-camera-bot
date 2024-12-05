import random
from typing import Optional
from aiogram import F, Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from apscheduler.executors.base import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.handlers.user.feedback.utils import (
    get_feedback_id_from_state,
)
import re
from app.core.keyboards.measurable_category import get_measurable_category_keyboard

from app.core.keyboards.yes_no import get_yes_no_reply_ketboard
from app.core.states.states import GetFeedback
from app.services.client_database.dao.feedback import FeedbackDAO
from app.services.client_database.dao.message import MessageDAO
from app.services.client_database.dao.question import QuestionDAO
from app.services.client_database.dao.user import UserDAO
from app.services.client_database.models.feedback import Feedback
from app.services.client_database.models.question import CategoryEnum, Question
from app.services.client_database.models.user import User
from app.services.client_database.models.washing import Washing
from app.services.terminal.session import TerminalSession
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove

logger = logging.getLogger(__name__)

get_static_questions_feedback_router = Router()
get_static_questions_feedback_router.message.filter(
    GetFeedback.get_static_questions_feedback
)

pattern = re.compile(r"[1-5] ⭐", re.UNICODE)


@get_static_questions_feedback_router.message(F.text)
async def msg_measurable_feedback(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
    terminal_session: TerminalSession,
):
    assert message.text is not None
    if not pattern.match(message.text):
        await message.answer(
            "Выберите рейтинг из клавиатуры!",
            reply_markup=get_measurable_category_keyboard(),
        )
        return

    feedback_id = await get_feedback_id_from_state(state)
    await state.clear()

    mark = message.text.split()[0]
    assert feedback_id is not None

    feedbackdao = FeedbackDAO(session)
    messagedao = MessageDAO(session)
    await feedbackdao.attach_message_by_ids(feedback_id, message.message_id)
    await messagedao.change_message(message.message_id, mark)

    feedback: Feedback = await feedbackdao.get_by_id(feedback_id)

    # 39, 40, 41 - ids of for first 3 questions

    if (
        await feedbackdao.is_feedback_question_have_category(
            feedback_id, CategoryEnum.WASHING
        )
        and int(mark) <= 3
    ):
        await send_bonuses_for_bad_serivce(
            message, feedback_id, terminal_session, session
        )

    match feedback.question_id:
        case 39:
            await send_static_question_feedback_message(
                bot, message.chat.id, feedback.washing_id, 40, state, session
            )
            return
        case 40:
            await send_static_question_feedback_message(
                bot, message.chat.id, feedback.washing_id, 41, state, session
            )
            return

    await bot.send_message(
        message.chat.id,
        text="Ответьте пожалуйста ещё на один вопрос",
        reply_markup=ReplyKeyboardRemove(),
    )

    question = await get_random_question(session)
    new_feedback = await create_feedback(
        message.chat.id, question.id, feedback.washing_id, session
    )

    await send_feedback_request_message(
        bot, message.chat.id, new_feedback.id, question, state, session
    )


async def send_static_question_feedback_message(
    bot: Bot,
    user_id: int,
    washing_id: int,
    question_id: int,
    state: FSMContext,
    session: AsyncSession,
):
    questiondao = QuestionDAO(session)
    question = await questiondao.get_by_id(question_id)

    feedback = await create_feedback(user_id, question_id, washing_id, session)
    text = f"{question.text}"

    await state.set_state(GetFeedback.get_static_questions_feedback)
    await state.update_data(feedback={"id": feedback.id})
    await bot.send_message(
        user_id, text=text, reply_markup=get_measurable_category_keyboard()
    )


async def send_bonuses_for_bad_serivce(
    message: Message,
    feedback_id: int,
    terminal_session: TerminalSession,
    session: AsyncSession,
):
    client_id = message.chat.id
    if await is_client_already_sent_before_bad_feedback(
        client_id, feedback_id, CategoryEnum.WASHING, session
    ):
        return

    userdao = UserDAO(session)
    user: User = await userdao.get_by_id(client_id)

    await message.answer(
        "Очень жаль, что вы так оценили наши услуги(\nВ качестве извенения мы начислим вам 100 бонусов"
    )

    async with terminal_session as term_session:
        await term_session.add_bonuses_by_phone(user.phone, 100, "За плохой отзыв")


async def get_random_question(
    session: AsyncSession, category: Optional[CategoryEnum] = None
) -> Question:
    questiondao = QuestionDAO(session)
    questions = await questiondao.get_active_questions(category)
    return random.choice(questions)


async def create_feedback(
    user_id: int, question_id: int, washing_id: int, session: AsyncSession
) -> Feedback:
    feedback = Feedback(user_id=user_id, question_id=question_id, washing_id=washing_id)
    feedback = await FeedbackDAO(session).add(feedback)
    return feedback


async def is_client_already_sent_before_bad_feedback(
    client_id: int, feedback_id: int, category: CategoryEnum, session: AsyncSession
):
    feedbackdao = FeedbackDAO(session)
    feedbacks = await feedbackdao.get_client_feedbacks(client_id, category)
    for feedback in feedbacks:
        if feedback.id == feedback_id:
            continue
        messages: list = await feedbackdao.get_feedback_messages(feedback.id)
        mark = messages[0].text
        if int(mark) <= 3:
            return True
    return False


async def send_feedback_request_message(
    bot: Bot,
    user_id: int,
    feedback_id: int,
    question: Question,
    state: FSMContext,
    session: AsyncSession,
):
    questiondao = QuestionDAO(session)
    categories = await questiondao.get_question_categories(question.id)
    categories_names = [c.name for c in categories]
    match categories_names:
        case _ if CategoryEnum.MEASURABLE in categories_names:
            await send_measurable_feedback_request(
                bot, user_id, feedback_id, question, state
            )
        case _ if CategoryEnum.YES_NO in categories_names:
            await send_yes_no_feedback_request(
                bot, user_id, feedback_id, question, state
            )
        case _:
            await send_default_feedback_request(
                bot, user_id, feedback_id, question, state
            )


async def send_measurable_feedback_request(
    bot: Bot,
    user_id: int,
    feedback_id: int,
    question: Question,
    state: FSMContext,
):
    text = f"{question.text}"

    await state.set_state(GetFeedback.get_measurable_feedback)
    await state.update_data(feedback={"id": feedback_id})
    await bot.send_message(
        user_id, text=text, reply_markup=get_measurable_category_keyboard()
    )


async def send_yes_no_feedback_request(
    bot: Bot,
    user_id: int,
    feedback_id: int,
    question: Question,
    state: FSMContext,
):
    text = f"{question.text}"

    await state.set_state(GetFeedback.get_yes_no_feedback)
    await state.update_data(feedback={"id": feedback_id})
    await bot.send_message(user_id, text=text, reply_markup=get_yes_no_reply_ketboard())


async def send_default_feedback_request(
    bot: Bot,
    user_id: int,
    feedback_id: int,
    question: Question,
    state: FSMContext,
):
    text = f"{question.text}"

    await state.set_state(GetFeedback.get_feedback)
    await state.update_data(feedback={"id": feedback_id})
    await bot.send_message(user_id, text=text)
