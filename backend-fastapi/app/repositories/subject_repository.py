"""科目查询的持久化边界。"""
from typing import Any, Optional

from sqlmodel import select, func, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.entities import ExamQuestion, Subject


class SubjectRepository:
    """封装科目列表、统计和唯一性查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[Subject]:
        result = await self.session.exec(
            select(Subject).order_by(Subject.order_num, Subject.id)
        )
        return result.all()

    async def list_enabled_with_counts(self) -> list[Any]:
        result = await self.session.exec(
            select(
                Subject.id,
                Subject.name,
                Subject.code,
                Subject.description,
                Subject.order_num,
                Subject.enabled,
                func.count(ExamQuestion.id).label("question_count"),
            )
            .outerjoin(ExamQuestion, Subject.id == ExamQuestion.subject_id)
            .where(Subject.enabled == True)
            .group_by(Subject.id)
            .order_by(Subject.order_num, Subject.id)
        )
        return result.all()

    async def get_by_id(self, subject_id: int) -> Optional[Subject]:
        result = await self.session.exec(
            select(Subject).where(Subject.id == subject_id)
        )
        return result.first()

    async def get_by_code(self, code: str) -> Optional[Subject]:
        result = await self.session.exec(
            select(Subject).where(Subject.code == code)
        )
        return result.first()

    async def count_name_conflicts(
        self,
        name: str,
        *,
        exclude_id: Optional[int] = None,
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
        exclude_id: Optional[int] = None,
    ) -> int:
        conditions: list[Any] = [Subject.code == code]
        if exclude_id is not None:
            conditions.append(Subject.id != exclude_id)
        result = await self.session.exec(
            select(func.count()).select_from(Subject).where(and_(*conditions))
        )
        return result.one() or 0
