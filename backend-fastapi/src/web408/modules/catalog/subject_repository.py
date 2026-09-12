"""科目查询的持久化边界。"""
from typing import Any

from sqlmodel import and_, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.catalog.models import Subject


class SubjectRepository:
    """封装科目列表、统计和唯一性查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[Subject]:
        result = await self.session.exec(
            select(Subject).order_by(Subject.order_num, Subject.id)
        )
        return result.all()

    async def list_enabled(self) -> list[Subject]:
        """按目录顺序读取启用科目，不关联题库模型。"""
        result = await self.session.exec(
            select(Subject)
            .where(Subject.enabled.is_(True))
            .order_by(Subject.order_num, Subject.id)
        )
        return result.all()

    async def get_by_id(self, subject_id: int) -> Subject | None:
        result = await self.session.exec(
            select(Subject).where(Subject.id == subject_id)
        )
        return result.first()

    async def get_by_code(self, code: str) -> Subject | None:
        result = await self.session.exec(
            select(Subject).where(Subject.code == code)
        )
        return result.first()

    async def count_name_conflicts(
        self,
        name: str,
        *,
        exclude_id: int | None = None,
    ) -> int:
        conditions: list[Any] = [Subject.name == name]
        if exclude_id is not None:
            conditions.append(Subject.id != exclude_id)
        result = await self.session.exec(
            select(func.count()).select_from(Subject).where(and_(*conditions))
        )
        return result.one() or 0

    async def count_code_conflicts(
        self,
        code: str,
        *,
        exclude_id: int | None = None,
    ) -> int:
        conditions: list[Any] = [Subject.code == code]
        if exclude_id is not None:
            conditions.append(Subject.id != exclude_id)
        result = await self.session.exec(
            select(func.count()).select_from(Subject).where(and_(*conditions))
        )
        return result.one() or 0
