"""业务异常及应用级异常映射。"""
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.schemas.common import error_response


logger = logging.getLogger(__name__)


class BusinessException(Exception):
    """可安全返回给客户端的业务异常。"""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class NotFoundException(BusinessException):
    """资源不存在异常。"""

    def __init__(self, resource: str = "资源") -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, f"{resource}不存在")


class UnauthorizedException(BusinessException):
    """未认证异常。"""

    def __init__(self, message: str = "未登录或登录已过期") -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, message)


class ForbiddenException(BusinessException):
    """无权限异常。"""

    def __init__(self, message: str = "无权访问") -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, message)


class ValidationException(BusinessException):
    """业务参数校验异常。"""

    def __init__(self, message: str = "参数错误") -> None:
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


class ConflictException(BusinessException):
    """资源冲突异常。"""

    def __init__(self, message: str = "资源冲突") -> None:
        super().__init__(status.HTTP_409_CONFLICT, message)


class InfrastructureException(BusinessException):
    """基础设施异常，客户端只接收固定公开消息。"""

    def __init__(self, message: str = "服务器内部错误") -> None:
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, message)


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """处理业务异常。"""
    return JSONResponse(
        status_code=exc.code,
        content=error_response(exc.code, exc.message),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理 HTTP 异常并保持统一响应结构。"""
    message = exc.detail if isinstance(exc.detail, str) else "请求处理失败"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, message),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """处理请求 Schema 校验异常。"""
    messages = []
    for error in exc.errors():
        location = " -> ".join(str(item) for item in error.get("loc", ()))
        message = error.get("msg", "参数错误")
        messages.append(f"{location}: {message}" if location else message)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "; ".join(messages) or "参数错误",
        ),
    )


async def integrity_exception_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """将数据库约束错误映射为安全的业务错误。"""
    logger.error(
        "数据库完整性约束失败: path=%s",
        request.url.path,
        exc_info=True,
    )
    source_message = str(getattr(exc, "orig", "")).upper()
    if "UNIQUE" in source_message:
        code = status.HTTP_409_CONFLICT
        message = "资源已存在"
    elif "FOREIGN KEY" in source_message:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        message = "关联数据无效"
    else:
        code = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = "服务器内部错误"

    return JSONResponse(status_code=code, content=error_response(code, message))


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """处理其他数据库异常。"""
    logger.error("数据库操作失败: path=%s", request.url.path, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "服务器内部错误"),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理未分类异常，不向客户端暴露内部异常文本。"""
    logger.error("未处理的服务器异常: path=%s", request.url.path, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "服务器内部错误"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """注册统一异常处理器。"""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
