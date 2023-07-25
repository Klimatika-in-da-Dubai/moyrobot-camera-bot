from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


async def setup_get_pool(db_uri: str) -> async_sessionmaker:
    """
    Setup postgres database, creates tables if not exists. Connect to database.
    :param db_uri: postgres dsn
    :return sessionmaker: provides to bot instance to manage sessions.
    """

    engine = create_async_engine(db_uri, future=True)

    sessionmaker_ = async_sessionmaker(engine, expire_on_commit=False, future=True)
    return sessionmaker_
