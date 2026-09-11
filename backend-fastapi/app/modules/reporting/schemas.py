"""统计与导出模块请求、响应模型。"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExamCategoryStatsRequest(BaseModel):
    """真题分类统计请求。"""

    subject_id: int | None = Field(default=None, ge=1, description="科目 ID")


class ExamCategoryStatsExportRequest(BaseModel):
    """真题分类统计导出请求。"""

    subject_id: int | None = Field(default=None, ge=1, description="科目 ID")
    format: Literal["markdown", "xlsx"] = Field(
        default="markdown",
        description="导出格式",
    )


class ExamExportRequest(BaseModel):
    """真题导出请求。"""

    subject_id: int = Field(..., ge=1, description="科目 ID")
    format: Literal["markdown"] = Field(default="markdown", description="导出格式")


class ExamCategoryStatItem(BaseModel):
    """真题分类统计项。"""

    category_name: str
    count: int = Field(..., ge=0)
    choice_count: int = Field(default=0, ge=0)
    subjective_count: int = Field(default=0, ge=0)

    model_config = ConfigDict(from_attributes=True)


class ExamCategoryStatsTreeItem(BaseModel):
    """真题分类统计树节点。"""

    category_id: int | None = Field(
        default=None,
        ge=1,
        description="分类 ID；未归档节点为空",
    )
    parent_id: int | None = Field(default=None, ge=1, description="父分类 ID")
    category_name: str = Field(..., description="分类名称")
    order_num: int = Field(default=0, ge=0, description="同级手工顺序")
    enabled: bool = Field(default=True, description="是否启用")
    is_unfiled: bool = Field(default=False, description="是否为未归档虚拟节点")
    count: int = Field(default=0, ge=0, description="本节点直接引用的题目数")
    choice_count: int = Field(default=0, ge=0, description="本节点直接引用的选择题数")
    subjective_count: int = Field(default=0, ge=0, description="本节点直接引用的主观题数")
    subtree_count: int = Field(
        default=0,
        ge=0,
        description="本节点及所有后代的题目 ID 去重数",
    )
    subtree_choice_count: int = Field(
        default=0,
        ge=0,
        description="本节点及所有后代的选择题 ID 去重数",
    )
    subtree_subjective_count: int = Field(
        default=0,
        ge=0,
        description="本节点及所有后代的主观题 ID 去重数",
    )
    children: list["ExamCategoryStatsTreeItem"] = Field(
        default_factory=list,
        description="子分类统计节点",
    )

    model_config = ConfigDict(from_attributes=True)


class ExamSubjectCategoryStats(BaseModel):
    """单个科目的真题分类统计树。"""

    subject_id: int | None = Field(default=None, ge=1, description="科目 ID")
    subject_name: str = Field(..., description="科目名称")
    total_count: int = Field(default=0, ge=0, description="该科目去重题目总数")
    category_reference_count: int = Field(
        default=0,
        ge=0,
        description="该科目分类引用总数",
    )
    categories: list[ExamCategoryStatsTreeItem] = Field(
        default_factory=list,
        description="按手工顺序排列的分类树",
    )

    model_config = ConfigDict(from_attributes=True)


class ExamCategoryStatsResponse(BaseModel):
    """真题分类统计响应。"""

    subject_id: int | None = Field(default=None, ge=1)
    subject_name: str | None = None
    total_count: int = Field(default=0, ge=0, description="按题目 ID 去重后的题目总数")
    category_reference_count: int = Field(
        default=0,
        ge=0,
        description="分类引用总数，一题多分类时分别计入",
    )
    stats: list[ExamCategoryStatItem] = Field(default_factory=list)
    category_tree: list[ExamSubjectCategoryStats] = Field(
        default_factory=list,
        description="按科目和分类层级排列的统计树",
    )

    model_config = ConfigDict(from_attributes=True)


class ExportResultResponse(BaseModel):
    """文件导出结果。"""

    filename: str
    content_type: str
    file_bytes: bytes


ExamCategoryStatsTreeItem.model_rebuild()
