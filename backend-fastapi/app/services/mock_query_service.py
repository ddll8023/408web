"""模拟题查询用例。"""
import json
from typing import List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.entities import MockQuestion
from app.repositories.mock_repository import MockQuery, MockRepository
from app.schemas.common import PageInfo
from app.schemas.mock import (
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
from app.services.question_mapping import parse_categories, parse_options


class MockQueryService:
    """编排模拟题列表、来源/分类统计和详情查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = MockRepository(session)

    async def get_paginated(self, params: MockQueryParams) -> PaginatedMockResponse:
        """分页查询模拟题。"""
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
            )
        )
        data = [await self.to_response(question) for question in questions]
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
            try:
                categories = json.loads(question.category)
            except json.JSONDecodeError:
                continue
            if isinstance(categories, list):
                for category in categories:
                    category_counts[category] = category_counts.get(category, 0) + 1

        subject = await self.repository.get_subject(subject_id)
        return MockCategoryStatsResponse(
            subject_id=subject_id,
            subject_name=subject.name if subject else None,
            stats=[
                MockCategoryStatItem(category=category, count=count)
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
        return [await self.to_response(question) for question in questions]

    async def find_categories_by_subject(self, subject_id: int) -> List[str]:
        """返回科目下模拟题实际使用的分类名称。"""
        category_set: set[str] = set()
        for raw_categories in await self.repository.list_category_values(subject_id):
            if not raw_categories:
                continue
            try:
                categories = json.loads(raw_categories)
            except json.JSONDecodeError:
                continue
            if isinstance(categories, list):
                category_set.update(categories)
        return sorted(category_set)

    async def count_by_subject(self) -> List[MockSubjectStatItem]:
        """按科目统计模拟题数量。"""
        return [
            MockSubjectStatItem(
                subject_id=row.id,
                subject_name=row.name,
                count=row.count or 0,
            )
            for row in await self.repository.count_by_subject()
        ]

    async def get_titles_by_source(self, source: str) -> List[str]:
        """返回指定来源下去重后的标题。"""
        return [
            title
            for title in await self.repository.get_titles_by_source(source)
            if title
        ]

    async def to_response(self, question: MockQuestion) -> MockResponse:
        """将模拟题实体转换为公开响应。"""
        subject_name = None
        if question.subject_id:
            subject = await self.repository.get_subject(question.subject_id)
            subject_name = subject.name if subject else None
        author_name = None
        if question.author_id:
            author = await self.repository.get_author(question.author_id)
            author_name = author.username if author else None
        return MockResponse(
            id=question.id,
            source=question.source,
            question_number=question.question_number,
            question_type=question.question_type,
            title=question.title,
            content=question.content,
            options=parse_options(question.options),
            answer=question.answer,
            category=parse_categories(question.category),
            subject_id=question.subject_id,
            subject_name=subject_name,
            difficulty=question.difficulty,
            author_id=question.author_id,
            author_name=author_name,
            create_time=question.create_time.isoformat() if question.create_time else None,
            update_time=question.update_time.isoformat() if question.update_time else None,
        )
