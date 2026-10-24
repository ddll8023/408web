# 出题工作台

模块标识：`compose`。返回 [项目结构](../项目结构文档.md)。

## 职责与入口

管理端「出题工作台」：按科目与目录范围挑题、临时编排、预览与批量导出的**前端组合能力**。它没有独立后端模块，取数与写状态全部复用 mock / adaptation / catalog 的既有接口。

入口：`frontend/src/views/admin/QuestionCompose.vue`，路由 `/manage/compose`（`meta.layout: 'admin'`、`requiresAdmin`、`keepAlive`）。

不负责：题目数据的读写规则（[模拟题](mock.md)、[真题改编题](adaptation.md)）、目录树维护（[目录与分类管理](catalog.md)）。工作台只做筛选、编排与导出。

## 专属文件

| 文件 | 当前用途及纳入依据 |
| --- | --- |
| `frontend/src/views/admin/QuestionCompose.vue` | 工作台页面：章节树取范围、筛选（来源/关键词/题型/出题状态/年份）、滚动加载、编排、预览、批量复制 |
| `frontend/src/components/business/QuestionComposeLayout.vue` | 三栏（章节 / 题目 / 出题篮）宽屏布局，窄屏改顶部入口 + 底部抽屉 |
| `frontend/src/components/business/QuestionChapterTree.vue` | 目录树导航（键盘可操作），显示题库总数与已选数量 |
| `frontend/src/components/business/QuestionChapterSection.vue` | 按分组承载题目卡片、分组统计与全选 |
| `frontend/src/components/business/QuestionCard.vue` | 单题卡片：摘要、分类、状态、单题出题菜单、编辑入口 |
| `frontend/src/components/business/QuestionBasket.vue` | 临时出题篮：调整顺序、清空、触发批量复制 |
| `frontend/src/components/business/QuestionBatchCopyMenu.vue` | 按选中顺序合并生成一次 Word 富文本复制 |
| `frontend/src/components/business/QuestionExamActionMenu.vue` | 单题「出题」菜单：与其他页面同构的 Markdown / Word / 图片分组复制，另附一组切换出题状态 |
| `frontend/src/components/business/QuestionPreviewDrawer.vue` | 完整内容预览抽屉 |
| `frontend/src/components/business/QuestionJsonImportPanel.vue` | 编辑弹窗内的 JSON 导入面板（三类题目共用，支持完整导入、仅更新题目内容、仅更新答案） |
| `frontend/src/composables/useQuestionSelection.ts` | 临时选题集合与顺序维护 |

`components/business/QuestionImageRenderer.vue`、`utils/questionCopy.ts` 归[公共记录](shared.md#题目渲染与复制导出共享)，本模块引用；`useAdminTable.ts`、`useInfiniteQuestionList.ts`、`useConfirm.ts`、`useToast.ts` 也归公共记录。

## 公共与跨模块引用

| 所属 | 文件与使用范围 | 本模块为何引用 |
| --- | --- | --- |
| `mock` 模块 | `api/mock.ts#getMockQuestions`、`setMockExamMarks` | 取模拟题、批量改出题状态 |
| `adaptation` 模块 | `api/adaptation.ts#getAdaptationList`、`setAdaptationExamMarks` | 取改编题、批量改出题状态 |
| `catalog` 模块 | `api/category.ts#getEnabledCategoryTreeBySubjectWithStats` | 「章节树」数据源（实为大纲分类树） |
| `mock` / `adaptation` 编辑弹窗 | `MockEditDialog.vue`、`AdaptationEditDialog.vue` | 卡片内直接编辑 |
| [公共记录](shared.md) | `useAdminTable`、`useInfiniteQuestionList`、`useQuestionSelection`、`QuestionImageRenderer`、`questionCopy`、基础组件与单例 | 表格状态、分页、复制与提示 |

## 关键调用链

1. 进入页面 → `useAdminTable` 初始化科目筛选，选科目后 `getEnabledCategoryTreeBySubjectWithStats(subjectId, kind)` 取树（此处 kind 为 mock / adaptation），按需追加「未归档」分组。
2. 选节点 → `useInfiniteQuestionList` 以 `getMockQuestions` 或 `getAdaptationList` 分页加载，两路响应先用 `withQuestionKind` 打标统一成 `QuestionRow`。
3. 勾选题目 → `useQuestionSelection` 维护顺序 → `QuestionBasket` 内调整 → `QuestionBatchCopyMenu` 调用 `utils/questionCopy.ts` 与 `QuestionImageRenderer.vue` 生成 Word 富文本，一次写入剪贴板。
4. 单题操作 → `QuestionExamActionMenu` 复用 `QuestionCopyMenu` 面板：Markdown 复制内联调用 `utils/questionMarkdown.ts`，PNG 与 Word 分别走 `html-to-image` 与同一隐藏渲染器；完整内容复制成功后组件派发 `content-copied`，页面据此自动标记已出题；出题状态切换调用单个 `POST /exam-mark`，批量 `/exam-mark/batch`。

## 状态与数据所有者

| 状态／资源 | 所有者 | 副本或消费者 | 生命周期／持久化 |
| --- | --- | --- | --- |
| 出题篮选题 | `composables/useQuestionSelection.ts`（页面内） | `QuestionBasket`、`QuestionBatchCopyMenu` | 仅内存，离页即丢 |
| 筛选条件 | `composables/useAdminTable.ts` + 页面局部 ref | 表格与分页请求 | 内存；路由 `keepAlive` 保留 |
| 出题状态 | 后端 `mock_question_exam_mark` / `adaptation_question_exam_mark` | 工作台筛选、管理页 | 数据库持久，本模块只切换不定义规则 |

## 生命周期与约束

- 工作台只处理模拟题与改编题，真题不参与出题编排。
- 「章节」在本页指大纲分类树，而不是 `/api/chapter` 的 `Chapter` 表；术语与实现不一致，读代码时以实际接口为准。
- 批量复制依赖 `QuestionImageRenderer` 的隐藏渲染，公式、代码与图片处理规则与单题复制共用，避免两套输出。
- 页面在 `keepAlive` 下保留筛选与选中项；离页不清理出题篮。

## 当前覆盖边界

- `QuestionCompose.vue`（1455 行）的筛选联动、滚动加载与批量操作分支只读主流程，未逐条核对边界。
- 导出的 Markdown/Word/PNG 结果均未做运行时验证；兼容性取决于浏览器与 Word 实现。
