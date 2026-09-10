"""真题查询用例。

查询持久化由 :class:`ExamRepository` 负责，Service 只处理查询参数到业务响应的转换。
"""
import json
import logging
from typing import List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.entities import ExamCategory, ExamQuestion
from app.modules.catalog.category_repository import CategoryRepository
from app.repositories.exam_repository import ExamQuery, ExamRepository
from app.schemas.common import PageInfo
from app.schemas.exam import (
    ExamCategoryStatItem,
    ExamCategoryStatsResponse,
    ExamCategoryStatsTreeItem,
    ExamDuplicateCheckResponse,
    ExamIndexItem,
    ExamIndexResponse,
    ExamNavItem,
    ExamResponse,
    ExamSubjectCategoryStats,
    ExamYearStatResponse,
    ExamQueryParams,
    PaginatedExamResponse,
)
from app.services.exam_category_stats import (
    CategoryStatsNode,
    QuestionStats,
    SubjectCategoryStats,
    build_subject_category_stats,
)
from app.services.question_mapping import parse_categories, parse_options


logger = logging.getLogger(__name__)


class ExamQueryService:
    """编排真题列表、统计、索引和详情查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ExamRepository(session)
        self.category_repository = CategoryRepository(session)

    async def get_paginated(self, params: ExamQueryParams) -> PaginatedExamResponse:
        """分页查询真题。"""
        logger.info(
            "ExamQueryService.get_paginated started, page: %d, page_size: %d, year: %s, subject_id: %s",
            params.page,
            params.page_size,
            params.year,
            params.subject_id,
        )
        category_names: Optional[tuple[str, ...]] = None
        if params.category and params.subject_id is not None:
            category_names = tuple(
                await self.category_repository.list_category_scope_names(
                    params.subject_id,
                    params.category,
                )
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
                category_names=category_names,
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
        """按科目和分类树顺序统计真题。"""
        questions = await self.repository.list_for_category_stats(subject_id)
        subjects = await self.category_repository.list_subjects()
        categories = (
            await self.category_repository.list_all()
            if subject_id is None
            else await self.category_repository.list_by_subject(
                subject_id,
                include_subject=True,
            )
        )

        questions_by_subject: dict[int | None, list[ExamQuestion]] = {}
        for question in questions:
            questions_by_subject.setdefault(question.subject_id, []).append(question)

        categories_by_subject: dict[int | None, list[ExamCategory]] = {}
        for category in categories:
            categories_by_subject.setdefault(category.subject_id, []).append(category)

        subject_names = {subject.id: subject.name for subject in subjects}
        subject_ids: list[int | None]
        if subject_id is None:
            ordered_ids = [subject.id for subject in subjects]
            candidate_ids = set(subject_names)
            candidate_ids.update(categories_by_subject)
            candidate_ids.update(
                current_id
                for current_id in questions_by_subject
                if current_id is not None
            )
            subject_ids = ordered_ids + sorted(
                current_id
                for current_id in candidate_ids
                if current_id not in ordered_ids
            )
            if None in questions_by_subject:
                subject_ids.append(None)
        elif subject_id in subject_names:
            subject_ids = [subject_id]
        else:
            subject_ids = []

        subject_stats: list[SubjectCategoryStats] = []
        for current_subject_id in subject_ids:
            current_name = (
                subject_names.get(current_subject_id, f"科目{current_subject_id}")
                if current_subject_id is not None
                else "未归属科目"
            )
            current_stats = build_subject_category_stats(
                questions_by_subject.get(current_subject_id, []),
                categories_by_subject.get(current_subject_id, []),
                subject_id=current_subject_id,
                subject_name=current_name,
            )
            for question_id in current_stats.invalid_question_ids:
                logger.warning(
                    "跳过无效真题分类数据: question_id=%s",
                    question_id,
                )
            subject_stats.append(current_stats)

        flat_stats: dict[str, QuestionStats] = {}
        categorized_question_ids: set[int] = set()
        for current_stats in subject_stats:
            categorized_question_ids.update(current_stats.categorized.question_ids)
            self._collect_direct_stats(current_stats.categories, flat_stats)

        stats = [
            ExamCategoryStatItem(
                category_name=category_name,
                count=data.count,
                choice_count=data.choice_count,
                subjective_count=data.subjective_count,
            )
            for category_name, data in sorted(flat_stats.items())
        ]
        category_tree = [
            ExamSubjectCategoryStats(
                subject_id=current_stats.subject_id,
                subject_name=current_stats.subject_name,
                total_count=current_stats.categorized.count,
                category_reference_count=current_stats.category_reference_count,
                categories=[
                    self._to_category_stats_tree(node)
                    for node in current_stats.categories
                ],
            )
            for current_stats in subject_stats
        ]
        return ExamCategoryStatsResponse(
            subject_id=subject_id,
            subject_name=(
                subject_names.get(subject_id)
                if subject_id is not None
                else None
            ),
            total_count=len(categorized_question_ids),
            category_reference_count=sum(
                current_stats.category_reference_count
                for current_stats in subject_stats
            ),
            stats=stats,
            category_tree=category_tree,
        )

    @staticmethod
    def _collect_direct_stats(
        nodes: list[CategoryStatsNode],
        flat_stats: dict[str, QuestionStats],
    ) -> None:
        """收集平面统计字段，保留旧响应的兼容数据。"""
        for node in nodes:
            if node.direct.count:
                flat_stats.setdefault(node.name, QuestionStats()).merge(node.direct)
            ExamQueryService._collect_direct_stats(node.children, flat_stats)

    @staticmethod
    def _to_category_stats_tree(
        node: CategoryStatsNode,
    ) -> ExamCategoryStatsTreeItem:
        """将内部分类统计节点转换为 API 响应。"""
        return ExamCategoryStatsTreeItem(
            category_id=node.category_id,
            parent_id=node.parent_id,
            category_name=node.name,
            order_num=node.order_num,
            enabled=node.enabled,
            is_unfiled=node.is_unfiled,
            count=node.direct.count,
            choice_count=node.direct.choice_count,
            subjective_count=node.direct.subjective_count,
            subtree_count=node.subtree.count,
            subtree_choice_count=node.subtree.choice_count,
            subtree_subjective_count=node.subtree.subjective_count,
            children=[
                ExamQueryService._to_category_stats_tree(child)
                for child in node.children
            ],
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
