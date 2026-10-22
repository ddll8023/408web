# 目录与分类管理

模块标识：`catalog`。返回 [项目结构](../项目结构文档.md)。

## 职责与入口

管理阅读与出题的三级基础目录：**科目 → 章节 → 大纲分类（分类标签）**，并向后端其他模块公开只读边界。含分类层级编码生成、拖拽/移动子树、改名回写题目标签、删除前的引用保护、题目计数与「未归档标签」提示。

入口：

- 后端 `backend-fastapi/src/web408/modules/catalog/router.py` 聚合三组子路由（前缀见 `api/router.py`）：
  - 科目：`POST /api/subject/query`、`/query-all`、`/{id}/detail`、`/query-by-code`、`POST /api/subject`、`/{id}`（改）、`/{id}/delete`
  - 章节：`POST /api/chapter/subject/{subject_id}`、`/subject/{subject_id}/all`、`/{id}/detail`、`POST /api/chapter`、`/{id}`、`/{id}/delete`
  - 分类：`POST /api/exam-category/query`、`/subject/{id}/query`、`/subject/{id}/enabled`、`/subject/{id}/tree`、`/subject/{id}/tree/enabled`、`/subject/{id}/tree/enabled-with-stats`、`/available-parents`、`/rebuild-codes`、`/stats`、`/{id}/usage`、`/{id}/detail`、`POST /api/exam-category`、`/{id}`、`/{id}/move`、`/{id}/delete`
- 前端：`frontend/src/views/admin/SubjectManage.vue`（科目 CRUD）、`CategoryManage.vue`（分类树 CRUD、拖拽、未归档模拟题标签）。

不负责：自定义分类树（[自定义分类](custom-category.md)）虽然复用同一编码算法，但归独立模块；题目的分类标签值由各题目模块写入，本模块只在改名时调用它们的 `*_category_tag_service`。

## 专属文件

| 文件 | 当前用途及纳入依据 |
| --- | --- |
| `backend-fastapi/src/web408/modules/catalog/router.py` | 子路由聚合 |
| `backend-fastapi/src/web408/modules/catalog/routers/subject.py` | 科目 HTTP 用例（写接口要求管理员） |
| `backend-fastapi/src/web408/modules/catalog/routers/chapter.py` | 章节 HTTP 用例（查询开箱即用，写接口要求管理员） |
| `backend-fastapi/src/web408/modules/catalog/routers/category.py` | 分类 HTTP 用例（读接口公开，写接口与 usage/stats 视需要鉴权） |
| `backend-fastapi/src/web408/modules/catalog/subject_service.py` / `subject_repository.py` | 科目 CRUD、启用过滤、删除前真题计数提示 |
| `backend-fastapi/src/web408/modules/catalog/chapter_service.py` / `chapter_repository.py` | 章节树构建、CRUD |
| `backend-fastapi/src/web408/modules/catalog/category_query_service.py` | 分类列表/树/启用树/带统计树的组装、父分类候选、使用量、子孙 ID 展开 |
| `backend-fastapi/src/web408/modules/catalog/category_command_service.py` | 分类增删改移、子树编码重建、改名回写三类题目、删除前三类题目引用检查 |
| `backend-fastapi/src/web408/modules/catalog/category_repository.py` | 分类持久化查询与名称冲突计数 |
| `backend-fastapi/src/web408/modules/catalog/category_code.py` | 分类层级编码生成（拼音首字母 + 层级序号），大纲分类与自定义分类共用 |
| `backend-fastapi/src/web408/modules/catalog/question_scope_repository.py` | 题目归属校验用的科目存在性与分类名称集合 |
| `backend-fastapi/src/web408/modules/catalog/read_service.py` | `CatalogReadService`：对外公开的科目/分类只读数据与分类范围校验 |
| `backend-fastapi/src/web408/modules/catalog/models.py` | `Subject`、`Chapter`、`ExamCategory` 三张表 |
| `backend-fastapi/src/web408/modules/catalog/schemas/{subject,chapter,category}.py` | 请求/响应模型 |
| `frontend/src/api/subject.ts`、`api/category.ts` | 科目与分类请求封装 |
| `frontend/src/types/subject.ts`、`types/category.ts` | 领域类型 |
| `frontend/src/views/admin/SubjectManage.vue` | 科目管理页 |
| `frontend/src/views/admin/CategoryManage.vue` | 分类标签管理页：树形大纲、拖拽排序/改父级、编码重建、未归档模拟题标签展示 |
| `frontend/src/components/business/CategorySubjectFilter.vue` | 分类管理页的科目筛选（桌面侧栏 + 窄屏抽屉共用） |
| `frontend/src/components/business/CategoryTreeItem.vue` | 递归分类节点（阅读端科目侧栏用） |
| `frontend/src/composables/useCategoryDrag.ts` | 分类拖拽移动（分类管理与自定义分类管理共用） |

