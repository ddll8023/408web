"""真题导出用例。"""
import json
from datetime import datetime
from typing import List

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.entities import ExamQuestion
from app.repositories.exam_repository import ExamRepository
from app.schemas.exam import ExportResultResponse

class ExamExportService:
    """查询真题并生成 Markdown 导出结果。"""

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

    @staticmethod
    def _generate_markdown(questions: List[ExamQuestion]) -> str:
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
                    try:
                        options = json.loads(question.options)
                    except (TypeError, json.JSONDecodeError):
                        lines.append(question.options)
                    else:
                        if isinstance(options, dict):
                            lines.extend(
                                f"- **{key}**: {value}"
                                for key, value in options.items()
                            )
                        else:
                            lines.append(question.options)
                lines.append("")
                if question.answer:
                    lines.append(f"**答案：** {question.answer}")
                lines.extend(["---", ""])
        return "\n".join(lines)
