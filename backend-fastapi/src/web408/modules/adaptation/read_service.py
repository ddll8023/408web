"""改编题模块的底层公开读取边界，不依赖目录或 HTTP 响应编排。"""
from dataclasses import dataclass

from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.adaptation.repository import AdaptationRepository


@dataclass(frozen=True, slots=True)
class AdaptationCategoryReferenceRead:
    """目录统计所需的改编题分类引用，只携带标识和原始 JSON。"""

    id: int
    category: str


class AdaptationReadService:
    """向目录用例提供分类引用和科目计数，复用调用方会话且不提交事务。"""

    def __init__(self, session: AsyncSession) -> None:
        """绑定改编题持久化读取边界。"""
        self.repository = AdaptationRepository(session)

    async def list_question_categories(
        self,
        subject_id: int,
    ) -> list[AdaptationCategoryReferenceRead]:
        """转换为不可变引用 DTO，不向外暴露 ORM 或数据库行。"""
        rows = await self.repository.list_question_categories(subject_id)
        return [AdaptationCategoryReferenceRead(id=row.id, category=row.category) for row in rows]

    async def count_questions_with_categories(self, subject_id: int) -> int:
        """返回科目下分类字段非空的去重题目数。"""
        return await self.repository.count_questions_with_categories(subject_id)

    async def count_question_references(self, subject_id: int, category_name: str) -> int:
        """返回指定分类名称的引用数，供使用检查和删除保护调用。"""
        return await self.repository.count_question_references(subject_id, category_name)
