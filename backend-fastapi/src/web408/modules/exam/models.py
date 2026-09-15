"""真题模块持久化模型。"""
from typing import Optional

from sqlalchemy import CheckConstraint, Index, text
from sqlmodel import Field, Relationship

from web408.models.base import BaseModel
from web408.models.enums import DifficultyEnum, QuestionTypeEnum


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


class ExamProcessImage(BaseModel, table=True):
    """真题讲解过程图片关联模型。"""

    __tablename__ = "exam_process_image"
    __table_args__ = (
        Index(
            "ix_exam_process_image_exam_sort",
            "exam_id",
            "sort_order",
        ),
    )

    exam_id: int = Field(
        foreign_key="exam_question.id",
        ondelete="CASCADE",
        index=True,
        description="真题 ID",
    )
    filename: str = Field(description="图片文件名")
    sort_order: int = Field(default=0, ge=0, description="展示顺序")
    created_by: int = Field(
        foreign_key="user.id",
        ondelete="RESTRICT",
        index=True,
        description="上传管理员 ID",
    )
