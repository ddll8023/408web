# backend-fastapi

408 考研真题知识点阅读网站的 FastAPI 后端。

## 项目入口

- 源码入口：`src/web408/main.py`
- ASGI 入口：`web408.main:app`（先执行 `uv sync --locked` 安装项目）
- API 前缀：`/api`
- Swagger：`http://localhost:7785/docs`
- ReDoc：`http://localhost:7785/redoc`

后端按业务模块纵向组织在 `src/web408/modules/` 下；各模块内部包含 Router、Schema、Query/Command Service、Repository 和 Model。`src/web408/api/` 仅负责通用请求依赖和路由聚合，配置、异常、日志和安全基础设施位于 `src/web408/core/`；写用例由模块内 Command Service 显式提交事务。

项目使用 `uv_build` 打包，显式声明 `src` 下的 `web408` 隐式命名空间包，不创建 `__init__.py`，也不保留旧 `app` 包别名。`uv sync` 默认以可编辑方式安装项目，无需设置 `PYTHONPATH`。

## 环境与启动

要求 Python 3.12 或更高版本，并使用 uv 管理依赖。以下命令必须在 `backend-fastapi/` 目录执行：

```bash
uv sync --locked
# 仅在没有 .env 时创建，已有配置不要覆盖
# macOS/Linux:
cp -n .env.example .env
# Windows PowerShell:
# if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

在 `.env` 中设置至少 32 个字符的 `JWT_SECRET`，然后启动开发服务：

```bash
uv run --locked python -m uvicorn web408.main:app --host 0.0.0.0 --port 7785 --reload --reload-dir src/web408
```

从仓库根目录运行时，使用 `uv run --directory backend-fastapi --locked python -m uvicorn web408.main:app --host 0.0.0.0 --port 7785 --reload --reload-dir src/web408`，或使用根目录的 `startup-backend.command`（macOS）/ `startup-backend.bat`（Windows）。两种脚本都会切换到后端工作目录，且要求项目已安装。

`.env` 与数据库、上传、日志均相对后端工作目录解析，不依赖源码在虚拟环境中的安装位置。不要切换到 `src/` 启动服务。

应用启动时仅通过当前 SQLModel 定义补齐缺失表，并在 `data/`、`uploads/images/` 和 `logs/` 下创建运行时目录；不负责删除或清理数据库中的其他表。当前项目保留数据库历史 `schema_migrations` 记录，但不维护通用迁移脚本；数据库表结构、字段和约束见 [`../doc/数据库设计.md`](../doc/数据库设计.md)。修改现有数据库前须按项目规则确认影响范围。

## 运行时配置

配置项见 `.env.example`，主要包括：

- `DATABASE_URL`：默认 `sqlite+aiosqlite:///./data/web408.db`
- `SERVER_HOST`、`SERVER_PORT`、`API_PREFIX`
- `CORS_ORIGINS`
- `UPLOAD_DIR`、`MAX_FILE_SIZE`
- `JWT_SECRET`、`JWT_ALGORITHM`

图片通过 `/uploads/images` 静态路径访问；日志和数据库文件属于本地运行时产物，不提交到版本库。
