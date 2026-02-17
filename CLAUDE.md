# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

408考研真题知识点阅读网站 - 一个专为408计算机考研设计的真题与模拟题在线学习平台，采用前后端分离架构。

## 技术栈

- **前端**: Vue 3 + Vite + Pinia + Vue Router + Element Plus
- **后端**: FastAPI + SQLModel + AioSQLite
- **认证**: JWT (python-jose)
- **Markdown**: @kangc/v-md-editor + KaTeX (数学公式)
- **样式**: Tailwind CSS 4 + Sass

## 常用命令

### 前端

```bash
cd frontend
npm install          # 安装依赖
npm run dev         # 启动开发服务器 (端口 5174)
npm run build       # 构建生产版本
npm run preview    # 预览生产版本
```

### 后端

```bash
cd backend-fastapi
pip install -r requirements.txt  # 安装Python依赖
python -m uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
```

后端默认运行在 `http://localhost:8081`，API前缀为 `/api`。

## 项目架构

### 前端结构 (`frontend/src/`)

- `api/` - Axios API 接口封装
- `components/basic/` - 基础通用组件
- `components/business/` - 业务组件（分类树、题目卡片、导航等）
- `views/user/` - 用户页面
- `views/admin/` - 管理后台页面
- `stores/` - Pinia 状态管理
- `router/` - Vue Router 配置
- `composables/` - Vue 组合式函数

### 后端结构 (`backend-fastapi/app/`)

- `config/` - 配置管理 (settings.py)
- `database/` - 数据库连接和初始化
- `models/` - SQLModel 数据模型
- `schemas/` - Pydantic 请求/响应模型
- `api/v1/` - API 路由端点
- `services/` - 业务逻辑层
- `middleware/` - 中间件 (CORS, JWT认证)
- `utils/` - 工具函数

### 数据库

SQLite 数据库位于 `data/web408.db`，主要表包括：
- `user` - 用户表
- `subject` - 科目表（数据结构、操作系统、计算机网络、计算机组成原理）
- `chapter` - 章节表（树形结构）
- `exam_category` - 分类标签表
- `exam_question` - 真题表
- `mock_question` - 模拟题表
- `resource_file` - 资源文件表

### 配置文件

- 前端: `frontend/vite.config.js` (路径别名 `@` -> `./src`, API代理 `/api` -> `http://localhost:8081`)
- 后端: `backend-fastapi/.env` 和 `backend-fastapi/app/config/settings.py`
- Tailwind: `frontend/tailwind.config.js`

## API 路由前缀

所有 API 请求需要加上 `/api` 前缀，例如 `/api/auth/login`、`api/subject`、`api/chapter`、`api/exam`、`api/mock`。

## 开发规范

在执行任何前后端任务时，必须遵守以下规范文档：

### 前端规范
- `规范文档/前端组件规范.md` - Vue 组件开发规范
- `规范文档/前端页面规范.md` - 页面设计规范
- `规范文档/Tailwind迁移进度.md` - Tailwind CSS 迁移规范

### 后端规范
- `规范文档/fastapi后端规范文档.md` - FastAPI 后端开发规范
- `规范文档/API接口文档.md` - API 接口设计规范

## 注意事项

- 前端开发服务器代理 `/api` 请求到后端 `http://localhost:8081`
- CORS 配置允许 `http://localhost:5173` 和 `http://localhost:5174`
- 文件上传存储在 `backend-fastapi/uploads/images/`
- 日志存储在 `backend-fastapi/logs/`
