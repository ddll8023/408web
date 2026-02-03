"""
章节管理模块请求与响应模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ChapterCreateRequest(BaseModel):
    """章节创建请求"""
    subject_id: int = Field(
        ...,
        description="所属科目ID",
        examples=[1]
    )
    parent_id: Optional[int] = Field(
        default=None,
        description="父章节ID（NULL表示顶级章节）",
        examples=[None]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="章节名称",
        examples=["线性表"]
    )
    order_num: int = Field(
        ...,
        ge=0,
        description="排序序号（升序）",
        examples=[1]
    )
    enabled: bool = Field(
        default=True,
        description="是否启用",
        examples=[True]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subject_id": 1,
                    "parent_id": None,
                    "name": "线性表",
                    "order_num": 2,
                    "enabled": True
                }
            ]
        }
    }


class ChapterUpdateRequest(BaseModel):
    """章节更新请求"""
    subject_id: Optional[int] = Field(
        default=None,
        description="所属科目ID"
    )
    parent_id: Optional[int] = Field(
        default=None,
        description="父章节ID"
    )
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="章节名称"
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
                    "name": "线性表（修订版）",
                    "order_num": 3,
                    "enabled": True
                }
            ]
        }
    }


class ChapterResponse(BaseModel):
    """章节响应（单个节点）"""
    id: int = Field(..., description="章节ID", examples=[1])
    subject_id: int = Field(..., description="所属科目ID", examples=[1])
    parent_id: Optional[int] = Field(default=None, description="父章节ID")
    name: str = Field(..., description="章节名称", examples=["线性表"])
    order_num: int = Field(..., description="排序序号", examples=[1])
    enabled: bool = Field(..., description="是否启用", examples=[True])
    create_time: Optional[str] = Field(default=None, description="创建时间")
    update_time: Optional[str] = Field(default=None, description="更新时间")

    model_config = {
        "from_attributes": True
    }


class ChapterTreeResponse(BaseModel):
    """章节树形响应（带子章节列表）"""
    id: int = Field(..., description="章节ID", examples=[1])
    subject_id: int = Field(..., description="所属科目ID", examples=[1])
    parent_id: Optional[int] = Field(default=None, description="父章节ID")
    name: str = Field(..., description="章节名称", examples=["线性表"])
    order_num: int = Field(..., description="排序序号", examples=[1])
    enabled: bool = Field(..., description="是否启用", examples=[True])
    children: List["ChapterTreeResponse"] = Field(
        default_factory=list,
        description="子章节列表"
    )

    model_config = {
        "from_attributes": True
    }


# 更新正向引用
ChapterTreeResponse.model_rebuild()
