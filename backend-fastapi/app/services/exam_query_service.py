"""真题查询用例。

查询持久化由 :class:`ExamRepository` 负责，Service 只处理查询参数到业务响应的转换。
"""
import json
import logging
from typing import List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.entities import ExamQuestion
from app.repositories.exam_repository import ExamQuery, ExamRepository
from app.schemas.common import PageInfo
from app.schemas.exam import (
    ExamCategoryStatItem,
    ExamCategoryStatsResponse,
    ExamDuplicateCheckResponse,
    ExamIndexItem,
    ExamIndexResponse,
    ExamNavItem,
    ExamResponse,
    ExamYearStatResponse,
    ExamQueryParams,
    PaginatedExamResponse,
)
from app.services.question_mapping import parse_categories, parse_options


logger = logging.getLogger(__name__)


class ExamQueryService:
    """编排真题列表、统计、索引和详情查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ExamRepository(session)

    async def get_paginated(self, params: ExamQueryParams) -> PaginatedExamResponse:
        """分页查询真题。"""
        logger.info(
            "ExamQueryService.get_paginated started, page: %d, page_size: %d, year: %s, subject_id: %s",
            params.page,
            params.page_size,
            params.year,
            params.subject_id,
        )
        total, questions = await self.repository.list_paginated(
            ExamQuery(
                page=params.page,
                page_size=params.page_size,
                year=params.year,
                subject_id=params.subject_id,
                category=params.category,
                no_category=params.no_category is True,
                keyword=params.keyword,
                sort_field=params.sort_field,
                sort_order=params.sort_order,
            )
        )
        data_list = [await self.to_response(question) for question in questions]
        total_pages = (total + params.page_size - 1) // params.page_size if total else 0
        return PaginatedExamResponse(
            lists=data_list,
            pagination=PageInfo(
                page=params.page,
                page_size=params.page_size,
                total=total,
                total_pages=total_pages,
            ),
        )

    async def get_by_id(self, question_id: int) -> ExamResponse:
        """按主键查询真题。"""
        question = await self.repository.get_by_id(question_id)
        if question is None:
            raise NotFoundException(f"真题不存在：ID={question_id}")
        return await self.to_response(question)

    async def check_duplicate(
        self,
        year: int,
        question_number: Optional[int],
        exclude_id: Optional[int] = None,
    ) -> ExamDuplicateCheckResponse:
        """检查年份和题号组合是否重复。"""
        existing = await self.repository.find_duplicate(
            year,
            question_number,
            exclude_id,
        )
        if existing is None:
            return ExamDuplicateCheckResponse(is_duplicate=False)
        return ExamDuplicateCheckResponse(
            is_duplicate=True,
            existing_question=await self.to_response(existing),
        )

    async def get_year_stats(
        self,
        category: Optional[str] = None,
    ) -> List[ExamYearStatResponse]:
        """按年份统计真题。"""
        rows = await self.repository.get_year_stats(category)
        return [
            ExamYearStatResponse(
                year=row.year,
                count=row.count,
                choice_count=row.choice_count or 0,
                subjective_count=row.count - (row.choice_count or 0),
            )
            for row in rows
        ]

    async def get_category_stats(
        self,
        subject_id: Optional[int] = None,
    ) -> ExamCategoryStatsResponse:
        """展开题目分类 JSON 并统计题型数量。"""
        questions = await self.repository.list_for_category_stats(subject_id)
        category_counts: dict[str, dict[str, int]] = {}
        for question in questions:
            if not question.category:
                continue
            try:
                categories = json.loads(question.category)
            except json.JSONDecodeError:
                continue
            if not isinstance(categories, list):
                continue
            for category in categories:
                data = category_counts.setdefault(
                    category,
                    {"count": 0, "choice": 0, "subjective": 0},
                )
                data["count"] += 1
                data["choice" if question.question_type == "CHOICE" else "subjective"] += 1

        stats = [
            ExamCategoryStatItem(
                category_name=category,
                count=data["count"],
                choice_count=data["choice"],
                subjective_count=data["subjective"],
            )
            for category, data in sorted(category_counts.items())
        ]
        subject_name = None
        if subject_id:
            subject = await self.repository.get_subject(subject_id)
            subject_name = subject.name if subject else None
        return ExamCategoryStatsResponse(
            subject_id=subject_id,
            subject_name=subject_name,
            stats=stats,
        )

    async def get_index(self, subject_id: Optional[int] = None) -> ExamIndexResponse:
        """返回真题年份和题号索引。"""
        rows = await self.repository.list_index_rows(subject_id)
        index_data = [
            ExamIndexItem(
                id=row.id,
                year=row.year,
                question_number=row.question_number,
            )
            for row in rows
        ]
        subject_name = None
        if subject_id:
            subject = await self.repository.get_subject(subject_id)
            subject_name = subject.name if subject else None
        return ExamIndexResponse(
            subject_id=subject_id,
            subject_name=subject_name,
            index_data=index_data,
        )

    async def find_by_year(
        self,
        year: int,
        category: Optional[str] = None,
        subject_id: Optional[int] = None,
    ) -> List[ExamResponse]:
        """按年份查询真题。"""
        questions = await self.repository.find_by_year(year, category, subject_id)
        return [await self.to_response(question) for question in questions]

    async def get_categories_by_subject(self, subject_id: int) -> List[str]:
        """返回科目下真题实际使用的分类名称。"""
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

    async def find_all_for_index(
        self,
        category: Optional[str] = None,
    ) -> List[ExamResponse]:
        """返回年份导航使用的真题列表。"""
        questions = await self.repository.find_all_for_index(category)
        return [await self.to_response(question) for question in questions]

    async def find_for_nav_index(
        self,
        category: Optional[str] = None,
    ) -> List[ExamNavItem]:
        """返回侧边栏导航所需的轻量数据。"""
        return [
            ExamNavItem(
                id=row.id,
                year=row.year,
                question_number=row.question_number,
                title=row.title,
                category=parse_categories(row.category),
            )
            for row in await self.repository.find_nav_rows(category)
        ]

    async def find_by_subject_and_category(
        self,
        subject_id: Optional[int],
        category: str,
    ) -> List[ExamResponse]:
        """按科目和分类查询真题。"""
        questions = await self.repository.find_by_subject_and_category(
            subject_id,
            category,
        )
        return [await self.to_response(question) for question in questions]

    async def to_response(self, question: ExamQuestion) -> ExamResponse:
        """将真题实体转换为公开响应。"""
        subject_name = None
        if question.subject_id:
            subject = await self.repository.get_subject(question.subject_id)
            subject_name = subject.name if subject else None
        author_name = None
        if question.author_id:
            author = await self.repository.get_author(question.author_id)
            author_name = author.username if author else None
        return ExamResponse(
            id=question.id,
            year=question.year,
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