## 公共与跨模块引用

| 所属 | 文件与使用范围 | 本模块为何引用 |
| --- | --- | --- |
| [公共记录](shared.md) | `question_content.serialization.parse_categories`、`category_code` | 统计题目分类引用、生成编码 |
| `exam` 模块 | `modules/exam/read_service.py`（`list_question_categories`、`count_question_references`、`count_questions_with_categories`）、`modules/exam/category_tag_service.py` | 分类统计与题目计数、改名回写 |
| `mock` 模块 | `modules/mock/read_service.py`、`category_tag_service.py` | 同上；未归档标签也来自模拟题 |
| `adaptation` 模块 | `modules/adaptation/read_service.py`、`category_tag_service.py` | 同上 |
| `question_content` | `parse_categories` | 解析题目分类 JSON |

被引用方向：`exam`、`mock`、`adaptation`、`reporting`、`ai` 通过 `CatalogReadService` / `catalog.models` 取科目与分类；前端 `views/admin/QuestionCompose.vue` 用分类接口当章节树，`views/user/*Classify.vue` 用分类树做阅读侧栏。

## 关键调用链

分类改名（跨模块写）：

1. `CategoryManage.vue` 提交编辑 → `POST /api/exam-category/{id}`。
2. `CategoryCommandService.update`：先 `_lock_structure()` 串行化结构变更，再校验科目不可改、父级不能是自身或子孙、同科目内名称唯一。
3. 名称或父级变化时 `_rebuild_subtree_codes` 重建整棵子树编码（编码含层级路径与名称首字母）。
4. 名称变化时依次调用 exam / mock / adaptation 的 `rename_category`，在同一会话内改写题目分类 JSON。
5. `session.commit()` 后返回更新后的分类。

分类删除保护：

1. `CategoryManage.vue` 删除 → `POST /api/exam-category/{id}/delete`。
2. `CategoryCommandService.delete` 先查子分类数量，再分别查三类题目的引用数，任一不为 0 就抛 `ConflictException` 并带出引用数。
3. 通过后 `session.delete` + `commit`；分类名称作为题目文本标签，数据库不会级联清理。

阅读端取分类树：

1. `ExamClassify.vue` 等页面 mount → `api/category.ts#getEnabledCategoryTreeBySubject`（或带统计版本）。
2. `CategoryQueryService.get_category_tree` 取启用节点并构树，带统计时再叠加题目计数。
3. 页面用 `utils/examCategoryGrouping.ts` 把题目与树对齐。

## 状态与数据所有者

| 状态／资源 | 所有者 | 副本或消费者 | 生命周期／持久化 |
| --- | --- | --- | --- |
| 科目 / 章节 / 分类 | `catalog/models.py`（`subject`、`chapter`、`exam_category`） | 三类题目 `subject_id` 外键；分类名称被题目 JSON 引用 | 数据库持久；删除科目 `cascade_delete` 章节与分类，题目 `subject_id` 置空 |
| 分类编码 | `category_command_service` 写入 `ExamCategory.code` | 管理页展示 | 父级或名称变化时整棵子树重算，不是用户手填的稳定 ID |
| 「未归档」模拟题标签 | 由 `CategoryManage.vue` 用 `getMockCategoryStatsBySubject` 与分类树比对派生 | 仅管理页展示 | 不落库；只是提示，不会自动建分类 |

## 生命周期与约束

- 分类结构变更先 `_lock_structure()`（执行 `UPDATE exam_category SET order_num = order_num WHERE 0` 取得写锁，锁冲突转为 `ConflictException` "分类正在被修改，请刷新后重试"），避免并发移动/改名交错；跨表改名与移动在同一会话内一起提交。
- 名称是题目标签的持久标识：改名必须回写，移动父级不改变标签；因此同名限制只在科目内生效。
- 删除科目是级联删除章节与分类；对题目只是把 `subject_id` 置 `NULL`，不删题。

## 当前覆盖边界

- 章节能力在后端完整（`/api/chapter/*`），但前端当前**没有任何 `/api/chapter` 调用**：分类管理页只维护分类；出题工作台的「章节树」实际渲染大纲分类树。若需要真正的章节管理界面，是新增能力而非修复。
- 分类 `usage` / `stats` 接口的鉴权细节按需在 `routers/category.py` 中确认，本页未逐条列出。
