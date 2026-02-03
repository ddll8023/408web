"""
科目管理模块请求与响应模型
"""
from typing import Optional
from pydantic import BaseModel, Field


class SubjectCreateRequest(BaseModel):
    """科目创建请求"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="科目名称",
        examples=["数据结构"]
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="科目编码",
        examples=["data-structure"]
    )
    description: Optional[str] = Field(
        default=None,
        description="科目描述",
        examples=["数据结构相关题目"]
    )
    order_num: int = Field(
        ...,
        ge=0,
        description="排序序号",
        examples=[1]
    )
    enabled: bool = Field(
        ...,
        description="是否启用",
        examples=[True]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "数据结构",
                    "code": "data-structure",
                    "description": "数据结构相关题目",
                    "order_num": 1,
                    "enabled": True
                }
            ]
        }
    }


class SubjectUpdateRequest(BaseModel):
    """科目更新请求"""
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="科目名称"
    )
    code: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="科目编码"
    )
    description: Optional[str] = Field(
        default=None,
        description="科目描述"
    )
    order_num: Optional[int] = Field(
        default=None,
        ge=0,
        description="排序序号"
    )
    enabled: Optional[bool] = Field(
        default=None,
        description="是否启用"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "数据结构",
                    "code": "data-structure",
                    "description": "数据结构相关题目",
                    "order_num": 1,
                    "enabled": True
                }
            ]
        }
    }


class SubjectResponse(BaseModel):
    """科目响应"""
    id: int = Field(..., description="科目ID", examples=[1])
    name: str = Field(..., description="科目名称", examples=["数据结构"])
    code: str = Field(..., description="科目编码", examples=["data-structure"])
    description: Optional[str] = Field(default=None, description="科目描述")
    order_num: int = Field(..., description="排序序号", examples=[1])
    enabled: bool = Field(..., description="是否启用", examples=[True])
    question_count: Optional[int] = Field(
        default=None,
        description="题目总数（统计）",
        examples=[100]
    )

    model_config = {
        "from_attributes": True
    }
