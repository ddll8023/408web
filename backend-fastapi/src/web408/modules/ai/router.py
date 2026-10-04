"""AI 设置与题目咨询接口，沿用网站鉴权，流响应保证断线后的原请求清理。"""
import asyncio
from collections.abc import Coroutine
from typing import Annotated, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from starlette.types import Receive, Scope, Send

from web408.api.dependencies import SessionDep
from web408.core.exceptions import BusinessException
from web408.modules.ai.answer_schemas import AiAnswerSessionCreateRequest, AiAnswerSessionView
from web408.modules.ai.consultation_service import AiConsultationService
from web408.modules.ai.model_service import AiModelService
from web408.modules.ai.runtime.manager import AiRuntime
from web408.modules.ai.runtime.session import AiStream
from web408.modules.ai.schemas import (
    AiModelCheckRequest, AiModelCheckView, AiModelsQueryRequest, AiModelsView,
    AiProviderConfigView, AiProviderRequest, AiProviderSaveRequest, AiProvidersView,
    AiSettingsActionRequest, AiSettingsSaveRequest, AiSettingsView,
)
from web408.modules.ai.service import AiSettingsService
from web408.modules.ai.session_schemas import (
    AiAbortRequest,
    AiCloseRequest,
    AiMessageRequest,
    AiSessionActionView,
    AiSessionCreateRequest,
    AiSessionView,
)
from web408.modules.auth.dependencies import AuthUser, get_current_admin, get_current_user
from web408.schemas.common import ApiResponse


router = APIRouter()
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]


def get_ai_runtime(request: Request) -> AiRuntime:
    """从应用生命周期取得进程内运行模块，不在依赖中启动服务或调用模型。"""
    runtime = getattr(request.app.state, "ai_runtime", None)
    if not isinstance(runtime, AiRuntime):
        raise BusinessException(503, "AI 运行模块尚未初始化")
    return runtime


RuntimeDep = Annotated[AiRuntime, Depends(get_ai_runtime)]
Result = TypeVar("Result")


async def while_connected(request: Request, operation: Coroutine[object, object, Result]) -> Result:
    """浏览器停止等待时取消本次检测，由运行模块清理原请求。"""
    task = asyncio.create_task(operation)
    try:
        while not task.done():
            await asyncio.wait({task}, timeout=0.25)
            if not task.done() and await request.is_disconnected():
                raise asyncio.CancelledError
        return await task
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)


