"""模拟题模块持久化模型。"""
from typing import Optional

from sqlalchemy import CheckConstraint, Index, UniqueConstraint, text
from sqlmodel import Field, Relationship

from web408.models.base import BaseModel
from web408.models.enums import DifficultyEnum, QuestionTypeEnum


class MockQuestion(BaseModel, table=True):
    """模拟题模型。"""
    __tablename__ = "mock_question"
    __table_args__ = (
        CheckConstraint(
            "question_type IN ('CHOICE', 'ESSAY')",
            name="ck_mock_question_type",
        ),
        CheckConstraint(
            "difficulty IS NULL OR difficulty IN ('EASY', 'MEDIUM', 'HARD')",
            name="ck_mock_question_difficulty",
        ),
        Index(
            "uq_mock_question_source_title_number",
            "source",
            "title",
            "question_number",
            unique=True,
            sqlite_where=text("title IS NOT NULL AND question_number IS NOT NULL"),
        ),
    )

    source: str = Field(description="来源机构")
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
    subject: Optional["Subject"] = Relationship(back_populates="mock_questions")
    author: Optional["User"] = Relationship(back_populates="mock_questions")


class MockQuestionExamMark(BaseModel, table=True):
    """模拟题出题标记；独立保存状态，不修改模拟题主体记录。"""

    __tablename__ = "mock_question_exam_mark"
    __table_args__ = (
        UniqueConstraint(
            "mock_question_id",
            name="uq_mock_question_exam_mark_question",
        ),
    )

    mock_question_id: int = Field(
        foreign_key="mock_question.id",
        ondelete="CASCADE",
        index=True,
        description="模拟题 ID",
    )


class MockQuestionWrongCount(BaseModel, table=True):
    """模拟题答错次数；独立保存统计，不修改模拟题主体记录。"""

    __tablename__ = "mock_question_wrong_count"
    __table_args__ = (
        CheckConstraint(
            "wrong_count >= 0",
            name="ck_mock_question_wrong_count_non_negative",
        ),
        UniqueConstraint(
            "mock_question_id",
            name="uq_mock_question_wrong_count_question",
        ),
    )

    mock_question_id: int = Field(
        foreign_key="mock_question.id",
        ondelete="CASCADE",
        index=True,
        description="模拟题 ID",
    )
    wrong_count: int = Field(default=0, ge=0, description="答错次数")
