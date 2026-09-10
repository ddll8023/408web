"""分类业务服务门面。

查询/树形组装与写入事务分别由专用 Service 负责，保留原有
``ExamCategoryService`` 公共入口。
"""
from typing import List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.catalog.schemas.category import (
    ExamCategoryCreateRequest,
    ExamCategoryMoveRequest,
    ExamCategoryResponse,
    ExamCategoryStatResponse,
    ExamCategoryTreeResponse,
    ExamCategoryUpdateRequest,
    ExamCategoryUsageResponse,
)
from app.modules.catalog.category_command_service import CategoryCommandService
from app.modules.catalog.category_query_service import CategoryQueryService


class ExamCategoryService:
    """兼容 API 层的分类业务入口。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.query_service = CategoryQueryService(session)
        self.command_service = CategoryCommandService(session, self.query_service)

    async def get_all_categories(
        self,
        question_type: str = "exam",
    ) -> List[ExamCategoryResponse]:
        return await self.query_service.get_all_categories(question_type)

    async def get_enabled_categories_by_subject(
        self,
        subject_id: int,
    ) -> List[ExamCategoryResponse]:
        return await self.query_service.get_enabled_categories_by_subject(subject_id)

    async def get_categories_by_subject(
        self,
        subject_id: int,
        enabled_only: bool = False,
        question_type: str = "exam",
    ) -> List[ExamCategoryResponse]:
        return await self.query_service.get_categories_by_subject(
            subject_id,
            enabled_only,
            question_type,
        )

    async def get_category_tree(
        self,
        subject_id: int,
        enabled_only: bool = False,
        question_type: str = "exam",
    ) -> List[ExamCategoryTreeResponse]:
        return await self.query_service.get_category_tree(
            subject_id,
            enabled_only,
            question_type,
        )

    async def get_enabled_category_tree_with_stats(
        self,
        subject_id: int,
        question_type: str = "exam",
    ) -> List[ExamCategoryTreeResponse]:
        return await self.query_service.get_enabled_category_tree_with_stats(
            subject_id,
            question_type,
        )

    async def get_category_stats(
        self,
        question_type: str = "exam",
    ) -> ExamCategoryStatResponse:
        return await self.query_service.get_category_stats(question_type)

    async def get_available_parent_categories(
        self,
        subject_id: int,
        exclude_id: Optional[int] = None,
    ) -> List[ExamCategoryResponse]:
        return await self.query_service.get_available_parent_categories(
            subject_id,
            exclude_id,
        )

    async def check_category_usage(self, category_id: int) -> int:
        return await self.query_service.check_category_usage(category_id)

    async def get_category_usage(self, category_id: int) -> ExamCategoryUsageResponse:
        return await self.query_service.get_category_usage(category_id)

    async def get_by_id(self, category_id: int) -> ExamCategoryResponse:
        return await self.query_service.get_by_id(category_id)

    async def create(self, request: ExamCategoryCreateRequest) -> ExamCategoryResponse:
        return await self.command_service.create(request)

    async def update(
        self,
        category_id: int,
        request: ExamCategoryUpdateRequest,
    ) -> ExamCategoryResponse:
        return await self.command_service.update(category_id, request)

    async def move(
        self,
        category_id: int,
        request: ExamCategoryMoveRequest,
    ) -> List[ExamCategoryResponse]:
        return await self.command_service.move(category_id, request)

    async def delete(self, category_id: int) -> None:
        await self.command_service.delete(category_id)
