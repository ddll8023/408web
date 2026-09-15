"""向其他模块提供真题过程图片的只读数据边界。"""
from dataclasses import dataclass

from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.exam.process_image_repository import ExamProcessImageRepository


@dataclass(frozen=True, slots=True)
class ExamProcessImageReferenceRead:
    """媒体模块扫描过程图片引用所需的只读数据。"""

    exam_id: int
    filename: str
    year: int
    question_number: int | None
    title: str | None


class ExamProcessImageReadService:
    """向媒体模块公开过程图片引用查询，避免跨模块直接访问模型。"""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = ExamProcessImageRepository(session)

    async def list_for_media_reference(self) -> list[ExamProcessImageReferenceRead]:
        """返回媒体资源引用扫描所需的过程图片信息。"""
        return [
            ExamProcessImageReferenceRead(
                exam_id=row.exam_id,
                filename=row.filename,
                year=row.year,
                question_number=row.question_number,
                title=row.title,
            )
            for row in await self.repository.list_for_media_reference()
        ]
