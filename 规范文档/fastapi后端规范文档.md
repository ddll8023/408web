# FastAPI 后端开发规范文档

## 1. 文档概述
本文档定义了基于 FastAPI 框架的后端开发统一规范。所有开发人员必须遵循本规范，以确保代码的现代性、高性能和可维护性。
**核心原则**：KISS (保持简单)、YAGNI (不过度设计)、SOLID (面向对象设计)。

## 2. 技术栈标准
- **语言版本**: Python 3.10+
- **Web框架**: FastAPI
- **数据验证**: Pydantic V2
- **ORM框架**: SQLModel (基于 SQLAlchemy 2.0+)
- **数据库**: 支持 SQLite（开发/测试）、MySQL/PostgreSQL（生产）
- **数据库驱动**: aiosqlite（SQLite）、aiomysql（MySQL）
- **包/环境管理**: conda + requirements.txt

## 3. 项目结构规范
采用功能模块化与分层架构相结合：
- `app/main.py`: 应用入口。
- `app/config`: 项目核心配置。
- `app/db`: 数据库连接与会话管理 (Session)。
- `app/models`: SQLAlchemy ORM 模型定义（按模块划分）。
- `app/schemas`: 统一响应模型与分页模型定义。
- `app/api`: 路由与控制器 (Routers, Dependencies)。
- `app/services`: 业务逻辑与数据库操作实现。
- `app/utils`: 通用工具函数组件。

## 4. 命名与代码风格
- **代码格式**: 严格遵循 **PEP 8** 规范。
- **类名**: 使用 `PascalCase` (如 `UserCreate`).
- **函数/变量名**: 使用 `snake_case` (如 `get_active_users`).
- **类型提示**: 所有函数参数和返回值**必须**使用 Type Hints。
- **Docstrings**: 使用 Google Style 编写函数/类文档。

## 5. API 层开发规范 (Routers)
- **职责**: 处理 HTTP 请求/响应、通过 `Depends` 注入依赖、参数校验、调用 Service。
- **禁止**: 禁止在 Router 中直接编写复杂 SQL 或逻辑处理。
- **HTTP方法**:
    - `GET`: 获取资源。
    - `POST`: 创建资源。
    - `PUT` / `PATCH`: 更新资源。
    - `DELETE`: 删除资源。
- **响应模型**: 必须在路由装饰器中指定 `response_model`，利用 Pydantic 自动过滤数据。
- **依赖注入**: 数据库 Session、当前用户等必须通过 `Depends()` 或 `Annotated` 注入，严禁使用全局变量。

### 5.1 依赖注入写法（官方推荐）

FastAPI 官方推荐使用 `Annotated` 简化依赖注入：

```python
from typing import Annotated
from fastapi import Depends

# 定义依赖类型别名
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]

# 在路由函数中使用
async def get_items(session: SessionDep):
    pass
```

### 5.2 Router 函数签名示例

```python
@router.get("/items", response_model=Response[ItemListResponse])
async def get_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
) -> Response[ItemListResponse]:
    """分页获取列表"""
    service = ItemService(session)
    return await service.get_paginated(page, page_size)
```

## 6. 数据模型规范 (Schemas)
- **职责**: 仅定义全局统一的 **响应模板** (Response Template) 和 **分页模板** (Pagination Template)。
- **输入参数**: 不强制要求定义复杂的 Pydantic Input Model，可灵活处理。
- **验证**: 侧重于响应数据的标准化格式 (如 `code`, `msg`, `data`)。

## 7. 数据库层规范 (Models & Services)

### 7.1 数据库连接配置

**支持多种数据库驱动**：

| 数据库 | 驱动 | 连接字符串示例 |
|--------|------|--------------|
| SQLite（开发/测试） | aiosqlite | `sqlite+aiosqlite:///./data/web408.db` |
| MySQL（生产） | aiomysql | `mysql+aiomysql://user:password@host/db` |
| PostgreSQL（生产） | asyncpg | `postgresql+asyncpg://user:password@host/db` |

**注意**：严禁使用同步驱动（如 pymysql、psycopg2），否则会阻塞整个 Event Loop。

### 7.2 Session 依赖注入（官方推荐方式）

