"""认证 HTTP 路由。"""
from fastapi import APIRouter, status

from app.api.dependencies import SessionDep
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService


router = APIRouter()


@router.post(
    "/register",
    summary="用户注册",
    description="新用户注册，提供用户名、密码和邮箱",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
async def register(request: RegisterRequest, session: SessionDep) -> ApiResponse[None]:
    """用户注册接口。"""
    await AuthService(session).register(request)
    return ApiResponse(code=200, message="注册成功")


@router.post(
    "/login",
    summary="用户登录",
    description="用户登录，成功返回 JWT Token 和用户信息",
    response_model=ApiResponse[AuthResponse],
    status_code=status.HTTP_200_OK,
)
async def login(request: LoginRequest, session: SessionDep) -> ApiResponse[AuthResponse]:
    """用户登录接口。"""
    auth_response = await AuthService(session).login(request)
    return ApiResponse(data=auth_response, message="登录成功")
