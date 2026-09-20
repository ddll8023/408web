"""真题模块的底层公开读取边界，不依赖目录或 HTTP 响应编排。"""
from dataclasses import dataclass

from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.exam.repository import ExamRepository


@dataclass(frozen=True, slots=True)
class ExamCategoryReferenceRead:
    """目录统计所需的真题分类引用，只携带标识和原始 JSON。"""

    id: int
    category: str


@dataclass(frozen=True, slots=True)
class ExamSourceRead:
    """改编题来源解析所需的真题只读数据。"""

    id: int
    year: int
    question_number: int
    title: str | None
    question_type: str
    subject_id: int | None


class ExamReadService:
    """向目录用例提供分类引用和科目计数，复用调用方会话且不提交事务。"""

    def __init__(self, session: AsyncSession) -> None:
        """绑定真题持久化读取边界。"""
        self.repository = ExamRepository(session)

    async def list_question_categories(self, subject_id: int) -> list[ExamCategoryReferenceRead]:
        """转换为不可变引用 DTO，不向外暴露 ORM 或数据库行。"""
        rows = await self.repository.list_question_categories(subject_id)
        return [ExamCategoryReferenceRead(id=row.id, category=row.category) for row in rows]

    async def count_questions_with_categories(self, subject_id: int) -> int:
        """返回科目下分类字段非空的去重题目数。"""
        return await self.repository.count_questions_with_categories(subject_id)

    async def count_question_references(self, subject_id: int, category_name: str) -> int:
        """返回指定分类名称的引用数，供使用检查和删除保护调用。"""
        return await self.repository.count_question_references(subject_id, category_name)

    async def count_by_subject(self, subject_ids: set[int]) -> dict[int, int]:
        """批量返回科目题目数，未出现的科目由调用方补零。"""
        if not subject_ids:
            return {}
        rows = await self.repository.count_by_subject(subject_ids)
        return {row.subject_id: row.count for row in rows}

    async def resolve_sources(
        self,
        keys: set[tuple[int, int]],
    ) -> dict[tuple[int, int], ExamSourceRead]:
        """按「年份 + 题号」批量解析真题，未命中的键由调用方判定为未入库。"""
        rows = await self.repository.list_exam_refs(keys)
        return {
            (row.year, row.question_number): ExamSourceRead(
                id=row.id,
                year=row.year,
                question_number=row.question_number,
                title=row.title,
                question_type=row.question_type,
                subject_id=row.subject_id,
            )
            for row in rows
            if row.question_number is not None
        }

    async def list_question_numbers(
        self,
        years: set[int],
        subject_id: int | None = None,
    ) -> dict[int, list[int]]:
        """返回年份到题号的映射，缺失年份由调用方补空列表。"""
        rows = await self.repository.list_question_numbers(years, subject_id)
        numbers_by_year: dict[int, list[int]] = {}
        for row in rows:
            if row.question_number is None:
                continue
            numbers_by_year.setdefault(row.year, []).append(row.question_number)
        return numbers_by_year

    async def list_years(self, subject_id: int | None = None) -> list[int]:
        """返回真题库中已录入的年份，供改编覆盖统计使用。"""
        return await self.repository.list_years(subject_id)
