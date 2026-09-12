"""目录模块持久化模型。"""
from typing import List, Optional

from sqlalchemy import Index
from sqlmodel import Field, Relationship

from web408.models.base import BaseModel


class Subject(BaseModel, table=True):
    """科目模型。"""
    __tablename__ = "subject"

    name: str = Field(unique=True, description="科目名称")
    code: str = Field(unique=True, description="科目编码")
    description: str | None = Field(default=None, description="科目描述")
    order_num: int = Field(default=0, description="排序序号")
    enabled: bool = Field(default=True, description="是否启用")

    # 关系
    chapters: List["Chapter"] = Relationship(
        back_populates="subject",
        cascade_delete=True,
        passive_deletes=True,
    )
    exam_categories: List["ExamCategory"] = Relationship(
        back_populates="subject",
        cascade_delete=True,
        passive_deletes=True,
    )
    exam_questions: List["ExamQuestion"] = Relationship(
        back_populates="subject",
        passive_deletes=True,
    )
    mock_questions: List["MockQuestion"] = Relationship(
        back_populates="subject",
        passive_deletes=True,
    )


class Chapter(BaseModel, table=True):
    """章节模型。"""
    __tablename__ = "chapter"

    subject_id: int = Field(
        foreign_key="subject.id",
        ondelete="CASCADE",
        index=True,
        description="所属科目ID",
    )
    parent_id: int | None = Field(
        default=None,
        foreign_key="chapter.id",
        ondelete="CASCADE",
        index=True,
        description="父章节ID",
    )
    name: str = Field(description="章节名称")
    order_num: int = Field(default=0, description="排序序号")
    enabled: bool = Field(default=True, description="是否启用")

    # 关系
    subject: Optional["Subject"] = Relationship(back_populates="chapters")
    parent: Optional["Chapter"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Chapter.id"}
    )
    children: List["Chapter"] = Relationship(
        back_populates="parent",
        passive_deletes=True,
    )


class ExamCategory(BaseModel, table=True):
    """分类标签模型。"""
    __tablename__ = "exam_category"
    __table_args__ = (
        Index("uq_exam_category_subject_name", "subject_id", "name", unique=True),
        Index("uq_exam_category_subject_code", "subject_id", "code", unique=True),
    )

    subject_id: int = Field(
        foreign_key="subject.id",
        ondelete="CASCADE",
        index=True,
        description="所属科目ID",
    )
    parent_id: int | None = Field(
        default=None,
        foreign_key="exam_category.id",
        ondelete="CASCADE",
        index=True,
        description="父分类ID",
    )
    name: str = Field(description="分类名称")
    code: str = Field(description="系统生成的层级分类编码")
    description: str | None = Field(default=None, description="分类描述")
    order_num: int = Field(default=0, description="排序序号")
    enabled: bool = Field(default=True, description="是否启用")

    # 关系
    subject: Optional["Subject"] = Relationship(back_populates="exam_categories")
    parent: Optional["ExamCategory"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "ExamCategory.id"}
    )
    children: List["ExamCategory"] = Relationship(
        back_populates="parent",
        passive_deletes=True,
    )
