"""
认证依赖模块
提供 FastAPI 依赖注入的认证依赖函数
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlmodel import select
from app.database.connection import get_async_session
from app.models.entities import User
from app.utils.security import (
    extract_token_from_header,
    get_token_payload,
    verify_password
)
from app.exception import UnauthorizedException, ForbiddenException


class AuthUser:
    """认证用户信息"""

    def __init__(self, user_id: int, username: str, role: str):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.is_admin = role == "ADMIN"


async def get_current_user(
    request: Request,
    session=Depends(get_async_session)
) -> AuthUser:
    """
    获取当前登录用户

    Args:
        request: FastAPI 请求对象
        session: 数据库会话

    Returns:
        AuthUser: 当前登录用户信息

    Raises:
        UnauthorizedException: 未登录或 Token 无效
    """
    # 从请求头提取 Token
    auth_header = request.headers.get("Authorization")
    token = extract_token_from_header(auth_header)

    if not token:
        raise UnauthorizedException("未提供认证令牌")

    # 解析 Token
    payload = get_token_payload(token)

    username = payload.get("username")
    role = payload.get("role", "USER")

    if not username:
        raise UnauthorizedException("令牌中缺少用户信息")

    # 从数据库获取用户
    user = await session.exec(
        select(User).where(User.username == username)
    )
    user = user.first()

    if user is None:
        raise UnauthorizedException("用户不存在")

    if not user.enabled:
        raise UnauthorizedException("用户账户已禁用")

    return AuthUser(
        user_id=user.id,
        username=user.username,
        role=user.role
    )


async def get_current_admin(
    current_user: AuthUser = Depends(get_current_user)
) -> AuthUser:
    """
    获取当前管理员用户

    Args:
        current_user: 当前登录用户

    Returns:
        AuthUser: 管理员用户信息

    Raises:
        ForbiddenException: 无管理员权限
    """
    if current_user.role != "ADMIN":
        raise ForbiddenException("需要管理员权限")

    return current_user


async def get_optional_user(
    request: Request,
    session=Depends(get_async_session)
) -> Optional[AuthUser]:
    """
    获取当前用户（可选）

    如果未登录返回 None，不会抛出异常

    Args:
        request: FastAPI 请求对象
        session: 数据库会话

    Returns:
        AuthUser | None: 当前登录用户或 None
    """
    try:
        return await get_current_user(request, session)
    except UnauthorizedException:
        return None
