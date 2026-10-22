# 公共记录

本页集中登记共享能力、混合职责与全局上下文。源码路径相对仓库根；各模块引用本页，不重复认领这些文件。返回 [项目结构](../项目结构文档.md)。

## 题目内容数据契约（共享）

三类题目（真题、模拟题、改编题）共用同一套选项模型、内容校验与 JSON 文本序列化。

| 文件 | 共同职责 | 已知消费者与用途 |
| --- | --- | --- |
| `backend-fastapi/src/web408/modules/question_content/schemas.py` | `QuestionOptions` 及题目载荷校验（题型与内容/选项一致性） | exam、mock、adaptation 的 `schemas.py`；`ai/answer_schemas.py`（草稿校验） |
| `backend-fastapi/src/web408/modules/question_content/serialization.py` | `serialize_options`、`serialize_categories`、`parse_options`、`parse_categories`、`replace_category_name` | exam/mock/adaptation 的 `mapper.py` 与命令服务读取；catalog、custom_category 的分类统计与改名回写 |
| `backend-fastapi/src/web408/modules/question_content/validation.py` | `validate_question_values`：把纯数据校验错误转成 `ValidationException` | exam、mock、adaptation 的 Command Service |

边界：本记录只管「题目 JSON 字段的读写口径」，不拥有任何表、不提交事务、不涉及 HTTP。`category` / `custom_category` 以**名称数组**存于文本列，是三类题目一致的既有约定；转换成 ID 或拆关联表不在当前实现范围内。

同一组口径的人工约定见 `.agents/memory/topics/conventions/custom-category-tags.md`（项目记忆，不在此复制）。

## 题目渲染与复制导出（共享）

把题目与答案安全地渲染成页面、图片与 Word 富文本。三条渲染路径使用**各自独立**的 Markdown/XSS 策略，互不复用白名单：

| 文件 | 共同职责 | 已知消费者与用途 |
| --- | --- | --- |
| `frontend/src/components/basic/MarkdownViewer.vue` | 题目正文渲染（v-md preview + KaTeX）、点击插图全屏、`resizable` 时正文大图可拖拽调尺寸 | `ExamQuestionCard.vue`、`QuestionImageRenderer.vue`、`QuestionPreviewDrawer.vue` |
| `frontend/src/components/basic/MarkdownEditor.vue` | 编辑 + 预览 + 公式 + 图片上传（保存相对路径）、单栏/双栏与同步滚动 | 三类题目的 `*EditDialog.vue` |
| `frontend/src/components/basic/AiAnswerViewer.vue` | AI 回答渲染：独立 MarkdownIt 关原始 HTML、独立 XSS 白名单（不含 svg/img/iframe/style） | `AiConsultationDialog.vue`、`AiGeneratedAnswerViewer.vue` |
| `frontend/src/components/basic/AiGeneratedAnswerViewer.vue` | 生成答案预览，为独立 SVG 代码块开放受限图形 | `AiAnswerGenerationDialog.vue` |
| `frontend/src/utils/questionMarkdown.ts` | 三类阅读页共用的 Markdown 复制拼装与剪贴板降级 | `ExamList.vue`、`ExamClassify.vue`、`MockClassify.vue`、`AdaptationClassify.vue`、`CustomCategoryClassify.vue` |
| `frontend/src/utils/questionOptions.ts` | 选项解析与 A–D 文本化 | `questionMarkdown.ts`、`utils/aiAnswer.ts`、`QuestionImageRenderer.vue`、`QuestionPreviewDrawer.vue` |
| `frontend/src/utils/questionCopy.ts` | 复制范围类型（题干/选项/答案/完整）、富文本内容构造 | `QuestionCopyMenu.vue`、`QuestionBatchCopyMenu.vue`、`QuestionCard.vue`、`QuestionChapterSection.vue`、`QuestionExamActionMenu.vue`、`QuestionImageRenderer.vue`、`QuestionCompose.vue` |
| `frontend/src/components/business/QuestionImageRenderer.vue` | 隐藏渲染器：为 Word / PNG / 富文本复制准备隔离的 Markdown 内容 | `QuestionCopyMenu.vue`、`QuestionBatchCopyMenu.vue` |
| `frontend/src/utils/markdownMedia.ts` | 图片地址归一与尺寸样式（页面渲染与复制共用） | `MarkdownEditor.vue`、`MarkdownViewer.vue`、`QuestionImageRenderer.vue` |
| `frontend/src/utils/markdownSourceMapping.ts` | Markdown 源位置与渲染块映射（双栏同步滚动用） | `MarkdownEditor.vue`、`MarkdownViewer.vue`、`useMarkdownScrollSync.ts` |
| `frontend/src/composables/useMarkdownScrollSync.ts` | 编辑器与预览的滚动同步 | `MarkdownEditor.vue` |
| `frontend/src/composables/useMarkdownMediaResize.ts` | 正文大图拖拽缩放，尺寸按图片地址存 `localStorage` | `MarkdownViewer.vue` |
| `frontend/src/utils/aiAnswer.ts` | AI 回答正文与草稿的规范化/解析，供生成答案回填编辑框 | 三类 `*EditDialog.vue`、`AiAnswerGenerationDialog.vue`、五个阅读页 |
| `frontend/src/types/aiAnswer.ts` | 答案草稿与来源的领域类型 | 同上 |

