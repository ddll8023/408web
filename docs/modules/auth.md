# 认证与账号

模块标识：`auth`。返回 [项目结构](../项目结构文档.md)。

## 职责与入口

负责注册、登录、请求身份解析与管理员校验，以及个人中心页面（账号信息、本地分类收藏、个人 AI 设置入口）。

入口：

- 后端 `backend-fastapi/src/web408/modules/auth/router.py` → `POST /api/auth/register`、`POST /api/auth/login`。
- 后端 `backend-fastapi/src/web408/modules/auth/dependencies.py`：`get_current_user`、`get_current_admin`、`get_optional_user`，被其余所有模块的路由复用。
- 前端 `frontend/src/views/user/Login.vue`、`Register.vue`、`UserCenter.vue`；路由守卫 `frontend/src/router/index.ts`。

不负责：分类、题目、图片、统计、AI 设置本身的业务——只提供身份，具体能力在各自模块。个人中心内嵌的收藏与 AI 设置分别在 `useFavorites` 与 [AI 题目咨询](ai.md) 中。

## 专属文件

| 文件 | 当前用途及纳入依据 |
| --- | --- |
| `backend-fastapi/src/web408/modules/auth/router.py` | 注册、登录两个 HTTP 用例 |
| `backend-fastapi/src/web408/modules/auth/service.py` | `AuthService.register`（查重 + Argon2 哈希）与 `login`（校验密码、启用状态、签发 JWT） |
| `backend-fastapi/src/web408/modules/auth/repository.py` | `UserRepository`：按 ID / 用户名查询、批量取用户名 |
| `backend-fastapi/src/web408/modules/auth/read_service.py` | `AuthReadService.get_user_names`，供 exam、adaptation 补作者名 |
| `backend-fastapi/src/web408/modules/auth/dependencies.py` | `AuthUser` 与三个依赖；角色与启用状态每次查库确认 |
| `backend-fastapi/src/web408/modules/auth/models.py` | `User`（`user` 表）：用户名、密码哈希、邮箱、角色、启用 |
| `backend-fastapi/src/web408/modules/auth/schemas.py` | 注册/登录请求与 `AuthResponse` |
| `frontend/src/api/auth.ts` | `register`、`login` 封装 |
| `frontend/src/stores/auth.ts` | `token` / `userInfo` 状态、`isLoggedIn()`、`isAdmin()`（要求 Token 与 `ADMIN` 同时成立） |
| `frontend/src/types/auth.ts` | `UserInfo`、登录/注册请求类型 |
| `frontend/src/views/user/Login.vue`、`Register.vue` | 表单页，路由 `meta.layout: 'blank'` |
| `frontend/src/views/user/UserCenter.vue` | 个人中心页：账号信息、收藏菜单、AI 设置菜单（混合职责，见[公共记录 ](shared.md#混合职责文件)） |

## 公共与跨模块引用

| 所属 | 文件与使用范围 | 本模块为何引用 |
| --- | --- | --- |
| [公共记录 ](shared.md) | `frontend/src/api/request.ts`（Bearer 注入、401 清 Token 并跳转）、`utils/token.ts`、`utils/storage.ts` | 登录态存 `localStorage`，所有请求自动带 Token |
| [公共记录 ](shared.md) | `frontend/src/components/basic/*`、`composables/useToast.ts` | 登录/注册/个人中心表单与提示 |
| `ai` 模块 | `frontend/src/components/business/AiSettings.vue` | 个人中心内嵌的个人模型服务设置 |
| `composables/useFavorites.ts` | 本地收藏分类的读写 | 个人中心收藏菜单 |

后端被引用的方向：`exam`、`adaptation` 通过 `AuthReadService` 取作者用户名；全部业务路由通过 `auth/dependencies.py` 取 `AuthUser`。

## 关键调用链

登录：

1. `Login.vue` 提交 → `api/auth.ts#login` → `POST /api/auth/login`。
2. `AuthService.login` 查用户、验 Argon2 密码、检查 `enabled`。
3. `core/security.py#create_access_token` 签发 `{sub: <user_id>}`，**不设过期时间**。
4. 前端 `stores/auth.ts` 写 `token` 与 `userInfo` 到 `localStorage`，后续请求由拦截器补 `Authorization`。
5. 每次需要身份的请求，`get_current_user` 重新解码 Token 并查库，确认用户存在且启用。

路由守卫：

1. `router.beforeEach` 读取 `to.meta.requiresAuth` / `requiresAdmin`。
2. 未登录跳 `/login?redirect=<fullPath>`；非管理员访问管理页弹提示并回 `/`。

## 状态与数据所有者

| 状态／资源 | 所有者 | 副本或消费者 | 生命周期／持久化 |
| --- | --- | --- | --- |
| 用户账户 | `auth/models.py` 的 `User`（`user` 表） | `user_id` 外键被三类题目、`exam_process_image`、`user_ai_*` 引用 | 数据库持久；删除被外键 `RESTRICT` 阻止 |
| JWT | `core/security.py` | 前端 `localStorage` 的 `web408_token` | 无过期；登出仅前端清除，服务端不维护黑名单 |
| 登录用户信息 | `frontend/src/stores/auth.ts` | 路由守卫、导航、管理入口 | `localStorage` 的 `userInfo`，解析失败视为未登录 |
| 本地收藏 | `composables/useFavorites.ts` | `UserCenter.vue` | 仅 `localStorage`，不落库、不跨设备 |

## 生命周期与约束

- 密码哈希为 `pwdlib` 推荐的 Argon2；`verify_password` 对未知哈希格式返回 `False` 而不是抛错。
- Token 只携带 `sub`，角色由数据库实时决定，管理员降权立即生效；但 Token 本身不会自动失效。
- `JWT_SECRET` 必须由环境提供且长度 ≥ 32，缺失时应用启动即失败（`core/config.py`）。
- `storage.ts#parseUserInfo` 把 `localStorage` 视为不可信外部输入，字段不合规就丢弃。

## 当前覆盖边界

注册/登录的错误分支与并发竞争（如同时注册同名用户）只确认了 `ConflictException` 与唯一约束的存在，未做运行时验证。
