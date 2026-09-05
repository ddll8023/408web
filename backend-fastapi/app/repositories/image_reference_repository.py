"""图片引用扫描的持久化边界。"""
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.entities import ExamQuestion, MockQuestion


class ImageReferenceRepository:
    """读取真题和模拟题中用于图片引用扫描的文本字段。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_exam_texts(self) -> list[Any]:
        result = await self.session.exec(
            select(
                ExamQuestion.id,
                ExamQuestion.year,
                ExamQuestion.question_number,
                ExamQuestion.title,
                ExamQuestion.content,
                ExamQuestion.answer,
                ExamQuestion.options,
            )
        )
        return result.all()

    async def list_mock_texts(self) -> list[Any]:
        result = await self.session.exec(
            select(
                MockQuestion.id,
                MockQuestion.question_number,
                MockQuestion.title,
                MockQuestion.source,
                MockQuestion.content,
                MockQuestion.answer,
                MockQuestion.options,
            )
        )
        return result.all()
