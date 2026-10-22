# 真题

模块标识：`exam`。返回 [项目结构](../项目结构文档.md)。

## 职责与入口

真题的浏览、检索、维护与讲解过程图片：按年份、科目、分类（大纲/自定义）筛选，统计年份与分类分布，查重，增删改，以及过程图片的上传、排序与解绑。

入口（前缀 `/api/exam`，见 `backend-fastapi/src/web408/modules/exam/router.py`）：

- 读：`POST /query`（分页查询）、`/year/{year}`、`/categories/{subject_id}`、`/year-stats`、`/index`、`/nav-index`、`/by-category`、`/{exam_id}/detail`、`/{exam_id}/process-images`
- 写（管理员）：`POST /api/exam`、`/{exam_id}`（改）、`/{exam_id}/delete`、`/check-duplicate`、`/{exam_id}/process-images/upload`、`/{exam_id}/process-images/{image_id}/delete`、`/{exam_id}/process-images/reorder`
- 前端页面：`views/user/ExamIndex.vue`（年份入口）、`ExamList.vue`（按年份阅读）、`ExamClassify.vue`（按分类阅读）；`views/admin/ExamManage.vue`（管理表格）。

不负责：分类树本身（[目录与分类管理](catalog.md)、[自定义分类](custom-category.md)）、分类统计与导出（[统计与导出](reporting.md)）、图片物理文件的落盘与清理（[图片资源](media.md)）、改编题（[真题改编题](adaptation.md)）。

## 专属文件

