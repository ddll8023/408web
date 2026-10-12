"""自定义分类模块对其他业务模块公开的只读查询边界。"""
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.exceptions import ValidationException
from web408.modules.custom_category.repository import CustomCategoryRepository


class CustomCategoryReadService:
    """提供自定义分类数据的最小跨模块读取接口。"""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = CustomCategoryRepository(session)

    async def list_category_names(self, subject_id: int) -> set[str]:
        """返回科目下全部自定义分类名称。"""
        categories = await self.repository.list_by_subject(
            subject_id,
            include_subject=False,
        )
        return {category.name for category in categories}

    async def get_category_scope_names(
        self,
        subject_id: int,
        category_name: str,
    ) -> list[str]:
        """返回指定自定义分类及其全部启用子孙分类名称。"""
        return await self.repository.list_category_scope_names(
            subject_id,
            category_name,
        )

    async def validate_question_scope(
        self,
        subject_id: Optional[int],
        categories: Optional[list[str]],
        *,
        existing_subject_id: Optional[int] = None,
        existing_custom_categories: Optional[list[str]] = None,
    ) -> None:
        """校验题目的自定义分类归属，并保留历史标签兼容规则。"""
        if not categories:
            return
        if subject_id is None:
            raise ValidationException("选择自定义分类时必须指定科目")

        valid_names = await self.list_category_names(subject_id)
        invalid_names = [name for name in categories if name not in valid_names]
        legacy_unchanged = (
            existing_subject_id == subject_id
            and existing_custom_categories == categories
        )
        if invalid_names and not legacy_unchanged:
            raise ValidationException(
                f"自定义分类不属于指定科目或不存在: {', '.join(invalid_names)}"
            )
