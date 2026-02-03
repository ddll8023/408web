"""
全局响应中间件
统一处理所有HTTP响应的CORS头，确保异常响应也携带CORS头
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.config.settings import settings


class GlobalCorsMiddleware(BaseHTTPMiddleware):
    """
    全局CORS响应中间件

    职责：
    - 为所有响应注入CORS头
    - 处理OPTIONS预检请求
    - 确保异常响应也携带CORS头（FastAPI异常处理器可能生成不包含CORS头的响应）
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        中间件分发处理

        Args:
            request: HTTP请求
            call_next: 下一个处理函数

        Returns:
            HTTP响应（包含CORS头）
        """
        # 处理OPTIONS预检请求
        if request.method == "OPTIONS":
            response = Response(status_code=204)
            self._add_cors_headers(response, request)
            return response

        # 继续处理请求
        response = await call_next(request)

        # 为所有响应添加CORS头（无论是否发生异常）
        self._add_cors_headers(response, request)

        return response

    def _add_cors_headers(self, response: Response, request: Request) -> None:
        """
        添加CORS头到响应

        Args:
            response: HTTP响应对象
            request: HTTP请求对象（用于获取原始请求头）
        """
        # 从请求头获取原始来源，用于动态响应
        origin = request.headers.get("Origin", "")

        # 如果是允许的来源之一，使用该来源；否则拒绝请求
        allowed_origins = settings.cors.origins
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        elif not origin:
            # 如果没有Origin头（非浏览器请求），使用通配符
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            # 未授权的来源，使用通配符但不允许凭证
            response.headers["Access-Control-Allow-Origin"] = "*"

        # 允许携带凭证（仅当使用具体来源时）
        if response.headers.get("Access-Control-Allow-Origin") != "*":
            response.headers["Access-Control-Allow-Credentials"] = "true"

        # 允许的请求方法
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"

        # 允许的请求头
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, X-Requested-With"

        # 暴露的响应头（客户端可读取）
        response.headers["Access-Control-Expose-Headers"] = "Authorization, Content-Disposition"

        # 预检请求缓存时间（1小时）
        if request.method == "OPTIONS":
            response.headers["Access-Control-Max-Age"] = "3600"
