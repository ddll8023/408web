"""模拟题查询用例。"""
from dataclasses import dataclass
from typing import List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.exceptions import NotFoundException
from web408.modules.auth.read_service import AuthReadService
from web408.modules.mock.models import MockQuestion
from web408.modules.catalog.read_service import CatalogReadService
from web408.modules.mock.mapper import to_mock_response
from web408.modules.mock.repository import MockQuery, MockRepository
from web408.modules.mock.read_service import MockReadService
from web408.modules.mock.schemas import (
    MockCategoryStatItem,
    MockCategoryStatsResponse,
    MockDuplicateCheckResponse,
    MockResponse,
    MockSourceItem,
    MockSourceStatResponse,
    MockSourcesResponse,
    MockSubjectStatItem,
    MockQueryParams,
    PaginatedMockResponse,
)
from web408.modules.question_content.serialization import parse_categories
from web408.schemas.common import PageInfo


@dataclass(frozen=True, slots=True)
class MockImageReferenceRead:
    """供媒体模块使用的模拟题文本只读数据。"""

    id: int
    question_number: int | None
    title: str | None
    source: str
    content: str
    answer: str | None
    options: str | None


class MockQueryService:
    """编排模拟题列表、来源/分类统计和详情查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = MockRepository(session)
        self.read_service = MockReadService(session)
        self.catalog_read_service = CatalogReadService(session)
        self.auth_read_service = AuthReadService(session)

    async def get_paginated(self, params: MockQueryParams) -> PaginatedMockResponse:
        """分页查询模拟题，并将父分类展开为完整子树范围。"""
        category_names: Optional[tuple[str, ...]] = None
        if params.category and params.subject_id is not None:
            category_names = tuple(
                await self.catalog_read_service.get_category_scope_names(
                    params.subject_id,
                    params.category,
                )
            )

        total, questions = await self.repository.list_paginated(
            MockQuery(
                page=params.page,
                page_size=params.page_size,
                source=params.source,
                category=params.category,
                subject_id=params.subject_id,
                no_category=params.no_category is True,
                keyword=params.keyword,
                sort_field=params.sort_field,
                sort_order=params.sort_order,
                category_names=category_names,
            )
        )
        data = await self._to_responses(questions)
        total_pages = (total + params.page_size - 1) // params.page_size if total else 0
        return PaginatedMockResponse(
            lists=data,
            pagination=PageInfo(
                page=params.page,
                page_size=params.page_size,
                total=total,
                total_pages=total_pages,
            ),
        )

    async def get_by_id(self, question_id: int) -> MockResponse:
        """按主键查询模拟题。"""
        question = await self.repository.get_by_id(question_id)
        if question is None:
            raise NotFoundException(f"模拟题不存在：ID={question_id}")
        return await self.to_response(question)

    async def check_duplicate(
        self,
        source: str,
        title: Optional[str],
        question_number: Optional[int],
        exclude_id: Optional[int] = None,
    ) -> MockDuplicateCheckResponse:
        """检查来源、标题和题号组合是否重复。"""
        existing = await self.repository.find_duplicate(
            source,
            title,
            question_number,
            exclude_id,
        )
        if existing is None:
            return MockDuplicateCheckResponse(is_duplicate=False)
        return MockDuplicateCheckResponse(
            is_duplicate=True,
            existing_question=await self.to_response(existing),
        )

    async def get_source_stats(
        self,
        category: Optional[str] = None,
    ) -> List[MockSourceStatResponse]:
        """按来源统计模拟题数量。"""
        return [
            MockSourceStatResponse(source=row.source, count=row.count)
            for row in await self.repository.get_source_stats(category)
        ]

    async def get_sources(self) -> MockSourcesResponse:
        """返回来源及其题目数量。"""
        return MockSourcesResponse(
            sources=[
                MockSourceItem(
                    source=row.source,
                    question_count=row.question_count,
                )
                for row in await self.repository.get_sources()
            ]
        )

    async def get_category_stats(self, subject_id: int) -> MockCategoryStatsResponse:
        """展开分类 JSON 并统计模拟题数量。"""
        questions = await self.repository.list_for_category_stats(subject_id)
        category_counts: dict[str, int] = {}
        question_ids: set[int] = set()
        for question in questions:
            question_ids.add(question.id)
            if not question.category:
                continue
            categories = parse_categories(question.category)
            if categories:
                for category in categories:
                    category_counts[category] = category_counts.get(category, 0) + 1

        subject_name = await self.catalog_read_service.get_subject_name(subject_id)
        return MockCategoryStatsResponse(
            subject_id=subject_id,
            subject_name=subject_name,
            stats=[
                MockCategoryStatItem(category_name=category, count=count)
                for category, count in sorted(category_counts.items())
            ],
            total_count=len(question_ids),
        )

    async def find_by_source(
        self,
        source: str,
        category: Optional[str] = None,
        subject_id: Optional[int] = None,
    ) -> List[MockResponse]:
        """按来源查询模拟题。"""
        questions = await self.repository.find_by_source(source, category, subject_id)
        return await self._to_responses(questions)

    async def find_categories_by_subject(self, subject_id: int) -> List[str]:
        """返回科目下模拟题实际使用的分类名称。"""
        category_set: set[str] = set()
        for raw_categories in await self.repository.list_category_values(subject_id):
            if not raw_categories:
                continue
            categories = parse_categories(raw_categories)
            if categories:
                category_set.update(categories)
        return sorted(category_set)

    async def count_by_subject(self) -> List[MockSubjectStatItem]:
        """组合目录和模拟题计数，保留名称排序、禁用科目及零题目科目。"""
        subjects = await self.catalog_read_service.list_subjects(order_by_name=True)
        counts = await self.read_service.count_by_subject({subject.id for subject in subjects})
        return [
            MockSubjectStatItem(
                subject_id=subject.id,
                subject_name=subject.name,
                count=counts.get(subject.id, 0),
            )
            for subject in subjects
        ]

    async def get_titles_by_source(self, source: str) -> List[str]:
        """返回指定来源下去重后的标题。"""
        return [
            title
            for title in await self.repository.get_titles_by_source(source)
            if title
        ]

    async def list_image_reference_texts(self) -> list[MockImageReferenceRead]:
        """返回媒体模块扫描图片引用所需的模拟题文本。"""
        return [
            MockImageReferenceRead(
                id=row.id,
                question_number=row.question_number,
                title=row.title,
                source=row.source,
                content=row.content,
                answer=row.answer,
                options=row.options,
            )
            for row in await self.repository.list_image_reference_texts()
        ]

    async def _to_responses(
        self,
        questions: list[MockQuestion],
    ) -> list[MockResponse]:
        """批量读取显示字段并转换题目响应。"""
        if not questions:
            return []
        subject_names = await self.catalog_read_service.get_subject_names(
            {question.subject_id for question in questions if question.subject_id is not None}
        )
        author_names = await self.auth_read_service.get_user_names(
            {question.author_id for question in questions if question.author_id is not None}
        )
        return [
            to_mock_response(
                question,
                subject_name=subject_names.get(question.subject_id),
                author_name=author_names.get(question.author_id),
            )
            for question in questions
        ]

    async def to_response(self, question: MockQuestion) -> MockResponse:
        """将模拟题实体转换为公开响应。"""
        responses = await self._to_responses([question])
        return responses[0]
