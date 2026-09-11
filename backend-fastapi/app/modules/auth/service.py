"""
认证服务模块
实现用户注册和登录业务逻辑
"""
import logging

from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.auth.models import User
from app.models.enums import UserRoleEnum
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_access_token, get_password_hash, verify_password
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import RegisterRequest, LoginRequest, AuthResponse


logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)

    async def register(self, request: RegisterRequest) -> None:
        """
        用户注册

        Args:
            request: 注册请求

        Raises:
            ConflictException: 用户名已存在
        """
        logger.info("AuthService.register started with username: %s", request.username)

        # 检查用户名是否已存在
        existing_user = await self.repository.get_by_username(request.username)

        if existing_user is not None:
            logger.warning("AuthService.register failed: username already exists: %s", request.username)
            raise ConflictException(f"用户名已存在: {request.username}")

        # 创建用户
        user = User(
            username=request.username,
            password=get_password_hash(request.password),
            email=request.email,
            role=UserRoleEnum.USER.value,
            enabled=True
        )
        self.session.add(user)
        await self.session.commit()

        logger.info("AuthService.register completed for username: %s", request.username)

    async def login(self, request: LoginRequest) -> AuthResponse:
        """
        用户登录

        Args:
            request: 登录请求

        Returns:
            AuthResponse: 认证响应（包含Token）

        Raises:
            UnauthorizedException: 用户名或密码错误
            UnauthorizedException: 账户已禁用
        """
        logger.info("AuthService.login started with username: %s", request.username)

        # 查询用户
        user = await self.repository.get_by_username(request.username)

        if user is None:
            logger.warning("AuthService.login failed: user not found: %s", request.username)
            raise UnauthorizedException("用户名或密码错误")

        # 验证密码
        if user.password and not verify_password(request.password, user.password):
            logger.warning("AuthService.login failed: invalid password for user: %s", request.username)
            raise UnauthorizedException("用户名或密码错误")

        # 检查账户状态
        if not user.enabled:
            logger.warning("AuthService.login failed: user disabled: %s", request.username)
            raise UnauthorizedException("账户已被禁用")

        # 生成Token
        token = create_access_token(data={"sub": str(user.id)})

        logger.info("AuthService.login completed for user: %s", request.username)

        return AuthResponse(
            token=token,
            username=user.username,
            role=user.role
        )
