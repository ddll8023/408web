"""内置目录与账号自定义型号共用的不可变型号定义。

本模块只描述协议、地址与能力，不读取数据库、不加载凭据、不发起请求；
自定义端点的合法性由业务层校验，运行模块只接收已构造好的 ModelSpec。
"""
from dataclasses import dataclass
from typing import Literal, Mapping


ApiProtocol = Literal["openai-completions", "openai-responses", "anthropic-messages"]


@dataclass(frozen=True, slots=True)
class ThinkingSpec:
    """推理档位的逐级映射；目前只有内置 OpenCode Go 目录声明该元数据。"""

    levels: Mapping[str, str | None]
    toggle: bool = False
    reasoning_required: bool = False
    allow_empty_signature: bool = False


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """一次调用所需的型号定义；凭据与会话标识都由调用方另行传入。"""

    provider_id: str
    id: str
    name: str
    api: ApiProtocol
    base_url: str
    context_window: int
    max_tokens: int
    reasoning: bool = False
    supports_images: bool = False
    thinking: ThinkingSpec | None = None
    # 只有内置 Go 需要会话与归属请求头；自定义端点不伪造客户端身份。
    provider_headers: bool = False

    def effort_for(self, level: str) -> str | None:
        """把档位映射为 reasoning_effort；未声明的档位按档位名回退，off 需显式取值。"""
        levels = self.thinking.levels if self.thinking is not None else {}
        if level == "off":
            value = levels.get("off")
            return value if isinstance(value, str) else None
        value = levels.get(level)
        return level if value is None else value


def custom_spec(
    *, provider_id: str, base_url: str, protocol: ApiProtocol, model_id: str, name: str,
    supports_images: bool, context_window: int, max_tokens: int,
) -> ModelSpec:
    """把账号自定义型号转换为运行时定义；不声明推理参数与 Go 专用请求头。"""
    return ModelSpec(
        provider_id=provider_id, id=model_id, name=name or model_id, api=protocol, base_url=base_url,
        context_window=context_window, max_tokens=max_tokens, supports_images=supports_images,
    )
