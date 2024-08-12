"""Модуль для настройки подключения к базе данных и создания сессий."""
from contextlib import asynccontextmanager

from sqlalchemy import MetaData, NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DB_USER, DB_NAME, DB_PORT, DB_HOST, DB_PASS



DATABASE_URL = (
        f"postgresql+asyncpg://" f"{DB_USER}:{DB_PASS}@{DB_HOST}:"
        f"{DB_PORT}/{DB_NAME}"
)

metadata = MetaData()
Base = declarative_base(metadata=metadata)

engine = create_async_engine(DATABASE_URL, echo=True, poolclass=NullPool)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@asynccontextmanager
async def get_async_session() -> AsyncSession:
    """
    Асинхронный контекстный менеджер для получения сессии базы данных.

    Данный контекстный менеджер предоставляет асинхронную сессию для работы с базой данных.
    Он автоматически управляет началом и завершением сессии.

    Использование:
        async with get_async_session() as session:
            # Выполнение операций с базой данных
            ...

    Возвращает:
        AsyncSession: Асинхронная сессия для взаимодействия с базой данных.

    Примечание:
        После завершения блока кода, сессия автоматически закрывается,
        что позволяет избежать утечек ресурсов и обеспечить корректное завершение работы с базой данных.
    """
    async with AsyncSessionLocal() as session:
        yield session