from collections.abc import Awaitable, Callable
from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.types.message import Message
from apscheduler.executors.base import logging
from apscheduler.schedulers.asyncio import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.keyboards.answer_feedback import get_answer_feedback_keyboard
from app.services.client_database.dao.feedback import FeedbackDAO
from app.services.client_database.dao.question import QuestionDAO
from app.services.client_database.dao.user import UserDAO

from app.services.client_database.models.feedback import Feedback
from app.services.client_database.models.question import Question
from app.services.client_database.models.role import PermissionEnum
from app.services.client_database.models.user import User
from app.services.terminal import session

SEND_FEEDBACK_DELAY = 0.05

SendFeedbackFunction = Callable[
    [Bot, User, int, AsyncSession], Awaitable[types.Message]
]


async def get_feedback_dict_from_state(state: FSMContext) -> dict | None:
    data = await state.get_data()
    return data.get("feedback")


async def get_feedback_id_from_state(state: FSMContext) -> int | None:
    feedback = await get_feedback_dict_from_state(state)
    if feedback is None:
        return None
    return feedback.get("id")


async def get_feedback_from_state(
    state: FSMContext, session: AsyncSession
) -> Feedback | None:
    feedback_id: int | None = await get_feedback_id_from_state(state)

    feedbackdao = FeedbackDAO(session)
    if feedback_id is None:
        return None
    return await feedbackdao.get_by_id(feedback_id)


async def send_feedback_to_reviewers(
    bot: Bot, feedback_id: int, session: AsyncSession, send_func: SendFeedbackFunction
):
    userdao = UserDAO(session)
    feedbackdao = FeedbackDAO(session)
    reviewers = await userdao.get_users_by_permission(PermissionEnum.GET_FEEDBACK)

    for user in reviewers:
        try:
            message = await send_func(bot, user, feedback_id, session)
            await feedbackdao.add_feedback_notification(
                feedback_id, user.id, message.message_id
            )
        except Exception as e:
            logging.error(e)

        await asyncio.sleep(SEND_FEEDBACK_DELAY)


async def send_text_feedback(
    bot: Bot, user: User, feedback_id: int, session: AsyncSession
) -> Message:
    feedbackdao = FeedbackDAO(session)
    userdao = UserDAO(session)
    feedback: Feedback = await feedbackdao.get_by_id(feedback_id)
    text = await get_notification_message(session, feedback.user_id)
    reply_markup = None
    if await userdao.is_user_have_permission(user.id, PermissionEnum.ANSWER_FEEDBACK):
        reply_markup = get_answer_feedback_keyboard(feedback.id)

    return await bot.send_message(user.id, text, reply_markup=reply_markup)


async def get_notification_message(session: AsyncSession, client_id: int) -> str:
    questions = await get_user_questions(session, client_id)
    first_question = questions[3]
    second_question = questions[2]
    third_question = questions[1]
    main_question = questions[0]

    main_answer = main_question[1]
    if main_answer.isnumeric() and 1 <= int(main_answer) <= 5:

        main_answer = int(main_answer) * "⭐"

    first_answer = int(first_question[1]) * "⭐"
    second_answer = int(second_question[1]) * "⭐"
    third_answer = int(third_question[1]) * "⭐"
    return (
        "Получен отзыв от клиента!\n"
        f"1. {first_question[0]}:\t{first_answer}\n"
        f"2. {second_question[0]}:\t{second_answer}\n"
        f"3. {third_question[0]}:\t{third_answer}\n"
        f"4. {main_question[0]}\n"
        f"Ответ: {main_answer}"
    )


async def get_user_questions(
    session: AsyncSession, client_id: int
) -> list[tuple[str, str]]:
    feedbackdao = FeedbackDAO(session)
    questiondao = QuestionDAO(session)

    feedbacks: list[Feedback] = await feedbackdao.get_last_4_answered_feedbacks(
        client_id
    )
    questions_texts: list[str] = [
        (await questiondao.get_by_id(feedback.question_id)).text
        for feedback in feedbacks
    ]
    answers: list[str] = [
        (await feedbackdao.get_feedback_messages(feedback.id))[0].text
        for feedback in feedbacks
    ]

    return [(text, answer) for text, answer in zip(questions_texts, answers)]