边界：这些是渲染与导出能力，不拥有题目数据；复制不写库，问答内容不持久化。

## 基础组件库、样式与请求传输（共享）

| 文件 | 共同职责 | 已知消费者与用途 |
| --- | --- | --- |
| `frontend/src/components/basic/*.vue`（30 个） | 无业务语义的按钮、表单、弹层、表格、展示组件；清单与用途见 `frontend/src/components/组件列表文档.md` | 全部页面与业务组件 |
| `frontend/src/components/basic/types.ts` | 公共选项、级联、表格排序等类型 | 基础组件与 `useAdminTable.ts` |
| `frontend/src/components/basic/config/xssWhitelist.ts` | 题目区共用的 XSS 白名单 | `MarkdownViewer.vue`、`MarkdownEditor.vue` 等题目渲染路径 |
| `frontend/src/styles/tailwind.css`、`dropdown.css`、`edit-form.css`、`fullscreen-question.css` | 主题变量、语义色、公共下拉视觉基座、编辑表单与全屏题目样式 | `main.ts` 全局引入 + 各组件类名 |
| `frontend/src/shared/responsive/breakpoints.ts`、`useViewport.ts` | 统一断点（420/640/768/1024/1280）与媒体查询组合式 | `ResponsiveDialog.vue`、`BottomSheet.vue`、`CategoryManage.vue`、`CustomCategoryManage.vue`、`QuestionComposeLayout.vue`、`MobileQuestionNav.vue` |
| `frontend/src/api/request.ts` | axios 实例、Bearer 注入、信封校验、camelCase 转换、401/403/404/500 统一提示、`requestBlob` | 所有 `api/*.ts`；`aiSession.ts` 复用其 `API_BASE_URL` |
| `frontend/src/utils/convertKeys.ts` | snake_case ↔ camelCase 字段转换 | 所有 `api/*.ts`、`ai.ts`、`aiSession.ts` |
| `frontend/src/utils/toast.ts` + `components/basic/Toast.vue` | 全局轻提示单例 | `request.ts`、`useToast.ts`、多个页面与业务组件 |
| `frontend/src/utils/confirm.ts` + `components/basic/Confirm.vue` | 全局确认/警告弹窗单例（独立 `createApp` 挂载） | `useConfirm.ts`、`useJsonImport.ts`、`ExamClassify.vue`、`ExamList.vue` |
| `frontend/src/composables/useToast.ts`、`useConfirm.ts` | 上述两个单例的薄封装 | 多数页面与业务组件 |
| `frontend/src/utils/uuid.ts` | 生成 AI 请求标识 | `api/aiSession.ts`、`AiProviderSettings.vue` |
| `frontend/src/utils/format.ts` | 时间等展示格式化 | `QuestionCard.vue`、`useAdminTable.ts` |
| `frontend/src/utils/errors.ts` | 错误消息提取 | `Login.vue`、`Register.vue`、`MockClassify.vue` |
| `frontend/src/stores/subjects.ts` | 科目选项与 ID→名称映射的全局缓存（挂载后预加载） | `main.ts`、`useSubjects.ts` |
| `frontend/src/composables/useSubjects.ts` | `stores/subjects` 的封装 | **当前无消费者**（页面直接使用 store 或 `useAdminTable`），保留并在结构上标记为未使用 |
| `frontend/src/composables/useAdminTable.ts` | 管理端表格的筛选、分页、排序、科目加载与难度文本 | `ExamManage.vue`、`MockManage.vue`、`AdaptationManage.vue`、`QuestionCompose.vue` |
| `frontend/src/composables/useInfiniteQuestionList.ts` | 分页增量加载 + 请求竞态保护 + `loadAll` 全量取数 | 三类分类阅读页、`QuestionCompose.vue` |
| `frontend/src/types/common.ts` | `ApiResponse`、分页与通用展示类型 | 全前端 |
| `frontend/src/constants/exam.ts` | 难度标签与样式映射 | 三类题目卡片头部、`QuestionCard.vue`、`QuestionImageRenderer.vue`、`useAdminTable.ts`、`MockClassify.vue` |

