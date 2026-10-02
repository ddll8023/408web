"""按 Go 型号协议构造 PydanticAI 模型与每轮请求设置，隔离凭据、工具与隐式副作用。

只使用 PydanticAI 的模型与消息转换能力：不启用 Agent 编排、工具、上下文压缩或输出重试；
SDK 客户端由本模块自建并显式关闭重试、环境代理与重定向，Key 只进入当前实例。
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
from web408.modules.ai.runtime.go_catalog import (
    CLIENT_HEADER,
    CLIENT_LABEL,
    SESSION_HEADER,
    GoModel,
)


CONNECT_TIMEOUT: Final = 5.0
MIN_THINKING_BUDGET: Final = 1024


def _http_client(read_seconds: int) -> httpx2.AsyncClient:
    """自建 HTTP 客户端：不继承环境代理，也不向重定向地址继续携带认证头。"""
    return httpx2.AsyncClient(
        timeout=httpx2.Timeout(read=read_seconds, connect=CONNECT_TIMEOUT, write=read_seconds, pool=CONNECT_TIMEOUT),
        follow_redirects=False,
        trust_env=False,
    )


def _profile(model: GoModel) -> OpenAIModelProfile | None:
    """给出协议级 profile：字段名、请求角色、thinking 回传方式与无状态 store 行为。

    Go 的 compat 声明 maxTokensField=max_tokens、supportsDeveloperRole=false、supportsStore=false，
    这里逐条落到 PydanticAI 的 profile 上，避免使用库默认值造成静默差异。
    """
    if model.api == "openai-completions":
        options: dict[str, object] = {
            "openai_chat_supports_max_completion_tokens": False,
            "openai_system_prompt_role": "system",
            "openai_supports_strict_tool_definition": False,
        }
        if model.reasoning:
            options["openai_chat_thinking_field"] = "reasoning_content"
            options["openai_chat_send_back_thinking_parts"] = "field" if model.reasoning_required else "auto"
        return OpenAIModelProfile(**options)  # pyright: ignore[reportArgumentType]
    if model.api == "openai-responses":
        return OpenAIModelProfile(
            openai_responses_requires_store_false=True,
            openai_supports_encrypted_reasoning_content=model.reasoning,
            openai_system_prompt_role="system",
        )
    # anthropic-messages 使用库默认 profile：型号不在 Anthropic 官方表中，不做能力猜测。
    return None


def _extra_body(model: GoModel, level: str) -> dict[str, object]:
    """注入 Go 特有的 thinking 参数；这些参数没有统一的库声明，只能逐型号显式给出。"""
    if model.api == "anthropic-messages" or not model.reasoning:
        return {}
    if model.api == "openai-completions":
        body: dict[str, object] = {}
        if model.thinking_toggle:
            body["thinking"] = {"type": "disabled" if level == "off" else "enabled"}
        effort = model.effort_for(level)
        if effort is not None:
            body["reasoning_effort"] = effort
        return body
    levels = model.thinking_levels
    if level == "off" and levels is not None and "off" in levels and levels["off"] is None:
        # Pi 对显式 off:null 的型号不发送 reasoning 参数。
        return {}
    effort = model.effort_for(level) or "none"
    return {"reasoning": {"effort": effort, "summary": "auto"}}


def _anthropic_thinking(model: GoModel, level: str, max_tokens: int) -> dict[str, object] | None:
    """把档位换算为 Anthropic thinking 配置，预算上限不超过输出上限并留出回答空间。"""
    if not model.reasoning:
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

    go_model: GoModel
    model: Model
    client: AsyncOpenAI | AsyncAnthropic

    def settings(self, *, level: str, session_id: str, timeout_seconds: int, max_tokens: int) -> ModelSettings:
        """构造单轮设置：固定会话与归属头、Go thinking 参数、输出上限与超时。

        不设置 unified `thinking`，避免库再自行推导一份 reasoning_effort；
        thinking 一律通过 extra_body 按 Go 的 compat 形状发送。
        """
        settings: ModelSettings = {
            "extra_headers": {SESSION_HEADER: session_id, CLIENT_HEADER: CLIENT_LABEL},
            "max_tokens": max_tokens,
            "timeout": timeout_seconds,
        }
        body = _extra_body(self.go_model, level)
        if body:
            settings["extra_body"] = body
        if self.go_model.api == "anthropic-messages":
            thinking = _anthropic_thinking(self.go_model, level, max_tokens)
            if thinking is not None:
                settings["anthropic_thinking"] = thinking
        return settings

    async def aclose(self) -> None:
        """关闭私有 HTTP 客户端；失败只表示本地收尾未确认，不影响上游已经发生的调用。"""
        await self.client.close()


def build_model(model: GoModel, api_key: str, timeout_seconds: int) -> BuiltModel:
    """按型号协议构造模型实例；Key 只进入当前客户端，不做环境变量兜底。"""
    if not api_key:
        raise AiRuntimeError("INVALID_KEY")
    http_client = _http_client(timeout_seconds)
    try:
        if model.api == "anthropic-messages":
            anthropic_client = AsyncAnthropic(
                api_key=api_key, base_url=model.base_url, http_client=http_client, max_retries=0,
            )
            return BuiltModel(
                go_model=model,
                model=AnthropicModel(model.id, provider=AnthropicProvider(anthropic_client=anthropic_client)),
                client=anthropic_client,
            )
        openai_client = AsyncOpenAI(
            api_key=api_key, base_url=model.base_url, http_client=http_client, max_retries=0,
        )
        provider = OpenAIProvider(openai_client=openai_client)
        instance = (
            OpenAIResponsesModel(model.id, provider=provider, profile=_profile(model))
            if model.api == "openai-responses"
            else OpenAIChatModel(model.id, provider=provider, profile=_profile(model))
        )
        return BuiltModel(go_model=model, model=instance, client=openai_client)
    except AiRuntimeError:
        raise
    except Exception:
        # 构造失败不暴露库异常原文；已创建的客户端在下一层回收。
        raise AiRuntimeError("SDK_UNAVAILABLE") from None
