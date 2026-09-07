"""真题业务服务门面。

查询、写入和导出分别由专用 Service 负责，保留原有 ``ExamService`` 公共入口。
"""
from typing import List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.exam import (
    ExamCategoryStatsResponse,
    ExamCreateRequest,
    ExamDuplicateCheckResponse,
    ExamIndexResponse,
    ExamNavItem,
    ExamResponse,
    ExamUpdateRequest,
    ExamYearStatResponse,
    ExamQueryParams,
    ExportResultResponse,
    PaginatedExamResponse,
)
from app.services.exam_command_service import ExamCommandService
from app.services.exam_export_service import ExamExportService
from app.services.exam_query_service import ExamQueryService


class ExamService:
    """兼容 API 层的真题业务入口。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.query_service = ExamQueryService(session)
        self.command_service = ExamCommandService(session, self.query_service)
        self.export_service = ExamExportService(session)

    async def get_paginated(self, params: ExamQueryParams) -> PaginatedExamResponse:
        return await self.query_service.get_paginated(params)

    async def get_by_id(self, question_id: int) -> ExamResponse:
        return await self.query_service.get_by_id(question_id)

    async def check_duplicate(
        self,
        year: int,
        question_number: Optional[int],
        exclude_id: Optional[int] = None,
    ) -> ExamDuplicateCheckResponse:
        return await self.query_service.check_duplicate(
            year,
            question_number,
            exclude_id,
        )

    async def get_year_stats(
        self,
        category: Optional[str] = None,
    ) -> List[ExamYearStatResponse]:
        return await self.query_service.get_year_stats(category)

    async def get_category_stats(
        self,
        subject_id: Optional[int] = None,
    ) -> ExamCategoryStatsResponse:
        return await self.query_service.get_category_stats(subject_id)

    async def get_index(self, subject_id: Optional[int] = None) -> ExamIndexResponse:
        return await self.query_service.get_index(subject_id)

    async def create(self, request: ExamCreateRequest, author_id: int) -> ExamResponse:
        return await self.command_service.create(request, author_id)

    async def update(
        self,
        question_id: int,
        request: ExamUpdateRequest,
    ) -> ExamResponse:
        return await self.command_service.update(question_id, request)

    async def delete(self, question_id: int) -> None:
        await self.command_service.delete(question_id)

    async def find_by_year(
        self,
        year: int,
        category: Optional[str] = None,
        subject_id: Optional[int] = None,
    ) -> List[ExamResponse]:
        return await self.query_service.find_by_year(year, category, subject_id)

    async def get_categories_by_subject(self, subject_id: int) -> List[str]:
        return await self.query_service.get_categories_by_subject(subject_id)

    async def find_all_for_index(
        self,
        category: Optional[str] = None,
    ) -> List[ExamResponse]:
        return await self.query_service.find_all_for_index(category)

    async def find_for_nav_index(
        self,
        category: Optional[str] = None,
    ) -> List[ExamNavItem]:
        return await self.query_service.find_for_nav_index(category)

    async def find_by_subject_and_category(
        self,
        subject_id: Optional[int],
        category: str,
    ) -> List[ExamResponse]:
        return await self.query_service.find_by_subject_and_category(
            subject_id,
            category,
        )

    async def export_by_subject(
        self,
        subject_id: int,
        format: str = "markdown",
    ) -> ExportResultResponse:
        return await self.export_service.export_by_subject(subject_id, format)

    async def export_category_stats(
        self,
        subject_id: Optional[int],
        format: str,
    ) -> ExportResultResponse:
        return await self.export_service.export_category_stats(subject_id, format)
