from aiogram import Router
from app.core.handlers.admin.promo import promo_router
from app.core.handlers.admin.tests import tests_router
from app.core.handlers.admin.errors import errors_router

admin_router = Router()

admin_router.include_routers(promo_router, tests_router, errors_router)
