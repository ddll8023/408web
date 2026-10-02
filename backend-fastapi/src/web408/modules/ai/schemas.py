"""模型服务的公开及内部契约；Key 只允许进入保存和私有发送边界。"""
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints, field_validator


# 与 Node 的准入窗口一致；必须在读取配置之前固定，解密和网络等待不延长。
AGENT_ADMISSION_MS = 60_000
AiInputMode = Literal["text", "text_image"]
ProviderId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*$")]
ModelId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class AiSchema(BaseModel):
    """AI 边界不接受未声明字段。"""

    model_config = ConfigDict(extra="forbid")


class AiSettingsActionRequest(AiSchema):
    """账号由认证依赖提供，查询与清除默认设置只接受空对象。"""


class AiProviderRequest(AiSchema):
    provider_id: ProviderId


class AiProviderSaveRequest(AiProviderRequest):
    enabled: bool = Field(strict=True)
    api_key: SecretStr | None = Field(default=None, max_length=4096, repr=False)

    @field_validator("api_key")
    @classmethod
    def normalize_api_key(cls, value: SecretStr | None) -> SecretStr | None:
        """空白保留原 Key，认证载荷与 Node 一致只接受可打印 ASCII。"""
        if value is None:
            return None
        key = value.get_secret_value().strip()
        if not key:
            return None
        if any(not 0x21 <= ord(char) <= 0x7E for char in key):
            raise ValueError("API Key 格式无效，请重新填写")
        return SecretStr(key)


class AiProviderConfigView(AiSchema):
    provider_id: ProviderId
    enabled: bool
    has_api_key: bool
    revision: UUID


class AiCatalogProviderView(AiSchema):
    id: ProviderId
    name: str = Field(min_length=1, max_length=200)
    supported: bool
    unsupported_reason: str | None = Field(default=None, max_length=300)
    base_urls: list[str] = Field(max_length=8)
    model_count: int = Field(ge=0)


class AgentProvidersView(AiSchema):
    providers: list[AiCatalogProviderView] = Field(max_length=100)


class AiProviderView(AiCatalogProviderView):
    configured: bool
    enabled: bool
    has_api_key: bool
    revision: UUID | None


class AiProvidersView(AiSchema):
    providers: list[AiProviderView] = Field(max_length=100)


class AiSettingsSaveRequest(AiProviderRequest):
    """默认选择不携带 Key，不能把保存成功当作供应商调用验证。"""

    model_id: ModelId
    input_mode: AiInputMode
    enabled: bool = Field(strict=True)


class AiSettingsView(AiSchema):
    provider_id: ProviderId
    model_id: ModelId
    input_mode: AiInputMode
    enabled: bool
    revision: UUID


class AiModelsQueryRequest(AiProviderRequest):
    search: str = Field(default="", max_length=200)
    offset: int = Field(default=0, ge=0, le=100000, strict=True)
    limit: int = Field(default=30, ge=1, le=100, strict=True)
    model_id: ModelId | None = None

    @field_validator("search")
    @classmethod
    def validate_search(cls, value: str) -> str:
        """拒绝控制字符和无效 Unicode，保持搜索词与内部文本契约一致。"""
        if any(ord(char) < 0x20 or ord(char) == 0x7F or 0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise ValueError("搜索词格式无效")
        return value


class AiModelView(AiSchema):
    provider: ProviderId
    id: ModelId
    name: str = Field(min_length=1, max_length=200)
    supports_images: bool


class AiCatalogModelView(AiModelView):
    reasoning: bool
    context_window: int = Field(ge=0)
    max_tokens: int = Field(ge=0)
    api: str = Field(min_length=1, max_length=100)


class AiModelsView(AiSchema):
    provider_id: ProviderId
    models: list[AiCatalogModelView] = Field(max_length=100)
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    source: Literal["bundled"]


class AiModelCheckRequest(AiProviderRequest):
    """显式确认一次真实请求，UUID 防止相同请求在 Node 重复执行。"""

    model_id: ModelId
    provider_revision: UUID
    request_id: UUID
    confirm_usage: Literal[True]

    @field_validator("confirm_usage", mode="before")
    @classmethod
    def require_explicit_confirmation(cls, value: object) -> object:
        """只有布尔 True 才算明确确认，不能用其他真值隐式同意额度消耗。"""
        if value is not True:
            raise ValueError("检测前必须明确确认额度消耗")
        return value


class AiModelCheckView(AiSchema):
    request_id: UUID
    model: AiModelView
    success: Literal[True]
