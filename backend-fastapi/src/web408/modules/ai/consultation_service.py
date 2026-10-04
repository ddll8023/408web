"""题目咨询编排，释放数据库读事务后再读取本地凭据、题目图片或等待模型生成。"""
import asyncio
from time import time_ns
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.config import settings
from web408.core.exceptions import ConflictException, ValidationException
from web408.modules.ai.key_cipher import decrypt_api_key
from web408.modules.ai.question_context import build_question_snapshot
from web408.modules.ai.question_images import load_question_images
from web408.modules.ai.repository import AiSettingsRepository
from web408.modules.ai.runtime.manager import AiRuntime
from web408.modules.ai.runtime.session import ADMISSION_MS, AiStream
from web408.modules.ai.session_schemas import (
    AiMessageRequest,
    AiSessionActionView,
    AiSessionCreateRequest,
    AiSessionView,
)


class AiConsultationService:
    """鉴权账号由路由传入，不信任浏览器提供归属或配置快照。"""

    def __init__(self, session: AsyncSession, runtime: AiRuntime) -> None:
        """绑定请求级读事务和进程内运行模块，不初始化模型或读取本地凭据。"""
        self.session = session
        self.runtime = runtime
        self.repository = AiSettingsRepository(session)

    async def create(self, user_id: int, request: AiSessionCreateRequest) -> AiSessionView:
        """固定题目、双修订与读取前的登记期限；释放事务后解密，不调用模型。"""
        expires_at = time_ns() // 1_000_000 + ADMISSION_MS
        try:
            config = await self.repository.get_by_user_id(user_id)
            if config is None or not config.enabled:
                raise ConflictException("请先保存并启用个人 AI 配置")
            provider = await self.repository.get_provider(user_id, config.provider_id)
            if provider is None or not provider.enabled:
                raise ConflictException("默认模型的供应商已清除或暂停，请重新配置")
            ciphertext = provider.api_key_ciphertext
            key_version = provider.key_version
            revision = config.revision
            provider_id = provider.provider_id
            provider_revision = provider.revision
            model_id = config.model_id
            snapshot = await build_question_snapshot(
                self.session,
                request.question_kind,
                request.question_id,
                settings.ai,
            )
        finally:
            # AuthUser 依赖与业务读取共用会话；只复制普通字段，不跨文件或网络等待使用 ORM。
            await self.session.rollback()
        # 图片字节读取属于受控本地文件 IO，不占用数据库读事务，也不发起网络请求。
        payload = await load_question_images(
            snapshot.images,
            settings.upload.upload_dir,
            max_count=settings.ai.question_image_max_count,
            max_image_bytes=settings.ai.question_image_max_bytes,
            max_total_bytes=settings.ai.question_image_total_max_bytes,
        )
        api_key = await asyncio.to_thread(decrypt_api_key, ciphertext, key_version)
        if not api_key.get_secret_value().strip():
            raise ValidationException("AI 凭据为空，请重新填写 API Key")
        return self.runtime.create_session(
            user_id=user_id, provider_id=provider_id, model_id=model_id,
            kind=request.question_kind, question_id=request.question_id, snapshot=snapshot.text,
            images=payload.images, omitted=payload.omitted,
            default_revision=revision, provider_revision=provider_revision,
            admission_expires_at=expires_at, api_key=api_key.get_secret_value(),
        )

    async def messages(
        self,
        user_id: int,
        session_id: UUID,
        request: AiMessageRequest,
    ) -> AiStream:
        """每轮读取最新双修订并固定期限；解密等待不延长旧配置载荷的准入。"""
        expires_at = time_ns() // 1_000_000 + ADMISSION_MS
        try:
            config = await self.repository.get_by_user_id(user_id)
            if config is None or not config.enabled:
                raise ConflictException("AI 配置已清除或暂停，请重新配置后咨询")
            provider = await self.repository.get_provider(user_id, config.provider_id)
            if provider is None or not provider.enabled:
                raise ConflictException("默认模型的供应商已清除或暂停，请重新配置")
            ciphertext = provider.api_key_ciphertext
            key_version = provider.key_version
            revision = config.revision
            provider_revision = provider.revision
        finally:
            await self.session.rollback()
        # 即使会话内存已有客户端，也不能绕过当前主密钥不可用的状态。
        api_key = await asyncio.to_thread(decrypt_api_key, ciphertext, key_version)
        if not api_key.get_secret_value().strip():
            raise ValidationException("AI 凭据为空，请重新填写 API Key")
        return self.runtime.reserve_message(
            user_id=user_id, session_id=str(session_id), request_id=str(request.request_id),
            message=request.message, default_revision=revision, provider_revision=provider_revision,
            admission_expires_at=expires_at,
        )

    async def abort(self, user_id: int, session_id: UUID, request_id: UUID) -> AiSessionActionView:
        """停止不依赖 AI 配置仍然存在，运行模块再核对账号和原请求。"""
        await self.session.rollback()
        return await self.runtime.abort(user_id, str(session_id), str(request_id))

    async def close(self, user_id: int, session_id: UUID) -> AiSessionActionView:
        """显式关闭仅作用于当前账号拥有的会话。"""
        await self.session.rollback()
        return await self.runtime.close(user_id, str(session_id))
