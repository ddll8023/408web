"""真题过程图片的持久化查询边界。"""
from typing import Any

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.exam.models import ExamProcessImage, ExamQuestion


class ExamProcessImageRepository:
    """封装真题过程图片的查询，不负责事务提交和文件操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_exam(self, exam_id: int) -> ExamQuestion | None:
        """查询过程图片所属真题。"""
        result = await self.session.exec(
            select(ExamQuestion).where(ExamQuestion.id == exam_id)
        )
        return result.first()

    async def list_by_exam_id(self, exam_id: int) -> list[ExamProcessImage]:
        """按展示顺序查询指定真题的过程图片。"""
        result = await self.session.exec(
            select(ExamProcessImage)
            .where(ExamProcessImage.exam_id == exam_id)
            .order_by(
                ExamProcessImage.sort_order.asc(),
                ExamProcessImage.id.asc(),
            )
        )
        return result.all()

    async def get_by_exam_and_id(
        self,
        exam_id: int,
        image_id: int,
    ) -> ExamProcessImage | None:
        """查询指定真题下的一张过程图片。"""
        result = await self.session.exec(
            select(ExamProcessImage).where(
                ExamProcessImage.exam_id == exam_id,
                ExamProcessImage.id == image_id,
            )
        )
        return result.first()

    async def get_next_sort_order(self, exam_id: int) -> int:
        """返回指定真题下一张图片的默认顺序。"""
        result = await self.session.exec(
            select(func.max(ExamProcessImage.sort_order)).where(
                ExamProcessImage.exam_id == exam_id
            )
        )
        max_sort_order = result.one()
        return (max_sort_order if max_sort_order is not None else -1) + 1

    async def list_for_media_reference(self) -> list[Any]:
        """返回图片资源管理所需的过程图片引用信息。"""
        result = await self.session.exec(
            select(
                ExamProcessImage.exam_id,
                ExamProcessImage.filename,
                ExamQuestion.year,
                ExamQuestion.question_number,
                ExamQuestion.title,
            )
            .join(ExamQuestion, ExamQuestion.id == ExamProcessImage.exam_id)
            .order_by(ExamProcessImage.id.asc())
        )
        return result.all()
