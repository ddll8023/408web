"""自定义分类查询、树形组装和科目统计用例。"""
from collections import defaultdict
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.custom_category.models import CustomCategory
from web408.modules.custom_category.repository import CustomCategoryRepository
from web408.modules.custom_category.schemas import (
    CustomCategoryResponse,
    CustomCategoryStatResponse,
    CustomCategorySubjectStatItem,
    CustomCategoryTreeResponse,
)


class CustomCategoryQueryService:
    """编排自定义分类列表、树形结构和科目统计。"""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = CustomCategoryRepository(session)

    async def get_category_tree(
        self,
        subject_id: int,
        *,
        enabled_only: bool = False,
    ) -> list[CustomCategoryTreeResponse]:
        """返回指定科目的自定义分类树。"""
        categories = await self.repository.list_by_subject(
            subject_id,
            enabled_only=enabled_only,
        )
        if not categories:
            return []
        responses = [self.to_response(category) for category in categories]
        return self.build_tree(responses)

    async def get_categories_by_subject(
        self,
        subject_id: int,
    ) -> list[CustomCategoryResponse]:
        """返回指定科目的扁平自定义分类列表。"""
        categories = await self.repository.list_by_subject(subject_id)
        return [self.to_response(category) for category in categories]

    async def get_subject_stats(self) -> CustomCategoryStatResponse:
        """按科目统计自定义分类数量，供管理页筛选栏使用。"""
        subject_stats: list[CustomCategorySubjectStatItem] = []
        total_categories = 0
        enabled_categories = 0
        for subject in await self.repository.list_subjects():
            category_count = await self.repository.count_categories(subject.id)
            enabled_count = await self.repository.count_categories(
                subject.id,
                enabled_only=True,
            )
            subject_stats.append(
                CustomCategorySubjectStatItem(
                    subject_id=subject.id,
                    subject_name=subject.name,
                    category_count=category_count,
                    enabled_category_count=enabled_count,
                )
            )
            total_categories += category_count
            enabled_categories += enabled_count
        return CustomCategoryStatResponse(
            subject_stats=subject_stats,
            total_categories=total_categories,
            enabled_categories=enabled_categories,
        )

    async def get_available_parent_categories(
        self,
        subject_id: int,
        exclude_id: Optional[int] = None,
    ) -> list[CustomCategoryResponse]:
        """返回可作为父级的分类，排除自身及其全部子孙。"""
        categories = await self.repository.list_by_subject(subject_id)
        excluded = {exclude_id} if exclude_id else set()
        if exclude_id:
            excluded.update(await self.get_descendant_ids(exclude_id))
        return [
            self.to_response(category)
            for category in categories
            if category.id not in excluded
        ]

    async def get_descendant_ids(self, category_id: int) -> set[int]:
        """返回分类的全部子孙 ID。"""
        return await self.repository.list_descendants(category_id)

    @staticmethod
    def to_response(category: CustomCategory) -> CustomCategoryResponse:
        """将自定义分类实体转换为公开响应。"""
        return CustomCategoryResponse(
            id=category.id,
            subject_id=category.subject_id,
            subject_name=category.subject.name if category.subject else None,
            parent_id=category.parent_id,
            parent_name=None,
            name=category.name,
            code=category.code,
            description=category.description,
            order_num=category.order_num,
            enabled=category.enabled,
            create_time=category.create_time.isoformat() if category.create_time else None,
            update_time=category.update_time.isoformat() if category.update_time else None,
        )

    def build_tree(
        self,
        categories: list[CustomCategoryResponse],
    ) -> list[CustomCategoryTreeResponse]:
        """把扁平分类列表组装成按顺序排列的树。"""
        category_map = {
            category.id: CustomCategoryTreeResponse(
                id=category.id,
                subject_id=category.subject_id,
                subject_name=category.subject_name,
                parent_id=category.parent_id,
                parent_name=category.parent_name,
                name=category.name,
                code=category.code,
                description=category.description,
                order_num=category.order_num,
                enabled=category.enabled,
                create_time=category.create_time,
                update_time=category.update_time,
                children=[],
            )
            for category in categories
        }
        children_map: dict[Optional[int], list[CustomCategoryTreeResponse]] = defaultdict(list)
        for category in category_map.values():
            children_map[category.parent_id].append(category)
        tree: list[CustomCategoryTreeResponse] = []
        for category in category_map.values():
            if category.parent_id is None:
                self._build_children_recursively(category, children_map)
                tree.append(category)
        tree.sort(key=lambda category: category.order_num)
        return tree

    def _build_children_recursively(
        self,
        parent: CustomCategoryTreeResponse,
        children_map: dict[Optional[int], list[CustomCategoryTreeResponse]],
    ) -> None:
        """递归挂载子分类。"""
        children = children_map.get(parent.id, [])
        for child in children:
            self._build_children_recursively(child, children_map)
        parent.children = children
