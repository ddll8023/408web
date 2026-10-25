"""自定义分类模块持久化模型。"""
from typing import List, Optional

from sqlalchemy import Index
from sqlmodel import Field, Relationship

from web408.models.base import BaseModel
from web408.modules.catalog.models import Subject


class CustomCategory(BaseModel, table=True):
    """自定义分类模型。

    与大纲分类平行存在，按科目组织为多级树；仅管理员维护。
    真题通过 custom_category 名称数组关联节点，而非保存分类 ID；改名需同步回写标签。
    """

    __tablename__ = "custom_category"
    __table_args__ = (
        Index(
            "uq_custom_category_subject_name",
            "subject_id",
            "name",
            unique=True,
        ),
        Index(
            "uq_custom_category_subject_code",
            "subject_id",
            "code",
            unique=True,
        ),
    )

    subject_id: int = Field(
        foreign_key="subject.id",
        ondelete="CASCADE",
        index=True,
        description="所属科目ID",
    )
    parent_id: int | None = Field(
        default=None,
        foreign_key="custom_category.id",
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
    subject: Optional[Subject] = Relationship()
    parent: Optional["CustomCategory"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "CustomCategory.id"},
    )
    children: List["CustomCategory"] = Relationship(
        back_populates="parent",
        passive_deletes=True,
    )