边界：`components/basic/` 不引用 `components/business/`（`ResponsiveDialog` 只组合 `Dialog` 与 `BottomSheet`）；`Toast.vue`、`Confirm.vue`、`Dialog.vue`、`InputSelect.vue` 目前仅通过各自的 `utils/` 单例或 `ResponsiveDialog`/`MockEditDialog` 间接使用。

## 全站外壳、导航与路由（全局上下文）

| 文件 | 全局作用 | 相关模块需要读取的范围 |
| --- | --- | --- |
| `frontend/src/main.ts` | 创建应用、注册 Pinia/Router、全量注册 FontAwesome 图标、引入全局样式、挂载后预加载科目 | 新增图标必须在此 `library.add`，否则 `font-awesome-icon` 渲染为空 |
| `frontend/src/App.vue` | 只渲染 `AppShell` | — |
| `frontend/src/app/layouts/AppShell.vue` | 导航显示、按 `route.meta.layout` 选布局、按 `keepAlive` 包裹路由视图、内置 `AiConsultationDialog`、路由或账号变化时清理 AI 窗 | 页面级 AI 状态应在离页/换账号时释放 |
| `frontend/src/app/layouts/AdminLayout.vue` | 管理端页面外壳 | 管理页由 `meta.layout: 'admin'` 进入 |
| `frontend/src/app/layouts/ReadingLayout.vue` | 阅读页骨架：`#wide-nav` 插槽 + 滚动内容容器 + `content-ready` 事件 | 阅读页滚动容器与大纲高亮依赖该事件 |
| `frontend/src/router/index.ts` | 路由表、`RouteMeta` 声明（`requiresAuth`/`requiresAdmin`/`keepAlive`/`layout`）、`beforeEach` 权限守卫 | 新增页面需在此登记，管理页加 `requiresAdmin` |
| `frontend/src/components/business/Navigation.vue`（+`NavigationDesktop`、`NavigationMobile`） | 全站导航：搜索、主菜单、管理入口、用户操作，宽/窄屏两套呈现 | 通过 `composables/useNavigation.ts` 取路由动作 |
| `frontend/src/composables/useNavigation.ts` | 导航项定义与跳转逻辑 | 三个导航组件 |
| `frontend/src/utils/token.ts`、`utils/storage.ts` | `localStorage` 读写 Token 与用户信息；`storage.ts` 负责把外部输入解析成可信 `UserInfo` | 登录态只能通过 `stores/auth.ts` 变更 |

## 阅读页共享导航（共享）

