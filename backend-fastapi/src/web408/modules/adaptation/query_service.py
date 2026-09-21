"""改编题查询用例。"""
from dataclasses import dataclass

from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.exceptions import NotFoundException
from web408.modules.adaptation.mapper import to_adaptation_response
from web408.modules.adaptation.models import AdaptationQuestion, AdaptationSource
from web408.modules.adaptation.repository import AdaptationQuery, AdaptationRepository
from web408.modules.adaptation.schemas import (
    AdaptationBySourceItem,
    AdaptationBySourceRequest,
    AdaptationCoverageCountItem,
    AdaptationCoverageItem,
    AdaptationCoverageRequest,
    AdaptationSourceUsageCheckResponse,
    AdaptationQueryParams,
    AdaptationResponse,
    AdaptationSourceLookupItem,
    AdaptationSourceRefInput,
    AdaptationSourceRefResponse,
    AdaptationSourceUsageItem,
    PaginatedAdaptationResponse,
)
from web408.modules.auth.read_service import AuthReadService
from web408.modules.catalog.read_service import CatalogReadService
from web408.modules.exam.read_service import ExamReadService, ExamSourceRead
from web408.modules.question_content.serialization import parse_categories
from web408.schemas.common import PageInfo


@dataclass(frozen=True, slots=True)
class AdaptationImageReferenceRead:
    """供媒体模块使用的改编题文本只读数据。"""

    id: int
    title: str | None
    content: str
    answer: str | None
    options: str | None


def format_source_label(source_year: int, source_question_number: int) -> str:
    """生成来源展示文案，例如「2021 年第 15 题」。"""
    return f"{source_year} 年第 {source_question_number} 题"


