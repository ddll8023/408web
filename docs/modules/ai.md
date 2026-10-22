# AI 题目咨询

模块标识：`ai`。返回 [项目结构](../项目结构文档.md)。

## 职责与入口

账号级模型服务设置与题目咨询：

- **设置**：内置供应商（OpenCode Go）与账号自建供应商、自定义型号、默认咨询模型与输入模式；API Key 以 Fernet 密文入库，主密钥在系统私有目录。
- **检测**：用户明确确认额度后主动调用一次模型。
- **咨询**：从真题/模拟题/改编题固定文本快照 + 图片创建内存会话，流式回答；**答案生成**（管理员）在编辑弹窗里生成答案草稿，只回填编辑框、不写库。

入口（前缀 `/api/ai`，见 `backend-fastapi/src/web408/modules/ai/router.py`）：`/providers/query|save|delete`、`/custom-providers/save|delete`、`/custom-models/save|delete`、`/models/query`、`/models/check`、`/settings/query|save|delete`、`/sessions/create`、`/answers/sessions/create`（管理员）、`/sessions/{id}/messages`（SSE）、`/sessions/{id}/abort`、`/sessions/{id}/close`。

前端：`views/user/UserCenter.vue` → `components/business/AiSettings.vue`（设置）；`components/business/AiConsultationDialog.vue`（全站唯一客服窗，由 `AppShell.vue` 挂载）；`components/business/AiAnswerGenerationDialog.vue`（三个编辑弹窗内嵌的答案生成）。

不负责：题目数据的读写（只读取快照）、图片文件读取之外的资源访问、任何工具/联网/检索能力（会话系统提示明确禁用）。

## 专属文件

后端业务层 `backend-fastapi/src/web408/modules/ai/`：

| 文件 | 当前用途 |
| --- | --- |
| `router.py` | 全部 HTTP 用例；`ConsultationResponse`（`text/event-stream`）与 `while_connected`（浏览器断开即取消） |
| `service.py` | `AiSettingsService`：供应商凭据、自定义供应商、自定义型号、默认设置的读写与上限（每账号 50 个自定义型号） |
| `model_service.py` | `AiModelService`：目录查询与显式检测编排；网络等待不持有数据库事务 |
| `consultation_service.py` | `AiConsultationService`：会话创建（含答案生成）、发送、停止、关闭的编排与鉴权归属 |
| `question_context.py` | 从三类题目详情构建有界文本快照（Markdown → 文本，登记 `[图 N]` 引用），不读文件 |
| `question_images.py` | 在受控目录内解析并读取本地图片、SVG 内联与超限降级登记 |
| `answer_prompt.py`、`answer_schemas.py` | 答案生成的系统提示与请求/视图模型 |
| `key_cipher.py` | Fernet 加解密 API Key，`KEY_VERSION` 版本标记 |
| `models.py` | `UserAiProviderConfig`、`UserAiCustomModel`、`UserAiConfig` |
| `repository.py` | 上述三表的持久化 |
| `schemas.py`、`session_schemas.py` | 设置/目录/检测与会话/SSE 事件模型 |
| `runtime/manager.py` | `AiRuntime` 门面：目录、检测、会话编排；启动不读凭据不联网 |
| `runtime/session.py` | 内存会话、生成位、停止、修订失效、闲置回收（上限常量集中在此） |
| `runtime/model_factory.py` | 按协议构造 PydanticAI 模型与请求设置；自建 HTTP 客户端（不继承代理、不跟随重定向） |
| `runtime/go_catalog.py` | 内置 OpenCode Go 型号注册表（协议、固定地址、能力、thinking 元数据） |
| `runtime/model_spec.py`、`runtime/errors.py` | 型号规格与公开错误码 |
| `backend-fastapi/src/web408/integrations/ai_local_secrets.py` | 系统私有目录中的主密钥文件读写与权限校验 |

前端：

| 文件 | 当前用途 |
| --- | --- |
| `frontend/src/api/ai.ts` | 设置/目录/检测请求与响应守卫 |
| `frontend/src/api/aiSession.ts` | 会话创建、SSE 流式消费（`fetch` + `ReadableStream`，含帧解析与终态校验）、abort/close |
| `frontend/src/api/aiGuards.ts` | 响应字段的类型守卫（不合法即抛错） |
| `frontend/src/types/aiAnswer.ts` | 答案草稿与来源类型 |
| `frontend/src/utils/aiAnswer.ts` | 回答正文/草稿规范化 |
| `frontend/src/composables/useAiConsultation.ts` | 单次咨询的会话状态机（生成中、终态、错误） |
| `frontend/src/composables/useAiConsultationPanel.ts` | 页面级唯一 AI 窗的协调器：同题恢复、切题先确认、离页释放 |
| `frontend/src/components/business/AiSettings.vue` | 个人模型服务总览（组合下述四个组件） |
| `frontend/src/components/business/AiProviderSettings.vue` | 单供应商标记、凭据保存与检测 |
| `frontend/src/components/business/AiModelPicker.vue` | 模型搜索分页与能力展示 |
| `frontend/src/components/business/AiCustomProviderDialog.vue` | 自建供应商增改（展示名、地址、协议） |
| `frontend/src/components/business/AiCustomModelManager.vue` | 账号自定义型号的维护 |
| `frontend/src/components/business/AiConsultationDialog.vue` | 右下角非模态咨询窗 |
| `frontend/src/components/business/AiAnswerGenerationDialog.vue` | 原答案/生成答案对比，手动开始 |

