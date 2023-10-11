from aiogram import Router
from app.core.handlers.main import router as main_router
from app.core.handlers.send_promo import send_promo_router
from app.core.handlers.user import user_router


handlers_router = Router()
handlers_router.include_routers(main_router, user_router, send_promo_router)
