# 408考研真题知识点阅读网站

一个专为408计算机考研设计的真题与模拟题在线学习平台，支持按科目和分类浏览、Markdown 文档渲染、即时作答反馈和资料导出。

## 项目简介

本项目是一个全栈Web应用，旨在帮助408计算机考研学子高效学习和复习。平台提供：

- **真题资源**：收录历年考研真题，支持按年份、科目和分类浏览
- **模拟题练习**：提供按来源、科目和分类浏览的模拟题及即时作答反馈
- **知识点管理**：支持树形章节结构，方便知识点梳理
- **Markdown支持**：题目和答案支持完整的Markdown渲染，包含LaTeX数学公式
- **用户系统**：提供注册登录、个人中心和浏览器本地分类收藏

## 技术栈

### 前端
- **Vue 3 + TypeScript 5.9** - Composition API 与严格类型检查
- **Vite 7** - 现代化构建工具
- **Pinia** - 状态管理
- **Vue Router 4** - 路由管理
- **项目自定义基础组件** - 按钮、表单、弹窗、提示和数据展示组件
- **Axios** - HTTP客户端
- **@kangc/v-md-editor** - Markdown编辑器
- **KaTeX** - 数学公式渲染
- **html-to-image** - 将题目内容生成 PNG，支持图片复制和下载
- **Tailwind CSS 4** - 样式工具

### 后端
- **FastAPI** - 现代化Python异步Web框架
- **SQLModel** - SQLAlchemy + Pydantic组合
- **AioSQLite** - 异步SQLite数据库
- **JWT** - JSON Web Token认证
- **Python-Jose** - JWT加密/解密
- **pwdlib[argon2]** - 密码哈希

## 项目结构

```
408web/
├── frontend/                 # Vue 3前端项目
│   ├── src/
│   │   ├── api/             # API接口封装
│   │   ├── components/      # 组件
│   │   │   ├── basic/       # 基础组件
│   │   │   └── business/    # 业务组件
│   │   ├── views/           # 页面视图
│   │   │   ├── user/        # 用户相关页面
│   │   │   └── admin/       # 管理页面
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia状态管理
│   │   ├── composables/     # 组合式函数
│   │   ├── types/           # API 与业务公共类型
│   │   ├── utils/           # 数据转换与输入校验
│   │   └── styles/          # 样式文件
│   ├── tests/              # Node 内置测试器回归测试
│   ├── tsconfig.app.json    # 应用严格 TS 检查
│   ├── tsconfig.node.json   # Vite 配置类型检查
│   ├── vite.config.ts       # Vite 配置
│   └── package.json
│
├── backend-fastapi/          # FastAPI后端项目
│   ├── app/
│   │   ├── api/             # HTTP 路由与请求依赖
│   │   ├── core/            # 配置、异常、日志与安全
│   │   ├── database/        # 数据库连接
│   │   ├── repositories/    # 复杂查询与持久化边界
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic模式定义
│   │   ├── services/        # 业务逻辑层
│   │   └── middleware/      # 中间件
│   ├── pyproject.toml       # 依赖与项目元数据
│   └── uv.lock              # 依赖锁定结果
│
├── doc/                      # 项目结构与模块设计文档
│   ├── 项目结构文档.md
│   ├── 模块说明文档.md
│   └── 模块/                  # 各业务模块开发设计
│
├── backend-fastapi/data/     # SQLite数据库目录（运行时）
├── backend-fastapi/uploads/  # 上传文件目录（运行时）
├── backend-fastapi/logs/     # 后端日志目录（运行时）
└── 规范文档/                 # 项目开发规范文档
```

## 功能模块

### 用户功能
- 用户注册与登录
- 个人中心
- 收藏管理

### 真题模块
- 历年真题浏览（按年份）
- 按科目/分类筛选
- Markdown格式题目和答案展示
- 数学公式支持（LaTeX）

### 模拟题模块
- 模拟题列表
- 按机构分类
- 选择题作答反馈

### 管理功能（管理员）
- 科目管理
- 章节管理
- 分类标签管理
- 题目管理（真题/模拟题）
- 图片资源管理
- 数据统计

