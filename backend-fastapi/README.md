# backend-fastapi

408 考研真题知识点阅读网站的 FastAPI 后端。

## 项目入口

- 应用入口：`app/main.py`
- API 前缀：`/api`
- Swagger：`http://localhost:7785/docs`
- ReDoc：`http://localhost:7785/redoc`

后端按业务模块纵向组织在 `app/modules/` 下；各模块内部包含 Router、Schema、Query/Command Service、Repository 和 Model。`app/api/` 仅负责通用请求依赖和路由聚合，配置、异常、日志和安全基础设施位于 `app/core/`；写用例由模块内 Command Service 显式提交事务。

## 环境与启动

要求 Python 3.12 或更高版本，并使用 uv 管理依赖：

```bash
uv sync
cp .env.example .env
```

在 `.env` 中设置至少 32 个字符的 `JWT_SECRET`，然后启动开发服务：

```bash
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 7785 --reload
```

应用启动时通过当前 SQLModel 定义补齐缺失表，并在 `data/`、`uploads/images/` 和 `logs/` 下创建运行时目录；不会删除未映射的历史表。当前项目保留数据库历史 `schema_migrations` 记录，但不维护通用迁移脚本；修改现有数据库前须按项目规则确认影响范围。

## 运行时配置

配置项见 `.env.example`，主要包括：

- `DATABASE_URL`：默认 `sqlite+aiosqlite:///./data/web408.db`
- `SERVER_HOST`、`SERVER_PORT`、`API_PREFIX`
- `CORS_ORIGINS`
- `UPLOAD_DIR`、`MAX_FILE_SIZE`
- `JWT_SECRET`、`JWT_ALGORITHM`

图片通过 `/uploads/images` 静态路径访问；日志和数据库文件属于本地运行时产物，不提交到版本库。
