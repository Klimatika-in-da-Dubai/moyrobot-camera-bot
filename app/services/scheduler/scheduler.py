from sqlalchemy.ext.asyncio import async_sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.scheduler.update_db import setup_update_db_job

from app.services.terminal.session import TerminalSession


def setup_scheduler(
    terminal_sessions: list[TerminalSession], sessionmaker: async_sessionmaker
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    setup_update_db_job(scheduler, terminal_sessions, sessionmaker)
    return scheduler
