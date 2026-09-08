"""应用级密码和 JWT 安全工具。"""
from typing import Mapping, Optional

from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.core.config import settings
from app.core.exceptions import UnauthorizedException


pwd_context = PasswordHash.recommended()
JWT_SECRET = settings.jwt.secret
JWT_ALGORITHM = settings.jwt.algorithm


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码。"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False


def get_password_hash(password: str) -> str:
    """生成 Argon2 密码哈希。"""
    return pwd_context.hash(password)


def create_access_token(data: Mapping[str, object]) -> str:
    """创建不会自动过期的访问令牌。"""
    return jwt.encode(dict(data), JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, object]]:
    """验证并解码访问令牌。"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return dict(payload)
    except JWTError:
        return None


def get_token_payload(token: str) -> dict[str, object]:
    """获取已验证的 Token 载荷。"""
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedException("无效的认证令牌")
    return payload


def extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """从 Bearer Authorization 头提取令牌。"""
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]
