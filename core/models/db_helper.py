from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.config import settings
from sqlalchemy.orm import sessionmaker




class DataBaseHelper:
    def __init__(self, url:str, echo:bool = False):
        self.engine = create_async_engine(
            url = url,
            echo = echo,
        )
        self.session_factory  = async_sessionmaker(
            bind=self.engine,
            autoflush = False,
            autocommit = False,
            expire_on_commit = False,

        )
db_helper = DataBaseHelper(
    settings.db_url,
    settings.db_echo,
)


