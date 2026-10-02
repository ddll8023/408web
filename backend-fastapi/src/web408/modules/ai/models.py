"""账号 AI 凭据与默认咨询配置分表保存，不持久化模型响应或聊天。"""
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, ForeignKeyConstraint, Text, UniqueConstraint
from sqlmodel import Field

from web408.models.base import BaseModel


class UserAiProviderConfig(BaseModel, table=True):
    """每个账号、每个供应商一份加密 Key，不能被其他账号引用。"""

    __tablename__ = "user_ai_provider_config"
    __table_args__ = (
        UniqueConstraint("user_id", "provider_id", name="uq_user_ai_provider_owner"),
    )

    user_id: int = Field(foreign_key="user.id", nullable=False)
    provider_id: str = Field(max_length=100, nullable=False)
    enabled: bool = Field(default=True, nullable=False)
    api_key_ciphertext: str = Field(sa_column=Column(Text, nullable=False), repr=False)
    key_version: str = Field(max_length=32, nullable=False)
    revision: str = Field(default_factory=lambda: str(uuid4()), max_length=36, nullable=False)


class UserAiConfig(BaseModel, table=True):
    """每个账号一套默认选择；复合外键保证只能选择自己配置的供应商。"""

    __tablename__ = "user_ai_config"
    __table_args__ = (
        CheckConstraint("input_mode IN ('text', 'text_image')", name="ck_user_ai_config_input_mode"),
        ForeignKeyConstraint(
            ["user_id", "provider_id"],
            ["user_ai_provider_config.user_id", "user_ai_provider_config.provider_id"],
            name="fk_user_ai_default_provider",
        ),
    )

    user_id: int = Field(foreign_key="user.id", unique=True, nullable=False)
    provider_id: str = Field(max_length=100, nullable=False)
    model_id: str = Field(max_length=200, nullable=False)
    input_mode: str = Field(default="text", max_length=20, nullable=False)
    enabled: bool = Field(default=True, nullable=False)
    revision: str = Field(default_factory=lambda: str(uuid4()), max_length=36, nullable=False)
