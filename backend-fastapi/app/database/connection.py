"""
数据库连接与会话管理模块
使用 SQLModel + aiosqlite 实现异步数据库操作
"""
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from app.config.settings import settings


# SQLite 数据库连接配置
# 注意：SQLite 在多进程环境下有限制，生产环境建议使用 MySQL/PostgreSQL
DATABASE_URL = settings.database.database_url

# 创建异步引擎
# connect_args 用于传递特定驱动的连接参数
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # SQL日志由服务层统一记录，此处关闭
    pool_pre_ping=True,  # 连接前健康检查
)


async def init_db():
    """
    初始化数据库
    在应用启动时调用，创建所有表结构
    """
    # SQLModel.metadata 包含所有定义的表模型
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


def get_session():
    """获取数据库会话（同步版本，用于非异步场景）"""
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话
    用作 FastAPI 依赖注入
    """
    async with AsyncSession(engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    异步上下文管理器方式的数据库会话
    用于非 FastAPI 依赖注入场景
    """
    async with AsyncSession(engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_url() -> str:
    """获取数据库连接 URL"""
    return DATABASE_URL
