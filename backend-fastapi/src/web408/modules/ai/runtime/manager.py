"""AI 运行模块门面：固定供应商目录、型号查询、检测与咨询编排。

启动只准备内存结构与回收任务，不读取凭据、不联网、不预热模型；
调用方传入经过认证与校验的账号、双修订、型号和已解密凭据，模块不回写数据库。
"""
from dataclasses import dataclass

from web408.core.config import AiConfig
from web408.modules.ai.runtime.errors import AiRuntimeError
from web408.modules.ai.runtime.go_catalog import (
    ANTHROPIC_BASE_URL,
    MODELS,
    OPENAI_BASE_URL,
    PROVIDER_ID,
    PROVIDER_NAME,
    find_model,
)
from web408.modules.ai.runtime.session import AiConsultationManager, AiStream
from web408.modules.ai.schemas import (
    AgentProvidersView,
    AiCatalogModelView,
    AiCatalogProviderView,
    AiModelCheckView,
    AiModelsView,
)
from web408.modules.ai.session_schemas import AiSessionActionView, AiSessionView, QuestionKind


@dataclass(slots=True)
class CatalogQuery:
    """一次离线目录查询的已校验条件；不接受端点、协议或账号字段。"""

    search: str = ""
    offset: int = 0
    limit: int = 30
    model_id: str | None = None


class AiRuntime:
    """进程内 AI 运行模块：目录能力、检测互斥与咨询生命周期都在单进程内完成。"""

    def __init__(self, config: AiConfig) -> None:
        """只绑定固定运行参数并创建内存管理器，不启动任务或网络连接。"""
        self.config = config
        self.consultation = AiConsultationManager(config.generation_timeout_seconds, config.check_timeout_seconds)

    async def startup(self) -> None:
        """启动闲置回收任务；不读取凭据、不创建模型客户端。"""
        self.consultation.start()

    async def aclose(self) -> None:
        """停止接收新生成并释放活跃会话与私有客户端，等待有界收尾。"""
        await self.consultation.aclose()

    # ---- 目录 ----

    @staticmethod
    def _provider_view() -> AiCatalogProviderView:
        """目录只收录固定地址、单一 API Key 的 OpenCode Go；协议映射在注册表中。"""
        return AiCatalogProviderView(
            id=PROVIDER_ID, name=PROVIDER_NAME, supported=True, unsupported_reason=None,
            base_urls=[OPENAI_BASE_URL, ANTHROPIC_BASE_URL], model_count=len(MODELS),
        )

    def providers(self) -> AgentProvidersView:
        """离线返回支持方式与限制，不读取账号凭据、不探测调用权限。"""
        return AgentProvidersView(providers=[self._provider_view()])

    def models(self, query: CatalogQuery, provider_id: str) -> AiModelsView:
        """按精确型号或搜索分页返回离线目录；目录收录不代表账号有调用权限。"""
        if provider_id != PROVIDER_ID:
            raise AiRuntimeError("PROVIDER_UNSUPPORTED")
        if query.model_id is not None:
            selected = [model for model in MODELS if model.id == query.model_id]
        else:
            keyword = query.search.strip().lower()
            selected = [
                model for model in MODELS
                if not keyword or keyword in f"{model.name} {model.id}".lower()
            ]
        ordered = sorted(selected, key=lambda model: (model.name.lower(), model.id))
        page = ordered[query.offset:query.offset + query.limit]
        return AiModelsView(
            provider_id=PROVIDER_ID,
            models=[AiCatalogModelView(
                provider=PROVIDER_ID, id=model.id, name=model.name, supports_images=model.supports_images,
                reasoning=model.reasoning, context_window=model.context_window, max_tokens=model.max_tokens,
                api=model.api,
            ) for model in page],
            total=len(ordered), offset=query.offset, limit=query.limit, source="bundled",
        )

    # ---- 检测与咨询 ----

    async def check(self, *, user_id: int, provider_id: str, model_id: str, provider_revision: str,
                    admission_expires_at: int, api_key: str, request_id: str) -> AiModelCheckView:
        """账号取自认证与数据库，只有明确确认额度时才调用模型。"""
        if provider_id != PROVIDER_ID:
            raise AiRuntimeError("PROVIDER_UNSUPPORTED")
        return await self.consultation.check(
            user_id=user_id, model_id=model_id, provider_revision=provider_revision,
            admission_expires_at=admission_expires_at, api_key=api_key, request_id=request_id,
        )

    def create_session(self, *, user_id: int, provider_id: str, model_id: str, kind: QuestionKind,
                       question_id: int, snapshot: str, default_revision: str, provider_revision: str,
                       admission_expires_at: int, api_key: str) -> AiSessionView:
        """固定可信快照创建内存会话；创建本身不调用模型。"""
        if provider_id != PROVIDER_ID:
            raise AiRuntimeError("PROVIDER_UNSUPPORTED")
        return self.consultation.create(
            user_id=user_id, model_id=model_id, kind=kind, question_id=question_id, snapshot=snapshot,
            default_revision=default_revision, provider_revision=provider_revision,
            admission_expires_at=admission_expires_at, api_key=api_key,
        )

    def reserve_message(self, *, user_id: int, session_id: str, request_id: str, message: str,
                        default_revision: str, provider_revision: str,
                        admission_expires_at: int) -> AiStream:
        """发送前完成全部归属与容量校验，只有明确发送才占用生成位。"""
        return self.consultation.reserve(
            user_id=user_id, session_id=session_id, request_id=request_id, message=message,
            default_revision=default_revision, provider_revision=provider_revision,
            admission_expires_at=admission_expires_at,
        )

    async def abort(self, user_id: int, session_id: str, request_id: str) -> AiSessionActionView:
        """只停止原 request_id，不取消已经开始的下一轮生成。"""
        return await self.consultation.abort(user_id, session_id, request_id)

    async def close(self, user_id: int, session_id: str) -> AiSessionActionView:
        """显式关闭整个会话并释放其内存与客户端。"""
        return await self.consultation.close(user_id, session_id)

    def invalidate_revision(self, user_id: int, revision: str | None, provider_id: str | None = None) -> None:
        """配置提交后在同一进程内登记旧修订失效，不再依赖跨服务通知送达。"""
        self.consultation.remember_invalidation(user_id, revision, provider_id)

    def find_model(self, model_id: str):
        """按精确型号查询注册表，供业务层判断型号是否收录。"""
        return find_model(model_id)
