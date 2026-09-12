"""分类查询、树形组装和引用统计用例。"""
from collections import defaultdict
from typing import List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.exceptions import NotFoundException
from web408.modules.catalog.models import ExamCategory
from web408.modules.catalog.category_repository import CategoryRepository
from web408.modules.catalog.schemas.category import (
    ExamCategoryResponse,
    ExamCategoryStatResponse,
    ExamCategoryTreeResponse,
    ExamCategoryUsageResponse,
    SubjectStatItem,
)
from web408.modules.exam.read_service import ExamReadService
from web408.modules.mock.read_service import MockReadService
from web408.modules.question_content.serialization import parse_categories


class CategoryQueryService:
    """编排分类列表、树形结构和使用统计。"""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = CategoryRepository(session)
        self.exam_read_service = ExamReadService(session)
        self.mock_read_service = MockReadService(session)

    async def get_all_categories(
        self,
        question_type: str = "exam",
    ) -> List[ExamCategoryResponse]:
        categories = await self.repository.list_all()
        responses = [self.to_response(category) for category in categories]
        await self._apply_question_counts(responses, question_type)
        return responses

    async def get_enabled_categories_by_subject(
        self,
        subject_id: int,
    ) -> List[ExamCategoryResponse]:
        categories = await self.repository.list_by_subject(
            subject_id,
            enabled_only=True,
        )
        return [self.to_response(category) for category in categories]

    async def get_categories_by_subject(
        self,
        subject_id: int,
        enabled_only: bool = False,
        question_type: str = "exam",
    ) -> List[ExamCategoryResponse]:
        categories = await self.repository.list_by_subject(
            subject_id,
            enabled_only=enabled_only,
        )
        responses = [self.to_response(category) for category in categories]
        await self._apply_question_counts(responses, question_type)
        return responses

    async def get_category_tree(
        self,
        subject_id: int,
        enabled_only: bool = False,
        question_type: str = "exam",
    ) -> List[ExamCategoryTreeResponse]:
        categories = await self.get_categories_by_subject(
            subject_id,
            enabled_only,
            question_type,
        )
        return self._build_tree(categories) if categories else []

    async def get_enabled_category_tree_with_stats(
        self,
        subject_id: int,
        question_type: str = "exam",
    ) -> List[ExamCategoryTreeResponse]:
        categories = await self.get_categories_by_subject(
            subject_id,
            enabled_only=True,
            question_type=question_type,
        )
        if not categories:
            return []
        return self._filter_empty_categories(self._build_tree(categories))

    async def get_category_stats(
        self,
        question_type: str = "exam",
    ) -> ExamCategoryStatResponse:
        subject_stats: list[SubjectStatItem] = []
        question_reader = self.mock_read_service if question_type == "mock" else self.exam_read_service
        total_questions = 0
        total_categories = 0
        enabled_categories = 0
        for subject in await self.repository.list_subjects():
            category_count = await self.repository.count_categories(subject.id)
            enabled_count = await self.repository.count_categories(
                subject.id,
                enabled_only=True,
            )
            question_count = await question_reader.count_questions_with_categories(subject.id)
            subject_stats.append(
                SubjectStatItem(
                    subject_id=subject.id,
                    subject_name=subject.name,
                    category_count=category_count,
                    enabled_category_count=enabled_count,
                    question_count=question_count,
                )
            )
            total_categories += category_count
            enabled_categories += enabled_count
            total_questions += question_count
        return ExamCategoryStatResponse(
            subject_stats=subject_stats,
            total_question_count=total_questions,
            total_categories=total_categories,
            enabled_categories=enabled_categories,
            question_type=question_type,
        )

    async def get_available_parent_categories(
        self,
        subject_id: int,
        exclude_id: Optional[int] = None,
    ) -> List[ExamCategoryResponse]:
        categories = await self.repository.list_parents_for_subject(subject_id)
        excluded = {exclude_id} if exclude_id else set()
        if exclude_id:
            excluded.update(await self.get_descendant_ids(exclude_id))
        return [
            self.to_response(category)
            for category in categories
            if category.id not in excluded
        ]

    async def check_category_usage(self, category_id: int) -> int:
        category = await self._get_category_or_raise(category_id)
        return (
            await self.exam_read_service.count_question_references(
                category.subject_id,
                category.name,
            )
            + await self.mock_read_service.count_question_references(
                category.subject_id,
                category.name,
            )
        )

    async def get_category_usage(self, category_id: int) -> ExamCategoryUsageResponse:
        category = await self._get_category_or_raise(category_id)
        question_count = await self.exam_read_service.count_question_references(
            category.subject_id,
            category.name,
        )
        mock_count = await self.mock_read_service.count_question_references(
            category.subject_id,
            category.name,
        )
        has_children = await self.repository.count_children(category_id) > 0
        return ExamCategoryUsageResponse(
            id=category.id,
            name=category.name,
            has_children=has_children,
            question_count=question_count,
            mock_count=mock_count,
            can_delete=not has_children and question_count == 0 and mock_count == 0,
        )

    async def get_by_id(self, category_id: int) -> ExamCategoryResponse:
        category = await self._get_category_or_raise(category_id, include_subject=True)
        return self.to_response(category)

    async def get_descendant_ids(self, category_id: int) -> set[int]:
        return await self.repository.list_descendants(category_id)

    async def _get_category_or_raise(
        self,
        category_id: int,
        *,
        include_subject: bool = False,
    ) -> ExamCategory:
        category = await self.repository.get_by_id(
            category_id,
            include_subject=include_subject,
        )
        if category is None:
            raise NotFoundException(f"分类不存在：ID={category_id}")
        return category

    async def _apply_question_counts(
        self,
        categories: List[ExamCategoryResponse],
        question_type: str,
    ) -> None:
        question_reader = self.mock_read_service if question_type == "mock" else self.exam_read_service
        categories_by_subject: dict[int, list[ExamCategoryResponse]] = defaultdict(list)
        for category in categories:
            categories_by_subject[category.subject_id].append(category)
        for subject_categories in categories_by_subject.values():
            rows = await question_reader.list_question_categories(subject_categories[0].subject_id)
            question_ids_by_category: dict[str, set[int]] = defaultdict(set)
            for row in rows:
                for name in set(parse_categories(row.category)):
                    question_ids_by_category[name].add(row.id)
            children_map: dict[Optional[int], list[ExamCategoryResponse]] = defaultdict(list)
            for category in subject_categories:
                category.question_count = len(
                    question_ids_by_category.get(category.name, set())
                )
                children_map[category.parent_id].append(category)
            subtree_cache: dict[int, set[int]] = {}
            visiting: set[int] = set()

            def collect(category: ExamCategoryResponse) -> set[int]:
                if category.id in subtree_cache:
                    return subtree_cache[category.id]
                if category.id in visiting:
                    return set(question_ids_by_category.get(category.name, set()))
                visiting.add(category.id)
                question_ids = set(question_ids_by_category.get(category.name, set()))
                for child in children_map.get(category.id, []):
                    question_ids.update(collect(child))
                visiting.remove(category.id)
                subtree_cache[category.id] = question_ids
                category.subtree_question_count = len(question_ids)
                return question_ids

            for category in subject_categories:
                collect(category)

    def _build_tree(
        self,
        categories: List[ExamCategoryResponse],
    ) -> List[ExamCategoryTreeResponse]:
        category_map = {
            category.id: ExamCategoryTreeResponse(
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
                question_count=category.question_count,
                subtree_question_count=category.subtree_question_count,
                children=[],
            )
            for category in categories
        }
        children_map: dict[Optional[int], list[ExamCategoryTreeResponse]] = defaultdict(list)
        for category in category_map.values():
            children_map[category.parent_id].append(category)
        tree: list[ExamCategoryTreeResponse] = []
        for category in category_map.values():
            if category.parent_id is None:
                self._build_children_recursively(category, children_map)
                tree.append(category)
        tree.sort(key=lambda category: category.order_num)
        return tree

    def _build_children_recursively(
        self,
        parent: ExamCategoryTreeResponse,
        children_map: dict[Optional[int], list[ExamCategoryTreeResponse]],
    ) -> None:
        children = children_map.get(parent.id, [])
        for child in children:
            self._build_children_recursively(child, children_map)
        parent.children = children

    def _filter_empty_categories(
        self,
        categories: List[ExamCategoryTreeResponse],
    ) -> List[ExamCategoryTreeResponse]:
        result: list[ExamCategoryTreeResponse] = []
        for category in categories:
            category.children = self._filter_empty_categories(category.children)
            if (category.question_count or 0) > 0 or category.children:
                result.append(category)
        return result

    @staticmethod
    def to_response(category: ExamCategory) -> ExamCategoryResponse:
        """将分类实体转换为公开响应。"""
        return ExamCategoryResponse(
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
            question_count=None,
            subtree_question_count=None,
            create_time=category.create_time.isoformat() if category.create_time else None,
            update_time=category.update_time.isoformat() if category.update_time else None,
        )
