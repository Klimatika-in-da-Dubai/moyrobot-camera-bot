from aiogram import Router
from app.core.handlers.main import router as main_router


handlers_router = Router()
handlers_router.include_routers(main_router)
