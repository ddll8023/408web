"""统一 API 响应与分页模型。"""
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应结构。"""

    code: int = Field(default=200, description="业务状态码")
    message: str = Field(default="成功", description="状态描述")
    data: T | None = Field(default=None, description="响应数据")


class PageInfo(BaseModel):
    """分页元数据。"""

    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, description="每页大小")
    total: int = Field(..., ge=0, description="总记录数")
    total_pages: int = Field(..., ge=0, description="总页数")


class PaginatedResponse(BaseModel, Generic[T]):
    """统一列表响应数据结构。"""

    lists: list[T] = Field(default_factory=list, description="当前页数据")
    pagination: PageInfo = Field(..., description="分页信息")


def success_response(data: object | None = None, message: str = "成功") -> dict[str, object | None]:
    """构造统一成功响应。"""
    return {
        "code": 200,
        "message": message,
        "data": data,
    }


def error_response(code: int, message: str) -> dict[str, object | None]:
    """构造统一错误响应。"""
    return {
        "code": code,
        "message": message,
        "data": None,
    }


# 兼容尚未迁移的外部导入；新代码统一使用 ApiResponse。
Response = ApiResponse
