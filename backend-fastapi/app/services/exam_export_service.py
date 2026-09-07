"""真题导出用例。"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Iterable
from xml.etree.ElementTree import Element, SubElement, register_namespace, tostring
from zipfile import ZIP_DEFLATED, ZipFile

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import ValidationException
from app.models.entities import ExamQuestion
from app.repositories.exam_repository import ExamRepository
from app.schemas.exam import ExportResultResponse
from app.services.question_mapping import parse_categories


logger = logging.getLogger(__name__)

_XLSX_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_RELATIONSHIP_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PACKAGE_RELATIONSHIP_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"

register_namespace("", _XLSX_NAMESPACE)
register_namespace("r", _RELATIONSHIP_NAMESPACE)
register_namespace("pr", _PACKAGE_RELATIONSHIP_NAMESPACE)


@dataclass(frozen=True, slots=True)
class CategorySummary:
    """一个分类及其关联题目的统计结果。"""

    name: str
    questions: list[ExamQuestion]
    choice_count: int
    subjective_count: int

    @property
    def count(self) -> int:
        """返回该分类关联的去重题数。"""
        return len(self.questions)


class ExamExportService:
    """查询真题并生成 Markdown 或 Excel 导出结果。"""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = ExamRepository(session)

    async def export_by_subject(
        self,
        subject_id: int,
        format: str = "markdown",
    ) -> ExportResultResponse:
        """按科目导出真题。"""
        questions = await self.repository.find_for_export(subject_id)
        content = self._generate_markdown(questions)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return ExportResultResponse(
            filename=f"真题_{subject_id}_{timestamp}.md",
            content_type="text/markdown; charset=utf-8",
            file_bytes=content.encode("utf-8"),
        )

    async def export_category_stats(
        self,
        subject_id: int | None,
        format: str,
    ) -> ExportResultResponse:
        """按科目导出只包含汇总数据的真题分类统计。"""
        if format not in {"markdown", "xlsx"}:
            raise ValidationException("不支持的导出格式")

        questions = await self.repository.list_for_category_stats(subject_id)
        subject_name = await self._get_subject_name(subject_id)
        summaries = self._build_category_summaries(questions)
        total_count = len(
            {
                question.id
                for summary in summaries
                for question in summary.questions
            }
        )
        category_reference_count = sum(summary.count for summary in summaries)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "markdown":
            content = self._generate_category_markdown(
                subject_name,
                summaries,
                total_count,
                category_reference_count,
            )
            return ExportResultResponse(
                filename=self._build_filename(subject_name, timestamp, "md"),
                content_type="text/markdown; charset=utf-8",
                file_bytes=content.encode("utf-8"),
            )

        content = self._generate_category_xlsx(
            subject_name,
            summaries,
            total_count,
            category_reference_count,
        )
        return ExportResultResponse(
            filename=self._build_filename(subject_name, timestamp, "xlsx"),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            file_bytes=content,
        )

    async def _get_subject_name(self, subject_id: int | None) -> str:
        """返回导出范围对应的科目名称。"""
        if subject_id is None:
            return "全部科目"
        subject = await self.repository.get_subject(subject_id)
        return subject.name if subject else f"科目{subject_id}"

    @staticmethod
    def _build_category_summaries(
        questions: Iterable[ExamQuestion],
    ) -> list[CategorySummary]:
        """按分类展开题目，并保证同一题在同一分类内只计一次。"""
        category_questions: dict[str, list[ExamQuestion]] = {}
        for question in questions:
            categories = parse_categories(question.category)
            if categories is None:
                if question.category:
                    logger.warning(
                        "跳过无效真题分类数据: question_id=%s",
                        question.id,
                    )
                continue

            unique_categories = dict.fromkeys(
                category.strip()
                for category in categories
                if category.strip()
            )
            for category in unique_categories:
                category_questions.setdefault(category, []).append(question)

        summaries = [
            CategorySummary(
                name=name,
                questions=category_items,
                choice_count=sum(
                    question.question_type == "CHOICE"
                    for question in category_items
                ),
                subjective_count=sum(
                    question.question_type != "CHOICE"
                    for question in category_items
                ),
            )
            for name, category_items in category_questions.items()
        ]
        return sorted(summaries, key=lambda item: (-item.count, item.name))

    @staticmethod
    def _generate_category_markdown(
        subject_name: str,
        summaries: list[CategorySummary],
        total_count: int,
        category_reference_count: int,
    ) -> str:
        """生成只包含汇总数据的分类统计 Markdown 文件内容。"""
        lines = [
            "# 真题分类统计",
            "",
            f"- 科目：{subject_name}",
            f"- 去重题目总数：{total_count}",
            f"- 分类引用总数：{category_reference_count}",
            "",
            "## 分类统计",
            "",
            "| 分类 | 选择题数量 | 主观题数量 | 分类题数 |",
            "| --- | ---: | ---: | ---: |",
        ]
        for summary in summaries:
            lines.append(
                "| {name} | {choice} | {subjective} | {count} |".format(
                    name=summary.name.replace("|", "\\|"),
                    choice=summary.choice_count,
                    subjective=summary.subjective_count,
                    count=summary.count,
                )
            )

        if not summaries:
            lines.append("| 暂无分类数据 | 0 | 0 | 0 |")

        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _generate_category_xlsx(
        subject_name: str,
        summaries: list[CategorySummary],
        total_count: int,
        category_reference_count: int,
    ) -> bytes:
        """生成只包含汇总数据的最小 Excel 工作簿。"""
        rows: list[list[object]] = [
            ["真题分类统计"],
            ["科目", subject_name],
            ["去重题目总数", total_count],
            ["分类引用总数", category_reference_count],
            [],
            ["分类", "选择题数量", "主观题数量", "分类题数"],
        ]
        rows.extend(
            [
                [
                    summary.name,
                    summary.choice_count,
                    summary.subjective_count,
                    summary.count,
                ]
                for summary in summaries
            ]
        )
        if not summaries:
            rows.append(["暂无分类数据", 0, 0, 0])

        return ExamExportService._build_xlsx(rows)

    @staticmethod
    def _format_options_markdown(value: str) -> str:
        """将数据库中的选项 JSON 转换为 Markdown。"""
        try:
            options = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return value
        if isinstance(options, dict):
            return "\n".join(
                f"- **{key}**: {option_value}"
                for key, option_value in options.items()
            )
        return value

    @staticmethod
    def _build_filename(subject_name: str, timestamp: str, extension: str) -> str:
        """构造安全的下载文件名。"""
        safe_subject_name = "".join(
            char if char.isalnum() or char in {" ", "-", "_"} else "_"
            for char in subject_name
        ).strip(" ._") or "全部科目"
        return f"真题分类统计_{safe_subject_name}_{timestamp}.{extension}"

    @staticmethod
    def _build_xlsx(rows: list[list[object]]) -> bytes:
        """将二维数据写入最小的 XLSX Open XML 包。"""
        worksheet = Element(f"{{{_XLSX_NAMESPACE}}}worksheet")
        max_columns = max((len(row) for row in rows), default=1)
        max_row = max(len(rows), 1)
        dimension = SubElement(worksheet, f"{{{_XLSX_NAMESPACE}}}dimension")
        dimension.set("ref", f"A1:{ExamExportService._column_name(max_columns)}{max_row}")
        sheet_data = SubElement(worksheet, f"{{{_XLSX_NAMESPACE}}}sheetData")

        for row_number, values in enumerate(rows, start=1):
            row_element = SubElement(
                sheet_data,
                f"{{{_XLSX_NAMESPACE}}}row",
                {"r": str(row_number)},
            )
            for column_number, value in enumerate(values, start=1):
                if value is None or value == "":
                    continue
                cell = SubElement(
                    row_element,
                    f"{{{_XLSX_NAMESPACE}}}c",
                    {"r": f"{ExamExportService._column_name(column_number)}{row_number}"},
                )
                if isinstance(value, bool):
                    cell.set("t", "b")
                    SubElement(cell, f"{{{_XLSX_NAMESPACE}}}v").text = "1" if value else "0"
                elif isinstance(value, (int, float)):
                    SubElement(cell, f"{{{_XLSX_NAMESPACE}}}v").text = str(value)
                else:
                    cell.set("t", "inlineStr")
                    inline_string = SubElement(cell, f"{{{_XLSX_NAMESPACE}}}is")
                    text = SubElement(inline_string, f"{{{_XLSX_NAMESPACE}}}t")
                    text.text = str(value)
                    if str(value)[:1].isspace() or str(value)[-1:].isspace():
                        text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

        workbook = Element(f"{{{_XLSX_NAMESPACE}}}workbook")
        sheets = SubElement(workbook, f"{{{_XLSX_NAMESPACE}}}sheets")
        SubElement(
            sheets,
            f"{{{_XLSX_NAMESPACE}}}sheet",
            {
                "name": "分类统计",
                "sheetId": "1",
                f"{{{_RELATIONSHIP_NAMESPACE}}}id": "rId1",
            },
        )

        content_types = Element(
            "{http://schemas.openxmlformats.org/package/2006/content-types}Types"
        )
        content_types_namespace = "http://schemas.openxmlformats.org/package/2006/content-types"
        SubElement(
            content_types,
            f"{{{content_types_namespace}}}Default",
            {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"},
        )
        SubElement(
            content_types,
            f"{{{content_types_namespace}}}Default",
            {"Extension": "xml", "ContentType": "application/xml"},
        )
        SubElement(
            content_types,
            f"{{{content_types_namespace}}}Override",
            {
                "PartName": "/xl/workbook.xml",
                "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
            },
        )
        SubElement(
            content_types,
            f"{{{content_types_namespace}}}Override",
            {
                "PartName": "/xl/worksheets/sheet1.xml",
                "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
            },
        )

        package_relationships = Element(
            f"{{{_PACKAGE_RELATIONSHIP_NAMESPACE}}}Relationships"
        )
        SubElement(
            package_relationships,
            f"{{{_PACKAGE_RELATIONSHIP_NAMESPACE}}}Relationship",
            {
                "Id": "rId1",
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
                "Target": "xl/workbook.xml",
            },
        )

        workbook_relationships = Element(
            f"{{{_PACKAGE_RELATIONSHIP_NAMESPACE}}}Relationships"
        )
        SubElement(
            workbook_relationships,
            f"{{{_PACKAGE_RELATIONSHIP_NAMESPACE}}}Relationship",
            {
                "Id": "rId1",
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
                "Target": "worksheets/sheet1.xml",
            },
        )

        package = BytesIO()
        with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", tostring(content_types, encoding="utf-8", xml_declaration=True))
            archive.writestr("_rels/.rels", tostring(package_relationships, encoding="utf-8", xml_declaration=True))
            archive.writestr("xl/workbook.xml", tostring(workbook, encoding="utf-8", xml_declaration=True))
            archive.writestr("xl/_rels/workbook.xml.rels", tostring(workbook_relationships, encoding="utf-8", xml_declaration=True))
            archive.writestr("xl/worksheets/sheet1.xml", tostring(worksheet, encoding="utf-8", xml_declaration=True))
        return package.getvalue()

    @staticmethod
    def _column_name(column_number: int) -> str:
        """将 1-based 列号转换为 Excel 列名。"""
        name = ""
        current = column_number
        while current:
            current, remainder = divmod(current - 1, 26)
            name = chr(65 + remainder) + name
        return name

    @staticmethod
    def _generate_markdown(questions: list[ExamQuestion]) -> str:
        """生成 Markdown 格式的真题内容。"""
        year_groups: dict[int, list[ExamQuestion]] = {}
        for question in questions:
            year_groups.setdefault(question.year, []).append(question)

        lines = ["# 真题列表\n"]
        for year in sorted(year_groups, reverse=True):
            lines.append(f"## {year}年\n")
            for question in year_groups[year]:
                lines.append(f"### 第{question.question_number}题")
                if question.title:
                    lines.append(f"**{question.title}**")
                lines.extend(["", question.content])
                if question.options:
                    lines.append("**选项：**")
                    lines.append(ExamExportService._format_options_markdown(question.options))
                lines.append("")
                if question.answer:
                    lines.append(f"**答案：** {question.answer}")
                lines.extend(["---", ""])
        return "\n".join(lines)
