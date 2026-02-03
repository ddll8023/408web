# 408考研真题知识点阅读网站

一个专为408计算机考研设计的真题与模拟题在线学习平台，支持知识点分类、Markdown文档渲染、随机出题练习等功能。

## 项目简介

本项目是一个全栈Web应用，旨在帮助408计算机考研学子高效学习和复习。平台提供：

- **真题资源**：收录历年考研真题，支持按年份、科目、章节分类浏览
- **模拟题练习**：提供模拟题目练习，包含来源机构标注
- **知识点管理**：支持树形章节结构，方便知识点梳理
- **Markdown支持**：题目和答案支持完整的Markdown渲染，包含LaTeX数学公式
- **用户系统**：注册登录功能，记录学习进度

## 技术栈

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **Vite 6** - 现代化构建工具
- **Pinia** - 状态管理
- **Vue Router 4** - 路由管理
- **Element Plus** - Vue 3 UI组件库
- **Axios** - HTTP客户端
- **@kangc/v-md-editor** - Markdown编辑器
- **KaTeX** - 数学公式渲染
- **Sass** - CSS预处理器

### 后端
- **FastAPI** - 现代化Python异步Web框架
- **SQLModel** - SQLAlchemy + Pydantic组合
- **AioSQLite** - 异步SQLite数据库
- **JWT** - JSON Web Token认证
- **Python-Jose** - JWT加密/解密
- **Passlib** - 密码加密

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
│   │   └── styles/          # 样式文件
│   └── package.json
│
├── backend-fastapi/          # FastAPI后端项目
│   ├── app/
│   │   ├── config/          # 配置文件
│   │   ├── database/        # 数据库连接
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic模式定义
│   │   ├── api/v1/          # API路由
│   │   ├── services/        # 业务逻辑层
│   │   ├── middleware/      # 中间件
│   │   └── utils/           # 工具函数
│   └── requirements.txt
│
├── backend/                  # Spring Boot后端（备用）
├── data/                    # 数据库文件目录
├── uploads/                 # 上传文件目录
├── logs/                    # 日志目录
└── 规范文档/                 # 项目开发规范文档
```

## 功能模块

### 用户功能
- 用户注册与登录
- 个人中心
- 收藏管理

### 真题模块
- 历年真题浏览（按年份）
- 按科目/章节筛选
- Markdown格式题目和答案展示
- 数学公式支持（LaTeX）

### 模拟题模块
- 模拟题列表
- 按机构分类
- 出题练习

### 管理功能（管理员）
- 科目管理
- 章节管理
- 分类标签管理
- 题目管理（真题/模拟题）
- 图片资源管理
- 数据统计

## 快速开始

### 环境要求

- Node.js >= 16
- Python >= 3.8
- Git

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/408web.git
cd 408web
```

### 2. 后端部署

```bash
cd backend-fastapi

# 创建虚拟环境（可选）
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
```

后端服务将在 `http://localhost:8081` 启动

### 3. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

### 4. 访问应用

打开浏览器访问 `http://localhost:5173`

## API文档

### 认证模块
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |

### 科目模块
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/subject` | GET | 获取所有科目 |
| `/api/subject/{id}` | GET | 获取单个科目 |

### 章节模块
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chapter` | GET | 获取章节树 |
| `/api/chapter` | POST | 创建章节 |
| `/api/chapter/{id}` | PUT | 更新章节 |
| `/api/chapter/{id}` | DELETE | 删除章节 |

### 真题模块
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/exam` | GET | 获取真题列表 |
| `/api/exam` | POST | 创建真题 |
| `/api/exam/{id}` | GET | 获取真题详情 |

### 模拟题模块
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/mock` | GET | 获取模拟题列表 |
| `/api/mock` | POST | 创建模拟题 |
| `/api/mock/{id}` | GET | 获取模拟题详情 |

详细API文档请参考 `规范文档/API接口文档.md`

## 配置说明

### 后端配置

在 `backend-fastapi/app/config/settings.py` 中配置：

```python
# 数据库配置
DATABASE_URL = "sqlite+aiosqlite:///./data/web408.db"

# JWT配置
JWT_SECRET = "your-secret-key"  # 建议使用环境变量
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 服务器配置
HOST = "0.0.0.0"
PORT = 8081

# CORS配置
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174"
]
```

### 环境变量

可在 `.env` 文件中配置：

```env
JWT_SECRET=your-super-secret-key
```

## 数据库

项目使用 SQLite 数据库，数据库文件位于 `data/web408.db`。

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

- [前端组件规范](./规范文档/前端组件规范.md)
- [前端页面规范](./规范文档/前端页面规范.md)
- [后端规范文档](./规范文档/后端规范文档.md)
- [API接口文档](./规范文档/API接口文档.md)

## License

本项目仅供学习交流使用。

## 贡献

欢迎提交 Issue 和 Pull Request！
