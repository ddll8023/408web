"""认证模块对其他业务模块公开的只读用户边界。"""
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.auth.repository import UserRepository


class AuthReadService:
    """提供用户显示信息的批量只读查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = UserRepository(session)

    async def get_user_names(self, user_ids: set[int]) -> dict[int, str]:
        """按用户 ID 批量返回用户名。"""
        if not user_ids:
            return {}
        rows = await self.repository.list_user_names(user_ids)
        return {row.id: row.username for row in rows}
