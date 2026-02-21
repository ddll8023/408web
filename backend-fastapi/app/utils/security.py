"""
安全工具模块
JWT Token 和密码处理工具
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from app.config.settings import settings
from app.exception import UnauthorizedException


# 密码加密上下文 - 使用官方推荐的 argon2id 算法
pwd_context = PasswordHash.recommended()

# JWT 配置
JWT_SECRET = settings.jwt.secret
JWT_ALGORITHM = settings.jwt.algorithm


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配

    Args:
        plain_password: 原始密码
        hashed_password: 加密后的密码

    Returns:
        bool: 是否匹配
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        # 无法识别的哈希格式（如旧 bcrypt），返回 False
        return False


def get_password_hash(password: str) -> str:
    """
    对密码进行 BCrypt 加密

    Args:
        password: 原始密码

    Returns:
        str: 加密后的密码
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建 JWT Token

    Args:
        data: 要编码到 Token 中的数据
        expires_delta: Token 过期时间

    Returns:
        str: 编码后的 Token 字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # 默认永不过期（与原 Java 实现保持一致）
        expire = datetime.utcnow() + timedelta(days=365 * 10)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码 JWT Token

    Args:
        token: JWT Token 字符串

    Returns:
        dict: 解码后的数据，失败返回 None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def get_token_payload(token: str) -> Dict[str, Any]:
    """
    获取 Token 载荷

    Args:
        token: JWT Token 字符串

    Returns:
        dict: 包含 username 和 role 的载荷

    Raises:
        UnauthorizedException: Token 无效
    """
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedException("无效的认证令牌")

    return payload


def extract_token_from_header(authorization: str) -> Optional[str]:
    """
    从 Authorization 请求头中提取 Token

    Args:
        authorization: Authorization 请求头值

    Returns:
        str: Token 字符串，格式无效返回 None
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]
