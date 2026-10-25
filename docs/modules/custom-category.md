# 自定义分类

模块标识：`custom-category`。返回 [项目结构](../项目结构文档.md)。

## 职责与入口

维护与大纲分类**并行**的第二套分类树，按科目组织成多级结构；真题通过 `exam_question.custom_category` 以**名称数组**挂载节点，阅读端可只按某棵子树浏览。

入口：

- 后端 `backend-fastapi/src/web408/modules/custom_category/router.py`，前缀 `/api/custom-category`：
  `POST /subject/{subject_id}/tree`、`/stats`、`/available-parents`、`/rebuild-codes`、`POST /api/custom-category`、`/{id}`、`/{id}/move`、`/{id}/delete`。
- 前端：`frontend/src/views/admin/CustomCategoryManage.vue`（管理）、`frontend/src/views/user/CustomCategoryClassify.vue`（阅读）。

不负责：大纲分类（[目录与分类管理](catalog.md)）；题目本身的增删改（[真题](exam.md)）。本模块不写题目数据，改名时通过 `ExamCustomCategoryTagService` 让 exam 模块回写。

## 专属文件

| 文件 | 当前用途及纳入依据 |
| --- | --- |
| `backend-fastapi/src/web408/modules/custom_category/router.py` | HTTP 用例，写接口要求管理员 |
| `backend-fastapi/src/web408/modules/custom_category/command_service.py` | 创建/更新/移动/重建编码/删除；删除前查子分类与真题引用 |
| `backend-fastapi/src/web408/modules/custom_category/query_service.py` | 树构建、科目统计、父级候选、子孙 ID 与题目计数 |
| `backend-fastapi/src/web408/modules/custom_category/repository.py` | 持久化查询与结构写锁 |
| `backend-fastapi/src/web408/modules/custom_category/read_service.py` | `CustomCategoryReadService`：分类名称集合、按节点展开子树名称范围、题目挂载范围校验 |
| `backend-fastapi/src/web408/modules/custom_category/models.py` | `CustomCategory`（`custom_category` 表）：科目 + 父级 + 名称/编码/排序/启用 |
| `backend-fastapi/src/web408/modules/custom_category/schemas.py` | 请求/响应模型与移动目标校验 |
| `frontend/src/api/customCategory.ts` | 请求封装（树、统计、父级候选、CRUD、移动、编码重建） |
| `frontend/src/types/customCategory.ts` | 领域类型 |
| `frontend/src/views/admin/CustomCategoryManage.vue` | 管理页（结构与分类管理页对齐，复用拖拽 composable） |
| `frontend/src/views/user/CustomCategoryClassify.vue` | 阅读页（结构与真题分类页一致） |

## 公共与跨模块引用

| 所属 | 文件与使用范围 | 本模块为何引用 |
| --- | --- | --- |
| [公共记录](shared.md) | `catalog/category_code.py`（编码算法）、`question_content.serialization.parse_categories` | 生成层级编码；统计题目挂载 |
| `catalog` 模块 | `modules/catalog/models.py` 的 `Subject` | 分类必须挂在科目下 |
| `exam` 模块 | `modules/exam/read_service.py#count_custom_category_references`、`modules/exam/custom_category_tag_service.py` | 删除保护；改名回写真题标签 |

被引用方向：`exam`（筛选与挂载校验）通过 `CustomCategoryReadService` 取子树名称范围；前端 `ExamEditDialog.vue` 与 `CustomCategoryClassify.vue` 调用本模块接口。

## 关键调用链

删除分类（保护）：

1. `CustomCategoryManage.vue` → `POST /api/custom-category/{id}/delete`。
2. `CustomCategoryCommandService.delete`：加结构写锁 → 查子分类数 → 查真题引用数（`ExamReadService.count_custom_category_references`）。
3. 任一非 0 直接抛 `ConflictException` 并带引用数；通过后删除。

改名同步：

1. 管理页提交 → `POST /api/custom-category/{id}`。
2. 命令服务校验科目内名称/编码唯一、父级合法，重算子树编码。
3. 名称变化时调用 `ExamCustomCategoryTagService.rename_category`，把真题 `custom_category` JSON 中的旧名替换为新名。
4. 同一会话提交。

按子树浏览：

1. `CustomCategoryClassify.vue` → `GET` 侧为 `POST /api/custom-category/subject/{subject_id}/tree` 取树，题目侧调用 `POST /api/exam/query` 并带 `subjectId` + `customCategory` 名称。
2. 后端 `ExamQueryService` 在科目已知时把所选节点展开为启用子树的名称集合，再下推为名称条件（必须带 `subject_id`，否则不同科目同名分类会互相命中）。

## 状态与数据所有者

| 状态／资源 | 所有者 | 副本或消费者 | 生命周期／持久化 |
| --- | --- | --- | --- |
| 自定义分类树 | `custom_category` 表 | 真题 `custom_category` 文本列 | 数据库持久；科目删除级联 |
| 真题挂载关系 | `exam_question.custom_category`（名称数组） | 阅读端筛选、统计 | **无外键**，靠名称匹配；不同步会留下悬空名称 |

## 生命周期与约束

- 标签是名称而非 ID，所以删除分类前必须先摘掉题目标签，接口直接拒绝而不是静默清理。
- 名称唯一性只在科目内成立。
- 结构写操作与大纲分类一致：先取写锁再改，冲突时提示重试。

## 当前覆盖边界

运行期行为（含并发改名）未验证；`/stats` 的题目计数来自对真题文本的解析，口径细节以 `query_service.py` 为准。
