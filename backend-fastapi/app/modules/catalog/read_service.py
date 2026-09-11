"""目录模块对其他业务模块公开的只读查询边界。"""
from dataclasses import dataclass
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.modules.catalog.category_repository import CategoryRepository
from app.modules.catalog.question_scope_repository import QuestionScopeRepository


@dataclass(frozen=True, slots=True)
class CatalogSubjectRead:
    """供其他模块使用的科目只读数据。"""

    id: int
    name: str


@dataclass(frozen=True, slots=True)
class CatalogCategoryRead:
    """供其他模块使用的分类只读数据。"""

    id: int
    subject_id: int
    parent_id: int | None
    name: str
    order_num: int
    enabled: bool


class CatalogReadService:
    """提供目录数据的最小跨模块读取接口。"""

    def __init__(self, session: AsyncSession) -> None:
        self.category_repository = CategoryRepository(session)
        self.scope_repository = QuestionScopeRepository(session)

    async def subject_exists(self, subject_id: int) -> bool:
        """判断科目是否存在。"""
        return await self.scope_repository.subject_exists(subject_id)

    async def list_subjects(self) -> list[CatalogSubjectRead]:
        """返回全部科目的只读数据。"""
        subjects = await self.category_repository.list_subjects()
        return [
            CatalogSubjectRead(id=subject.id, name=subject.name)
            for subject in subjects
            if subject.id is not None
        ]

    async def get_subject_name(self, subject_id: int | None) -> str | None:
        """按科目 ID 返回科目名称。"""
        if subject_id is None:
            return None
        subject = await self.category_repository.get_subject(subject_id)
        return subject.name if subject else None

    async def get_subject_names(self, subject_ids: set[int]) -> dict[int, str]:
        """按科目 ID 批量返回科目名称。"""
        if not subject_ids:
            return {}
        rows = await self.category_repository.list_subject_names(subject_ids)
        return {row.id: row.name for row in rows}

    async def list_categories(
        self,
        subject_id: int | None = None,
    ) -> list[CatalogCategoryRead]:
        """返回分类统计所需的只读数据。"""
        categories = (
            await self.category_repository.list_all()
            if subject_id is None
            else await self.category_repository.list_by_subject(
                subject_id,
                include_subject=False,
            )
        )
        return [
            CatalogCategoryRead(
                id=category.id,
                subject_id=category.subject_id,
                parent_id=category.parent_id,
                name=category.name,
                order_num=category.order_num,
                enabled=category.enabled,
            )
            for category in categories
            if category.id is not None
        ]

    async def get_category_scope_names(
        self,
        subject_id: int,
        category_name: str,
    ) -> list[str]:
        """返回指定分类及其启用子孙分类名称。"""
        return await self.category_repository.list_category_scope_names(
            subject_id,
            category_name,
        )

    async def validate_question_scope(
        self,
        subject_id: Optional[int],
        categories: Optional[list[str]],
        *,
        existing_subject_id: Optional[int] = None,
        existing_categories: Optional[list[str]] = None,
    ) -> None:
        """校验题目的科目与分类归属，并保留历史分类兼容规则。"""
        if subject_id is not None and not await self.subject_exists(subject_id):
            raise NotFoundException("科目")

        if not categories:
            return
        if subject_id is None:
            raise ValidationException("选择分类时必须指定科目")

        valid_names = await self.scope_repository.category_names(subject_id)
        invalid_names = [name for name in categories if name not in valid_names]
        legacy_unchanged = (
            existing_subject_id == subject_id and existing_categories == categories
        )
        if invalid_names and not legacy_unchanged:
            raise ValidationException(
                f"分类不属于指定科目或不存在: {', '.join(invalid_names)}"
            )
