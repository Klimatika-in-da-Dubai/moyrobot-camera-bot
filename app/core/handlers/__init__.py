from aiogram import Router
from app.core.handlers.main import router as main_router
from app.core.handlers.send_promo import send_promo_router


handlers_router = Router()
handlers_router.include_routers(main_router, send_promo_router)
