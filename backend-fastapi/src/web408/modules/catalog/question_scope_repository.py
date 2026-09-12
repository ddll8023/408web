"""题目科目与分类归属查询的持久化边界。"""
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.catalog.models import ExamCategory, Subject


class QuestionScopeRepository:
    """提供题目业务校验所需的科目和分类读取。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def subject_exists(self, subject_id: int) -> bool:
        result = await self.session.exec(
            select(Subject.id).where(Subject.id == subject_id)
        )
        return result.first() is not None

    async def category_names(self, subject_id: int) -> set[str]:
        result = await self.session.exec(
            select(ExamCategory.name).where(ExamCategory.subject_id == subject_id)
        )
        return set(result.all())
