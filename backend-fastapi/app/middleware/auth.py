"""认证与管理员权限依赖。"""
from typing import Optional

from fastapi import Depends, Request
from sqlmodel import select

from app.database.connection import SessionDep
from app.exception import ForbiddenException, UnauthorizedException
from app.models.entities import User
from app.models.enums import UserRoleEnum
from app.utils.security import extract_token_from_header, get_token_payload


class AuthUser:
    """经过数据库确认的当前用户。"""

    def __init__(self, user_id: int, username: str, role: str) -> None:
        self.user_id = user_id
        self.username = username
        self.role = role
        self.is_admin = role == UserRoleEnum.ADMIN.value


async def get_current_user(
    request: Request,
    session: SessionDep,
) -> AuthUser:
    """解析 Bearer Token，并以数据库账户状态为最终依据。"""
    token = extract_token_from_header(request.headers.get("Authorization"))
    if not token:
        raise UnauthorizedException("未提供认证令牌")

    payload = get_token_payload(token)
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise UnauthorizedException("认证令牌缺少有效用户信息")

    result = await session.exec(select(User).where(User.id == int(subject)))
    user = result.first()
    if user is None:
        raise UnauthorizedException("用户不存在")
    if not user.enabled:
        raise UnauthorizedException("用户账户已禁用")

    return AuthUser(user_id=user.id, username=user.username, role=user.role)


async def get_current_admin(
    current_user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    """要求当前用户为管理员。"""
    if current_user.role != UserRoleEnum.ADMIN.value:
        raise ForbiddenException("需要管理员权限")
    return current_user


async def get_optional_user(
    request: Request,
    session: SessionDep,
) -> Optional[AuthUser]:
    """获取可选的当前用户。"""
    try:
        return await get_current_user(request, session)
    except UnauthorizedException:
        return None
