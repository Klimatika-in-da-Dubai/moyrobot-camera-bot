from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.scheduler.update_db import setup_parser_job

from app.services.terminal.session import TerminalSession


def setup_scheduler(
    bot: Bot, terminal_sessions: list[TerminalSession], sessionmaker: async_sessionmaker
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    setup_parser_job(scheduler, terminal_sessions, sessionmaker)
    return scheduler