根据 FastAPI 官方文档，推荐使用 `yield` 的依赖注入函数管理 Session 生命周期：

```python
from typing import Annotated, Generator
from fastapi import Depends
from sqlmodel import Session, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# 数据库引擎（全局单例）
engine = create_async_engine(DATABASE_URL, echo=False)

def get_session() -> Generator[Session, None, None]:
    """官方推荐的 Session 依赖注入方式"""
    with Session(engine) as session:
        try:
            yield session
            session.commit()  # commit 在 yield 后自动执行
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# 使用 Annotated 简化依赖注入
SessionDep = Annotated[Session, Depends(get_session)]
```

### 7.3 ORM 模型规范

ORM 模型:

继承 SQLModel 的 BaseModel。

必须显式定义 __tablename__。

推荐使用字段类型注解语法（如 `Field`, `Mapped`）。

### 7.4 Service 层事务管理

**采用依赖层统一管理事务（FastAPI 官方推荐方式）**：
- 依赖注入函数中自动 commit/rollback
- Service 层不需要关心 commit
- 优点：代码简洁，事务自动管理

```python
# 依赖层（推荐使用 async 版本）
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        try:
            yield session
            await session.commit()  # 自动提交
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Service 层（无需手动 commit）
async def create(self, session: AsyncSession, request: CreateRequest):
    entity = MyModel(...)
    session.add(entity)
    # 无需手动 commit，依赖层会自动处理
    return entity
```

### 7.5 数据库操作规范

所有业务逻辑和数据库交互都在 app/services 中实现。

必须使用 Async/Await 异步语法。

使用 SQLAlchemy 2.0 风格的构建器 (select, insert, update, delete)。

### 7.6 异步关系加载规范

在使用 SQLAlchemy 异步会话（AsyncSession）时，必须遵守以下规范：

#### 7.6.1 禁止懒加载

在异步上下文中，**严禁使用默认的懒加载（Lazy Loading）**。懒加载机制是同步的，会导致以下错误：

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here.
```

#### 7.6.2 必须使用预加载策略

当查询需要访问关联关系（如 `category.subject`、`user.profile`）时，必须使用显式预加载策略：

```python
from sqlalchemy.orm import selectinload, joinedload

# 方式一：selectinload（推荐）
# 发起单独的 SELECT 语句，在异步中更高效
stmt = select(ExamCategory).options(selectinload(ExamCategory.subject))

# 方式二：joinedload
# 使用 JOIN 一次性加载，适合一对一关系
stmt = select(User).options(joinedload(User.profile))
```

#### 7.6.3 预加载策略选择

| 策略 | 适用场景 | 说明 |
|------|---------|------|
| `selectinload()` | 一对多、多对多关系 | 单独 SELECT，性能好 |
| `joinedload()` | 一对一、一对少 | 使用 JOIN，一次查询 |
| `subqueryload()` | 复杂嵌套 | 使用子查询 |

#### 7.6.4 完整示例

```python
async def get_categories_with_subject(self, subject_id: int):
    """查询分类列表并预加载科目信息"""
    stmt = (
        select(ExamCategory)
        .options(selectinload(ExamCategory.subject))  # 必须预加载
        .where(ExamCategory.subject_id == subject_id)
    )
    result = await self.session.exec(stmt)
    categories = result.all()

    # 预加载后可以安全访问
    for c in categories:
        print(c.subject.name)  # 不会触发懒加载错误
