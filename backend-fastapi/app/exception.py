"""
异常处理模块
定义业务异常和全局异常处理器
"""
from typing import Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from app.schemas.common import error_response


class BusinessException(Exception):
    """
    业务异常基类

    Attributes:
        code: HTTP 状态码
        message: 错误消息
    """

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(self.message)


class NotFoundException(BusinessException):
    """资源不存在异常"""

    def __init__(self, resource: str = "资源"):
        super().__init__(
            code=status.HTTP_404_NOT_FOUND,
            message=f"{resource}不存在"
        )


class UnauthorizedException(BusinessException):
    """未授权异常"""

    def __init__(self, message: str = "未登录或登录已过期"):
        super().__init__(
            code=status.HTTP_401_UNAUTHORIZED,
            message=message
        )


class ForbiddenException(BusinessException):
    """禁止访问异常"""

    def __init__(self, message: str = "无权访问"):
        super().__init__(
            code=status.HTTP_403_FORBIDDEN,
            message=message
        )


class ValidationException(BusinessException):
    """参数验证异常"""

    def __init__(self, message: str = "参数错误"):
        super().__init__(
            code=status.HTTP_400_BAD_REQUEST,
            message=message
        )


class ConflictException(BusinessException):
    """资源冲突异常"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(
            code=status.HTTP_409_CONFLICT,
            message=message
        )


async def business_exception_handler(request: Request, exc: BusinessException):
    """业务异常处理器"""
    return JSONResponse(
        status_code=exc.code,
        content=error_response(exc.code, exc.message)
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail if exc.detail else "请求处理失败")
    )


async def validation_exception_handler(request: Request, exc):
    """请求验证异常处理器（pydantic）"""
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = " -> ".join(str(l) for l in error["loc"])
        error_messages.append(f"{loc}: {error['msg']}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "; ".join(error_messages)
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器（兜底）"""
    from app.config.settings import settings
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"服务器内部错误: {str(exc)}"
        ),
        headers={
            "Access-Control-Allow-Origin": settings.cors.origins[0] if settings.cors.origins else "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        }
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValidationException, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
