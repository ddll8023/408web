"""
认证模块路由
"""
from fastapi import APIRouter, Depends, status
from app.database.connection import SessionDep
from app.services.auth_service import AuthService
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from app.schemas.common import Response

router = APIRouter()


@router.post(
    "/register",
    summary="用户注册",
    description="新用户注册，提供用户名、密码和邮箱",
    response_model=Response[None],
    status_code=status.HTTP_200_OK
)
async def register(
    request: RegisterRequest,
    session: SessionDep
) -> Response[None]:
    """
    用户注册接口

    Args:
        request: 注册请求
        session: 数据库会话

    Returns:
        注册结果
    """
    auth_service = AuthService(session)
    await auth_service.register(request)
    return Response(code=200, message="注册成功")


@router.post(
    "/login",
    summary="用户登录",
    description="用户登录，成功返回JWT Token和用户信息",
    response_model=Response[AuthResponse],
    status_code=status.HTTP_200_OK
)
async def login(
    request: LoginRequest,
    session: SessionDep
) -> Response[AuthResponse]:
    """
    用户登录接口

    Args:
        request: 登录请求
        session: 数据库会话

    Returns:
        认证响应（包含Token）
    """
    auth_service = AuthService(session)
    auth_response = await auth_service.login(request)
    return Response(data=auth_response, message="登录成功")
