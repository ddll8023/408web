"""
项目配置模块
使用 pydantic-settings 管理环境变量配置
"""
from typing import List
from functools import lru_cache
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    database_url: str = "sqlite+aiosqlite:///./data/web408.db"

    class Config:
        env_prefix = "DATABASE_"


class JwtConfig(BaseSettings):
    """JWT认证配置"""
    secret: str = "3f8b9e2a7c1d4f6e8a9b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f"
    algorithm: str = "HS256"

    class Config:
        env_prefix = "JWT_"


class UploadConfig(BaseSettings):
    """文件上传配置"""
    upload_dir: str = "uploads/images"
    max_file_size: int = 104857600  # 100MB

    class Config:
        env_prefix = "UPLOAD_"


class ServerConfig(BaseSettings):
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8081
    api_prefix: str = "/api"

    class Config:
        env_prefix = "SERVER_"


class CorsConfig(BaseSettings):
    """CORS配置"""
    origins: List[str] = ["http://localhost:5173", "http://localhost:5174"]

    class Config:
        env_prefix = "CORS_"

    @classmethod
    def from_env(cls):
        """从环境变量解析逗号分隔的 origins"""
        import os
        origins_env = os.getenv("CORS_ORIGINS", "")
        if origins_env:
            return cls(origins=origins_env.split(","))
        return cls()


class LoggingConfig(BaseSettings):
    """日志配置"""
    log_dir: str = "logs"
    log_file: str = "app.log"
    log_level: str = "INFO"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5

    class Config:
        env_prefix = "LOGGING_"


class Settings(BaseSettings):
    """项目聚合配置（所有配置类的统一入口）"""
    database: DatabaseConfig = DatabaseConfig()
    jwt: JwtConfig = JwtConfig()
    upload: UploadConfig = UploadConfig()
    server: ServerConfig = ServerConfig()
    cors: CorsConfig = CorsConfig()
    logging: LoggingConfig = LoggingConfig()

    class Config:
        env_prefix = ""


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例（带缓存），优先从环境变量加载 CORS 配置"""
    return Settings(
        cors=CorsConfig.from_env()
    )


# 便捷访问方式
settings = get_settings()
