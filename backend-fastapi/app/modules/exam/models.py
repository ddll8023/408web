"""真题模块持久化模型。"""
from typing import Optional

from sqlalchemy import CheckConstraint, Index, text
from sqlmodel import Field, Relationship

from app.models.base import BaseModel
from app.models.enums import DifficultyEnum, QuestionTypeEnum


class ExamQuestion(BaseModel, table=True):
    """真题模型。"""
    __tablename__ = "exam_question"
    __table_args__ = (
        CheckConstraint(
            "question_type IN ('CHOICE', 'ESSAY')",
            name="ck_exam_question_type",
        ),
        CheckConstraint(
            "difficulty IS NULL OR difficulty IN ('EASY', 'MEDIUM', 'HARD')",
            name="ck_exam_question_difficulty",
        ),
        Index(
            "uq_exam_question_year_number",
            "year",
            "question_number",
            unique=True,
            sqlite_where=text("question_number IS NOT NULL"),
        ),
    )

    year: int = Field(description="年份")
    question_number: int | None = Field(default=None, description="题号")
    question_type: str = Field(default=QuestionTypeEnum.ESSAY.value, description="题型")
    title: str | None = Field(default=None, description="题目标题")
    content: str = Field(description="题目内容")
    options: str | None = Field(default=None, description="选择题选项(JSON)")
    answer: str | None = Field(default=None, description="答案")
    category: str | None = Field(default=None, description="分类(JSON数组)")
    subject_id: int | None = Field(
        default=None,
        foreign_key="subject.id",
        ondelete="SET NULL",
        index=True,
        description="科目ID",
    )
    difficulty: str | None = Field(default=None, description="难度")
    author_id: int = Field(
        foreign_key="user.id",
        ondelete="RESTRICT",
        index=True,
        description="作者ID",
    )

    # 关系
    subject: Optional["Subject"] = Relationship(back_populates="exam_questions")
    author: Optional["User"] = Relationship(back_populates="exam_questions")