| 文件 | 共同职责 | 已知消费者与用途 |
| --- | --- | --- |
| `frontend/src/components/business/SubjectSidebar.vue`、`SubjectNavList.vue`、`CategoryTreeItem.vue` | 桌面端科目/分类侧栏（可折叠、可展开、当前分类高亮），与 `ReadingLayout` 的 `#wide-nav` 插槽配合 | `ExamClassify.vue`、`MockClassify.vue`、`AdaptationClassify.vue`、`CustomCategoryClassify.vue` |
| `frontend/src/components/business/YearNav.vue`、`YearNavList.vue` | 桌面端年份侧栏 | `ExamList.vue` |
| `frontend/src/components/business/MobileQuestionNav.vue` | 窄屏吸顶目录入口 + 底部抽屉，内容由页面通过 `#nav` 插槽注入，并展示本页分组锚点 | 上述五个阅读页 |
| `frontend/src/components/business/CategoryOutline.vue`、`CategorySectionHeader.vue` | 桌面端分类大纲、分组标题与题量 | 同上 |
| `frontend/src/composables/useCategoryOutline.ts` | 大纲激活态、滚动观察与页内跳转 | 五个阅读页 |
| `frontend/src/utils/examCategoryGrouping.ts` | 按分类树顺序分组取题并生成锚点 | 五个阅读页、`SubjectNavList.vue` |

边界：这些组件只负责导航与分组展示，不发起取数请求；数据由页面传给它们。

## 混合职责文件

| 文件 | 承载的多重职责 | 相关模块 |
| --- | --- | --- |
| `frontend/src/api/exam.ts` | 真题读写（`/api/exam/*`）**与**分类统计查询/导出（`/api/exam/category-stats`、`/api/exam/export-category-stats`，后端实现在 reporting） | [真题](exam.md)、[统计与导出](reporting.md) |
| `frontend/src/views/user/UserCenter.vue` | 账号信息展示、本地收藏管理、个人 AI 设置入口 | [认证与账号](auth.md)、[AI 题目咨询](ai.md) |
| `frontend/src/views/admin/ExamCategoryStats.vue` | 统计页面渲染 + 导出触发（列表/排序/折叠属统计只看） | [统计与导出](reporting.md) |
| `backend-fastapi/src/web408/modules/exam/process_image_service.py` | 过程图片关联管理 + 复用 `media` 的 `UploadService` 落盘 | [真题](exam.md)、[图片资源](media.md) |
| `backend-fastapi/src/web408/modules/reporting/router.py` | 挂在 `/api/exam` 前缀下，与 exam 模块共享 URL 空间 | [统计与导出](reporting.md) |
| `frontend/src/views/admin/QuestionCompose.vue` | 「章节树」实际使用大纲分类树接口，不调用 `/api/chapter` | [出题工作台](compose.md)、[目录与分类管理](catalog.md) |

## 共同数据与资源边界

| 数据／资源 | 定义与维护者 | 实际访问者 | 约束 |
| --- | --- | --- | --- |
| `ApiResponse{code,message,data}` 信封 | `backend-fastapi/src/web408/schemas/common.py`；前端 `frontend/src/types/common.ts` + `api/request.ts` | 全部接口与请求封装 | 非 200 `code` 在拦截器内抛错并提示；blob 下载绕过信封 |
| `uploads/images/` 物理文件 | `UploadService` 写入、`LocalFileStorage` 落盘 | 题目 Markdown、真题过程图片、`ImageManage.vue` | 三类来源共用同一目录，引用判定靠文本扫描文件名 |
| JWT 载荷 | `core/security.py`（`sub` = 用户 ID，无过期） | 前端 `utils/token.ts`；后端 `auth/dependencies.py` | 角色与启用状态每次以数据库为准 |

## 关系覆盖边界

消费者清单来自对 `frontend/src` 全量 grep 与后端 `import` 静态分析，覆盖范围为本仓库源码。动态加载（路由懒加载组件、`keep-alive` 缓存实例）、构建期注入与仓库外的使用方不在静态关系内；组件清单的完整性以 `frontend/src/components/组件列表文档.md` 为准。
