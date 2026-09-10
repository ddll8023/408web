"""章节查询的持久化边界。"""
from typing import Any

from sqlmodel import and_, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.entities import Chapter, Subject


class ChapterRepository:
    """封装章节树和章节管理所需的数据库查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_subject(
        self,
        subject_id: int,
        *,
        enabled_only: bool = False,
    ) -> list[Chapter]:
        conditions: list[Any] = [Chapter.subject_id == subject_id]
        if enabled_only:
            conditions.append(Chapter.enabled.is_(True))
        result = await self.session.exec(
            select(Chapter)
            .where(*conditions)
            .order_by(Chapter.order_num, Chapter.id)
        )
        return result.all()

    async def get_by_id(self, chapter_id: int) -> Chapter | None:
        result = await self.session.exec(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        return result.first()

    async def get_subject(self, subject_id: int) -> Subject | None:
        result = await self.session.exec(
            select(Subject).where(Subject.id == subject_id)
        )
        return result.first()

    async def count_name_conflicts(
        self,
        subject_id: int,
        parent_id: int | None,
        name: str,
        *,
        exclude_id: int | None = None,
    ) -> int:
        conditions: list[Any] = [
            Chapter.subject_id == subject_id,
            Chapter.parent_id == parent_id,
            Chapter.name == name,
        ]
        if exclude_id is not None:
            conditions.append(Chapter.id != exclude_id)
        result = await self.session.exec(
            select(func.count()).select_from(Chapter).where(and_(*conditions))
        )
        return result.one() or 0

    async def list_descendants(self, chapter_id: int) -> set[int]:
        descendants: set[int] = set()
        frontier = {chapter_id}
        while frontier:
            result = await self.session.exec(
                select(Chapter.id).where(Chapter.parent_id.in_(frontier))
            )
            children = set(result.all()) - descendants
            descendants.update(children)
            frontier = children
        return descendants