| 文件 | 当前用途及纳入依据 |
| --- | --- |
| `backend-fastapi/src/web408/modules/exam/router.py` | 全部真题与过程图片 HTTP 用例 |
| `backend-fastapi/src/web408/modules/exam/query_service.py` | 分页查询、详情、年份统计、分类统计取数、图片引用文本、按科目/分类检索 |
| `backend-fastapi/src/web408/modules/exam/command_service.py` | 创建/更新/删除；调用 `question_content` 校验与序列化，写前核对科目与分类范围 |
| `backend-fastapi/src/web408/modules/exam/repository.py` | `ExamQuery` 条件拼装与分页 SQL，含分类名称 LIKE 条件与排序 |
| `backend-fastapi/src/web408/modules/exam/mapper.py` | 实体 → `ExamResponse`（解 JSON 选项与分类） |
| `backend-fastapi/src/web408/modules/exam/models.py` | `ExamQuestion`（`exam_question`）、`ExamProcessImage`（`exam_process_image`） |
| `backend-fastapi/src/web408/modules/exam/schemas.py` | 查询参数（含 `custom_category`、`has_custom_category`）、创建/更新请求、响应与分页 |
| `backend-fastapi/src/web408/modules/exam/read_service.py` | `ExamReadService`：向 catalog/custom_category/media/adaptation 提供分类引用、计数、来源解析 |
| `backend-fastapi/src/web408/modules/exam/category_tag_service.py` | 大纲分类改名时回写真题标签 |
| `backend-fastapi/src/web408/modules/exam/custom_category_tag_service.py` | 自定义分类改名时回写真题标签 |
| `backend-fastapi/src/web408/modules/exam/process_image_repository.py` / `process_image_read_service.py` | 过程图片持久化与供 media 扫描的只读查询 |
| `backend-fastapi/src/web408/modules/exam/process_image_service.py` | 过程图片上传（复用 `UploadService`）、删除关联、排序 |
| `frontend/src/api/exam.ts` | 真题请求封装（另承载统计/导出接口，见[公共记录](shared.md#混合职责文件)） |
| `frontend/src/api/examProcessImage.ts` | 过程图片请求封装 |
| `frontend/src/types/exam.ts`、`types/examProcessImage.ts` | 领域类型 |
| `frontend/src/views/user/ExamIndex.vue` | 年份入口页，取 `/year-stats` 渲染年份卡片 |
| `frontend/src/views/user/ExamList.vue` | 按年份阅读页：`/nav-index` + `/year/{year}` |
| `frontend/src/views/user/ExamClassify.vue` | 按分类阅读页：科目侧栏 + 分类大纲 + 无限滚动 |
| `frontend/src/views/admin/ExamManage.vue` | 管理表格（筛选、排序、编辑弹窗、删除、出题操作） |
| `frontend/src/components/business/ExamEntryCard.vue` | 真题卡片组合（头部 + 题目内容） |
| `frontend/src/components/business/ExamItemHeader.vue` | 年份/题号/标签/复制/过程图片/管理操作 |
| `frontend/src/components/business/ExamProcessMenu.vue`、`ExamProcessDialog.vue` | 过程图片入口与查看/删除/排序弹窗 |
| `frontend/src/components/business/ExamEditDialog.vue` | 新增/编辑弹窗：JSON 完整导入、仅更新内容、Markdown 编辑、分类与自定义分类选择、AI 答案生成 |

`frontend/src/components/business/ExamQuestionCard.vue` 虽名为 Exam，但被三类题目共用，归[公共记录](shared.md#题目渲染与复制导出共享)的渲染路径；本模块只引用。

## 公共与跨模块引用

| 所属 | 文件与使用范围 | 本模块为何引用 |
| --- | --- | --- |
| [公共记录](shared.md) | `question_content/*`（校验、序列化、解析） | 题目 JSON 字段的读写口径 |
| `catalog` 模块 | `modules/catalog/read_service.py`（科目与分类范围校验）、`models.Subject` | 归属与前导校验 |
| `custom_category` 模块 | `modules/custom_category/read_service.py` | 自定义分类挂载与子树筛选名称集合 |
| `auth` 模块 | `modules/auth/read_service.py`、`auth/dependencies.py` | 作者名填充与管理员校验 |
| `media` 模块 | `modules/media/service.py#UploadService` | 过程图片落盘与删除文件 |
| `reporting` 模块 | `ExamQueryService.list_for_category_stats`、`ExamCategoryQuestionRead` | 统计取数 |
| `ai` 模块 | `ExamQueryService.to_response` / `get_by_id` | 组装题目快照 |
| 前端公共 | `SubjectSidebar`/`MobileQuestionNav`/`CategoryOutline`/`useCategoryOutline`/`useInfiniteQuestionList`/`questionMarkdown` | 阅读页导航、取数与复制（见[公共记录](shared.md#阅读页共享导航共享)） |

被引用方向：`catalog`/`custom_category`（计数与改名回写）、`media`（引用扫描）、`adaptation`（来源解析）、`reporting`（统计取数）、`ai`（题目快照）。

## 关键调用链

按分类阅读：

1. `ExamClassify.vue` mount → `getEnabledCategoryTreeBySubject` 取分类树，`getExamList` 拉分页题目。
2. `POST /api/exam/query` → `ExamQueryService.get_paginated` → `ExamRepository` 组 SQL（分类名 LIKE、科目、题型、难度、关键词、排序）。
3. 结果经 `mapper.to_exam_response` 解 JSON，`utils/examCategoryGrouping.ts` 按树分组，`CategoryOutline` 生成大纲与锚点。
4. 首页一次 `loadAll` 取全量以保证大纲完整；离开页面时 `keepAlive` 保留状态。

过程图片：

1. `ExamProcessMenu` → `POST /{exam_id}/process-images/upload`（管理员）。
2. `ExamProcessImageService.upload_image` 调用 `UploadService` 落盘到 `uploads/images/`，再写 `exam_process_image` 关联与排序。
3. 删除只移除 `exam_process_image` 关联（`delete_image` 不删物理文件，交由未引用清理机制处理）；`reorder` 要求请求的 ID 集合与当前过程图片完全一致，否则拒绝。
4. `media` 的引用扫描通过 `ExamProcessImageReadService.list_for_media_reference` 把过程图片计入「已引用」。

## 状态与数据所有者

| 状态／资源 | 所有者 | 副本或消费者 | 生命周期／持久化 |
| --- | --- | --- | --- |
| 真题记录 | `exam_question` 表 | 分类统计、改编题来源、AI 快照、图片引用扫描 | 数据库持久；`(year, question_number)` 在题号非空时唯一；`subject_id` 置空式删除 |
| 过程图片关联 | `exam_process_image` 表 | 阅读端展示、media 引用扫描 | 与真题级联删除；物理文件独立存在 |
| 分类标签 | `exam_question.category` / `custom_category` | 分类模块统计与改名回写 | 名称数组文本，不落外键 |

## 生命周期与约束

- 写接口与查重接口要求管理员（`get_current_admin`），列表、详情、索引、过程图片查询公开。
- 题目内容与选项在写入前经 `question_content` 校验（题型/内容/选项一致性）；分类值必须属于该科目的分类集合，自定义分类同理。
- 查重接口按年份/题号或来源判定；详情接口不做权限限制。
- `/index` 与 `/nav-index` 是两种索引粒度（完整行 vs 轻量导航项），前端只用 `nav-index`；`/by-category` 与 `/query` 并存，前者返回不分页的完整集合。

## 当前覆盖边界

- 分页查询与索引 SQL 只读到条件拼装结构，未逐条核对全部排序/边界分支。
- 过程图片删除仅删关联行，物理文件留在 `uploads/images/` 直到未引用扫描确认，删除后阅读端不再展示但文件仍可直接访问。
