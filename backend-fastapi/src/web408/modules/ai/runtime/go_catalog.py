"""OpenCode Go 型号注册表：协议、固定地址、能力与逐型号 thinking 元数据的唯一来源。

数据提取自 @earendil-works/pi-coding-agent 0.99.2 内嵌模型目录（MIT，2026-10-03 提取）。
原 Node 服务与 Pi 依赖已从工作区删除，本表是唯一副本，无法再自动生成，新增型号只能手工维护。
协议、固定地址、会话头与参数形状均以本文件为准，不接受浏览器传入端点、请求头或协议。
"""
from dataclasses import dataclass
from typing import Final, Literal, Mapping


ApiProtocol = Literal["openai-completions", "openai-responses", "anthropic-messages"]

PROVIDER_ID: Final = "opencode-go"
PROVIDER_NAME: Final = "OpenCode Go"
# anthropic-messages 走 Anthropic Messages 路径，其余两种协议共用 OpenAI 兼容地址。
OPENAI_BASE_URL: Final = "https://opencode.ai/zen/go/v1"
ANTHROPIC_BASE_URL: Final = "https://opencode.ai/zen/go"
SESSION_HEADER: Final = "x-opencode-session"
CLIENT_HEADER: Final = "x-opencode-client"
# Pi 0.99.2 使用的是 'pi'；本站不是 Pi 客户端，按设计约定不伪装客户端身份，只保留归属头。
CLIENT_LABEL: Final = "408web"
# Go 目录声明的图像缩放上限；本站按原始字节发送，不在此缩放，仅作为注册表事实保留。
REMOTE_IMAGE_MAX_BYTES: Final = 4718592

_COMPLETIONS: Final = "openai-completions"
_RESPONSES: Final = "openai-responses"
_ANTHROPIC: Final = "anthropic-messages"

# 各型号的 thinkingLevelMap：值为 None 表示该档位没有显式取值，按 Pi 的 ?? 语义回退为档位名。
_DS_FLASH = {"minimal": None, "low": "low", "medium": None, "high": "high", "max": "max"}
_DS_PRO = {"minimal": None, "low": None, "medium": None, "high": "high", "max": "max"}
_DS_41 = {"off": None, "minimal": None, "low": "low", "medium": None, "high": "high", "xhigh": None, "max": "max"}
_GLM_52 = {"off": None, "minimal": None, "low": None, "medium": None, "high": "high", "xhigh": None, "max": "max"}
_GLM_53 = {"off": None, "minimal": None, "low": "low", "medium": None, "high": "high", "xhigh": None, "max": "max"}
_HY3 = {"off": "none", "minimal": None, "low": "low", "medium": None, "high": "high", "xhigh": None, "max": None}
_HY4 = {"off": "none", "minimal": None, "low": None, "medium": None, "high": "high", "xhigh": None, "max": None}
_KIMI_K3 = {"off": None, "minimal": None, "low": None, "medium": None, "high": None, "xhigh": None, "max": "max"}
_QWEN_38_MAX = {"off": None, "minimal": None, "low": "low", "medium": "medium", "high": None, "xhigh": "xhigh", "max": None}
_SPACE_BUNNY = {"off": None, "minimal": None, "low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh", "max": "max"}
_LUNA = {"off": None, "minimal": None, "low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh", "max": "max"}
_LUNA_OFF_NONE = {"off": "none", "minimal": None, "low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh", "max": "max"}
_GROK = {"off": None, "minimal": None, "low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh", "max": None}
_MUSE = {"off": None, "minimal": "minimal", "low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh", "max": None}


@dataclass(frozen=True, slots=True)
class GoModel:
    """单个 Go 型号的固定元数据；目录收录只表示协议适配存在，不代表账号有调用权限。"""

    id: str
    name: str
    api: ApiProtocol
    context_window: int
    max_tokens: int
    reasoning: bool = False
    supports_images: bool = False
    thinking_levels: Mapping[str, str | None] | None = None
    # DeepSeek 系型号额外需要 thinking:{type:...} 开关，其余型号只使用 reasoning_effort。
    thinking_toggle: bool = False
    # Go 要求多轮请求在 assistant 消息上回传 reasoning_content。
    reasoning_required: bool = False
    # anthropic-messages 型号允许空 thinking 签名（Go 的 allowEmptySignature）。
    allow_empty_signature: bool = False

    @property
    def base_url(self) -> str:
        """按协议返回固定地址，不使用任何浏览器或环境提供的端点。"""
        return ANTHROPIC_BASE_URL if self.api == _ANTHROPIC else OPENAI_BASE_URL

    def effort_for(self, level: str) -> str | None:
        """把档位映射为 reasoning_effort；off 档只有显式字符串才发送，其余按 ?? 语义回退档位名。"""
        levels = self.thinking_levels or {}
        if level == "off":
            value = levels.get("off")
            return value if isinstance(value, str) else None
        value = levels.get(level)
        return level if value is None else value


