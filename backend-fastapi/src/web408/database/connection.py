"""异步 SQLite 引擎、建表入口和会话生命周期。"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Protocol

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.config import settings


DATABASE_URL = settings.database.database_url


class SqliteCursor(Protocol):
    """SQLite DB-API 游标的最小接口。"""

    def execute(self, statement: str) -> object: ...

    def close(self) -> None: ...


class SqliteConnection(Protocol):
    """SQLite DB-API 连接的最小接口。"""

    def cursor(self) -> SqliteCursor: ...


engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 5},
    echo=False,
)


if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine.sync_engine, "connect")
    def configure_sqlite_connection(
        dbapi_connection: SqliteConnection,
        _connection_record: object,
    ) -> None:
        """为每个 SQLite 连接启用外键、WAL 和忙等待。"""
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
        finally:
            cursor.close()


async def init_db() -> None:
    """按当前 SQLModel 定义创建缺失表。"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """提供每请求独立的异步数据库会话，不隐式提交业务写入。"""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            if session.in_transaction():
                await session.rollback()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """提供非 FastAPI 场景使用的异步会话上下文，不隐式提交。"""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            if session.in_transaction():
                await session.rollback()


def get_db_url() -> str:
    """获取数据库连接 URL。"""
    return DATABASE_URL
