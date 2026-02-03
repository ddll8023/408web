"""
统一响应格式定义模块
遵循 RESTful API 设计规范
"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field


T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """
    统一响应格式

    Attributes:
        code: 状态码，200 表示成功
        message: 状态描述信息
        data: 响应数据，可为 None
    """
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="成功", description="状态描述")
    data: Optional[T] = Field(default=None, description="响应数据")


class PageInfo(BaseModel):
    """分页信息"""
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total: int = Field(..., description="总记录数")
    total_pages: int = Field(..., description="总页数")


class PaginatedResponse(Response):
    """分页响应格式"""
    data: Optional[dict] = Field(default=None, description="分页数据")

    @classmethod
    def create(
        cls,
        items: list,
        page: int,
        page_size: int,
        total: int,
        message: str = "success"
    ) -> "PaginatedResponse":
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            code=200,
            message=message,
            data={
                "items": items,
                "page_info": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages
                }
            }
        )


def success_response(data=None, message: str = "成功") -> dict:
    """
    快捷创建成功响应

    Args:
        data: 响应数据
        message: 状态消息

    Returns:
        dict: 统一格式的响应字典
    """
    return {
        "code": 200,
        "message": message,
        "data": data
    }


def error_response(code: int, message: str) -> dict:
    """
    快捷创建错误响应

    Args:
        code: 错误码
        message: 错误消息

    Returns:
        dict: 统一格式的错误响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": None
    }