class AdaptationQueryService:
    """编排改编题列表、来源解析、反查、覆盖统计和详情查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AdaptationRepository(session)
        self.catalog_read_service = CatalogReadService(session)
        self.auth_read_service = AuthReadService(session)
        self.exam_read_service = ExamReadService(session)

    async def get_paginated(
        self,
        params: AdaptationQueryParams,
    ) -> PaginatedAdaptationResponse:
        """分页查询改编题，并将父分类展开为完整子树范围。"""
        category_names: tuple[str, ...] | None = None
        if params.category and params.subject_id is not None:
            category_names = tuple(
                await self.catalog_read_service.get_category_scope_names(
                    params.subject_id,
                    params.category,
                )
            )

        total, questions = await self.repository.list_paginated(
            AdaptationQuery(
                page=params.page,
                page_size=params.page_size,
                subject_id=params.subject_id,
                category=params.category,
                no_category=params.no_category is True,
                category_names=category_names,
                sort_field=params.sort_field,
                sort_order=params.sort_order,
                question_type=params.question_type,
                keyword=params.keyword,
                source_year=params.source_year,
                source_question_number=params.source_question_number,
                source_state=params.source_state,
            )
        )
        data = await self._to_responses(questions)
        total_pages = (total + params.page_size - 1) // params.page_size if total else 0
        return PaginatedAdaptationResponse(
            lists=data,
            pagination=PageInfo(
                page=params.page,
                page_size=params.page_size,
                total=total,
                total_pages=total_pages,
            ),
        )

    async def get_by_id(self, question_id: int) -> AdaptationResponse:
        """按主键查询改编题。"""
        question = await self.repository.get_by_id(question_id)
        if question is None:
            raise NotFoundException(f"改编题不存在：ID={question_id}")
        return await self.to_response(question)

    async def check_source_usage(
        self,
        sources: list[AdaptationSourceRefInput],
        exclude_id: int | None = None,
    ) -> AdaptationSourceUsageCheckResponse:
        """检查来源是否已被其他改编题使用。"""
        reused_sources = await self._find_reused_sources(sources, exclude_id)
        return AdaptationSourceUsageCheckResponse(reused_sources=reused_sources)

    async def lookup_sources(
        self,
        sources: list[AdaptationSourceRefInput],
    ) -> list[AdaptationSourceLookupItem]:
        """批量解析来源，返回与输入顺序一致的命中结果。"""
        keys = {(item.source_year, item.source_question_number) for item in sources}
        exam_refs = await self.exam_read_service.resolve_sources(keys)
        return [
            self._to_lookup_item(item, exam_refs.get((item.source_year, item.source_question_number)))
            for item in sources
        ]

    async def find_by_source(
        self,
        request: AdaptationBySourceRequest,
    ) -> list[AdaptationBySourceItem]:
        """按来源年份与题号反查引用它的改编题。"""
        rows = await self.repository.list_sources_by_keys(
            {(request.source_year, request.source_question_number)}
        )
        if not rows:
            return []

        question_ids = {row.adaptation_id for row in rows}
        questions = await self.repository.list_by_ids(question_ids)
        if request.subject_id is not None:
            questions = [
                question for question in questions if question.subject_id == request.subject_id
            ]
        subject_names = await self.catalog_read_service.get_subject_names(
            {question.subject_id for question in questions if question.subject_id is not None}
        )
        items = [
            AdaptationBySourceItem(
                id=question.id,
                title=question.title,
                question_type=question.question_type,
                subject_id=question.subject_id,
                subject_name=subject_names.get(question.subject_id),
                update_time=question.update_time.isoformat() if question.update_time else None,
            )
            for question in questions
        ]
        return sorted(items, key=lambda item: item.id, reverse=True)

    async def get_coverage(
        self,
        request: AdaptationCoverageRequest,
    ) -> list[AdaptationCoverageItem]:
        """统计各年份真题的改编覆盖，并单独报告无法对应真题库的来源数。"""
        years = (
            sorted(set(request.years))
            if request.years
            else await self.exam_read_service.list_years(request.subject_id)
        )
        if not years:
            return []

        year_set = set(years)
        numbers_by_year = await self.exam_read_service.list_question_numbers(
            year_set,
            request.subject_id,
        )
        counts_by_year = await self._build_source_counts(year_set, request.subject_id)

        items: list[AdaptationCoverageItem] = []
        for year in years:
            numbers = numbers_by_year.get(year, [])
            year_counts = counts_by_year.get(year, {})
            known_numbers = set(numbers)
            items.append(
                AdaptationCoverageItem(
                    year=year,
                    total=len(numbers),
                    adapted=sum(1 for number in numbers if year_counts.get(number, 0) > 0),
                    missing_numbers=[
                        number for number in numbers if year_counts.get(number, 0) == 0
                    ],
                    dangling_sources=sum(
                        count
                        for number, count in year_counts.items()
                        if number not in known_numbers
                    ),
                    counts=[
                        AdaptationCoverageCountItem(
                            question_number=number,
                            adaptation_count=year_counts.get(number, 0),
                        )
                        for number in numbers
                    ],
                )
            )
        return sorted(items, key=lambda item: item.year, reverse=True)

    async def find_categories_by_subject(self, subject_id: int) -> list[str]:
        """返回科目下改编题实际使用的分类名称。"""
        category_set: set[str] = set()
        for raw_categories in await self.repository.list_category_values(subject_id):
            if not raw_categories:
                continue
            categories = parse_categories(raw_categories)
            if categories:
                category_set.update(categories)
        return sorted(category_set)

    async def list_image_reference_texts(self) -> list[AdaptationImageReferenceRead]:
        """返回媒体模块扫描图片引用所需的改编题文本。"""
        return [
            AdaptationImageReferenceRead(
                id=row.id,
                title=row.title,
                content=row.content,
                answer=row.answer,
                options=row.options,
            )
            for row in await self.repository.list_image_reference_texts()
        ]

    async def to_response(self, question: AdaptationQuestion) -> AdaptationResponse:
        """将改编题实体转换为公开响应。"""
        responses = await self._to_responses([question])
        return responses[0]

    async def _to_responses(
        self,
        questions: list[AdaptationQuestion],
    ) -> list[AdaptationResponse]:
        """批量读取来源与显示字段并转换题目响应。"""
        if not questions:
            return []
        question_ids = {question.id for question in questions if question.id is not None}
        source_rows = await self.repository.list_sources(question_ids)
        sources_by_question, summary_by_question = await self._build_sources(source_rows)
        subject_names = await self.catalog_read_service.get_subject_names(
            {question.subject_id for question in questions if question.subject_id is not None}
        )
        author_names = await self.auth_read_service.get_user_names(
            {question.author_id for question in questions if question.author_id is not None}
        )
        return [
            to_adaptation_response(
                question,
                subject_name=subject_names.get(question.subject_id),
                author_name=author_names.get(question.author_id),
                sources=sources_by_question.get(question.id, []),
                source_summary=summary_by_question.get(question.id, ""),
            )
            for question in questions
        ]

    async def _build_sources(
        self,
        rows: list[AdaptationSource],
    ) -> tuple[dict[int, list[AdaptationSourceRefResponse]], dict[int, str]]:
        """解析来源命中的真题标题，并生成按题目分组的来源响应与展示摘要。"""
        if not rows:
            return {}, {}

        keys = {(row.source_year, row.source_question_number) for row in rows}
        exam_refs = await self.exam_read_service.resolve_sources(keys)
        sources_by_question: dict[int, list[AdaptationSourceRefResponse]] = {}
        labels_by_question: dict[int, list[str]] = {}
        for row in rows:
            exam_ref = exam_refs.get((row.source_year, row.source_question_number))
            sources_by_question.setdefault(row.adaptation_id, []).append(
                AdaptationSourceRefResponse(
                    id=row.id,
                    source_year=row.source_year,
                    source_question_number=row.source_question_number,
                    exam_question_id=exam_ref.id if exam_ref else None,
                    source_exists=exam_ref is not None,
                    exam_title=exam_ref.title if exam_ref else None,
                )
            )
            labels_by_question.setdefault(row.adaptation_id, []).append(
                format_source_label(
                    row.source_year,
                    row.source_question_number,
                )
            )
        summaries = {
            adaptation_id: f"改编自 {'、'.join(labels)}"
            for adaptation_id, labels in labels_by_question.items()
        }
        return sources_by_question, summaries

    async def _build_source_counts(
        self,
        years: set[int],
        subject_id: int | None,
    ) -> dict[int, dict[int, int]]:
        """把来源引用计数整理为年份到题号的映射。"""
        counts: dict[int, dict[int, int]] = {}
        for row in await self.repository.list_source_counts(years, subject_id):
            counts.setdefault(row.source_year, {})[row.source_question_number] = row.count
        return counts

    async def _find_reused_sources(
        self,
        sources: list[AdaptationSourceRefInput],
        exclude_id: int | None = None,
    ) -> list[AdaptationSourceUsageItem]:
        """提示待保存来源已被哪些改编题引用，不阻断保存。"""
        if not sources:
            return []
        keys = {(item.source_year, item.source_question_number) for item in sources}
        rows = await self.repository.list_sources_by_keys(
            keys,
            exclude_adaptation_id=exclude_id,
        )
        if not rows:
            return []
        questions = {
            question.id: question
            for question in await self.repository.list_by_ids(
                {row.adaptation_id for row in rows}
            )
        }
        return [
            AdaptationSourceUsageItem(
                source_year=row.source_year,
                source_question_number=row.source_question_number,
                adaptation_id=row.adaptation_id,
                title=(
                    questions[row.adaptation_id].title
                    if row.adaptation_id in questions
                    else None
                ),
            )
            for row in rows
        ]

    @staticmethod
    def _to_lookup_item(
        source: AdaptationSourceRefInput,
        exam_ref: ExamSourceRead | None,
    ) -> AdaptationSourceLookupItem:
        """把来源输入与真题解析结果组合为解析响应项。"""
        return AdaptationSourceLookupItem(
            source_year=source.source_year,
            source_question_number=source.source_question_number,
            exists=exam_ref is not None,
            exam_question_id=exam_ref.id if exam_ref else None,
            exam_title=exam_ref.title if exam_ref else None,
            exam_question_type=exam_ref.question_type if exam_ref else None,
        )
