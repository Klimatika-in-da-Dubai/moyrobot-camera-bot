import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.core.handlers import handlers_router
from app.core.middlewares.camera_streams import CamerasStreamsMiddleware
from app.core.middlewares.config import ConfigMiddleware
from app.core.middlewares.db import AddUserDbMiddleware, DbSessionMiddleware
from app.core.middlewares.ga4 import GA4Middleware
from app.core.middlewares.metrics import UsageMetricsMiddleware
from app.services.cameras.camera_stream import CameraStream
from app.services.database.connector import setup_get_pool

from app.settings.config import Config, load_config

logging.basicConfig(
    format=f"%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s",
    level=logging.DEBUG,
)


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(handlers_router)


def setup_middlewares(
    dp: Dispatcher,
    session: async_sessionmaker,
    config: Config,
    cameras: list[CameraStream],
):
    """
    Setup middlewares for dispatcher and returns middlewares which need to be used in other functions
    """
    dp.update.middleware(DbSessionMiddleware(session))
    dp.update.middleware(ConfigMiddleware(config))
    dp.update.middleware(CamerasStreamsMiddleware(cameras))

    dp.message.middleware(GA4Middleware(config.ga4))
    dp.message.middleware(AddUserDbMiddleware(session))
    dp.message.middleware(UsageMetricsMiddleware(session))


def get_cameras(config: Config) -> list[CameraStream]:
    return [
        CameraStream(
            camera_uri=camera_config.camera_uri,
            name=camera_config.name,
            description=camera_config.description,
            tags=camera_config.tags,
        )
        for camera_config in config.cameras
    ]


async def main():
    config: Config = load_config()
    bot = Bot(config.bot.token, parse_mode=config.bot.parse_mode)
    session = await setup_get_pool(config.db.uri)
    dp = Dispatcher(storage=RedisStorage.from_url(config.redis.url))
    cameras = get_cameras(config)

    setup_routers(dp)
    setup_middlewares(dp, session, config, cameras)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await dp.storage.close()


if __name__ == "__main__":
    asyncio.run(main())
