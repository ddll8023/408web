"""应用级运行配置。"""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


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


class Settings(BaseSettings):
    """项目聚合配置。"""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    jwt: JwtConfig = Field(default_factory=JwtConfig)
    upload: UploadConfig = Field(default_factory=UploadConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

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
