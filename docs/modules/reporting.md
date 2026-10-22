# 统计与导出

模块标识：`reporting`。返回 [项目结构](../项目结构文档.md)。

## 职责与入口

按科目统计**真题分类分布**并导出为 Markdown / Excel：章级权重带数据（章号、科目占比、选择题/主观题双段）、两层分类明细、未归档统计与无效数据告警。

入口：

- 后端 `backend-fastapi/src/web408/modules/reporting/router.py`，挂在 `/api/exam` 前缀下：
  - `POST /api/exam/category-stats`（公开）
  - `POST /api/exam/export-category-stats`（管理员，返回附件流）
- 前端 `frontend/src/views/admin/ExamCategoryStats.vue`（路由 `/manage/exam-category`）；请求经 `frontend/src/api/exam.ts#getExamCategoryStats` 与 `exportExamCategoryStats`（该文件属混合职责，见[公共记录](shared.md#混合职责文件)）。

不负责：分类树维护（[目录与分类管理](catalog.md)）、真题数据本身（[真题](exam.md)）。本模块只读题目与分类，不写库。

## 专属文件

| 文件 | 当前用途及纳入依据 |
| --- | --- |
| `backend-fastapi/src/web408/modules/reporting/router.py` | 两个 HTTP 用例；导出设置 `Content-Disposition` 与 `Cache-Control: no-store` |
| `backend-fastapi/src/web408/modules/reporting/service.py` | `ReportingService.get_category_stats` / `export_category_stats`：按科目归集题目、构建科目级与分类级统计 |
| `backend-fastapi/src/web408/modules/reporting/exam_category_stats.py` | 纯计算：`build_subject_category_stats`、`CategoryStatsNode`、`QuestionStats`，含无效分类数据的 `invalid_question_ids` |
| `backend-fastapi/src/web408/modules/reporting/exporters.py` | `ReportingExporter`：Markdown 与手写 xlsx（`zipfile` + XML，无第三方依赖） |
| `backend-fastapi/src/web408/modules/reporting/schemas.py` | 请求（含 `format: markdown \| xlsx`）、统计响应树、导出结果 |
| `frontend/src/views/admin/ExamCategoryStats.vue` | 统计页面：科目筛选、章级权重带、两层明细、排序与折叠、导出菜单 |

## 公共与跨模块引用

| 所属 | 文件与使用范围 | 本模块为何引用 |
| --- | --- | --- |
| `exam` 模块 | `ExamQueryService.list_for_category_stats`、`ExamCategoryQuestionRead` | 取全部真题的分类与题型 |
| `catalog` 模块 | `CatalogReadService.list_subjects` / `list_categories`、`CatalogCategoryRead` | 科目顺序与分类树基准 |
| [公共记录](shared.md) | `frontend/src/api/exam.ts` 的统计/导出函数、基础组件与 `utils/toast` | 前端请求与展示 |

被引用方向：仅前端页面与 `api/exam.ts`。

## 关键调用链

查询统计：

1. `ExamCategoryStats.vue` 选科目 → `POST /api/exam/category-stats`。
2. `ReportingService.get_category_stats` 取题目（按 `subject_id` 过滤时可只取一科）、科目列表、分类列表。
3. 题目按 `subject_id` 分组 → `build_subject_category_stats` 按分类树归并出 `categorized`、`categories`、`invalid_question_ids`。
4. 汇总成扁平统计 + 树形统计（`ExamCategoryStatsResponse`），页面渲染权重带与明细行。

导出：

1. 页面导出菜单 → `POST /api/exam/export-category-stats`（带 `format`）。
2. `ReportingService.export_category_stats` 复用同一份统计 → `ReportingExporter` 生成 `BytesIO`。
3. 导出**不再输出范围文案列**，层级只用名称前缩进表达；列数变化属对外破坏性变更。

## 状态与数据所有者

| 状态／资源 | 所有者 | 副本或消费者 | 生命周期／持久化 |
| --- | --- | --- | --- |
| 统计结果 | 每次请求即时计算（`reporting/service.py`） | 页面；导出文件 | 不落库、不缓存 |
| 导出文件 | 请求内生成后直接返回字节流 | 前端 `requestBlob` 下载 | 不写磁盘 |

## 生命周期与约束

- 页面与导出必须同一口径：改页面明细表达时同步 `exporters.py`，两者不一致会让用户拿到与页面说法不同的文件。既有约定与已否决方案见 `.agents/memory/topics/conventions/exam-category-stats.md`（项目记忆，不在此复制）。
- 分类名无效（指向不存在的分类）的题目不会静默丢弃：服务层记录 `logger.warning("跳过无效真题分类数据: question_id=...")` 并在响应中带出 `invalid_question_ids`。
- 导出为管理员接口；查询接口公开。

## 当前覆盖边界

- 统计页 1243 行的展示逻辑（权重带缩放、窄屏降级、章号稳定性）只读结构与注释，未逐段核对。
- 导出 xlsx 为手写 OOXML 包，格式兼容性未做运行时验证。
