from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
    AsyncSession
)
from core.config import settings
from asyncio import current_task


class DataBaseHelper:
    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(
            url=url,
            echo=echo,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def get_scoped_session(self):
        session = async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task,   # 🔹 Muhim joy shu!
        )
        return session

    async def session_dependency(self) -> AsyncSession:
        async_session = self.get_scoped_session()
        async with async_session() as session:
            yield session
            await async_session.remove()


db_helper = DataBaseHelper(
    settings.db_url,
    settings.db_echo,
)
