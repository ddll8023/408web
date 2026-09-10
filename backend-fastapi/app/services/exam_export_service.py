"""真题导出用例。"""
import json
from datetime import datetime
from io import BytesIO
from xml.etree.ElementTree import Element, SubElement, register_namespace, tostring
from zipfile import ZIP_DEFLATED, ZipFile

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import ValidationException
from app.models.entities import ExamQuestion
from app.repositories.exam_repository import ExamRepository
from app.schemas.exam import (
    ExamCategoryStatsResponse,
    ExamCategoryStatsTreeItem,
    ExportResultResponse,
)
from app.services.exam_query_service import ExamQueryService


_XLSX_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_RELATIONSHIP_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PACKAGE_RELATIONSHIP_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"

register_namespace("", _XLSX_NAMESPACE)
register_namespace("r", _RELATIONSHIP_NAMESPACE)
register_namespace("pr", _PACKAGE_RELATIONSHIP_NAMESPACE)


class ExamExportService:
    """查询真题并生成 Markdown 或 Excel 导出结果。"""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = ExamRepository(session)
        self.query_service = ExamQueryService(session)

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
        """按科目导出按章节和知识点顺序排列的分类统计。"""
        if format not in {"markdown", "xlsx"}:
            raise ValidationException("不支持的导出格式")

        stats = await self.query_service.get_category_stats(subject_id)
        subject_name = stats.subject_name or "全部科目"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "markdown":
            content = self._generate_category_markdown(stats)
            return ExportResultResponse(
                filename=self._build_filename(subject_name, timestamp, "md"),
                content_type="text/markdown; charset=utf-8",
                file_bytes=content.encode("utf-8"),
            )

        content = self._generate_category_xlsx(stats)
        return ExportResultResponse(
            filename=self._build_filename(subject_name, timestamp, "xlsx"),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            file_bytes=content,
        )

    @staticmethod
    def _flatten_category_rows(
        nodes: list[ExamCategoryStatsTreeItem],
    ) -> list[tuple[str, str, int, int, int]]:
        """按树顺序展平分类，并选择章节或知识点的统计口径。"""
        rows: list[tuple[str, str, int, int, int]] = []

        def append_nodes(
            current_nodes: list[ExamCategoryStatsTreeItem],
            level: int,
        ) -> None:
            for node in current_nodes:
                is_chapter = level == 0 and not node.is_unfiled
                has_children = bool(node.children)
                use_subtree = has_children or level == 0
                if node.is_unfiled and level == 0:
                    scope = "未归档汇总"
                elif is_chapter:
                    scope = "章节合计"
                elif has_children:
                    scope = "知识点组汇总"
                elif node.is_unfiled:
                    scope = "未归档标签"
                else:
                    scope = "知识点直接引用"
                choice_count = (
                    node.subtree_choice_count
                    if use_subtree
                    else node.choice_count
                )
                subjective_count = (
                    node.subtree_subjective_count
                    if use_subtree
                    else node.subjective_count
                )
                count = node.subtree_count if use_subtree else node.count
                label = f"{'　' * level}{node.category_name}"
                rows.append((label, scope, choice_count, subjective_count, count))
                append_nodes(node.children, level + 1)

        append_nodes(nodes, 0)
        return rows

    @staticmethod
    def _generate_category_markdown(stats: ExamCategoryStatsResponse) -> str:
        """生成按科目和目录顺序排列的分类统计 Markdown。"""
        subject_name = stats.subject_name or "全部科目"
        lines = [
            "# 真题分类统计",
            "",
            f"- 科目：{subject_name}",
            f"- 去重题目总数：{stats.total_count}",
            f"- 分类引用总数：{stats.category_reference_count}",
            "",
            "## 分类统计",
            "",
        ]
        if not stats.category_tree:
            lines.extend(
                [
                    "| 分类 | 统计口径 | 选择题数量 | 主观题数量 | 总题数 |",
                    "| --- | --- | ---: | ---: | ---: |",
                    "| 暂无分类数据 | - | 0 | 0 | 0 |",
                ]
            )
            return "\n".join(lines).rstrip() + "\n"

        for subject_stats in stats.category_tree:
            lines.extend(
                [
                    f"### {subject_stats.subject_name}",
                    "",
                    "| 分类 | 统计口径 | 选择题数量 | 主观题数量 | 总题数 |",
                    "| --- | --- | ---: | ---: | ---: |",
                ]
            )
            rows = ExamExportService._flatten_category_rows(subject_stats.categories)
            if not rows:
                lines.append("| 暂无分类数据 | - | 0 | 0 | 0 |")
                continue
            for label, scope, choice_count, subjective_count, count in rows:
                lines.append(
                    "| {name} | {scope} | {choice} | {subjective} | {count} |".format(
                        name=label.replace("|", "\\|"),
                        scope=scope.replace("|", "\\|"),
                        choice=choice_count,
                        subjective=subjective_count,
                        count=count,
                    )
                )
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _generate_category_xlsx(stats: ExamCategoryStatsResponse) -> bytes:
        """生成按科目和目录顺序排列的最小 Excel 工作簿。"""
        rows: list[list[object]] = [
            ["真题分类统计"],
            ["科目", stats.subject_name or "全部科目"],
            ["去重题目总数", stats.total_count],
            ["分类引用总数", stats.category_reference_count],
            [],
            [
                "科目",
                "分类",
                "统计口径",
                "选择题数量",
                "主观题数量",
                "总题数",
            ],
        ]
        for subject_stats in stats.category_tree:
            for label, scope, choice_count, subjective_count, count in (
                ExamExportService._flatten_category_rows(subject_stats.categories)
            ):
                rows.append(
                    [
                        subject_stats.subject_name,
                        label,
                        scope,
                        choice_count,
                        subjective_count,
                        count,
                    ]
                )
        if len(rows) == 6:
            rows.append(["", "暂无分类数据", "-", 0, 0, 0])

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
