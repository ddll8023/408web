"""媒体模块的题目图片引用读取边界。"""
from web408.modules.exam.query_service import ExamQueryService
from web408.modules.media.schemas import ImageResourceResponse, ImageUsageResponse
from web408.modules.mock.query_service import MockQueryService
from sqlmodel.ext.asyncio.session import AsyncSession


class MediaReferenceReader:
    """通过题库公开 Query Service 扫描图片引用。"""

    def __init__(self, session: AsyncSession) -> None:
        self.exam_query_service = ExamQueryService(session)
        self.mock_query_service = MockQueryService(session)

    async def mark_references(self, images: list[ImageResourceResponse]) -> None:
        """扫描真题和模拟题文本并回填图片引用信息。"""
        if not images:
            return

        filename_set = {image.filename for image in images}
        image_map = {image.filename: image for image in images}

        exam_rows = await self.exam_query_service.list_image_reference_texts()
        mock_rows = await self.mock_query_service.list_image_reference_texts()

        for exam in exam_rows:
            text = " ".join(
                part for part in (exam.content, exam.answer, exam.options) if part
            )
            for filename in filename_set:
                if filename in text:
                    image = image_map[filename]
                    image.referenced = True
                    image.exams.append(
                        ImageUsageResponse(
                            id=exam.id,
                            year=exam.year,
                            question_number=exam.question_number,
                            title=exam.title
                            or f"真题-{exam.year}年第{exam.question_number or '?'}题",
                        )
                    )

        for mock in mock_rows:
            text = " ".join(
                part for part in (mock.content, mock.answer, mock.options) if part
            )
            for filename in filename_set:
                if filename in text:
                    image = image_map[filename]
                    image.referenced = True
                    if not any(item.id == mock.id for item in image.exams):
                        image.exams.append(
                            ImageUsageResponse(
                                id=mock.id,
                                year=None,
                                question_number=mock.question_number,
                                title=f"[模拟题] {mock.title or mock.source}",
                            )
                        )
