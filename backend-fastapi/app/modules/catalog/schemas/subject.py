"""科目管理模块请求与响应模型。"""

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreateRequest(BaseModel):
    """科目创建请求。"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="科目名称",
        examples=["数据结构"],
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="科目编码",
        examples=["data-structure"],
    )
    description: str | None = Field(
        default=None,
        description="科目描述",
        examples=["数据结构相关题目"],
    )
    order_num: int = Field(
        ...,
        ge=0,
        description="排序序号",
        examples=[1],
    )
    enabled: bool = Field(
        ...,
        description="是否启用",
        examples=[True],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "数据结构",
                    "code": "data-structure",
                    "description": "数据结构相关题目",
                    "order_num": 1,
                    "enabled": True,
                }
            ]
        }
    )


class SubjectUpdateRequest(BaseModel):
    """科目更新请求。"""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="科目名称"
    )
    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="科目编码"
    )
    description: str | None = Field(
        default=None,
        description="科目描述"
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
                    "name": "数据结构",
                    "code": "data-structure",
                    "description": "数据结构相关题目",
                    "order_num": 1,
                    "enabled": True,
                }
            ]
        }
    )


class SubjectCodeRequest(BaseModel):
    """按编码查询科目的请求。"""

    code: str = Field(..., min_length=1, max_length=50, description="科目编码")


class SubjectResponse(BaseModel):
    """科目响应。"""

    id: int = Field(..., ge=1, description="科目ID", examples=[1])
    name: str = Field(..., description="科目名称", examples=["数据结构"])
    code: str = Field(..., description="科目编码", examples=["data-structure"])
    description: str | None = Field(default=None, description="科目描述")
    order_num: int = Field(..., ge=0, description="排序序号", examples=[1])
    enabled: bool = Field(..., description="是否启用", examples=[True])
    question_count: int | None = Field(
        default=None,
        ge=0,
        description="题目总数（统计）",
        examples=[100],
    )

    model_config = ConfigDict(from_attributes=True)
