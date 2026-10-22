# 模拟题

模块标识：`mock`。返回 [项目结构](../项目结构文档.md)。

## 职责与入口

模拟题的浏览、筛选与维护，以及两个独立的状态维度：**出题标记**与**答错次数**（都在独立表中，不修改题目主体）。

入口（前缀 `/api/mock`，见 `backend-fastapi/src/web408/modules/mock/router.py`）：

- 读：`POST /query`、`/source/{source}`、`/source-stats`、`/sources`、`/categories/{subject_id}`、`/category-stats/{subject_id}`、`/subject-stats`、`/titles/{source}`、`/{mock_id}/detail`、`/check-duplicate`（管理员）
- 写：`POST /api/mock`、`/{mock_id}`、`/{mock_id}/delete`、`/{mock_id}/exam-mark`、`/exam-mark/batch`（管理员）；`/{mock_id}/wrong-count`（记录答错，**当前无鉴权依赖**）、`/{mock_id}/wrong-count/set`（管理员调整）
- 前端：`views/user/MockClassify.vue`（阅读/作答）、`views/admin/MockManage.vue`（管理）、`views/admin/CategoryManage.vue`（未归档模拟题标签提示，读本模块统计）。

不负责：真题（[真题](exam.md)）、改编题（[真题改编题](adaptation.md)）、出题工作台的编排（[出题工作台](compose.md)）。

## 专属文件

| 文件 | 当前用途及纳入依据 |
| --- | --- |
| `backend-fastapi/src/web408/modules/mock/router.py` | 全部模拟题 HTTP 用例 |
| `backend-fastapi/src/web408/modules/mock/query_service.py` | 分页查询、详情、来源/科目/分类统计、按来源取标题、图片引用文本 |
| `backend-fastapi/src/web408/modules/mock/command_service.py` | 创建/更新/删除、出题标记（单个与批量）、答错计数（记录与设定） |
| `backend-fastapi/src/web408/modules/mock/repository.py` | 条件拼装、分页、按来源/标题检索、计数表读写 |
| `backend-fastapi/src/web408/modules/mock/mapper.py` | 实体 → `MockResponse` |
| `backend-fastapi/src/web408/modules/mock/models.py` | `MockQuestion`、`MockQuestionExamMark`、`MockQuestionWrongCount` |
| `backend-fastapi/src/web408/modules/mock/schemas.py` | 查询参数、创建/更新请求、统计响应、出题与计数请求响应 |
| `backend-fastapi/src/web408/modules/mock/read_service.py` | `MockReadService`：向 catalog 提供分类引用与引用计数 |
| `backend-fastapi/src/web408/modules/mock/category_tag_service.py` | 大纲分类改名时回写模拟题标签 |
| `frontend/src/api/mock.ts` | 请求封装 |
| `frontend/src/types/mock.ts` | 领域类型 |
| `frontend/src/constants/exam.ts` | 难度标签与样式（三类题目共用，登记在公共记录） |
| `frontend/src/views/user/MockClassify.vue` | 分类阅读 + 选择题作答反馈；答错时静默调用记录接口 |
| `frontend/src/views/admin/MockManage.vue` | 管理表格：筛选、出题状态、答错次数调整、编辑、删除 |
| `frontend/src/components/business/MockEntryCard.vue`、`MockItemHeader.vue` | 阅读端卡片与头部（来源、标题、题号、难度、复制/出题操作） |
| `frontend/src/components/business/MockEditDialog.vue` | 新增/编辑弹窗（来源联动、标题候选、JSON 导入、Markdown 编辑） |

## 公共与跨模块引用

| 所属 | 文件与使用范围 | 本模块为何引用 |
| --- | --- | --- |
| [公共记录](shared.md) | `question_content/*`、`constants/exam.ts`、`ExamQuestionCard.vue` | 题目字段口径、难度展示、统一渲染 |
| `catalog` 模块 | `catalog/read_service.py`、`models.Subject` | 科目与分类校验 |
| `auth` 模块 | `auth/read_service.py`、`auth/dependencies.py` | 作者名、管理员校验 |
| `compose` 模块（前端） | `QuestionExamActionMenu.vue`（复制到 Word / PNG 导出 / 出题状态） | 管理页复用的出题操作菜单 |

被引用方向：`catalog`（分类计数与改名回写、未归档标签）、`media`（引用扫描）、`ai`（题目快照）、`compose`（工作台取题与批量复制）。

## 关键调用链

阅读作答与答错计数：

1. `MockClassify.vue` 拉 `/api/mock/query` 渲染题目，选择题作答后由页面判定正误。
2. 答错时静默 `POST /api/mock/{id}/wrong-count`（失败只记控制台，不影响反馈）。
3. `MockCommandService.record_wrong_answer` 校验题目存在 → `increment_wrong_count` → `commit`，返回最新计数。
4. 计数不在学习页面展示，只在 `MockManage.vue` 中可见/可改。

出题标记：

1. `MockManage.vue` 或出题工作台 → `POST /{id}/exam-mark` 或 `/exam-mark/batch`。
2. `MockCommandService.set_exam_mark(s)` 在 `mock_question_exam_mark` 上按「一题一记录 + 唯一约束」插入或删除，`commit` 后返回题目或批量结果。

## 状态与数据所有者

| 状态／资源 | 所有者 | 副本或消费者 | 生命周期／持久化 |
| --- | --- | --- | --- |
| 模拟题记录 | `mock_question` 表 | 工作台、统计、AI 快照 | 数据库持久；`(source, title, question_number)` 唯一（title 与题号均非空时） |
| 出题标记 | `mock_question_exam_mark`（题号唯一 + 级联删除） | 管理页与工作台的「出题状态」筛选 | 独立表，不改题目主体 |
| 答错次数 | `mock_question_wrong_count`（唯一 + `>= 0` 检查 + 级联删除） | 管理页展示与调整 | 独立表；计数只增不改题目 |
| 分类标签 | `mock_question.category` | catalog 统计、改名回写 | 名称数组文本 |

## 生命周期与约束

- 出题状态与答错次数都刻意拆表，避免状态写入与题目更新互相干扰。
- `POST /api/mock/{id}/wrong-count` 没有 `get_current_admin` 或 `get_current_user` 依赖：任何能访问接口的调用方都能给任意题目加计数。同名 `set` 接口则要求管理员。这是当前实现的事实边界，若要收紧需改路由。
- 来源与标题是自由文本，标题候选来自 `get_titles_by_source`；查重依赖来源 + 标题 + 题号组合。

## 当前覆盖边界

- 答错计数的用途（是否影响排序或统计）只在管理页展示层面确认，未追踪到统计口径。
- 答错递增使用 SQLite 的 `INSERT ... ON CONFLICT DO UPDATE SET wrong_count = wrong_count + 1`，在单条语句内完成，不先读后写。
