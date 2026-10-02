"""AI 配置数据访问：所有操作限定账号，Repository 不拥有提交事务。"""
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.modules.ai.models import UserAiConfig, UserAiProviderConfig


class AiSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        """复用请求级会话，数据访问层不自行提交或回滚。"""
        self.session = session

    async def get_by_user_id(self, user_id: int) -> UserAiConfig | None:
        """查询当前账号唯一的默认选择，未配置时返回空。"""
        result = await self.session.exec(select(UserAiConfig).where(UserAiConfig.user_id == user_id))
        return result.first()

    async def list_providers(self, user_id: int) -> list[UserAiProviderConfig]:
        """仅列出该账号保存的供应商，按标识排序。"""
        result = await self.session.exec(
            select(UserAiProviderConfig).where(UserAiProviderConfig.user_id == user_id)
            .order_by(UserAiProviderConfig.provider_id)
        )
        return list(result.all())

    async def get_provider(self, user_id: int, provider_id: str) -> UserAiProviderConfig | None:
        """用账号和供应商共同限定凭据归属，不能跨账号读取。"""
        result = await self.session.exec(select(UserAiProviderConfig).where(
            UserAiProviderConfig.user_id == user_id, UserAiProviderConfig.provider_id == provider_id,
        ))
        return result.first()

    def save(self, config: UserAiConfig | UserAiProviderConfig) -> None:
        """将配置加入当前写事务，提交责任留给业务用例。"""
        self.session.add(config)

    async def delete_by_user_id(self, user_id: int) -> str | None:
        """暂存默认选择删除并返回旧修订，保留供应商凭据且不提交事务。"""
        config = await self.get_by_user_id(user_id)
        if config is None:
            return None
        revision = config.revision
        await self.session.delete(config)
        return revision

    async def delete_provider(self, user_id: int, provider_id: str) -> tuple[str | None, str | None]:
        """在同一事务内先清当前默认引用再删凭据，返回两类旧修订但不提交。"""
        provider = await self.get_provider(user_id, provider_id)
        if provider is None:
            return None, None
        default = await self.get_by_user_id(user_id)
        default_revision = None
        if default is not None and default.provider_id == provider_id:
            default_revision = default.revision
            await self.session.delete(default)
            await self.session.flush()
        revision = provider.revision
        await self.session.delete(provider)
        return revision, default_revision
