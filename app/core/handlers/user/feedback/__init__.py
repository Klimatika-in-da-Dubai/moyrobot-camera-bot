from aiogram import Router
from app.core.handlers.user.feedback.get_feedback import get_feedback_router

feedback_router = Router()

feedback_router.include_routers(get_feedback_router)
