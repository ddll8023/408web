"""目录查询与显式检测编排，网络等待不持有数据库事务或 ORM 凭据对象。

内置目录由运行模块提供，账号自建型号从当前账号的配置读取；两条路径最终都解析成
同一份 ModelSpec，检测与咨询不再依赖固定的供应商标识。
"""
import asyncio
from dataclasses import dataclass
from time import time_ns
from uuid import UUID

from pydantic import SecretStr
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.exceptions import BusinessException, ConflictException, ValidationException
from web408.modules.ai.key_cipher import decrypt_api_key
from web408.modules.ai.models import UserAiProviderConfig
from web408.modules.ai.repository import AiSettingsRepository
from web408.modules.ai.runtime.go_catalog import find_spec
from web408.modules.ai.runtime.manager import AiRuntime, CatalogQuery
from web408.modules.ai.runtime.model_spec import ModelSpec, custom_spec
from web408.modules.ai.runtime.session import ADMISSION_MS
from web408.modules.ai.schemas import (
    AiCatalogModelView, AiModelCheckRequest, AiModelCheckView, AiModelsQueryRequest, AiModelsView,
)


@dataclass(slots=True)
class _Credential:
    """读取配置并释放读事务后复制的凭据字段；明文只在调用边界短暂存在。"""

    provider_revision: UUID
    admission_expires_at: int
    api_key: SecretStr
    model: ModelSpec


class AiModelService:
    def __init__(self, session: AsyncSession, runtime: AiRuntime) -> None:
        """绑定请求会话与进程内运行模块，不在构造时读取 Key 或发起请求。"""
        self.session = session
        self.repository = AiSettingsRepository(session)
        self.runtime = runtime

    async def query(self, user_id: int, request: AiModelsQueryRequest) -> AiModelsView:
        """无需保存 Key 即可浏览内置目录或自建型号，读取不联网、不刷新。"""
        await self.session.rollback()
        try:
            provider = await self.repository.get_provider(user_id, request.provider_id)
            if provider is not None and provider.base_url is not None:
                return await self._custom_page(user_id, provider, request)
            return self.runtime.models(
                CatalogQuery(search=request.search, offset=request.offset, limit=request.limit,
                             model_id=request.model_id),
                request.provider_id,
            )
        finally:
            await self.session.rollback()

    async def _custom_page(
        self, user_id: int, provider: UserAiProviderConfig, request: AiModelsQueryRequest,
    ) -> AiModelsView:
        """按精确型号或搜索分页返回账号自建型号，能力字段来自用户声明。"""
        models = await self.repository.list_custom_models(user_id, provider.provider_id)
        keyword = request.search.strip().lower()
        selected = [
            model for model in models
            if (request.model_id is None or model.model_id == request.model_id)
            and (not keyword or keyword in f"{model.name} {model.model_id}".lower())
        ]
        selected.sort(key=lambda model: (model.name.lower(), model.model_id))
        page = selected[request.offset:request.offset + request.limit]
        protocol = provider.protocol or "openai-completions"
        return AiModelsView(
            provider_id=provider.provider_id,
            models=[AiCatalogModelView(
                provider=provider.provider_id, id=model.model_id, name=model.name,
                supports_images=model.supports_images, reasoning=False,
                context_window=model.context_window, max_tokens=model.max_tokens, api=protocol,
            ) for model in page],
            total=len(selected), offset=request.offset, limit=request.limit, source="custom",
        )

    async def _credential(
        self, user_id: int, provider_id: str, model_id: str, expected_revision: UUID | None = None,
    ) -> _Credential:
        """读取账号凭据与型号定义并释放读事务；读取前固定期限，解密不能延长准入。"""
        expires_at = time_ns() // 1_000_000 + ADMISSION_MS
        try:
            config = await self.repository.get_provider(user_id, provider_id)
            if config is None or not config.enabled:
                raise ConflictException("请先保存并启用该供应商的 API Key")
            revision = UUID(config.revision)
            if expected_revision is not None and expected_revision != revision:
                raise ConflictException("供应商配置已变化，请重新加载后检测")
            ciphertext, key_version = config.api_key_ciphertext, config.key_version
            model = await self._resolve_model(user_id, config, model_id)
        finally:
            await self.session.rollback()
        key = await asyncio.to_thread(decrypt_api_key, ciphertext, key_version)
        return _Credential(
            provider_revision=revision, admission_expires_at=expires_at, api_key=key, model=model,
        )

    async def _resolve_model(self, user_id: int, provider: UserAiProviderConfig, model_id: str) -> ModelSpec:
        """把内置型号或账号自建型号解析为运行时定义，未收录时拒绝而不猜测协议。"""
        if provider.base_url is not None:
            model = await self.repository.get_custom_model(user_id, provider.provider_id, model_id)
            if model is None:
                raise ValidationException("该供应商下没有该型号，请重新选择")
            return custom_spec(
                provider_id=provider.provider_id, base_url=provider.base_url,
                protocol=provider.protocol or "openai-completions", model_id=model.model_id,
                name=model.name, supports_images=model.supports_images,
                context_window=model.context_window, max_tokens=model.max_tokens,
            )
        spec = find_spec(model_id)
        if spec is None:
            raise ValidationException("模型目录未收录该型号，请重新选择")
        return spec

    async def check(self, user_id: int, request: AiModelCheckRequest) -> AiModelCheckView:
        """只用已保存凭据发一次短文本请求，不携带题目或聊天历史。"""
        credential = await self._credential(
            user_id, request.provider_id, request.model_id, request.provider_revision,
        )
        result = await self.runtime.check(
            user_id=user_id, model=credential.model,
            provider_revision=str(credential.provider_revision),
            admission_expires_at=credential.admission_expires_at,
            api_key=credential.api_key.get_secret_value(), request_id=str(request.request_id),
        )
        if result.request_id != request.request_id or result.model.provider != request.provider_id or result.model.id != request.model_id:
            raise BusinessException(502, "AI 检测响应标识无效")
        # 长请求期间配置可能变化；旧结果不得被展示为新凭据的检测成功。
        try:
            current = await self.repository.get_provider(user_id, request.provider_id)
            if current is None or not current.enabled or UUID(current.revision) != request.provider_revision:
                raise ConflictException("供应商配置已变化，本次检测结果已失效")
        finally:
            await self.session.rollback()
        return result
