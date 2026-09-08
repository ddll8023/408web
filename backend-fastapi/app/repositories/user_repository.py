"""用户读取的持久化边界。"""
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.entities import User


class UserRepository:
    """封装认证流程所需的用户查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        """按主键查询用户。"""
        result = await self.session.exec(select(User).where(User.id == user_id))
        return result.first()

    async def get_by_username(self, username: str) -> User | None:
        """按用户名查询用户。"""
        result = await self.session.exec(
            select(User).where(User.username == username)
        )
        return result.first()