渲染组件 `AiAnswerViewer.vue`、`AiGeneratedAnswerViewer.vue` 归[公共记录](shared.md#题目渲染与复制导出共享)。

## 公共与跨模块引用

| 所属 | 文件与使用范围 | 本模块为何引用 |
| --- | --- | --- |
| `exam` / `mock` / `adaptation` | 各自 `query_service.py` 的详情读取 | 组装题目快照 |
| `catalog` 模块 | `catalog/read_service.py` | 快照中的科目名 |
| `auth` 模块 | `auth/dependencies.py`（`get_current_user` / `get_current_admin`） | 账号隔离与答案生成鉴权 |
| [公共记录](shared.md) | `api/request.ts` 的 `API_BASE_URL`、`utils/token`、`convertKeys`、`utils/uuid`、基础组件 | 请求与标识 |
| `core/config.py#AiConfig` | 固定运行默认值（超时、快照与图片字节上限） | 不通过环境变量覆盖 |

被引用方向：`AppShell.vue`（挂载客服窗并清理）、三类 `*EditDialog.vue`（答案生成）、三类阅读卡片（打开咨询）。

## 关键调用链

保存凭据：

1. `AiSettings.vue` → `POST /api/ai/providers/save`。
2. `AiSettingsService` 校验后调用 `key_cipher.encrypt_api_key`（主密钥来自 `ai_local_secrets`，首次写入时生成）。
3. 密文与 `revision` 存入 `user_ai_provider_config`；提交后 `AiRuntime.invalidate_revision` 让旧修订在本进程内失效。

创建会话并流式回答：

1. 题目卡片 → `useAiConsultationPanel.openQuestion` → `api/aiSession.ts#createAiSession` → `POST /api/ai/sessions/create`。
2. `AiConsultationService` 用**认证账号**重新读取题目（不信任浏览器提供的内容），`build_question_snapshot` 生成有界文本，`load_question_images` 在受控目录内读图并登记省略原因；随后读取并解密凭据，交给 `AiRuntime.create_session`（此步不调用模型）。
3. `POST /api/ai/sessions/{id}/messages` 返回 SSE：`meta` → 若干 `delta` → `done`；`ConsultationResponse` 在 ASGI 结束时兜底 `aclose()`。
4. 前端逐帧校验 `request_id`，非本请求的增量直接报错；停止走 `POST /abort`（只取消该 `request_id`），离开或切题走 `POST /close`。
5. 浏览器断开时 `while_connected` 取消本次操作，避免继续产生上游费用。

答案生成（管理员）：

1. `*EditDialog.vue` → `AiAnswerGenerationDialog` → `POST /api/ai/answers/sessions/create`（管理员），可带题面草稿。
2. 服务返回含 `answerSource` 的会话视图，前端对比原答案与生成答案；生成结果只回填编辑框，需用户自行保存题目。

## 状态与数据所有者

| 状态／资源 | 所有者 | 副本或消费者 | 生命周期／持久化 |
| --- | --- | --- | --- |
| 个人供应商配置 | `user_ai_provider_config`（每账号每供应商一行，`revision` 标记版本） | 设置页、检测与咨询 | 密文入库；内置供应商的自建字段为空 |
| 自定义型号 | `user_ai_custom_model`（复合外键指向供应商，级联删除） | 模型选择器 | 数据库持久，能力由账号自行声明，服务端不探测 |
| 默认咨询设置 | `user_ai_config`（`input_mode` 限 `text` / `text_image`） | 咨询会话创建 | 每账号一条 |
| 主密钥 | `integrations/ai_local_secrets.py` | `key_cipher.py` | 系统私有目录；缺失即报错，不自动重建覆盖 |
| 咨询会话 | `runtime/session.py`（内存） | 前端 `useAiConsultation` | 不落库；上限每账号 4 / 全局 128 / 每会话 12 轮，闲置 30 分钟回收，进程重启丢失 |
| 修订失效登记 | `runtime/session.py`（`INVALIDATED_LIMIT = 4096`） | 会话与检测校验 | 进程内存，重启清空 |

## 生命周期与约束

- `AiRuntime` 由 `main.py` 的 `lifespan` 创建、`startup()` 只启动回收任务、`aclose()` 停止接收新生成并等有界收尾；不启动独立进程、不监听端口。
- 快照与图片预算固定在 `AiConfig`（超时、题目文本 64 KB、单图 4 MB、单题合计 8 MB、SVG 单独限额），不通过环境变量覆盖。
- 系统提示把题目、参考解析与用户消息都视为待分析资料而非指令，并禁止使用工具、联网或声称验证过代码。
- 自建 HTTP 客户端显式关闭重试、环境代理与重定向跟随，API Key 只进入当前实例。
- 内置目录数据取自 pi-coding-agent 0.99.2 内嵌模型目录，无法再自动生成，新增型号需手工维护 `go_catalog.py`。
- 前端不持久化聊天内容；`AppShell.vue` 在路由或账号变化时清理窗口，防止跨账号显示历史。

## 当前覆盖边界

- `runtime/session.py`（615 行）的生成位、停止与修订失效细节只读到常量与主流程，未逐分支核对。
- 余额/额度确认的具体失败码与用户可见文案以 `runtime/errors.py` 为准，本页未逐条列举。
- 模型检测与咨询都涉及外部网络，未做任何运行时验证；`.env.example` 提到的主密钥备份要求属运维边界。