## 快速开始

### 环境要求

- Node.js 20.19+（20.x）或 >= 22.12（与 Vite 7 engines 一致）
- Python >= 3.12
- Git

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/408web.git
cd 408web
```

### 2. 后端部署

```bash
cd backend-fastapi

# 按锁文件创建环境并同步依赖
uv sync

# 创建本地环境配置（必须设置 JWT_SECRET）
cp .env.example .env

# 启动服务
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 7785 --reload
```

后端服务将在 `http://localhost:7785` 启动

### 3. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:7784` 启动

### 前端验证与构建

在 `frontend/` 目录执行：

```bash
# 应用 SFC/TS 与 Vite 配置类型检查
npm run type-check

# API、业务数据和基础组件回归测试
npm test

# 类型检查后生成 dist/
npm run build
```

应用源码使用 TypeScript，Vue 脚本使用 `lang="ts"`；`strict: true`、`allowJs: false`。PostCSS/Tailwind 使用独立的 JavaScript 工具配置，Node 测试脚本使用 `.mjs`；自动化测试使用模拟网络和自定义组件 renderer，不等同于真实浏览器全流程验证。

前端规范、项目结构和模块边界分别见 [`规范文档/前端规范文档.md`](./规范文档/前端规范文档.md)、[`doc/项目结构文档.md`](./doc/项目结构文档.md) 与 [`doc/模块/`](./doc/模块/)。

### 4. 访问应用

打开浏览器访问 `http://localhost:7784`

## 主要 API 示例

### 认证模块
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |

### 科目模块
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/subject/query` | POST | 获取启用科目 |
| `/api/subject/{id}/detail` | POST | 获取单个科目 |

### 章节模块
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chapter/subject/{id}` | POST | 获取章节树 |
| `/api/chapter` | POST | 创建章节 |
| `/api/chapter/{id}` | POST | 更新章节 |
| `/api/chapter/{id}/delete` | POST | 删除章节 |

### 真题模块
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/exam/query` | POST | 获取真题列表 |
| `/api/exam` | POST | 创建真题 |
| `/api/exam/{id}/detail` | POST | 获取真题详情 |

### 模拟题模块
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/mock/query` | POST | 获取模拟题列表 |
| `/api/mock` | POST | 创建模拟题 |
| `/api/mock/{id}/detail` | POST | 获取模拟题详情 |

以上为常用接口示例，不是完整路由清单。各模块的 API 目标契约和当前实现边界见 [`doc/模块/`](./doc/模块/)；完整路由与响应模型以 `backend-fastapi/app/api/` 和 `backend-fastapi/app/schemas/` 为准，运行中的接口还可通过后端 `/docs` 查看。

## 配置说明

### 后端配置

在 `backend-fastapi/.env`（或环境变量）中配置：

```env
# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./data/web408.db

# JWT配置
JWT_SECRET=replace-with-a-random-secret-at-least-32-characters
JWT_ALGORITHM=HS256

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=7785
API_PREFIX=/api

# CORS配置
CORS_ORIGINS=http://localhost:7784
```

### 环境变量

可在 `.env` 文件中配置：

```env
JWT_SECRET=replace-with-a-random-secret-at-least-32-characters
JWT_ALGORITHM=HS256
```

## 数据库

项目使用 SQLite 数据库；从 `backend-fastapi/` 启动时，数据库文件位于 `backend-fastapi/data/web408.db`。

主要数据表：
- `user` - 用户表
- `subject` - 科目表（数据结构、操作系统、计算机网络、计算机组成原理）
- `chapter` - 章节表
- `exam_category` - 分类标签表
- `exam_question` - 真题表
- `mock_question` - 模拟题表
- `resource_file` - 资源文件表

## 开发规范

本项目遵循以下开发规范：

- [前端规范文档](./规范文档/前端规范文档.md)
- [后端规范文档](./规范文档/后端规范文档.md)
- [模块开发设计文档](./doc/模块/)

## License

本项目仅供学习交流使用。

## 贡献

欢迎提交 Issue 和 Pull Request！
