"""模型服务的公开及内部契约；Key 只允许进入保存和私有发送边界。"""
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints, field_validator


# 与历史实现的准入窗口一致；必须在读取配置之前固定，解密和网络等待不延长。
AGENT_ADMISSION_MS = 60_000
# 配置层输入模式；本批运行时不读取该字段，按题目是否含图片自动判定，仅保留给历史配置。
AiInputMode = Literal["text", "text_image"]
# 自定义供应商可选的三种上游协议；地址与会话头由所选协议决定。
AiProtocol = Literal["openai-completions", "openai-responses", "anthropic-messages"]
ProviderId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*$")]
ModelId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


def _clean_api_key(value: SecretStr | None) -> SecretStr | None:
    """空白保留原 Key，认证载荷与历史实现一致只接受可打印 ASCII。"""
    if value is None:
        return None
    key = value.get_secret_value().strip()
    if not key:
        return None
    if any(not 0x21 <= ord(char) <= 0x7E for char in key):
        raise ValueError("API Key 格式无效，请重新填写")
    return SecretStr(key)


def _clean_base_url(value: str) -> str:
    """只接受带主机名的 http(s) 地址，拒绝控制字符、内嵌凭据、查询串与片段。

    自定义端点由账号自行填写，服务端不探测、不重定向；协议与主机合法性在此收口。
    """
    url = value.strip()
    if len(url) > 2048 or any(ord(char) < 0x20 or ord(char) == 0x7F for char in url):
        raise ValueError("接口地址格式无效，请填写 http(s) 地址")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("接口地址格式无效，请填写 http(s) 地址")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("接口地址不能包含账号、查询串或片段")
    return url


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
        """空白保留原 Key，认证载荷与历史实现一致只接受可打印 ASCII。"""
        return _clean_api_key(value)


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
    # 自定义供应商标记与可编辑的接口信息；内置供应商保持默认值。
    custom: bool = False
    base_url: str | None = Field(default=None, max_length=2048)
    protocol: AiProtocol | None = None


class AgentProvidersView(AiSchema):
    providers: list[AiCatalogProviderView] = Field(max_length=100)


class AiProviderView(AiCatalogProviderView):
    configured: bool
    enabled: bool
    has_api_key: bool
    revision: UUID | None


class AiProvidersView(AiSchema):
    providers: list[AiProviderView] = Field(max_length=100)


class AiCustomProviderSaveRequest(AiSchema):
    """新建或更新当前账号的自定义供应商；未提供 provider_id 时由服务端生成标识。"""

    provider_id: ProviderId | None = None
    name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=8, max_length=2048)
    protocol: AiProtocol
    enabled: bool = Field(strict=True)
    api_key: SecretStr | None = Field(default=None, max_length=4096, repr=False)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        """名称必须包含非空白字符，不保留首尾空白。"""
        name = value.strip()
        if not name:
            raise ValueError("请填写供应商名称")
        return name

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        """只接受 http(s) 地址，服务端不探测、不跟随重定向。"""
        return _clean_base_url(value)

    @field_validator("api_key")
    @classmethod
    def normalize_api_key(cls, value: SecretStr | None) -> SecretStr | None:
        """空值表示保留旧 Key；新值只接受可打印 ASCII。"""
        return _clean_api_key(value)


class AiCustomProviderView(AiProviderConfigView):
    name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=2048)
    protocol: AiProtocol
    model_count: int = Field(ge=0)


class AiCustomModelRequest(AiProviderRequest):
    """自定义型号操作都以供应商与型号精确定位。"""

    model_id: ModelId


class AiCustomModelSaveRequest(AiCustomModelRequest):
    """手工录入型号能力；服务端不探测上游真实能力。"""

    name: str = Field(min_length=1, max_length=200)
    supports_images: bool = Field(strict=True)
    context_window: int = Field(ge=0, le=10_000_000, strict=True)
    max_tokens: int = Field(ge=1, le=1_000_000, strict=True)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        """名称必须包含非空白字符，不保留首尾空白。"""
        name = value.strip()
        if not name:
            raise ValueError("请填写型号名称")
        return name


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
    source: Literal["bundled", "custom"]


class AiModelCheckRequest(AiProviderRequest):
    """显式确认一次真实请求，UUID 防止同一请求被重复执行。"""

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