```

#### 7.6.5 强制预加载检查

为防止遗漏预加载，可以在模型关系定义中使用 `lazy='raise'` 强制抛出异常：

```python
subject: Optional[Subject] = Relationship(
    back_populates="exam_categories",
    sa_relationship_kwargs={"lazy": "raise"}  # 访问未加载的关系会抛出异常
)
```

> 参考文档：https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html

## 8. 异常处理规范
- **HTTP 异常**: 业务逻辑错误必须抛出 `HTTPException`，指定准确的状态码 (400/401/403/404)。
- **全局处理**: 在 `main.py` 中注册 `exception_handler` 处理通用异常和验证错误 (`RequestValidationError`)。

## 9. 最佳实践
- **异步优先**: 所有 I/O 操作（DB、外部 API）必须是异步的。
- **配置管理**: 使用 `pydantic-settings` 管理环境变量和配置，禁止硬编码。
- **API 文档**: 利用 FastAPI 自动生成的 OpenAPI 文档，完善路由的 `summary` 和 `description`。

## 10. 日志规范

### 10.1 日志级别使用规范
| 级别 | 使用场景 |
|------|----------|
| **ERROR** | 程序错误，需要立即处理的问题（如数据库连接失败） |
| **WARNING** | 警告信息，不影响功能但需要关注（如参数校验失败） |
| **INFO** | 常规操作记录（请求入口、定时任务启动、业务关键流程） |
| **DEBUG** | 调试信息，开发环境使用，生产环境禁用 |

### 10.2 日志格式规范
日志输出必须包含时间戳、级别和消息，不使用 ANSI 颜色转义码：
```
2026-01-28 17:50:31 INFO: GET /api/subject 200 OK
2026-01-28 17:50:31 ERROR: Database connection failed
```

### 10.3 配置方式

#### 10.3.1 日志配置类

在 `app/config/settings.py` 中定义日志配置类：

```python
class LoggingConfig(BaseSettings):
    """日志配置"""
    log_dir: str = "logs"
    log_file: str = "app.log"
    log_level: str = "INFO"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5

    class Config:
        env_prefix = "LOGGING_"
```

在 `Settings` 聚合类中嵌套：
```python
class Settings(BaseSettings):
    """项目聚合配置"""
    database: DatabaseConfig = DatabaseConfig()
    jwt: JwtConfig = JwtConfig()
    upload: UploadConfig = UploadConfig()
    server: ServerConfig = ServerConfig()
    cors: CorsConfig = CorsConfig()
    logging: LoggingConfig = LoggingConfig()  # 新增日志配置
