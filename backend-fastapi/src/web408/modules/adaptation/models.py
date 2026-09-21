"""改编题模块持久化模型。

改编题主体与来源引用独立保存，一道改编题可引用多道真题；
来源以「年份 + 题号」为事实键，命中的真题 ID 只作为解析结果保存。
"""
from typing import Optional

from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from sqlmodel import Field, Relationship

from web408.models.base import BaseModel
from web408.models.enums import QuestionTypeEnum


class AdaptationQuestion(BaseModel, table=True):
    """真题改编题模型。"""

    __tablename__ = "adaptation_question"
    __table_args__ = (
        CheckConstraint(
            "question_type IN ('CHOICE', 'ESSAY')",
            name="ck_adaptation_question_type",
        ),
        CheckConstraint(
            "difficulty IS NULL OR difficulty IN ('EASY', 'MEDIUM', 'HARD')",
            name="ck_adaptation_question_difficulty",
        ),
    )

    question_type: str = Field(default=QuestionTypeEnum.ESSAY.value, description="题型")
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

    # 关系：只声明科目与作者，来源引用由独立表承载，删除依赖数据库级联
    subject: Optional["Subject"] = Relationship(back_populates="adaptation_questions")
    author: Optional["User"] = Relationship(back_populates="adaptation_questions")


class AdaptationSource(BaseModel, table=True):
    """改编题来源引用模型。"""

    __tablename__ = "adaptation_source"
    __table_args__ = (
        UniqueConstraint(
            "adaptation_id",
            "source_year",
            "source_question_number",
            name="uq_adaptation_source_ref",
        ),
        Index(
            "ix_adaptation_source_source",
            "source_year",
            "source_question_number",
        ),
    )

    adaptation_id: int = Field(
        foreign_key="adaptation_question.id",
        ondelete="CASCADE",
        index=True,
        description="改编题 ID",
    )
    source_year: int = Field(description="来源真题年份")
    source_question_number: int = Field(description="来源真题题号")
    exam_question_id: int | None = Field(
        default=None,
        foreign_key="exam_question.id",
        ondelete="SET NULL",
        index=True,
        description="解析命中的真题 ID",
    )
