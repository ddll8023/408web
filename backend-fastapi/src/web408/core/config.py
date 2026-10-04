"""应用级运行配置。"""
from functools import lru_cache
from pathlib import Path
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# 与数据库、上传和日志一样，以后端启动工作目录为基准，避免依赖安装后的源码层级。
ENV_FILE = Path.cwd() / ".env"


class DatabaseConfig(BaseSettings):
    """数据库配置。"""

    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/web408.db",
        validation_alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


class JwtConfig(BaseSettings):
    """JWT 认证配置。"""

    secret: str = Field(
        ...,
        min_length=32,
        validation_alias="JWT_SECRET",
        description="必须从环境变量或密钥管理系统提供",
    )
    algorithm: Literal["HS256"] = Field(
        default="HS256",
        validation_alias="JWT_ALGORITHM",
    )
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


class UploadConfig(BaseSettings):
    """文件上传配置。"""

    upload_dir: str = Field(
        default="uploads/images",
        validation_alias="UPLOAD_DIR",
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024,
        gt=0,
        le=100 * 1024 * 1024,
        validation_alias="MAX_FILE_SIZE",
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


class ServerConfig(BaseSettings):
    """服务器配置。"""

    host: str = Field(default="0.0.0.0", validation_alias="SERVER_HOST")
    port: int = Field(default=7785, ge=1, le=65535, validation_alias="SERVER_PORT")
    api_prefix: str = Field(default="/api", validation_alias="API_PREFIX")

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


class CorsConfig(BaseSettings):
    """CORS 配置。"""

    origins: str = Field(
        default="http://localhost:7784",
        validation_alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def allowed_origins(self) -> list[str]:
        """返回清理后的允许来源列表。"""
        return [origin.strip() for origin in self.origins.split(",") if origin.strip()]


class LoggingConfig(BaseSettings):
    """日志配置。"""

    log_dir: str = "logs"
    log_file: str = "app.log"
    log_level: str = "INFO"
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


class AiConfig(BaseModel):
    """固定的 AI 运行默认值，不读取环境配置或承载个人配置与系统凭据。"""

    generation_timeout_seconds: int = Field(default=120, ge=5, le=300)
    check_timeout_seconds: int = Field(default=30, ge=5, le=120)
    question_text_max_bytes: int = Field(default=65536, ge=1024, le=65536)
    stream_event_max_bytes: int = Field(default=524288, ge=131072, le=1048576)
    # 题目图片预算：单题张数、单图字节与单题总字节，超限的图不发送只登记原因。
    question_image_max_count: int = Field(default=6, ge=0, le=20)
    question_image_max_bytes: int = Field(default=4 * 1024 * 1024, ge=1024, le=20 * 1024 * 1024)
    question_image_total_max_bytes: int = Field(default=8 * 1024 * 1024, ge=1024, le=40 * 1024 * 1024)
    # 内联 SVG 以源码文本进入上下文，单独限额，不得挤占题目文本上限。
    question_svg_max_bytes: int = Field(default=8192, ge=0, le=65536)
    question_svg_total_max_bytes: int = Field(default=32768, ge=0, le=65536)

    model_config = ConfigDict(frozen=True, extra="forbid")


class Settings(BaseSettings):
    """项目聚合配置。"""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    jwt: JwtConfig = Field(default_factory=JwtConfig)
    upload: UploadConfig = Field(default_factory=UploadConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    # 非 Settings 字段，避免通过 AI JSON 环境变量覆盖固定运行默认值。
    ai: ClassVar[AiConfig] = AiConfig()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取缓存的项目配置。"""
    return Settings()


settings = get_settings()
