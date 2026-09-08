"""分类管理模块请求与响应模型。"""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


CategoryQuestionType = Literal["exam", "mock", "exercise"]


class CategoryQueryRequest(BaseModel):
    """分类查询请求。"""

    question_type: CategoryQuestionType = Field(
        default="exam",
        description="题目类型",
    )


class CategoryBySubjectQueryRequest(CategoryQueryRequest):
    """按科目查询分类的请求。"""


class AvailableParentCategoriesRequest(BaseModel):
    """查询可选父分类的请求。"""

    subject_id: int = Field(..., ge=1, description="科目 ID")
    exclude_id: int | None = Field(default=None, ge=1, description="排除的分类 ID")


class CategoryStatsRequest(CategoryQueryRequest):
    """分类统计请求。"""


class ExamCategoryCreateRequest(BaseModel):
    """分类创建请求；分类编码由服务端自动生成。"""
    subject_id: int = Field(
        ...,
        ge=1,
        description="所属科目ID",
        examples=[1],
    )
    parent_id: int | None = Field(
        default=None,
        ge=1,
        description="父分类ID（NULL表示顶级分类）",
        examples=[None],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="分类名称",
        examples=["栈和队列"],
    )
    description: str | None = Field(
        default=None,
        description="分类描述",
        examples=["栈和队列相关题目"],
    )
    order_num: int = Field(
        ...,
        ge=0,
        description="排序序号（升序）",
        examples=[1],
    )
    enabled: bool = Field(
        default=True,
        description="是否启用",
        examples=[True],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "subject_id": 1,
                    "parent_id": None,
                    "name": "栈和队列",
                    "description": "栈和队列相关题目",
                    "order_num": 1,
                    "enabled": True,
                }
            ]
        }
    )


class ExamCategoryUpdateRequest(BaseModel):
    """分类更新请求；分类编码不可手动修改。"""
    subject_id: int | None = Field(
        default=None,
        ge=1,
        description="所属科目ID",
        validation_alias=AliasChoices("subject_id", "subjectId"),
    )
    parent_id: int | None = Field(
        default=None,
        ge=1,
        description="父分类ID",
        validation_alias=AliasChoices("parent_id", "parentId"),
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="分类名称"
    )
    description: str | None = Field(
        default=None,
        description="分类描述"
    )
    order_num: int | None = Field(
        default=None,
        ge=0,
        description="排序序号",
        validation_alias=AliasChoices("order_num", "orderNum"),
    )
    enabled: bool | None = Field(
        default=None,
        description="是否启用"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "栈和队列（修订版）",
                    "order_num": 2,
                    "enabled": True,
                }
            ]
        }
    )


class ExamCategoryMoveRequest(BaseModel):
    """相对目标移动分类；空目标仅用于移至顶级末尾。"""

    target_id: int | None = Field(default=None, ge=1, description="目标分类 ID")
    position: Literal["before", "inside", "after"] = Field(
        ..., description="置于目标之前、移入目标或置于目标之后"
    )

    @model_validator(mode="after")
    def validate_target(self) -> "ExamCategoryMoveRequest":
        if self.target_id is None and self.position != "inside":
            raise ValueError("移至顶级时 position 必须为 inside")
        return self


