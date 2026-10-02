"""离线目录查询与显式检测编排，网络等待不持有数据库事务或 ORM 凭据对象。"""
import asyncio
from dataclasses import dataclass
from time import time_ns
from uuid import UUID

from pydantic import SecretStr
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.exceptions import BusinessException, ConflictException
from web408.modules.ai.key_cipher import decrypt_api_key
from web408.modules.ai.repository import AiSettingsRepository
from web408.modules.ai.runtime.manager import AiRuntime, CatalogQuery
from web408.modules.ai.runtime.session import ADMISSION_MS
from web408.modules.ai.schemas import (
    AiModelCheckRequest, AiModelCheckView, AiModelsQueryRequest, AiModelsView,
)


@dataclass(slots=True)
class _Credential:
    """读取配置并释放读事务后复制的凭据字段；明文只在调用边界短暂存在。"""

    provider_revision: UUID
    admission_expires_at: int
    api_key: SecretStr


class AiModelService:
    def __init__(self, session: AsyncSession, runtime: AiRuntime) -> None:
        """绑定请求会话与进程内运行模块，不在构造时读取 Key 或发起请求。"""
        self.session = session
        self.repository = AiSettingsRepository(session)
        self.runtime = runtime

    async def query(self, user_id: int, request: AiModelsQueryRequest) -> AiModelsView:
        """无需保存 Key 即可浏览固定目录，读取不联网、不刷新。"""
        await self.session.rollback()
        return self.runtime.models(
            CatalogQuery(search=request.search, offset=request.offset, limit=request.limit,
                         model_id=request.model_id),
            request.provider_id,
        )

    async def _credential(
        self, user_id: int, provider_id: str, expected_revision: UUID | None = None,
    ) -> _Credential:
        """读取账号凭据并释放读事务；读取前固定期限，异步解密不能延长准入。"""
        expires_at = time_ns() // 1_000_000 + ADMISSION_MS
        try:
            config = await self.repository.get_provider(user_id, provider_id)
            if config is None or not config.enabled:
                raise ConflictException("请先保存并启用该供应商的 API Key")
            revision = UUID(config.revision)
            if expected_revision is not None and expected_revision != revision:
                raise ConflictException("供应商配置已变化，请重新加载后检测")
            ciphertext, key_version = config.api_key_ciphertext, config.key_version
        finally:
            await self.session.rollback()
        key = await asyncio.to_thread(decrypt_api_key, ciphertext, key_version)
        return _Credential(provider_revision=revision, admission_expires_at=expires_at, api_key=key)

    async def check(self, user_id: int, request: AiModelCheckRequest) -> AiModelCheckView:
        """只用已保存凭据发一次短文本请求，不携带题目或聊天历史。"""
        credential = await self._credential(user_id, request.provider_id, request.provider_revision)
        result = await self.runtime.check(
            user_id=user_id, provider_id=request.provider_id, model_id=request.model_id,
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
