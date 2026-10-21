"""供应商凭据、自定义供应商与默认咨询设置用例；显式提交事务，不探测模型或自动调用。"""
import asyncio
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.exceptions import ConflictException, InfrastructureException, ValidationException
from web408.modules.ai.key_cipher import encrypt_api_key
from web408.modules.ai.models import UserAiConfig, UserAiCustomModel, UserAiProviderConfig
from web408.modules.ai.repository import AiSettingsRepository
from web408.modules.ai.runtime.manager import AiRuntime, CatalogQuery
from web408.modules.ai.schemas import (
    AiCatalogModelView,
    AiCustomModelSaveRequest,
    AiCustomProviderSaveRequest,
    AiCustomProviderView,
    AiProviderConfigView,
    AiProviderSaveRequest,
    AiProviderView,
    AiProvidersView,
    AiSettingsSaveRequest,
    AiSettingsView,
)


# 单账号自定义型号上限：避免目录与选择器被无限增长的型号拖慢。
CUSTOM_MODEL_LIMIT = 50


class AiSettingsService:
    def __init__(self, session: AsyncSession, runtime: AiRuntime | None = None) -> None:
        """绑定请求事务与进程内运行模块；纯本地默认查询不要求运行模块。"""
        self.session = session
        self.repository = AiSettingsRepository(session)
        self.runtime = runtime

    @staticmethod
    def _to_view(config: UserAiConfig) -> AiSettingsView:
        """显式提取默认选择的公开字段，不依赖 ORM 全量序列化。"""
        return AiSettingsView(
            provider_id=config.provider_id, model_id=config.model_id,
            input_mode=config.input_mode, enabled=config.enabled, revision=UUID(config.revision),
        )

    @staticmethod
    def _provider_view(config: UserAiProviderConfig) -> AiProviderConfigView:
        """只公开凭据存在状态和修订，不返回 Key、密文或加密版本。"""
        return AiProviderConfigView(
            provider_id=config.provider_id, enabled=config.enabled,
            has_api_key=bool(config.api_key_ciphertext), revision=UUID(config.revision),
        )

    @staticmethod
    def _custom_provider_view(config: UserAiProviderConfig, model_count: int) -> AiCustomProviderView:
        """只公开自定义供应商的展示信息与保存状态，不返回 Key 与密文。"""
        if config.base_url is None or config.protocol is None or config.display_name is None:
            raise InfrastructureException("自定义供应商配置不完整，请重新保存")
        return AiCustomProviderView(
            provider_id=config.provider_id, enabled=config.enabled,
            has_api_key=bool(config.api_key_ciphertext), revision=UUID(config.revision),
            name=config.display_name, base_url=config.base_url, protocol=config.protocol,
            model_count=model_count,
        )

    @staticmethod
    def _custom_model_view(config: UserAiProviderConfig, model: UserAiCustomModel) -> AiCatalogModelView:
        """自定义型号只公开协议与账号声明的能力，不暴露接口地址与凭据。"""
        if config.protocol is None:
            raise InfrastructureException("自定义供应商协议缺失，请重新保存配置")
        return AiCatalogModelView(
            provider=config.provider_id, id=model.model_id, name=model.name,
            supports_images=model.supports_images, reasoning=False,
            context_window=model.context_window, max_tokens=model.max_tokens, api=config.protocol,
        )

    def _runtime(self) -> AiRuntime:
        """为需要模型目录或失效登记的用例取得运行模块，缺失时返回固定基础设施错误。"""
        if self.runtime is None:
            raise InfrastructureException("AI 运行模块尚未初始化")
        return self.runtime

    async def _commit(self) -> None:
        """统一提交失败的安全映射，不记录含密文的 SQL 异常。"""
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictException("AI 配置发生并发变化，请重新加载后保存") from None
        except SQLAlchemyError:
            await self.session.rollback()
            raise InfrastructureException("AI 配置保存失败，请稍后重试") from None

    async def query(self, user_id: int) -> AiSettingsView | None:
        """查询当前账号默认选择，不解密凭据、不调用模型，也不提交读事务。"""
        config = await self.repository.get_by_user_id(user_id)
        return self._to_view(config) if config is not None else None

    async def providers(self, user_id: int) -> AiProvidersView:
        """内置目录与账号自建供应商合并返回；目录存在不表示真实调用权限。"""
        try:
            rows = await self.repository.list_providers(user_id)
            configs = {row.provider_id: self._provider_view(row) for row in rows}
            # rollback 会过期 ORM 实例，自定义供应商必须先复制成普通字段再离开读事务。
            custom_rows = [
                (row.display_name, row.provider_id, row.base_url, row.protocol, row.enabled,
                 bool(row.api_key_ciphertext), row.revision)
                for row in rows if row.base_url is not None
            ]
            custom_counts = {
                row.provider_id: len(await self.repository.list_custom_models(user_id, row.provider_id))
                for row in rows if row.base_url is not None
            }
        finally:
            await self.session.rollback()
        catalog = self._runtime().providers()
        views = [AiProviderView(
            **provider.model_dump(), configured=provider.id in configs,
            enabled=configs[provider.id].enabled if provider.id in configs else False,
            has_api_key=configs[provider.id].has_api_key if provider.id in configs else False,
            revision=configs[provider.id].revision if provider.id in configs else None,
        ) for provider in catalog.providers]
        for display_name, provider_id, base_url, protocol, enabled, has_key, revision in sorted(
            custom_rows, key=lambda item: (item[0] or item[1]).lower(),
        ):
            views.append(AiProviderView(
                id=provider_id, name=display_name or provider_id, supported=True,
                unsupported_reason=None, base_urls=[base_url or ""],
                model_count=custom_counts.get(provider_id, 0), custom=True,
                base_url=base_url, protocol=protocol, configured=True, enabled=enabled,
                has_api_key=has_key, revision=UUID(revision),
            ))
        return AiProvidersView(providers=views)

    async def save_provider(self, user_id: int, request: AiProviderSaveRequest) -> AiProviderConfigView:
        """保存当前账号内置供应商凭据，空 Key 仅保留同供应商旧值，不发模型请求。

        先释放读事务并核对接入方式，再异步加密、提交写事务及登记旧修订失效。
        """
        await self.session.rollback()
        runtime = self._runtime()
        provider = next((item for item in runtime.providers().providers if item.id == request.provider_id), None)
        if provider is None or not provider.supported:
            raise ValidationException("该供应商不支持当前接入方式，请重新选择")
        encrypted = await asyncio.to_thread(encrypt_api_key, request.api_key) if request.api_key is not None else None
        config = await self.repository.get_provider(user_id, request.provider_id)
        if config is not None and config.base_url is not None:
            raise ValidationException("请通过自定义供应商表单修改该配置")
        old_revision = config.revision if config is not None else None
        if encrypted is not None:
            ciphertext, key_version = encrypted
        elif config is not None and config.api_key_ciphertext:
            ciphertext, key_version = config.api_key_ciphertext, config.key_version
        else:
            raise ValidationException("尚未保存 API Key，请填写后保存")
        if config is None:
            config = UserAiProviderConfig(
                user_id=user_id, provider_id=request.provider_id, enabled=request.enabled,
                api_key_ciphertext=ciphertext, key_version=key_version,
            )
        else:
            config.enabled = request.enabled
            config.api_key_ciphertext = ciphertext
            config.key_version = key_version
            config.revision = str(uuid4())
        self.repository.save(config)
        await self._commit()
        view = self._provider_view(config)
        runtime.invalidate_revision(user_id, old_revision, request.provider_id)
        return view

    async def delete_provider(self, user_id: int, provider_id: str) -> None:
        """原子删除账号内置供应商及必要的默认引用，提交后登记两类旧修订失效。

        自定义供应商由其专用用例删除；清除本站密文不会撤销上游账户中的 Key。
        """
        config = await self.repository.get_provider(user_id, provider_id)
        if config is not None and config.base_url is not None:
            raise ValidationException("请通过自定义供应商删除该配置")
        try:
            revision, default_revision = await self.repository.delete_provider(user_id, provider_id)
            await self._commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise InfrastructureException("AI 供应商配置清除失败，请稍后重试") from None
        if self.runtime is not None:
            self.runtime.invalidate_revision(user_id, revision, provider_id)
            self.runtime.invalidate_revision(user_id, default_revision)

    async def save_custom_provider(
        self, user_id: int, request: AiCustomProviderSaveRequest,
    ) -> AiCustomProviderView:
        """保存账号自建供应商；新建时生成标识，空 Key 只保留同供应商旧值。"""
        await self.session.rollback()
        runtime = self._runtime()
        encrypted = await asyncio.to_thread(encrypt_api_key, request.api_key) if request.api_key is not None else None
        config = None
        if request.provider_id is not None:
            config = await self.repository.get_provider(user_id, request.provider_id)
            if config is None or config.base_url is None:
                raise ValidationException("自定义供应商不存在，请重新加载配置")
        if config is None:
            if encrypted is None:
                raise ValidationException("尚未保存 API Key，请填写后保存")
            config = UserAiProviderConfig(
                user_id=user_id, provider_id=f"custom-{uuid4()}", enabled=request.enabled,
                display_name=request.name, base_url=request.base_url, protocol=request.protocol,
                api_key_ciphertext=encrypted[0], key_version=encrypted[1],
            )
            old_revision = None
        else:
            if encrypted is not None:
                config.api_key_ciphertext, config.key_version = encrypted
            elif not config.api_key_ciphertext:
                raise ValidationException("尚未保存 API Key，请填写后保存")
            old_revision = config.revision
            config.display_name = request.name
            config.base_url = request.base_url
            config.protocol = request.protocol
            config.enabled = request.enabled
            config.revision = str(uuid4())
        count = len(await self.repository.list_custom_models(user_id, config.provider_id))
        self.repository.save(config)
        await self._commit()
        runtime.invalidate_revision(user_id, old_revision, config.provider_id)
        return self._custom_provider_view(config, count)

    async def delete_custom_provider(self, user_id: int, provider_id: str) -> None:
        """删除账号自建供应商及其型号与默认引用，提交后登记两类旧修订失效。"""
        config = await self.repository.get_provider(user_id, provider_id)
        if config is None or config.base_url is None:
            raise ValidationException("自定义供应商不存在，请重新加载配置")
        try:
            revision, default_revision = await self.repository.delete_custom_provider(user_id, provider_id)
            await self._commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise InfrastructureException("自定义供应商清除失败，请稍后重试") from None
        if self.runtime is not None:
            self.runtime.invalidate_revision(user_id, revision, provider_id)
            self.runtime.invalidate_revision(user_id, default_revision)

    async def save_custom_model(
        self, user_id: int, request: AiCustomModelSaveRequest,
    ) -> AiCatalogModelView:
        """新增或更新自定义型号；能力变化会作废旧修订与已有会话。"""
        await self.session.rollback()
        runtime = self._runtime()
        provider = await self.repository.get_provider(user_id, request.provider_id)
        if provider is None or provider.base_url is None:
            raise ValidationException("自定义供应商不存在，请重新加载配置")
        model = await self.repository.get_custom_model(user_id, request.provider_id, request.model_id)
        if model is None:
            if len(await self.repository.list_custom_models(user_id, request.provider_id)) >= CUSTOM_MODEL_LIMIT:
                raise ValidationException("自定义型号数量已达上限，请先删除不用的型号")
            model = UserAiCustomModel(
                user_id=user_id, provider_id=request.provider_id, model_id=request.model_id,
                name=request.name, supports_images=request.supports_images,
                context_window=request.context_window, max_tokens=request.max_tokens,
            )
        else:
            model.name = request.name
            model.supports_images = request.supports_images
            model.context_window = request.context_window
            model.max_tokens = request.max_tokens
        old_revision = provider.revision
        provider.revision = str(uuid4())
        self.repository.save(model)
        await self._commit()
        runtime.invalidate_revision(user_id, old_revision, request.provider_id)
        return self._custom_model_view(provider, model)

    async def delete_custom_model(self, user_id: int, provider_id: str, model_id: str) -> None:
        """删除自定义型号并作废旧修订；默认选择指向它时一并清除。"""
        await self.session.rollback()
        runtime = self._runtime()
        provider = await self.repository.get_provider(user_id, provider_id)
        if provider is None or provider.base_url is None:
            raise ValidationException("自定义供应商不存在，请重新加载配置")
        model = await self.repository.get_custom_model(user_id, provider_id, model_id)
        if model is None:
            raise ValidationException("自定义型号不存在，请重新加载配置")
        old_revision = provider.revision
        default = await self.repository.get_by_user_id(user_id)
        default_revision = None
        if default is not None and default.provider_id == provider_id and default.model_id == model_id:
            default_revision = default.revision
            await self.session.delete(default)
        await self.repository.delete(model)
        provider.revision = str(uuid4())
        await self._commit()
        runtime.invalidate_revision(user_id, old_revision, provider_id)
        runtime.invalidate_revision(user_id, default_revision)

    async def save(self, user_id: int, request: AiSettingsSaveRequest) -> AiSettingsView:
        """保存当前账号的精确型号及默认状态，不检测真实调用权限。

        目录查询不持有读事务；供应商须已保存且启用，写入提交后登记旧默认修订失效。
        """
        await self.session.rollback()
        runtime = self._runtime()
        provider = await self.repository.get_provider(user_id, request.provider_id)
        if provider is None or not provider.enabled or not provider.api_key_ciphertext:
            raise ConflictException("请先保存并启用该供应商的 API Key")
        if provider.base_url is not None:
            model = await self.repository.get_custom_model(user_id, request.provider_id, request.model_id)
            if model is None:
                raise ValidationException("模型目录未收录该型号，请重新选择")
            supports_images = model.supports_images
        else:
            models = runtime.models(CatalogQuery(model_id=request.model_id, limit=1), request.provider_id)
            if not models.models:
                raise ValidationException("模型目录未收录该型号，请重新选择")
            supports_images = models.models[0].supports_images
        # 该字段本批不启用：运行时按题目是否含图片自动判定，此校验只防历史遗留值。
        if request.input_mode == "text_image" and not supports_images:
            raise ValidationException("该型号不支持图像输入，请选择支持图像的型号")
        config = await self.repository.get_by_user_id(user_id)
        old_revision = config.revision if config is not None else None
        if config is None:
            config = UserAiConfig(
                user_id=user_id, provider_id=request.provider_id, model_id=request.model_id,
                input_mode=request.input_mode, enabled=request.enabled,
            )
        else:
            config.provider_id = request.provider_id
            config.model_id = request.model_id
            config.input_mode = request.input_mode
            config.enabled = request.enabled
            config.revision = str(uuid4())
        self.repository.save(config)
        await self._commit()
        view = self._to_view(config)
        runtime.invalidate_revision(user_id, old_revision)
        return view

    async def delete(self, user_id: int) -> None:
        """提交默认选择删除并登记旧修订失效，不连带删除已保存的供应商凭据。"""
        old_revision = await self.repository.delete_by_user_id(user_id)
        await self._commit()
        if self.runtime is not None:
            self.runtime.invalidate_revision(user_id, old_revision)