class ExamCategoryResponse(BaseModel):
    """分类响应（单个节点）"""
    id: int = Field(..., ge=1, description="分类ID", examples=[1])
    subject_id: int = Field(..., ge=1, description="所属科目ID", examples=[1])
    subject_name: str | None = Field(default=None, description="科目名称")
    parent_id: int | None = Field(default=None, ge=1, description="父分类ID")
    parent_name: str | None = Field(default=None, description="父分类名称")
    name: str = Field(..., description="分类名称", examples=["栈和队列"])
    code: str = Field(..., description="系统生成的层级分类编码", examples=["sjjg-01-xxb-01-sxb"])
    description: str | None = Field(default=None, description="分类描述")
    order_num: int = Field(..., ge=0, description="排序序号", examples=[1])
    enabled: bool = Field(..., description="是否启用", examples=[True])
    question_count: int | None = Field(
        default=None,
        ge=0,
        description="直接引用该分类的题目数量（统计）",
        examples=[10]
    )
    subtree_question_count: int | None = Field(
        default=None,
        ge=0,
        description="该分类及其子分类去重后的题目数量",
        examples=[10]
    )
    create_time: str | None = Field(default=None, description="创建时间")
    update_time: str | None = Field(default=None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class ExamCategoryTreeResponse(BaseModel):
    """分类树形响应（带子分类列表和题目统计）"""
    id: int = Field(..., ge=1, description="分类ID", examples=[1])
    subject_id: int = Field(..., ge=1, description="所属科目ID", examples=[1])
    subject_name: str | None = Field(default=None, description="科目名称")
    parent_id: int | None = Field(default=None, ge=1, description="父分类ID")
    parent_name: str | None = Field(default=None, description="父分类名称")
    name: str = Field(..., description="分类名称", examples=["栈和队列"])
    code: str = Field(..., description="系统生成的层级分类编码", examples=["sjjg-01-xxb-01-sxb"])
    description: str | None = Field(default=None, description="分类描述")
    order_num: int = Field(..., ge=0, description="排序序号", examples=[1])
    enabled: bool = Field(..., description="是否启用", examples=[True])
    question_count: int | None = Field(
        default=None,
        ge=0,
        description="直接引用该分类的题目数量（统计）",
        examples=[10]
    )
    subtree_question_count: int | None = Field(
        default=None,
        ge=0,
        description="该分类及其子分类去重后的题目数量",
        examples=[10]
    )
    children: list["ExamCategoryTreeResponse"] = Field(
        default_factory=list,
        description="子分类列表"
    )

    model_config = ConfigDict(from_attributes=True)


class SubjectStatItem(BaseModel):
    """按科目的统计数据项"""
    subject_id: int = Field(..., ge=1, description="科目ID")
    subject_name: str = Field(..., description="科目名称")
    category_count: int = Field(..., ge=0, description="分类数量")
    enabled_category_count: int = Field(..., ge=0, description="启用分类数量")
    question_count: int = Field(..., ge=0, description="去重后的题目数量")

    model_config = ConfigDict(from_attributes=True)


class ExamCategoryStatResponse(BaseModel):
    """分类统计响应"""
    subject_stats: list[SubjectStatItem] = Field(
        ...,
        description="按科目的统计数据"
    )
    total_question_count: int = Field(
        ...,
        ge=0,
        description="去重后的题目总数"
    )
    total_categories: int = Field(
        ...,
        ge=0,
        description="分类总数",
        examples=[100]
    )
    enabled_categories: int = Field(
        ...,
        ge=0,
        description="启用分类数",
        examples=[80]
    )
    question_type: CategoryQuestionType = Field(
        ...,
        description="统计的题目类型",
        examples=["exam"]
    )

    model_config = ConfigDict(from_attributes=True)


class ExamCategoryUsageResponse(BaseModel):
    """分类引用检查响应"""
    id: int = Field(..., ge=1, description="分类ID", examples=[1])
    name: str = Field(..., description="分类名称", examples=["栈和队列"])
    has_children: bool = Field(
        ...,
        description="是否有子分类",
        examples=[False]
    )
    question_count: int = Field(
        ...,
        ge=0,
        description="被真题引用的次数",
        examples=[5]
    )
    mock_count: int = Field(
        ...,
        ge=0,
        description="被模拟题引用的次数",
        examples=[3]
    )
    can_delete: bool = Field(
        ...,
        description="是否可以删除",
        examples=[True]
    )

    model_config = ConfigDict(from_attributes=True)


# 更新正向引用
ExamCategoryTreeResponse.model_rebuild()