```

#### 10.3.2 全局日志配置

在 `main.py` 中配置全局日志，支持控制台和文件双输出：

```python
import os
import logging.handlers
from app.config.settings import settings

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": os.path.join(settings.logging.log_dir, settings.logging.log_file),
            "maxBytes": settings.logging.max_bytes,
            "backupCount": settings.logging.backup_count,
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": settings.logging.log_level,
    },
    "loggers": {
        "uvicorn": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "sqlalchemy.engine": {"handlers": ["console", "file"], "level": "WARNING", "propagate": False},
    },
}
```

#### 10.3.3 日志目录初始化

在应用启动时确保日志目录存在：

```python
def ensure_directories():
    """确保运行时需要的目录存在"""
    os.makedirs(settings.upload.upload_dir, exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs(settings.logging.log_dir, exist_ok=True)  # 创建日志目录
```

#### 10.3.4 Uvicorn配置

在 `uvicorn.run()` 中使用：
```python
import uvicorn
uvicorn.run("main:app", log_config=LOGGING_CONFIG)
```

#### 10.3.5 环境变量配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `LOGGING_LOG_DIR` | 日志目录 | `logs` |
| `LOGGING_LOG_FILE` | 日志文件名 | `app.log` |
| `LOGGING_LOG_LEVEL` | 日志级别 | `INFO` |
| `LOGGING_MAX_BYTES` | 单文件最大字节数 | `10485760` (10MB) |
| `LOGGING_BACKUP_COUNT` | 备份文件数量 | `5` |

### 10.4 服务层日志记录规范

所有 Service 层方法必须在入口和出口处记录日志，用于追踪查询的开始和结束。

**引入方式**：
```python
import logging

logger = logging.getLogger(__name__)
```

**查询类方法日志模式**：
```python
async def get_by_id(self, question_id: int) -> ExamResponse:
    logger.info("ExamService.get_by_id started, question_id: %d", question_id)
    # ... 查询逻辑 ...
    logger.info("ExamService.get_by_id completed, question_id: %d", question_id)
    return response
```

**增删改类方法日志模式**：
```python
async def create(self, request: CreateRequest) -> Response:
    logger.info("ExamService.create started, name: %s", request.name)
    # ... 业务逻辑 ...
    logger.info("ExamService.create completed, id: %d", entity.id)
    return response
```

**异常日志**：
```python
    if entity is None:
        logger.warning("ExamService.get_by_id: entity not found, id: %d", question_id)
        raise NotFoundException(...)
```

### 10.5 日志消息格式规范

| 方法类型 | 开始日志 | 结束日志 |
|---------|---------|---------|
| 查询类 | `{ServiceName}.{method_name} started, param: {value}` | `{ServiceName}.{method_name} completed, count: {n}` |
| 增删改类 | `{ServiceName}.{method_name} started, param: {value}` | `{ServiceName}.{method_name} completed, id: {n}` |
| 异常 | `{ServiceName}.{method_name}: {error_type}, param: {value}` | - |

**示例**：
```
2026-01-28 18:30:00 INFO: ExamService.get_paginated started, page: 1, page_size: 10
2026-01-28 18:30:00 INFO: ExamService.get_paginated completed, total: 50
2026-01-28 18:30:01 INFO: AuthService.login started with username: test
2026-01-28 18:30:01 WARNING: AuthService.login failed: user not found: test
```

### 10.6 安全规范
- **禁止**在日志中记录密码、Token、用户敏感信息
- **禁止**记录完整的用户请求体（可能包含敏感数据）
- 生产环境日志级别建议设置为 **WARNING** 或 **ERROR**

### 10.7 日志记录规范
使用 Python 标准库 `logging`，推荐用法：

```python
import logging

logger = logging.getLogger(__name__)

# 推荐：使用 logger 记录
logger.info("User %s logged in", username)
logger.error("Failed to create order: %s", str(e))

# 禁止：使用 print() 记录
# print("debug info")  # 错误！
```

## 12. 配置管理规范

### 12.1 配置架构
采用分层配置模型设计：

```
app/config/settings.py
├── DatabaseConfig     # 数据库配置 (DATABASE_*)
├── JwtConfig          # JWT配置 (JWT_*)
├── UploadConfig       # 上传配置 (UPLOAD_*)
├── ServerConfig       # 服务配置 (SERVER_*)
├── CorsConfig         # CORS配置 (CORS_*)
├── LoggingConfig      # 日志配置 (LOGGING_*)
└── Settings           # 聚合配置（统一入口）
```

### 12.2 配置文件结构
每个子配置类必须满足以下规范：

```python
from pydantic_settings import BaseSettings

class XxxConfig(BaseSettings):
    """配置说明"""
    field1: type = default_value

    class Config:
        env_prefix = "XXX_"  # 必须与配置类名对应
```

### 12.3 聚合配置类
项目必须定义聚合配置类 `Settings`，包含所有子配置类：

```python
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
```

### 12.4 配置访问规范
全局配置访问必须使用统一的嵌套访问方式：

```python
from app.config.settings import settings

# 正确：嵌套访问
DATABASE_URL = settings.database.database_url
JWT_SECRET = settings.jwt.secret
API_PREFIX = settings.server.api_prefix

# 禁止：直接访问子配置属性
# DATABASE_URL = settings.database_url  # 错误！
```

### 12.5 配置单例工厂
必须使用带缓存的工厂函数获取配置单例：

```python
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    """获取配置单例（带缓存）"""
    return Settings()

settings = get_settings()
```

### 12.6 环境变量命名规则
| 配置类 | 环境变量前缀 | 示例 |
|--------|-------------|------|
| DatabaseConfig | DATABASE_ | DATABASE_URL |
| JwtConfig | JWT_ | JWT_SECRET |
| UploadConfig | UPLOAD_ | UPLOAD_DIR |
| ServerConfig | SERVER_ | SERVER_HOST |
| CorsConfig | CORS_ | CORS_ORIGINS |
| LoggingConfig | LOGGING_ | LOGGING_LOG_LEVEL |

### 12.7 禁止事项
- 禁止在子配置类上直接调用 `get_settings()`
- 禁止在运行时修改配置类属性
- 禁止使用 `os.getenv()` 直接读取配置（应通过配置类）

## 12. 依赖文件
- fastapi[standard]
- uvicorn[standard]
- httpx
- pydantic
- pydantic-settings
- sqlmodel
- pyjwt[crypto]
- pwdlib
