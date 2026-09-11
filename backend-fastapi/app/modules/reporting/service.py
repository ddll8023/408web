"""统计与导出业务用例。"""
from datetime import datetime
import logging

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import ValidationException
from app.modules.catalog.read_service import CatalogCategoryRead, CatalogReadService
from app.modules.exam.query_service import (
    ExamCategoryQuestionRead,
    ExamQueryService,
)
from app.modules.reporting.exam_category_stats import (
    CategoryStatsNode,
    QuestionStats,
    SubjectCategoryStats,
    build_subject_category_stats,
)
from app.modules.reporting.exporters import ReportingExporter
from app.modules.reporting.schemas import (
    ExamCategoryStatItem,
    ExamCategoryStatsResponse,
    ExamCategoryStatsTreeItem,
    ExamExportRequest,
    ExportResultResponse,
)


logger = logging.getLogger(__name__)


class ReportingService:
    """编排真题分类统计和文件导出。"""

    def __init__(self, session: AsyncSession) -> None:
        self.exam_query_service = ExamQueryService(session)
        self.catalog_read_service = CatalogReadService(session)

    async def get_category_stats(
        self,
        subject_id: int | None = None,
    ) -> ExamCategoryStatsResponse:
        """按科目和分类树顺序统计真题。"""
        questions = await self.exam_query_service.list_for_category_stats(subject_id)
        subjects = await self.catalog_read_service.list_subjects()
        categories = await self.catalog_read_service.list_categories(subject_id)

        questions_by_subject: dict[int | None, list[ExamCategoryQuestionRead]] = {}
        for question in questions:
            questions_by_subject.setdefault(question.subject_id, []).append(question)

        categories_by_subject: dict[int | None, list[CatalogCategoryRead]] = {}
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
            {
                "subject_id": current_stats.subject_id,
                "subject_name": current_stats.subject_name,
                "total_count": current_stats.categorized.count,
                "category_reference_count": current_stats.category_reference_count,
                "categories": [
                    self._to_category_stats_tree(node)
                    for node in current_stats.categories
                ],
            }
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

    async def export_by_subject(
        self,
        request: ExamExportRequest,
    ) -> ExportResultResponse:
        """按科目导出 Markdown 真题文件。"""
        questions = await self.exam_query_service.list_for_export(request.subject_id)
        content = ReportingExporter.generate_exam_markdown(questions)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return ExportResultResponse(
            filename=f"真题_{request.subject_id}_{timestamp}.md",
            content_type="text/markdown; charset=utf-8",
            file_bytes=content.encode("utf-8"),
        )

    async def export_category_stats(
        self,
        subject_id: int | None,
        format: str,
    ) -> ExportResultResponse:
        """按科目导出分类统计 Markdown 或 Excel 文件。"""
        if format not in {"markdown", "xlsx"}:
            raise ValidationException("不支持的导出格式")

        stats = await self.get_category_stats(subject_id)
        subject_name = stats.subject_name or "全部科目"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "markdown":
            content = ReportingExporter.generate_category_markdown(stats)
            return ExportResultResponse(
                filename=ReportingExporter.build_filename(subject_name, timestamp, "md"),
                content_type="text/markdown; charset=utf-8",
                file_bytes=content.encode("utf-8"),
            )

        content = ReportingExporter.generate_category_xlsx(stats)
        return ExportResultResponse(
            filename=ReportingExporter.build_filename(subject_name, timestamp, "xlsx"),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            file_bytes=content,
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
            ReportingService._collect_direct_stats(node.children, flat_stats)

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
                ReportingService._to_category_stats_tree(child)
                for child in node.children
            ],
        )