class ConsultationResponse(StreamingResponse):
    """即使流迭代尚未启动，也在 ASGI 调用结束时安排有界清理。"""

    def __init__(self, stream: AiStream) -> None:
        """接管已校验的进程内流，关闭缓存并保持增量转发，不创建后台生成任务。"""
        self.consultation_stream = stream
        super().__init__(
            stream.relay(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI 结束时总是收尾，即使响应取消发生在首次迭代之前。"""
        try:
            await super().__call__(scope, receive, send)
        finally:
            await self.consultation_stream.aclose()


@router.post("/providers/query", response_model=ApiResponse[AiProvidersView], summary="查询模型供应商与个人保存状态")
async def query_providers(
    request: AiSettingsActionRequest, session: SessionDep, current_user: CurrentUser, runtime: RuntimeDep,
) -> ApiResponse[AiProvidersView]:
    """以鉴权账号查询固定接入方式和个人保存状态，不返回凭据。"""
    return ApiResponse(data=await AiSettingsService(session, runtime).providers(current_user.user_id))


@router.post("/providers/save", response_model=ApiResponse[AiProviderConfigView], summary="保存个人供应商凭据")
async def save_provider(
    request: AiProviderSaveRequest, session: SessionDep, current_user: CurrentUser, runtime: RuntimeDep,
) -> ApiResponse[AiProviderConfigView]:
    """保存该账号供应商的加密 Key 与独立启用状态，不自动检测。"""
    data = await AiSettingsService(session, runtime).save_provider(current_user.user_id, request)
    return ApiResponse(data=data, message="供应商配置已保存，尚未检测调用权限")


@router.post("/providers/delete", response_model=ApiResponse[None], summary="清除个人供应商凭据")
async def delete_provider(
    request: AiProviderRequest, session: SessionDep, current_user: CurrentUser, runtime: RuntimeDep,
) -> ApiResponse[None]:
    """清除当前账号指定供应商及必要默认引用，不操作其他账号或上游 Key。"""
    await AiSettingsService(session, runtime).delete_provider(current_user.user_id, request.provider_id)
    return ApiResponse(message="供应商配置已清除")


@router.post("/models/query", response_model=ApiResponse[AiModelsView], summary="查询固定模型目录")
async def query_models(
    request: AiModelsQueryRequest, session: SessionDep, current_user: CurrentUser, runtime: RuntimeDep,
) -> ApiResponse[AiModelsView]:
    """离线查询随应用发布的固定目录并返回分页能力信息，不要求 Key 或发起生成。"""
    return ApiResponse(data=await AiModelService(session, runtime).query(current_user.user_id, request))


@router.post("/models/check", response_model=ApiResponse[AiModelCheckView], summary="确认额度后主动检测模型")
async def check_model(
    request: AiModelCheckRequest, http_request: Request,
    session: SessionDep, current_user: CurrentUser, runtime: RuntimeDep,
) -> ApiResponse[AiModelCheckView]:
    """显式确认额度后检测一个型号，账号取自鉴权，断线请求停止原检测。"""
    data = await while_connected(http_request, AiModelService(session, runtime).check(current_user.user_id, request))
    return ApiResponse(data=data)


@router.post("/settings/query", response_model=ApiResponse[AiSettingsView], summary="查询默认咨询设置")
async def query_settings(
    request: AiSettingsActionRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> ApiResponse[AiSettingsView]:
    """返回当前账号配置或空状态，不返回任何凭据。"""
    return ApiResponse(data=await AiSettingsService(session).query(current_user.user_id))


@router.post("/settings/save", response_model=ApiResponse[AiSettingsView], summary="保存个人 AI 设置")
async def save_settings(
    request: AiSettingsSaveRequest,
    session: SessionDep,
    current_user: CurrentUser,
    runtime: RuntimeDep,
) -> ApiResponse[AiSettingsView]:
    """只保存本地配置，不把成功响应当作模型连通证明。"""
    data = await AiSettingsService(session, runtime).save(current_user.user_id, request)
    return ApiResponse(data=data, message="AI 设置已保存")


@router.post("/settings/delete", response_model=ApiResponse[None], summary="清除默认咨询选择")
async def delete_settings(
    request: AiSettingsActionRequest,
    session: SessionDep,
    current_user: CurrentUser,
    runtime: RuntimeDep,
) -> ApiResponse[None]:
    """只清除当前账号默认选择，保留其供应商凭据。"""
    await AiSettingsService(session, runtime).delete(current_user.user_id)
    return ApiResponse(message="AI 设置已清除")


@router.post("/sessions/create", response_model=ApiResponse[AiSessionView], summary="创建题目咨询会话")
async def create_session(
    request: AiSessionCreateRequest,
    session: SessionDep,
    current_user: CurrentUser,
    runtime: RuntimeDep,
) -> ApiResponse[AiSessionView]:
    """读取可信题目并固定文本，创建时不调用模型。"""
    data = await AiConsultationService(session, runtime).create(current_user.user_id, request)
    return ApiResponse(data=data)


@router.post("/answers/sessions/create", response_model=ApiResponse[AiAnswerSessionView], summary="创建管理员答案生成会话")
async def create_answer_session(
    request: AiAnswerSessionCreateRequest,
    session: SessionDep,
    runtime: RuntimeDep,
    admin: Annotated[AuthUser, Depends(get_current_admin)],
) -> ApiResponse[AiAnswerSessionView]:
    """只固定题面与对比基线，不调用模型、不修改题库。"""
    data = await AiConsultationService(session, runtime).create(admin.user_id, request)
    if not isinstance(data, AiAnswerSessionView):
        raise BusinessException(503, "答案生成会话创建失败")
    return ApiResponse(data=data)


@router.post("/sessions/{session_id}/messages", response_class=StreamingResponse, response_model=None, summary="发送文本提问并流式回答")
async def session_messages(
    session_id: UUID,
    request: AiMessageRequest,
    session: SessionDep,
    current_user: CurrentUser,
    runtime: RuntimeDep,
) -> StreamingResponse:
    """接收前失败仍走统一 JSON；建立后通过唯一终态描述结果。"""
    stream = await AiConsultationService(session, runtime).messages(current_user.user_id, session_id, request)
    return ConsultationResponse(stream)


@router.post("/sessions/{session_id}/abort", response_model=ApiResponse[AiSessionActionView], summary="停止原咨询请求")
async def abort_session(
    session_id: UUID,
    request: AiAbortRequest,
    session: SessionDep,
    current_user: CurrentUser,
    runtime: RuntimeDep,
) -> ApiResponse[AiSessionActionView]:
    """停止绑定 request_id，不误取消已经开始的下一轮。"""
    data = await AiConsultationService(session, runtime).abort(current_user.user_id, session_id, request.request_id)
    return ApiResponse(data=data)


@router.post("/sessions/{session_id}/close", response_model=ApiResponse[AiSessionActionView], summary="关闭咨询会话")
async def close_session(
    session_id: UUID,
    request: AiCloseRequest,
    session: SessionDep,
    current_user: CurrentUser,
    runtime: RuntimeDep,
) -> ApiResponse[AiSessionActionView]:
    """配置已经清除时仍允许归属账号关闭残留会话。"""
    data = await AiConsultationService(session, runtime).close(current_user.user_id, session_id)
    return ApiResponse(data=data)
