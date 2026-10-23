# 真题改编题

模块标识：`adaptation`。返回 [项目结构](../项目结构文档.md)。

## 职责与入口

维护独立的改编题库：一道改编题可关联**多道、跨年份**的真题来源（年份 + 题号），提供来源解析状态、来源占用/查重提示，并按科目与分类浏览阅读。

入口（前缀 `/api/adaptation`，见 `backend-fastapi/src/web408/modules/adaptation/router.py`）：

- 读：`POST /query`、`/categories/{subject_id}`、`/check-source-usage`、`/source-lookup`、`/{adaptation_id}/detail`
- 写（管理员）：`POST /api/adaptation`、`/{adaptation_id}`、`/{adaptation_id}/delete`、`/{adaptation_id}/exam-mark`、`/exam-mark/batch`
- 前端：`views/user/AdaptationClassify.vue`（阅读）、`views/admin/AdaptationManage.vue`（管理）；真题页面通过 `AdaptationRelatedDialog.vue` 反向展示「该真题被哪些改编题引用」。

不负责：真题本身（[真题](exam.md)）；分类树（[目录与分类管理](catalog.md)）。

## 专属文件

| 文件 | 当前用途及纳入依据 |
| --- | --- |
| `backend-fastapi/src/web408/modules/adaptation/router.py` | HTTP 用例 |
| `backend-fastapi/src/web408/modules/adaptation/query_service.py` | 分页查询、详情（含来源与占用信息）、来源解析、分类列表、图片引用文本 |
| `backend-fastapi/src/web408/modules/adaptation/command_service.py` | 创建/更新/删除、来源替换与规范化、出题标记（单个与批量） |
| `backend-fastapi/src/web408/modules/adaptation/repository.py` | 条件拼装、来源表读写、复用来源检测 |
| `backend-fastapi/src/web408/modules/adaptation/mapper.py` | 实体 → 响应 |
| `backend-fastapi/src/web408/modules/adaptation/models.py` | `AdaptationQuestion`、`AdaptationSource`、`AdaptationQuestionExamMark` |
| `backend-fastapi/src/web408/modules/adaptation/schemas.py` | 查询参数、来源引用、创建/更新、出题请求与响应 |
| `backend-fastapi/src/web408/modules/adaptation/read_service.py` | `AdaptationReadService`：向 catalog 提供分类引用与计数 |
| `backend-fastapi/src/web408/modules/adaptation/category_tag_service.py` | 大纲分类改名时回写改编题标签 |
| `frontend/src/api/adaptation.ts` | 请求封装 |
| `frontend/src/types/adaptation.ts` | 领域类型 |
| `frontend/src/views/user/AdaptationClassify.vue` | 分类阅读页（含表格/答案显隐、新标签页定位） |
| `frontend/src/views/admin/AdaptationManage.vue` | 管理表格：来源筛选、解析状态、编辑、删除、出题操作 |
| `frontend/src/components/business/AdaptationEditDialog.vue` | 新增/编辑弹窗（来源维护 + JSON 导入、仅更新内容、仅更新答案 + AI 答案生成） |
| `frontend/src/components/business/AdaptationSourceEditor.vue` | 年份/题号/小问来源编辑与即时解析 |
| `frontend/src/components/business/AdaptationSourceDialog.vue` | 查看改编题关联的来源真题 |
| `frontend/src/components/business/AdaptationRelatedDialog.vue` | 在真题页面查看关联改编题并新标签页打开定位 |
| `frontend/src/components/business/AdaptationEntryCard.vue`、`AdaptationItemHeader.vue` | 阅读端卡片与头部 |

## 公共与跨模块引用

| 所属 | 文件与使用范围 | 本模块为何引用 |
| --- | --- | --- |
| [公共记录](shared.md) | `question_content/*`、`ExamQuestionCard.vue` | 题目字段口径与统一渲染 |
| `catalog` 模块 | `catalog/read_service.py` | 科目/分类校验 |
| `exam` 模块 | `exam/read_service.py#resolve_sources`（`ExamSourceRead`）、`exam/query_service.py` | 来源解析为真题 ID 与详情 |
| `auth` 模块 | `auth/read_service.py`、`auth/dependencies.py` | 作者名、管理员校验 |

被引用方向：`catalog`（分类计数与改名回写）、`media`（引用扫描）、`ai`（快照）、`exam` 前端（关联改编题弹窗）。

## 关键调用链

来源解析与占用提示：

1. `AdaptationSourceEditor.vue` 编辑年份/题号 → 打开或保存时调用 `POST /api/adaptation/source-lookup`。
2. `AdaptationQueryService.lookup_sources` 通过 `ExamReadService.resolve_sources` 查出命中的真题，`_find_reused_sources` 标记已被其他改编题占用的来源。
3. 保存时 `CommandService._replace_sources` 先删除旧来源行再按规范化后的集合重建，`exam_question_id` 存解析命中的真题 ID（未命中为 `NULL`）。

删除与级联：

1. 删除改编题 → `adaptation_source` 行随外键 `CASCADE` 一起消失。
2. 真题被删除时 `adaptation_source.exam_question_id` 置 `NULL`（`SET NULL`），改编题本身保留，来源退化为「仅年份 + 题号」。

## 状态与数据所有者

| 状态／资源 | 所有者 | 副本或消费者 | 生命周期／持久化 |
| --- | --- | --- | --- |
| 改编题记录 | `adaptation_question` 表 | 阅读页、AI 快照 | 数据库持久；无年份/题号唯一约束（非真题） |
| 来源引用 | `adaptation_source`（`adaptation_id + source_year + source_question_number` 唯一） | 真题页面的关联列表、查重 | 与改编题级联；`exam_question_id` 可为空 |
| 出题标记 | `adaptation_question_exam_mark` | 管理页与工作台 | 独立表 + 题号唯一 + 级联 |
| 分类标签 | `adaptation_question.category` | catalog 统计与改名回写 | 名称数组文本 |

## 生命周期与约束

- 来源是「年份 + 题号」的弱引用，解析结果可失效，因此每次编辑都重新解析并用 `sourceState` 表达命中/未命中/被占用。
- 写接口均要求管理员；读接口公开。
- 改编题没有年份，因此真题的唯一索引不适用于此表。

## 当前覆盖边界

- 来源解析的匹配键是「年份 + 题号」，通过 `ExamReadService.resolve_sources` 批量查真题；同一真题可被多道改编题共用，不构成唯一性冲突。
- 前端「新标签页定位」依赖 URL 与滚动逻辑，未做运行时验证。
