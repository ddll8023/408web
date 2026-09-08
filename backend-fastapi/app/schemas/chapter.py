"""章节管理模块请求与响应模型。"""

from pydantic import BaseModel, ConfigDict, Field


class ChapterCreateRequest(BaseModel):
    """章节创建请求。"""

    subject_id: int = Field(
        ...,
        ge=1,
        description="所属科目ID",
        examples=[1],
    )
    parent_id: int | None = Field(
        default=None,
        ge=1,
        description="父章节ID（NULL表示顶级章节）",
        examples=[None],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="章节名称",
        examples=["线性表"],
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
                    "name": "线性表",
                    "order_num": 2,
                    "enabled": True,
                }
            ]
        }
    )


class ChapterUpdateRequest(BaseModel):
    """章节更新请求。"""

    subject_id: int | None = Field(
        default=None,
        ge=1,
        description="所属科目ID"
    )
    parent_id: int | None = Field(
        default=None,
        ge=1,
        description="父章节ID"
    )
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="章节名称"
    )
    order_num: int | None = Field(
        default=None,
        ge=0,
        description="排序序号"
    )
    enabled: bool | None = Field(
        default=None,
        description="是否启用"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "线性表（修订版）",
                    "order_num": 3,
                    "enabled": True,
                }
            ]
        }
    )


class ChapterResponse(BaseModel):
    """章节响应（单个节点）。"""

    id: int = Field(..., ge=1, description="章节ID", examples=[1])
    subject_id: int = Field(..., ge=1, description="所属科目ID", examples=[1])
    parent_id: int | None = Field(default=None, ge=1, description="父章节ID")
    name: str = Field(..., description="章节名称", examples=["线性表"])
    order_num: int = Field(..., ge=0, description="排序序号", examples=[1])
    enabled: bool = Field(..., description="是否启用", examples=[True])
    create_time: str | None = Field(default=None, description="创建时间")
    update_time: str | None = Field(default=None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class ChapterTreeResponse(BaseModel):
    """章节树形响应（带子章节列表）。"""

    id: int = Field(..., ge=1, description="章节ID", examples=[1])
    subject_id: int = Field(..., ge=1, description="所属科目ID", examples=[1])
    parent_id: int | None = Field(default=None, ge=1, description="父章节ID")
    name: str = Field(..., description="章节名称", examples=["线性表"])
    order_num: int = Field(..., ge=0, description="排序序号", examples=[1])
    enabled: bool = Field(..., description="是否启用", examples=[True])
    children: list["ChapterTreeResponse"] = Field(
        default_factory=list,
        description="子章节列表"
    )

    model_config = ConfigDict(from_attributes=True)


# 更新正向引用
ChapterTreeResponse.model_rebuild()
