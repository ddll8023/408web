"""全局 HTTP 依赖。"""
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.connection import get_async_session


SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
