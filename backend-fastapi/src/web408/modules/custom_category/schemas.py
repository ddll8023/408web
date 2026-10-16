"""自定义分类模块请求与响应模型。"""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class CustomCategoryTreeRequest(BaseModel):
    """自定义分类树查询请求。"""

    enabled_only: bool = Field(
        default=False,
        description="是否仅返回启用分类",
        validation_alias=AliasChoices("enabled_only", "enabledOnly"),
    )


class CustomCategoryCreateRequest(BaseModel):
    """自定义分类创建请求；分类编码由服务端自动生成。"""

    subject_id: int = Field(
        ...,
        ge=1,
        description="所属科目ID",
        examples=[1],
    )
    parent_id: int | None = Field(
        default=None,
        ge=1,
        description="父分类ID（NULL 表示顶级分类）",
        examples=[None],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="分类名称",
        examples=["易错题"],
    )
    description: str | None = Field(
        default=None,
        description="分类描述",
        examples=["反复出错、需要二刷的题目"],
    )
    order_num: int = Field(
        default=0,
        ge=0,
        description="排序序号（升序）",
        examples=[1],
    )
    enabled: bool = Field(
        default=True,
        description="是否启用",
        examples=[True],
    )


class CustomCategoryUpdateRequest(BaseModel):
    """自定义分类更新请求；分类编码不可手动修改。"""

    subject_id: int | None = Field(
        default=None,
        ge=1,
        description="所属科目ID",
        validation_alias=AliasChoices("subject_id", "subjectId"),
    )
    parent_id: int | None = Field(
        default=None,
        ge=1,
        description="父分类ID（传 null 表示移到顶级）",
        validation_alias=AliasChoices("parent_id", "parentId"),
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="分类名称",
    )
    description: str | None = Field(
        default=None,
        description="分类描述",
    )
    order_num: int | None = Field(
        default=None,
        ge=0,
        description="排序序号",
        validation_alias=AliasChoices("order_num", "orderNum"),
    )
    enabled: bool | None = Field(
        default=None,
        description="是否启用",
    )

    model_config = ConfigDict(populate_by_name=True)


class CustomCategoryMoveRequest(BaseModel):
    """相对目标移动自定义分类；空目标仅用于移至顶级末尾。"""

    target_id: int | None = Field(
        default=None,
        ge=1,
        description="目标分类 ID",
    )
    position: Literal["before", "inside", "after"] = Field(
        ...,
        description="置于目标之前、移入目标或置于目标之后",
    )

    @model_validator(mode="after")
    def validate_target(self) -> "CustomCategoryMoveRequest":
        if self.target_id is None and self.position != "inside":
            raise ValueError("移至顶级时 position 必须为 inside")
        return self


class AvailableParentCategoriesRequest(BaseModel):
    """查询可选父分类的请求。"""

    subject_id: int = Field(..., ge=1, description="科目 ID")
    exclude_id: int | None = Field(
        default=None,
        ge=1,
        description="排除的分类 ID（自身及其子孙）",
    )


class CustomCategoryCodeRebuildRequest(BaseModel):
    """自定义分类编码重排请求；category_id 为空时按科目整体重排。"""

    subject_id: int = Field(
        ...,
        ge=1,
        description="科目 ID",
        validation_alias=AliasChoices("subject_id", "subjectId"),
    )
    category_id: int | None = Field(
        default=None,
        ge=1,
        description="只重排该分类的子孙编码，为空时重排整个科目",
        validation_alias=AliasChoices("category_id", "categoryId"),
    )

    model_config = ConfigDict(populate_by_name=True)


class CustomCategoryResponse(BaseModel):
    """自定义分类响应（单个节点）。"""

    id: int = Field(..., ge=1, description="分类ID")
    subject_id: int = Field(..., ge=1, description="所属科目ID")
    subject_name: str | None = Field(default=None, description="科目名称")
    parent_id: int | None = Field(default=None, ge=1, description="父分类ID")
    parent_name: str | None = Field(default=None, description="父分类名称")
    name: str = Field(..., description="分类名称")
    code: str = Field(..., description="系统生成的层级分类编码")
    description: str | None = Field(default=None, description="分类描述")
    order_num: int = Field(..., ge=0, description="排序序号")
    enabled: bool = Field(..., description="是否启用")
    create_time: str | None = Field(default=None, description="创建时间")
    update_time: str | None = Field(default=None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class CustomCategoryTreeResponse(CustomCategoryResponse):
    """自定义分类树形响应（带子分类列表）。"""

    question_count: int | None = Field(
        default=None,
        ge=0,
        description="直接挂该分类的真题数",
    )
    subtree_question_count: int | None = Field(
        default=None,
        ge=0,
        description="含子孙分类的真题数",
    )
    children: list["CustomCategoryTreeResponse"] = Field(
        default_factory=list,
        description="子分类列表",
    )


class CustomCategorySubjectStatItem(BaseModel):
    """按科目的自定义分类数量与已挂题目数统计项。"""

    subject_id: int = Field(..., ge=1, description="科目ID")
    subject_name: str = Field(..., description="科目名称")
    category_count: int = Field(..., ge=0, description="分类数量")
    enabled_category_count: int = Field(..., ge=0, description="启用分类数量")
    question_count: int = Field(..., ge=0, description="已挂自定义分类的题目数")


class CustomCategoryStatResponse(BaseModel):
    """自定义分类统计响应。"""

    subject_stats: list[CustomCategorySubjectStatItem] = Field(
        ...,
        description="按科目的统计数据",
    )
    total_categories: int = Field(..., ge=0, description="分类总数")
    enabled_categories: int = Field(..., ge=0, description="启用分类数")


# 更新正向引用
CustomCategoryTreeResponse.model_rebuild()
