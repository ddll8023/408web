"""模拟题业务服务门面。

查询和写入职责拆分到专用 Service，保留原有 ``MockService`` 公共入口。
"""
from typing import List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.mock import (
    MockCategoryStatsResponse,
    MockCreateRequest,
    MockDuplicateCheckResponse,
    MockResponse,
    MockSourceStatResponse,
    MockSourcesResponse,
    MockSubjectStatItem,
    MockUpdateRequest,
    MockQueryParams,
    PaginatedMockResponse,
)
from app.services.mock_command_service import MockCommandService
from app.services.mock_query_service import MockQueryService


class MockService:
    """兼容 API 层的模拟题业务入口。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.query_service = MockQueryService(session)
        self.command_service = MockCommandService(session, self.query_service)

    async def get_paginated(self, params: MockQueryParams) -> PaginatedMockResponse:
        return await self.query_service.get_paginated(params)

    async def get_by_id(self, question_id: int) -> MockResponse:
        return await self.query_service.get_by_id(question_id)

    async def check_duplicate(
        self,
        source: str,
        title: Optional[str],
        question_number: Optional[int],
        exclude_id: Optional[int] = None,
    ) -> MockDuplicateCheckResponse:
        return await self.query_service.check_duplicate(
            source,
            title,
            question_number,
            exclude_id,
        )

    async def get_source_stats(
        self,
        category: Optional[str] = None,
    ) -> List[MockSourceStatResponse]:
        return await self.query_service.get_source_stats(category)

    async def get_sources(self) -> MockSourcesResponse:
        return await self.query_service.get_sources()

    async def get_category_stats(self, subject_id: int) -> MockCategoryStatsResponse:
        return await self.query_service.get_category_stats(subject_id)

    async def create(self, request: MockCreateRequest, author_id: int) -> MockResponse:
        return await self.command_service.create(request, author_id)

    async def update(
        self,
        question_id: int,
        request: MockUpdateRequest,
    ) -> MockResponse:
        return await self.command_service.update(question_id, request)

    async def delete(self, question_id: int) -> None:
        await self.command_service.delete(question_id)

    async def find_by_source(
        self,
        source: str,
        category: Optional[str] = None,
        subject_id: Optional[int] = None,
    ) -> List[MockResponse]:
        return await self.query_service.find_by_source(source, category, subject_id)

    async def find_categories_by_subject(self, subject_id: int) -> List[str]:
        return await self.query_service.find_categories_by_subject(subject_id)

    async def count_by_subject(self) -> List[MockSubjectStatItem]:
        return await self.query_service.count_by_subject()

    async def get_titles_by_source(self, source: str) -> List[str]:
        return await self.query_service.get_titles_by_source(source)