MODELS: Final[tuple[GoModel, ...]] = (
    # anthropic-messages：仅两个型号，thinking 由 anthropic_thinking 单独配置。
    GoModel("minimax-m3", "MiniMax-M3", _ANTHROPIC, 1_000_000, 131_072, reasoning=True, supports_images=True),
    GoModel("qwen3.8-flash", "Qwen3.8 Flash", _ANTHROPIC, 1_000_000, 131_072, reasoning=True,
            supports_images=True, allow_empty_signature=True),
    # openai-completions：DeepSeek 系需要 thinking 开关与 reasoning_content 回传。
    GoModel("deepseek-v4-flash", "DeepSeek V4 Flash", _COMPLETIONS, 1_000_000, 384_000, reasoning=True,
            thinking_levels=_DS_FLASH, thinking_toggle=True, reasoning_required=True),
    GoModel("deepseek-v4-flash-vision-exp", "DeepSeek V4 Flash Vision Exp", _COMPLETIONS, 1_000_000, 384_000,
            reasoning=True, supports_images=True, thinking_levels=_DS_FLASH, thinking_toggle=True,
            reasoning_required=True),
    GoModel("deepseek-v4-pro", "DeepSeek V4 Pro (New)", _COMPLETIONS, 1_000_000, 384_000, reasoning=True,
            thinking_levels=_DS_PRO, thinking_toggle=True, reasoning_required=True),
    GoModel("deepseek-v4.1-flash", "DeepSeek V4.1 Flash", _COMPLETIONS, 1_000_000, 384_000, reasoning=True,
            supports_images=True, thinking_levels=_DS_41, thinking_toggle=True, reasoning_required=True),
    GoModel("glm-5.2", "GLM-5.2", _COMPLETIONS, 1_000_000, 131_072, reasoning=True, thinking_levels=_GLM_52),
    GoModel("glm-5.3", "GLM-5.3", _COMPLETIONS, 1_000_000, 131_072, reasoning=True, thinking_levels=_GLM_53),
    GoModel("glm-5.3-flash", "GLM-5.3-Flash", _COMPLETIONS, 1_000_000, 131_072, reasoning=True,
            supports_images=True, thinking_levels=_GLM_53),
    GoModel("hy3", "Hy3", _COMPLETIONS, 256_000, 128_000, reasoning=True, thinking_levels=_HY3),
    GoModel("hy4-preview", "Hy4 preview", _COMPLETIONS, 1_024_000, 64_000, reasoning=True, thinking_levels=_HY4),
    GoModel("kimi-k2.7-code", "Kimi K2.7 Code", _COMPLETIONS, 262_144, 262_144, reasoning=True,
            supports_images=True),
    GoModel("kimi-k3", "Kimi K3", _COMPLETIONS, 1_048_576, 131_072, reasoning=True, supports_images=True,
            thinking_levels=_KIMI_K3),
    GoModel("longcat-2.0", "LongCat-2.0", _COMPLETIONS, 1_000_000, 131_072, reasoning=True),
    GoModel("longcat-2.5-preview-free", "LongCat 2.5 Preview Free", _COMPLETIONS, 1_000_000, 131_072,
            reasoning=True, supports_images=True),
    GoModel("mimo-v2.5", "MiMo V2.5", _COMPLETIONS, 1_000_000, 128_000, reasoning=True, supports_images=True),
    GoModel("mimo-v2.5-pro", "MiMo V2.5 Pro", _COMPLETIONS, 1_048_576, 128_000, reasoning=True),
    GoModel("mimo-v2.6-flash", "MiMo-V2.6-Flash", _COMPLETIONS, 1_048_576, 131_072, reasoning=True,
            supports_images=True),
    GoModel("mimo-v2.6-pro", "MiMo-V2.6-Pro", _COMPLETIONS, 1_048_576, 131_072, reasoning=True,
            supports_images=True),
    GoModel("minimax-m2.7", "MiniMax-M2.7", _COMPLETIONS, 204_800, 131_072, reasoning=True),
    GoModel("qwen3.7-plus", "Qwen3.7 Plus", _COMPLETIONS, 1_000_000, 65_536, reasoning=True,
            supports_images=True),
    GoModel("qwen3.8-max", "Qwen3.8 Max", _COMPLETIONS, 1_000_000, 131_072, reasoning=True,
            supports_images=True, thinking_levels=_QWEN_38_MAX),
    GoModel("space-bunny-free", "Space Bunny Free", _COMPLETIONS, 1_048_576, 524_288, reasoning=True,
            supports_images=True, thinking_levels=_SPACE_BUNNY),
    # openai-responses：全部固定 store=false，并按型号决定是否请求加密推理内容。
    GoModel("gpt-5.6-luna", "GPT-5.6 Luna", _RESPONSES, 1_050_000, 128_000, reasoning=True,
            supports_images=True, thinking_levels=_LUNA),
    GoModel("gpt-6-luna", "GPT-6 Luna", _RESPONSES, 1_050_000, 128_000, reasoning=True,
            supports_images=True, thinking_levels=_LUNA_OFF_NONE),
    GoModel("grok-4.6", "Grok 4.6", _RESPONSES, 500_000, 500_000, reasoning=True, supports_images=True,
            thinking_levels=_GROK),
    GoModel("grok-4.7", "Grok 4.7", _RESPONSES, 500_000, 500_000, reasoning=True, supports_images=True,
            thinking_levels=_GROK),
    GoModel("muse-spark-1.2-contributor", "Muse Spark 1.2 Contributor", _RESPONSES, 1_048_576, 131_072,
            reasoning=True, supports_images=True, thinking_levels=_MUSE),
    GoModel("muse-spark-1.3-contributor", "Muse Spark 1.3 Contributor", _RESPONSES, 1_048_576, 131_072,
            reasoning=True, supports_images=True, thinking_levels=_MUSE),
)

MODEL_INDEX: Final[dict[str, GoModel]] = {model.id: model for model in MODELS}


def find_model(model_id: str) -> GoModel | None:
    """按精确型号标识查询；未收录型号只能拒绝，不猜测协议或能力。"""
    return MODEL_INDEX.get(model_id)
