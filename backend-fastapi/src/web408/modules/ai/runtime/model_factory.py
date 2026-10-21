"""按型号协议构造 PydanticAI 模型与每轮请求设置，隔离凭据、工具与隐式副作用。

内置 Go 与账号自定义型号共用本模块：只有显式声明 thinking 元数据的型号才注入
Go 的推理参数与会话头；自定义端点按所选协议的最小请求发送，不伪装客户端身份。
不启用 Agent 编排、工具、上下文压缩或输出重试；SDK 客户端由本模块自建并显式关闭
重试、环境代理与重定向，Key 只进入当前实例。
"""
from dataclasses import dataclass
from typing import Final

import httpx2
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel
from pydantic_ai.profiles.anthropic import ANTHROPIC_THINKING_BUDGET_MAP
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from web408.modules.ai.runtime.errors import AiRuntimeError
from web408.modules.ai.runtime.go_catalog import CLIENT_HEADER, CLIENT_LABEL, SESSION_HEADER
from web408.modules.ai.runtime.model_spec import ModelSpec


CONNECT_TIMEOUT: Final = 5.0
MIN_THINKING_BUDGET: Final = 1024


def _http_client(read_seconds: int) -> httpx2.AsyncClient:
    """自建 HTTP 客户端：不继承环境代理，也不向重定向地址继续携带认证头。"""
    return httpx2.AsyncClient(
        timeout=httpx2.Timeout(read=read_seconds, connect=CONNECT_TIMEOUT, write=read_seconds, pool=CONNECT_TIMEOUT),
        follow_redirects=False,
        trust_env=False,
    )


def _profile(spec: ModelSpec) -> OpenAIModelProfile | None:
    """给出协议级 profile：字段名、请求角色、thinking 回传方式与无状态 store 行为。

    内置 Go 的 compat 逐条落到 profile；自定义型号只保留通用约定，不猜测推理回传方式。
    """
    if spec.api == "openai-completions":
        options: dict[str, object] = {
            "openai_chat_supports_max_completion_tokens": False,
            "openai_system_prompt_role": "system",
            "openai_supports_strict_tool_definition": False,
        }
        if spec.thinking is not None and spec.reasoning:
            options["openai_chat_thinking_field"] = "reasoning_content"
            options["openai_chat_send_back_thinking_parts"] = (
                "field" if spec.thinking.reasoning_required else "auto"
            )
        return OpenAIModelProfile(**options)  # pyright: ignore[reportArgumentType]
    if spec.api == "openai-responses":
        return OpenAIModelProfile(
            openai_responses_requires_store_false=True,
            openai_supports_encrypted_reasoning_content=spec.reasoning,
            openai_system_prompt_role="system",
        )
    # anthropic-messages 使用库默认 profile：不做官方型号表之外的能力猜测。
    return None


def _extra_body(spec: ModelSpec, level: str) -> dict[str, object]:
    """注入内置 Go 特有的 thinking 参数；自定义型号不发送任何推理字段。"""
    if spec.thinking is None or not spec.reasoning or spec.api == "anthropic-messages":
        return {}
    if spec.api == "openai-completions":
        body: dict[str, object] = {}
        if spec.thinking.toggle:
            body["thinking"] = {"type": "disabled" if level == "off" else "enabled"}
        effort = spec.effort_for(level)
        if effort is not None:
            body["reasoning_effort"] = effort
        return body
    levels = spec.thinking.levels
    if level == "off" and "off" in levels and levels["off"] is None:
        # 内置目录对显式 off:null 的型号不发送 reasoning 参数。
        return {}
    effort = spec.effort_for(level) or "none"
    return {"reasoning": {"effort": effort, "summary": "auto"}}


def _anthropic_thinking(spec: ModelSpec, level: str, max_tokens: int) -> dict[str, object] | None:
    """把档位换算为 Anthropic thinking 配置，预算上限不超过输出上限并留出回答空间。"""
    if spec.thinking is None or not spec.reasoning:
        return None
    if level == "off":
        return {"type": "disabled"}
    budget = ANTHROPIC_THINKING_BUDGET_MAP.get(level, ANTHROPIC_THINKING_BUDGET_MAP[True])
    return {
        "type": "enabled",
        "budget_tokens": min(budget, max(MIN_THINKING_BUDGET, max_tokens - MIN_THINKING_BUDGET)),
    }


@dataclass(slots=True)
class BuiltModel:
    """会话或检测持有的模型实例与私有客户端；释放时必须关闭客户端。"""

    spec: ModelSpec
    model: Model
    client: AsyncOpenAI | AsyncAnthropic

    def settings(self, *, level: str, session_id: str, timeout_seconds: int, max_tokens: int) -> ModelSettings:
        """构造单轮设置：内置 Go 的会话与归属头、thinking 参数、输出上限与超时。

        不设置 unified `thinking`，避免库再自行推导一份 reasoning_effort；
        thinking 一律通过 extra_body 按型号声明发送，自定义型号不发送推理字段。
        """
        settings: ModelSettings = {"max_tokens": max_tokens, "timeout": timeout_seconds}
        if self.spec.provider_headers:
            settings["extra_headers"] = {SESSION_HEADER: session_id, CLIENT_HEADER: CLIENT_LABEL}
        body = _extra_body(self.spec, level)
        if body:
            settings["extra_body"] = body
        if self.spec.api == "anthropic-messages":
            thinking = _anthropic_thinking(self.spec, level, max_tokens)
            if thinking is not None:
                settings["anthropic_thinking"] = thinking
        return settings

    async def aclose(self) -> None:
        """关闭私有 HTTP 客户端；失败只表示本地收尾未确认，不影响上游已经发生的调用。"""
        await self.client.close()


def build_model(spec: ModelSpec, api_key: str, timeout_seconds: int) -> BuiltModel:
    """按型号协议构造模型实例；Key 只进入当前客户端，不做环境变量兜底。"""
    if not api_key:
        raise AiRuntimeError("INVALID_KEY")
    http_client = _http_client(timeout_seconds)
    try:
        if spec.api == "anthropic-messages":
            anthropic_client = AsyncAnthropic(
                api_key=api_key, base_url=spec.base_url, http_client=http_client, max_retries=0,
            )
            return BuiltModel(
                spec=spec,
                model=AnthropicModel(spec.id, provider=AnthropicProvider(anthropic_client=anthropic_client)),
                client=anthropic_client,
            )
        openai_client = AsyncOpenAI(
            api_key=api_key, base_url=spec.base_url, http_client=http_client, max_retries=0,
        )
        provider = OpenAIProvider(openai_client=openai_client)
        instance = (
            OpenAIResponsesModel(spec.id, provider=provider, profile=_profile(spec))
            if spec.api == "openai-responses"
            else OpenAIChatModel(spec.id, provider=provider, profile=_profile(spec))
        )
        return BuiltModel(spec=spec, model=instance, client=openai_client)
    except AiRuntimeError:
        raise
    except Exception:
        # 构造失败不暴露库异常原文；已创建的客户端在下一层回收。
        raise AiRuntimeError("SDK_UNAVAILABLE") from None
